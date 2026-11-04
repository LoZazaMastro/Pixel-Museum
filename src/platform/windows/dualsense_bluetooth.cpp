// SPDX-License-Identifier: GPL-3.0-or-later
#include "platform/windows/dualsense_bluetooth.hpp"
#include "audio/controller_feedback.hpp"
#include "platform/windows/dualsense_haptic_pcm.hpp"
#include "platform/ps5/system.hpp"
#include <SDL3/SDL_timer.h>
#include <windows.h>
#include <hidsdi.h>
#include <hidpi.h>
#include <algorithm>
#include <array>
#include <cmath>
#include <cstdint>
#include <memory>
#include <string_view>

namespace museum::desktop {
namespace {
constexpr DWORD write_bytes=547;
constexpr unsigned report_bytes=142;
constexpr unsigned haptic_frames=dualsense_haptic_frames;
constexpr unsigned haptic_payload_bytes=dualsense_haptic_payload_bytes;
constexpr Uint64 tick_ns=SDL_NS_PER_SECOND*haptic_frames/48'000;

struct Write {
    OVERLAPPED overlapped{};
    std::array<std::uint8_t,write_bytes> report{};
};

class Transport {
public:
    ~Transport(){
        if(device!=INVALID_HANDLE_VALUE)CloseHandle(device);
        if(timer)CloseHandle(timer);
        if(write&&write->overlapped.hEvent)CloseHandle(write->overlapped.hEvent);
    }

    bool open(SDL_Gamepad* pad){
        if(!pad||SDL_GetGamepadConnectionState(pad)!=SDL_JOYSTICK_CONNECTION_WIRELESS)return false;
        const auto product=SDL_GetGamepadProduct(pad);
        if(SDL_GetGamepadVendor(pad)!=0x054c||(product!=0x0ce6&&product!=0x0df2))return false;
        // SDL HIDAPI returns the same Win32 device interface path. Open that
        // specific collection, even when another identical pad is paired.
        const char*path=SDL_GetGamepadPath(pad);
        if(!path||!std::string_view(path).starts_with(R"(\\?\)"))return false;
        device=CreateFileA(path,GENERIC_WRITE,FILE_SHARE_READ|FILE_SHARE_WRITE,nullptr,
            OPEN_EXISTING,FILE_FLAG_OVERLAPPED,nullptr);
        if(device==INVALID_HANDLE_VALUE)return false;

        HIDD_ATTRIBUTES attrs{};
        attrs.Size=sizeof(attrs);
        if(!HidD_GetAttributes(device,&attrs)||attrs.VendorID!=0x054c||attrs.ProductID!=product)return false;
        PHIDP_PREPARSED_DATA data=nullptr;
        if(!HidD_GetPreparsedData(device,&data))return false;
        HIDP_CAPS caps{};
        const bool valid=HidP_GetCaps(data,&caps)==HIDP_STATUS_SUCCESS&&caps.UsagePage==1&&
            caps.Usage==5&&caps.OutputReportByteLength==write_bytes;
        HidD_FreePreparsedData(data);
        if(!valid)return false;

        write->overlapped.hEvent=CreateEventW(nullptr,TRUE,FALSE,nullptr);
        if(!write->overlapped.hEvent)return false;
        constexpr DWORD high_resolution_timer=0x2;
        timer=CreateWaitableTimerExW(nullptr,nullptr,high_resolution_timer,TIMER_ALL_ACCESS);
        if(!timer)timer=CreateWaitableTimerW(nullptr,FALSE,nullptr);
        return timer!=nullptr;
    }

    void wait(Uint64 nanoseconds)const{
        LARGE_INTEGER delay{};
        delay.QuadPart=-static_cast<LONGLONG>((nanoseconds+99)/100);
        if(SetWaitableTimer(timer,&delay,0,nullptr,nullptr,FALSE))WaitForSingleObject(timer,30);
        else SDL_DelayNS(nanoseconds);
    }

    bool send(const float*haptic){
        auto&report=write->report;
        report.fill(0);
        // SAxense documents 0x32 with a single 3 kHz stereo actuator block.
        // This contains no speaker media or controller state commands.
        report[0]=0x32;
        report[1]=std::uint8_t((sequence++&15u)<<4);
        report[2]=0x91;
        report[3]=7;
        report[4]=0xfe;
        report[9]=0xff;
        report[10]=packet++;
        report[11]=0x92;
        report[12]=haptic_payload_bytes;
        encode_dualsense_haptic_pcm(haptic,report.data()+13);

        // HIDCLASS requires the descriptor's largest report size for writes.
        // The Bluetooth CRC still belongs at the end of this report's own payload.
        const std::uint8_t seed=0xa2;
        const auto crc=SDL_crc32(SDL_crc32(0,&seed,1),report.data(),report_bytes-4);
        for(unsigned i=0;i<4;++i)report[report_bytes-4+i]=std::uint8_t(crc>>(i*8));

        auto&overlapped=write->overlapped;
        const HANDLE event=overlapped.hEvent;
        overlapped={};
        overlapped.hEvent=event;
        ResetEvent(event);
        DWORD bytes=0;
        if(WriteFile(device,report.data(),write_bytes,&bytes,&overlapped))return bytes==write_bytes;
        if(GetLastError()!=ERROR_IO_PENDING)return false;
        if(WaitForSingleObject(event,20)==WAIT_OBJECT_0)
            return GetOverlappedResult(device,&overlapped,&bytes,FALSE)&&bytes==write_bytes;
        CancelIoEx(device,&overlapped);
        if(WaitForSingleObject(event,100)!=WAIT_OBJECT_0){
            // A nonresponding driver may still own the OVERLAPPED and its
            // buffer. Keep that one allocation valid and disable retries.
            driver_stalled.store(true,std::memory_order_release);
            (void)write.release();
        }
        return false;
    }

    static inline std::atomic<bool> driver_stalled{false};

private:
    HANDLE device=INVALID_HANDLE_VALUE;
    HANDLE timer=nullptr;
    std::unique_ptr<Write> write=std::make_unique<Write>();
    std::uint8_t sequence=0,packet=0;
};
}

DualSenseBluetooth::~DualSenseBluetooth(){stop();}

bool DualSenseBluetooth::start(SDL_Gamepad*pad,hui::audio::ControllerFeedback&signals){
    stop();
    if(Transport::driver_stalled.load(std::memory_order_acquire))return false;
    auto transport=std::make_unique<Transport>();
    if(!transport->open(pad))return false;
    // Reset audio-mode motor attenuation inherited from another host/client.
    // The verified 0x31 configuration is the same one used by the Windows
    // Bluetooth proof in AnyPS5#2056/#9154. SDL applies its own report framing
    // and CRC; valid_flag0 stays clear so conventional rumble cannot take over.
    const auto effect=dualsense_pcm_effect();
    if(!SDL_SendGamepadEffect(pad,effect.data(),int(effect.size()))){
        hui::sys::log("[Windows] DualSense Bluetooth PCM configuration: %s",SDL_GetError());
        return false;
    }
    ready_.store(true,std::memory_order_release);
    try{
        worker_=std::jthread([this,&signals,transport=std::move(transport)](std::stop_token stop){
            std::array<float,haptic_frames*2> haptic{};
            auto due=SDL_GetTicksNS();
            // Keep the 3 kHz actuator sample clock alive between actions, as
            // with the continuously running USB audio endpoint. Fixed-rate
            // silence avoids dropping short cues on a new Bluetooth burst.
            while(!stop.stop_requested()){
                if(!stream_dualsense_haptic_tick(signals,haptic,[&](const float*pcm){return transport->send(pcm);})){
                    hui::sys::log("[Windows] DualSense Bluetooth PCM transport stopped, Win32 error=%lu",GetLastError());
                    break;
                }
                due+=tick_ns;
                const auto now=SDL_GetTicksNS();
                if(due>now)transport->wait(due-now);
                else if(now-due>=tick_ns)due=now;
            }
            ready_.store(false,std::memory_order_release);
        });
    }catch(...){
        ready_.store(false,std::memory_order_release);
        return false;
    }
    return true;
}

void DualSenseBluetooth::stop(){
    if(worker_.joinable()){
        worker_.request_stop();
        worker_.join();
    }
    ready_.store(false,std::memory_order_release);
}
}
