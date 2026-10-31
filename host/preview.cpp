// Pixel Museum — production OpenGL interface, rendered offscreen with Mesa.
// SPDX-License-Identifier: GPL-3.0-or-later
#include "museum/screen.hpp"
#include "museum/music.hpp"
#include "museum/intro_audio.hpp"
#include "host/behavior.hpp"
#include "host/culture_filter_checks.hpp"
#include "host/today_header_checks.hpp"
#include "host/workshop_space_haptic_checks.hpp"
#include "gfx/gl_program.hpp"
#include <EGL/egl.h>
#include <EGL/eglext.h>
#pragma clang diagnostic push
#pragma clang diagnostic ignored "-Wmissing-field-initializers"
#define STB_IMAGE_WRITE_IMPLEMENTATION
#include "third_party/stb/stb_image_write.h"
#undef STB_IMAGE_WRITE_IMPLEMENTATION
#pragma clang diagnostic pop
#include "host/collection_install_preview.hpp"
#include "host/collection_startup_checks.hpp"
#include <filesystem>
#include <thread>
#include <chrono>
#include <cstdio>
#include <cstdlib>
#include <fstream>
int main(int argc,char**argv){
    if(argc>1&&std::string(argv[1])=="workshop-space-haptics")return museum::verify_workshop_space_haptics()?0:35;
    const char*four_k=std::getenv("MUSEUM_PREVIEW_4K");const bool native4k=four_k&&std::string(four_k)=="1";
    const int output_width=native4k?3840:1920,output_height=native4k?2160:1080;
    const auto get=reinterpret_cast<PFNEGLGETPLATFORMDISPLAYEXTPROC>(eglGetProcAddress("eglGetPlatformDisplayEXT"));
    EGLDisplay display=get(EGL_PLATFORM_SURFACELESS_MESA,EGL_DEFAULT_DISPLAY,nullptr);EGLint major=0,minor=0;if(!eglInitialize(display,&major,&minor)||!eglBindAPI(EGL_OPENGL_API))return 2;
    const EGLint attrs[]={EGL_CONTEXT_MAJOR_VERSION,4,EGL_CONTEXT_MINOR_VERSION,5,EGL_CONTEXT_OPENGL_PROFILE_MASK,EGL_CONTEXT_OPENGL_CORE_PROFILE_BIT,EGL_NONE};
    EGLContext gl=eglCreateContext(display,EGL_NO_CONFIG_KHR,EGL_NO_CONTEXT,attrs);if(!eglMakeCurrent(display,EGL_NO_SURFACE,EGL_NO_SURFACE,gl))return 3;
    hui::gfx::set_glsl_prefix("#version 450 core\n");
    const char*preview_root=std::getenv("MUSEUM_PREVIEW_ROOT");
    if(argc>1&&std::string(argv[1])=="collection-install"){
        hui::gfx::Renderer renderer;if(!renderer.init())return 4;
        hui::gfx::Font regular,bold,mono;hui::ui::Fonts fonts;
        const std::string fonts_root=std::string(preview_root?preview_root:".")+"/assets/fonts/";
        const auto load=[&](const char*name,hui::gfx::Font&font,hui::ui::FontRef&ref){
            std::ifstream input(fonts_root+name,std::ios::binary);
            const std::string bytes((std::istreambuf_iterator<char>(input)),{});
            if(bytes.empty()||!font.load(bytes))return false;
            ref={&font,renderer.batch().create_font_texture(font)};return true;
        };
        if(!load("inter-regular.huifont",regular,fonts.regular)||!load("inter-semibold.huifont",bold,fonts.semibold)||!load("dejavu-sans-mono.huifont",mono,fonts.mono))return 4;
        fonts.display=fonts.semibold;fonts.hand=fonts.regular;fonts.pixel=fonts.mono;
        const bool passed=museum::capture_collection_install_previews(renderer,fonts);
        renderer.release();eglMakeCurrent(display,EGL_NO_SURFACE,EGL_NO_SURFACE,EGL_NO_CONTEXT);eglDestroyContext(display,gl);eglTerminate(display);
        return passed?0:66;
    }
    const bool onboarding_pong=argc>1&&std::string(argv[1])=="onboarding-pong";
    const bool onboarding_structure=onboarding_pong||(argc>1&&std::string(argv[1])=="onboarding-structure");
    const bool intro_saved=std::getenv("MUSEUM_HOST_SAVED_ACCESS")!=nullptr;
    const bool collection_e2e=argc>3&&std::string(argv[1])=="collection-end-to-end";
    const std::string preview_data=collection_e2e?argv[3]:onboarding_structure?(intro_saved?"build/onboarding-offline-saved-data":"build/onboarding-offline-fresh-data"):"build/preview-data";
    std::filesystem::create_directories(preview_data);
    if(onboarding_structure){const auto auth=preview_data+"/youtube-auth.json";if(intro_saved){std::ofstream fixture(auth);fixture<<"{\"offline_metadata_fixture_only\":true}";}else std::filesystem::remove(auth);}
    museum::Screen screen;if(!screen.init(preview_root?preview_root:".",preview_data))return 4;
    if(argc>1&&(std::string(argv[1])=="collection-existing"||collection_e2e)){
        const bool passed=collection_e2e?museum::CollectionStartupInspection::download(screen,argv[2],preview_data):museum::CollectionStartupInspection::existing(screen);
        screen.shutdown();eglMakeCurrent(display,EGL_NO_SURFACE,EGL_NO_SURFACE,EGL_NO_CONTEXT);eglDestroyContext(display,gl);eglTerminate(display);return passed?0:68;
    }
    if(argc>1&&std::string(argv[1])=="collection-startup"){
        const bool passed=museum::CollectionStartupInspection::check(screen);
        screen.shutdown();eglMakeCurrent(display,EGL_NO_SURFACE,EGL_NO_SURFACE,EGL_NO_CONTEXT);eglDestroyContext(display,gl);eglTerminate(display);return passed?0:67;
    }
    if(argc>1&&std::string(argv[1])=="culture-filters"){
        const bool passed=museum::ScreenInspection::verify_culture_filters(screen);
        screen.shutdown();eglMakeCurrent(display,EGL_NO_SURFACE,EGL_NO_SURFACE,EGL_NO_CONTEXT);eglDestroyContext(display,gl);eglTerminate(display);return passed?0:61;
    }
    museum::PinScene actual_pin;actual_pin.set_root(preview_root?preview_root:".");
    screen.set_trophy_pin_renderer([&](const museum::TrophyView&pin,int w,int h,float yaw,float pitch,float zoom,float pan_y){return actual_pin.render(pin.badge,pin.unlocked,w,h,yaw,pitch,zoom,pan_y);});
    if(argc>1&&std::string(argv[1])=="ui-action-haptics"){
        const bool passed=museum::ScreenInspection::verify_ui_action_haptics(screen);
        screen.shutdown();eglMakeCurrent(display,EGL_NO_SURFACE,EGL_NO_SURFACE,EGL_NO_CONTEXT);eglDestroyContext(display,gl);eglTerminate(display);return passed?0:45;
    }
    if(argc>1&&std::string(argv[1])=="timeline-input-today"){
        const bool passed=museum::ScreenInspection::verify_timeline_input_today(screen);
        screen.shutdown();eglMakeCurrent(display,EGL_NO_SURFACE,EGL_NO_SURFACE,EGL_NO_CONTEXT);eglDestroyContext(display,gl);eglTerminate(display);return passed?0:50;
    }
    if(argc>1&&std::string(argv[1])=="today-header"){
        hui::gfx::Canvas target;if(!target.create(output_width,output_height,1))return 5;
        std::filesystem::create_directories("build/previews");
        const bool passed=museum::ScreenInspection::verify_today_header(screen,target.framebuffer(),output_width,output_height);
        screen.shutdown();target.destroy();eglMakeCurrent(display,EGL_NO_SURFACE,EGL_NO_SURFACE,EGL_NO_CONTEXT);eglDestroyContext(display,gl);eglTerminate(display);return passed?0:49;
    }
    if(argc>1&&std::string(argv[1])=="arcade-cage"){
        hui::gfx::Canvas target;if(!target.create(output_width,output_height,1))return 5;
        std::filesystem::create_directories("build/previews");
        const bool passed=museum::ScreenInspection::verify_arcade_cage_visual(screen,target.framebuffer(),output_width,output_height);
        screen.shutdown();target.destroy();eglMakeCurrent(display,EGL_NO_SURFACE,EGL_NO_SURFACE,EGL_NO_CONTEXT);eglDestroyContext(display,gl);eglTerminate(display);return passed?0:51;
    }
    if(argc>1&&std::string(argv[1])=="chapter-boundaries"){
        const bool passed=museum::ScreenInspection::verify_main_chapter_boundaries(screen);
        screen.shutdown();eglMakeCurrent(display,EGL_NO_SURFACE,EGL_NO_SURFACE,EGL_NO_CONTEXT);eglDestroyContext(display,gl);eglTerminate(display);return passed?0:62;
    }
    const bool captions=argc>1&&std::string(argv[1])=="captions";
    const bool music_layout=argc>1&&std::string(argv[1])=="music-layout";
    const bool experience_completion=argc>1&&std::string(argv[1])=="experience-completion";
    const bool ui_locales=argc>1&&std::string(argv[1])=="ui-locales";
    const bool general_credits=argc>1&&std::string(argv[1])=="general-credits";
    const bool cover_probe=argc>2&&std::string(argv[1])=="cover-probe";
    const bool intro=argc>1&&std::string(argv[1])=="intro";
    const bool design=argc>1&&std::string(argv[1])=="design";
    const bool onboarding_locales=argc>1&&std::string(argv[1])=="onboarding-locales";
    const bool story_reading=argc>1&&std::string(argv[1])=="story-reading";
    const bool story_scrollbar=argc>1&&std::string(argv[1])=="story-scrollbar";
    const bool illustrated_story=argc>2&&std::string(argv[1])=="illustrated-story";
    const bool alpha_images=argc>1&&std::string(argv[1])=="alpha-images";
    const bool story_distribution=argc>1&&std::string(argv[1])=="story-distribution";
    const bool story_text_profile=argc>1&&std::string(argv[1])=="story-text-profile";
    const bool unicode_fonts=argc>1&&std::string(argv[1])=="unicode-fonts";
    const bool catalog_aliases=argc>1&&std::string(argv[1])=="catalog-aliases";
    const bool console_cutouts=argc>1&&(std::string(argv[1])=="gba-cutout"||std::string(argv[1])=="n64-cables"||std::string(argv[1])=="wii-console-only"||std::string(argv[1])=="ps5-no-base");
    const bool ps1_presentations=argc>1&&std::string(argv[1])=="ps1-presentations";
    const bool model_stage_1080=argc>1&&std::string(argv[1])=="model-stage-1080";
    const bool timeline_symbols=argc>1&&std::string(argv[1])=="timeline-symbols";
    const bool timeline_pause=argc>1&&std::string(argv[1])=="timeline-pause";
    const bool culture_staged=argc>1&&std::string(argv[1])=="culture-staged";
    const bool twelfth_scoped=argc>1&&std::string(argv[1])=="twelfth-scoped";
    const bool eleventh_scoped=argc>1&&std::string(argv[1])=="eleventh-scoped";
    const bool tenth_scoped=argc>1&&std::string(argv[1])=="tenth-scoped";
    const bool ninth_scoped=argc>1&&std::string(argv[1])=="ninth-scoped";
    const bool sayonara_reading=argc>1&&std::string(argv[1])=="sayonara-reading";
    const bool photo_feedback=argc>1&&std::string(argv[1])=="photo-feedback";
    const bool experience_focus=argc>1&&std::string(argv[1])=="experience-focus";
    const bool model_transitions=argc>1&&std::string(argv[1])=="model-transitions";
    if(!onboarding_structure&&!captions&&!general_credits&&!ui_locales&&!story_scrollbar&&!illustrated_story&&!experience_completion&&!cover_probe&&!music_layout&&!timeline_symbols&&!story_distribution&&!console_cutouts&&!ps1_presentations&&!model_stage_1080&&!timeline_pause&&!intro&&!design&&!onboarding_locales&&!model_transitions&&!experience_focus&&!photo_feedback&&!sayonara_reading&&!ninth_scoped&&!tenth_scoped&&!eleventh_scoped&&!twelfth_scoped&&!culture_staged&&!story_reading&&!alpha_images&&!story_text_profile&&!unicode_fonts&&!catalog_aliases&&!museum::ScreenInspection::verify(screen))return 8;
    if(argc>1&&std::string(argv[1])=="interactions"){screen.shutdown();eglMakeCurrent(display,EGL_NO_SURFACE,EGL_NO_SURFACE,EGL_NO_CONTEXT);eglDestroyContext(display,gl);eglTerminate(display);return 0;}
    hui::gfx::Canvas target;if(!target.create(output_width,output_height,1))return 5;std::filesystem::create_directories("build/previews");
    if(general_credits){const bool passed=museum::ScreenInspection::verify_general_credits(screen,target.framebuffer(),output_width,output_height);screen.shutdown();target.destroy();eglMakeCurrent(display,EGL_NO_SURFACE,EGL_NO_SURFACE,EGL_NO_CONTEXT);eglDestroyContext(display,gl);eglTerminate(display);return passed?0:48;}
    if(ui_locales){const bool passed=museum::ScreenInspection::verify_ui_locales(screen,target.framebuffer(),output_width,output_height);screen.shutdown();target.destroy();eglMakeCurrent(display,EGL_NO_SURFACE,EGL_NO_SURFACE,EGL_NO_CONTEXT);eglDestroyContext(display,gl);eglTerminate(display);return passed?0:47;}
    if(experience_completion){const bool passed=museum::ScreenInspection::verify_experience_completion(screen,target.framebuffer(),output_width,output_height);screen.shutdown();target.destroy();eglMakeCurrent(display,EGL_NO_SURFACE,EGL_NO_SURFACE,EGL_NO_CONTEXT);eglDestroyContext(display,gl);eglTerminate(display);return passed?0:46;}
    if(console_cutouts){const bool passed=museum::ScreenInspection::preview_console_cutouts(screen,target.framebuffer(),output_width,output_height,(std::string(argv[1])=="gba-cutout"?1:std::string(argv[1])=="n64-cables"?2:std::string(argv[1])=="wii-console-only"?3:4));screen.shutdown();target.destroy();eglMakeCurrent(display,EGL_NO_SURFACE,EGL_NO_SURFACE,EGL_NO_CONTEXT);eglDestroyContext(display,gl);eglTerminate(display);return passed?0:40;}
    if(ps1_presentations){const bool passed=museum::ScreenInspection::preview_ps1_presentations(screen,target.framebuffer(),output_width,output_height);screen.shutdown();target.destroy();eglMakeCurrent(display,EGL_NO_SURFACE,EGL_NO_SURFACE,EGL_NO_CONTEXT);eglDestroyContext(display,gl);eglTerminate(display);return passed?0:37;}
    if(model_stage_1080){const bool passed=museum::ScreenInspection::verify_model_stage_1080(screen,target.framebuffer(),output_width,output_height);screen.shutdown();target.destroy();eglMakeCurrent(display,EGL_NO_SURFACE,EGL_NO_SURFACE,EGL_NO_CONTEXT);eglDestroyContext(display,gl);eglTerminate(display);return passed?0:36;}
    if(timeline_symbols){const bool passed=museum::ScreenInspection::verify_timeline_symbols(screen,target.framebuffer(),output_width,output_height);screen.shutdown();target.destroy();eglMakeCurrent(display,EGL_NO_SURFACE,EGL_NO_SURFACE,EGL_NO_CONTEXT);eglDestroyContext(display,gl);eglTerminate(display);return passed?0:36;}
    if(timeline_pause){const bool passed=museum::ScreenInspection::verify_timeline_pause(screen,target.framebuffer(),output_width,output_height);screen.shutdown();target.destroy();eglMakeCurrent(display,EGL_NO_SURFACE,EGL_NO_SURFACE,EGL_NO_CONTEXT);eglDestroyContext(display,gl);eglTerminate(display);return passed?0:34;}
    if(catalog_aliases){const bool passed=museum::ScreenInspection::verify_catalog_aliases(screen);screen.shutdown();target.destroy();eglMakeCurrent(display,EGL_NO_SURFACE,EGL_NO_SURFACE,EGL_NO_CONTEXT);eglDestroyContext(display,gl);eglTerminate(display);return passed?0:32;}
    if(unicode_fonts){const bool passed=museum::ScreenInspection::verify_unicode_fonts(screen,target.framebuffer(),output_width,output_height);screen.shutdown();target.destroy();eglMakeCurrent(display,EGL_NO_SURFACE,EGL_NO_SURFACE,EGL_NO_CONTEXT);eglDestroyContext(display,gl);eglTerminate(display);return passed?0:31;}
    if(story_distribution){const bool passed=museum::ScreenInspection::verify_story_distribution(screen);screen.shutdown();target.destroy();eglMakeCurrent(display,EGL_NO_SURFACE,EGL_NO_SURFACE,EGL_NO_CONTEXT);eglDestroyContext(display,gl);eglTerminate(display);return passed?0:41;}
    if(story_text_profile){
        const bool passed=museum::ScreenInspection::profile_story_text(screen);
        screen.shutdown();target.destroy();eglMakeCurrent(display,EGL_NO_SURFACE,EGL_NO_SURFACE,EGL_NO_CONTEXT);eglDestroyContext(display,gl);eglTerminate(display);return passed?0:30;
    }
    if(alpha_images){
        const bool passed=museum::ScreenInspection::verify_alpha_images(screen,target.framebuffer(),output_width,output_height);
        screen.shutdown();target.destroy();eglMakeCurrent(display,EGL_NO_SURFACE,EGL_NO_SURFACE,EGL_NO_CONTEXT);eglDestroyContext(display,gl);eglTerminate(display);return passed?0:29;
    }
    if(story_scrollbar){
        const bool passed=museum::ScreenInspection::verify_story_scrollbar(screen,target.framebuffer(),output_width,output_height);
        screen.shutdown();target.destroy();eglMakeCurrent(display,EGL_NO_SURFACE,EGL_NO_SURFACE,EGL_NO_CONTEXT);eglDestroyContext(display,gl);eglTerminate(display);return passed?0:46;
    }
    if(story_reading){
        const bool passed=museum::ScreenInspection::verify_story_reading(screen,target.framebuffer(),output_width,output_height);
        screen.shutdown();target.destroy();eglMakeCurrent(display,EGL_NO_SURFACE,EGL_NO_SURFACE,EGL_NO_CONTEXT);eglDestroyContext(display,gl);eglTerminate(display);return passed?0:28;
    }
    if(culture_staged){const bool passed=museum::ScreenInspection::verify_culture_staged(screen,target.framebuffer(),output_width,output_height);screen.shutdown();target.destroy();eglMakeCurrent(display,EGL_NO_SURFACE,EGL_NO_SURFACE,EGL_NO_CONTEXT);eglDestroyContext(display,gl);eglTerminate(display);return passed?0:39;}
    if(twelfth_scoped){const bool passed=museum::ScreenInspection::verify_twelfth_scoped(screen,target.framebuffer(),output_width,output_height);screen.shutdown();target.destroy();eglMakeCurrent(display,EGL_NO_SURFACE,EGL_NO_SURFACE,EGL_NO_CONTEXT);eglDestroyContext(display,gl);eglTerminate(display);return passed?0:38;}
    if(eleventh_scoped){const bool passed=museum::ScreenInspection::verify_eleventh_scoped(screen,target.framebuffer(),output_width,output_height);screen.shutdown();target.destroy();eglMakeCurrent(display,EGL_NO_SURFACE,EGL_NO_SURFACE,EGL_NO_CONTEXT);eglDestroyContext(display,gl);eglTerminate(display);return passed?0:37;}
    if(tenth_scoped){const bool passed=museum::ScreenInspection::verify_tenth_scoped(screen,target.framebuffer(),output_width,output_height);screen.shutdown();target.destroy();eglMakeCurrent(display,EGL_NO_SURFACE,EGL_NO_SURFACE,EGL_NO_CONTEXT);eglDestroyContext(display,gl);eglTerminate(display);return passed?0:36;}
    if(ninth_scoped){const bool passed=museum::ScreenInspection::verify_ninth_scoped(screen,target.framebuffer(),output_width,output_height);screen.shutdown();target.destroy();eglMakeCurrent(display,EGL_NO_SURFACE,EGL_NO_SURFACE,EGL_NO_CONTEXT);eglDestroyContext(display,gl);eglTerminate(display);return passed?0:35;}
    if(sayonara_reading){const bool passed=museum::ScreenInspection::verify_sayonara_reading(screen,target.framebuffer(),output_width,output_height);screen.shutdown();target.destroy();eglMakeCurrent(display,EGL_NO_SURFACE,EGL_NO_SURFACE,EGL_NO_CONTEXT);eglDestroyContext(display,gl);eglTerminate(display);return passed?0:34;}
    if(photo_feedback){const bool passed=museum::ScreenInspection::verify_photo_feedback(screen,target.framebuffer(),output_width,output_height);screen.shutdown();target.destroy();eglMakeCurrent(display,EGL_NO_SURFACE,EGL_NO_SURFACE,EGL_NO_CONTEXT);eglDestroyContext(display,gl);eglTerminate(display);return passed?0:33;}
    if(experience_focus){
        const bool passed=museum::ScreenInspection::verify_experience_focus(screen,target.framebuffer(),output_width,output_height);
        screen.shutdown();target.destroy();eglMakeCurrent(display,EGL_NO_SURFACE,EGL_NO_SURFACE,EGL_NO_CONTEXT);eglDestroyContext(display,gl);eglTerminate(display);return passed?0:27;
    }
    if(model_transitions){
        const bool passed=museum::ScreenInspection::verify_model_transitions(screen,target.framebuffer(),output_width,output_height);
        screen.shutdown();target.destroy();eglMakeCurrent(display,EGL_NO_SURFACE,EGL_NO_SURFACE,EGL_NO_CONTEXT);eglDestroyContext(display,gl);eglTerminate(display);return passed?0:25;
    }
    if(argc>1&&std::string(argv[1])=="compositor"){
        const bool passed=museum::ScreenInspection::verify_startup_compositor(screen,target.framebuffer(),output_width,output_height);
        screen.shutdown();target.destroy();eglMakeCurrent(display,EGL_NO_SURFACE,EGL_NO_SURFACE,EGL_NO_CONTEXT);eglDestroyContext(display,gl);eglTerminate(display);return passed?0:17;
    }
    if(intro){
        std::filesystem::create_directories("build/intro/frames");
        museum::Music music;if(!music.init("music/eras"))return 9;
        hui::audio::Mixer mixer;music.select_year(screen.selected_year());music.volume(screen.music_volume());
        FILE* wav=std::fopen("build/intro/startup.wav","wb");if(!wav)return 10;
        constexpr unsigned count=360,grain=800,bytes=count*grain*4;
        const auto u32=[&](unsigned n){const unsigned char b[]={static_cast<unsigned char>(n),static_cast<unsigned char>(n>>8),static_cast<unsigned char>(n>>16),static_cast<unsigned char>(n>>24)};std::fwrite(b,1,4,wav);};
        const auto u16=[&](unsigned n){const unsigned char b[]={static_cast<unsigned char>(n),static_cast<unsigned char>(n>>8)};std::fwrite(b,1,2,wav);};
        std::fwrite("RIFF",1,4,wav);u32(bytes+36);std::fwrite("WAVEfmt ",1,8,wav);u32(16);u16(1);u16(2);u32(48000);u32(192000);u16(4);u16(16);std::fwrite("data",1,4,wav);u32(bytes);
        std::vector<uint8_t> pixels(std::size_t(output_width)*output_height*4);std::array<float,grain*2> score{};std::array<int16_t,grain*2> notes{},mixed{};
        stbi_flip_vertically_on_write(1);
        for(unsigned frame=0;frame<count;++frame){
            museum::play_startup_note(mixer,screen.take_startup_note());
            screen.update(1.f/60);screen.draw(output_width,output_height,target.framebuffer());
            glBindFramebuffer(GL_FRAMEBUFFER,target.framebuffer());glReadPixels(0,0,output_width,output_height,GL_RGBA,GL_UNSIGNED_BYTE,pixels.data());
            char name[100];std::snprintf(name,sizeof(name),"build/intro/frames/%04u.png",frame);stbi_write_png(name,output_width,output_height,4,pixels.data(),output_width*4);
            music.render(score.data(),grain);mixer.render(notes.data(),grain);
            for(unsigned i=0;i<grain*2;++i)mixed[i]=static_cast<int16_t>(std::clamp(score[i]+float(notes[i])/32768.f,-1.f,1.f)*32767.f);
            std::fwrite(mixed.data(),sizeof(int16_t),mixed.size(),wav);
        }
        std::fclose(wav);std::puts("Startup preview: 360 production frames and 48 kHz stereo soundtrack rendered");
        screen.shutdown();target.destroy();eglMakeCurrent(display,EGL_NO_SURFACE,EGL_NO_SURFACE,EGL_NO_CONTEXT);eglDestroyContext(display,gl);eglTerminate(display);return 0;
    }
    if(argc>1&&std::string(argv[1])=="captions"){
        const bool passed=museum::ScreenInspection::verify_captions(screen,target.framebuffer(),output_width,output_height);
        screen.shutdown();target.destroy();eglMakeCurrent(display,EGL_NO_SURFACE,EGL_NO_SURFACE,EGL_NO_CONTEXT);eglDestroyContext(display,gl);eglTerminate(display);return passed?0:18;
    }
    if(argc>1&&std::string(argv[1])=="editorial"){
        const bool passed=museum::ScreenInspection::verify_feature_cards(screen,target.framebuffer(),output_width,output_height);
        screen.shutdown();target.destroy();eglMakeCurrent(display,EGL_NO_SURFACE,EGL_NO_SURFACE,EGL_NO_CONTEXT);eglDestroyContext(display,gl);eglTerminate(display);return passed?0:19;
    }
    auto settle=[&](unsigned frames){for(unsigned n=0;n<frames;++n){screen.update(1.f/60);std::this_thread::sleep_for(std::chrono::milliseconds(12));}};
    auto await_object=[&](){
        const auto deadline=std::chrono::steady_clock::now()+std::chrono::seconds(45);
        while(!museum::ScreenInspection::object_ready(screen)&&std::chrono::steady_clock::now()<deadline){screen.update(1.f/60);std::this_thread::sleep_for(std::chrono::milliseconds(10));}
        if(!museum::ScreenInspection::object_ready(screen)){std::fputs("Model capture timed out after 45 seconds without a rendered object texture\n",stderr);return false;}
        return true;
    };
    auto capture_frame=[&](const char*name){screen.draw(output_width,output_height,target.framebuffer());glBindFramebuffer(GL_FRAMEBUFFER,target.framebuffer());std::vector<uint8_t>pixels(std::size_t(output_width)*output_height*4);glReadPixels(0,0,output_width,output_height,GL_RGBA,GL_UNSIGNED_BYTE,pixels.data());stbi_flip_vertically_on_write(1);const auto p=std::string("build/previews/")+name+(native4k?"-4k":"")+".png";stbi_write_png(p.c_str(),output_width,output_height,4,pixels.data(),output_width*4);std::printf("%s %dx%d GL=0x%x\n",p.c_str(),output_width,output_height,glGetError());};
    auto capture=[&](const char*name){settle(60);capture_frame(name);};
    if(onboarding_structure){
        if(onboarding_pong){
            for(int sec:{0,9,18,27}){museum::ScreenInspection::onboarding_pin_frame(screen,float(sec),false);capture_frame((std::string("intro-pong-3d-")+std::to_string(sec)).c_str());if(!actual_pin.error().empty()){std::fprintf(stderr,"Actual PinScene: %s\n",actual_pin.error().c_str());return 58;}}
            museum::ScreenInspection::onboarding_pin_frame(screen,27,true);capture_frame("intro-pong-3d-reduced");
            actual_pin.release();screen.shutdown();target.destroy();eglMakeCurrent(display,EGL_NO_SURFACE,EGL_NO_SURFACE,EGL_NO_CONTEXT);eglDestroyContext(display,gl);eglTerminate(display);return 0;
        }
        for(const char*locale:{"en","it","es","fr","de"}){
            museum::ScreenInspection::onboarding_structure_state(screen,locale,-2);capture((std::string("intro-language-")+locale).c_str());
            museum::ScreenInspection::onboarding_structure_state(screen,locale,-1);capture((std::string("intro-theme-")+locale).c_str());
            museum::ScreenInspection::onboarding_structure_state(screen,locale,-3);capture_frame((std::string("intro-theme-expand-")+locale).c_str());
            museum::ScreenInspection::onboarding_structure_state(screen,locale,-4);capture_frame((std::string("intro-theme-expand-dark-")+locale).c_str());
            for(int step=0;step<6;++step){museum::ScreenInspection::onboarding_structure_state(screen,locale,step);screen.draw(output_width,output_height,target.framebuffer());if(step==3){const auto deadline=std::chrono::steady_clock::now()+std::chrono::seconds(10);while(!museum::ScreenInspection::onboarding_pin_ready(screen)&&std::chrono::steady_clock::now()<deadline)settle(3);if(!museum::ScreenInspection::onboarding_pin_ready(screen))return 57;}capture((std::string("intro-centered-")+locale+"-"+std::to_string(step)).c_str());}
        }
        if(!museum::ScreenInspection::verify_onboarding_structure(screen,intro_saved))return 56;
        screen.shutdown();target.destroy();eglMakeCurrent(display,EGL_NO_SURFACE,EGL_NO_SURFACE,EGL_NO_CONTEXT);eglDestroyContext(display,gl);eglTerminate(display);return 0;
    }
    if(argc>1&&std::string(argv[1])=="trophy-pin-haptics"){
        const bool passed=museum::ScreenInspection::verify_trophy_pin_motion_haptics(screen);
        screen.shutdown();target.destroy();eglMakeCurrent(display,EGL_NO_SURFACE,EGL_NO_SURFACE,EGL_NO_CONTEXT);eglDestroyContext(display,gl);eglTerminate(display);return passed?0:61;
    }
    if(argc>1&&std::string(argv[1])=="trophy-awards-feedback"){
        if(!museum::ScreenInspection::verify_trophy_awards_feedback(screen))return 53;
        capture("feedback-tga-selected2024");
        const char*names[]={"feedback-trophy-public","feedback-trophy-curator-secret","feedback-trophy-secret-revealed","feedback-trophy-normal-secret","feedback-trophy-last-row","feedback-experience-controls","feedback-settings","feedback-credits","feedback-native-only-no-local-overlay"};
        for(int mode=0;mode<9;++mode){if(!museum::ScreenInspection::trophy_feedback_preview(screen,mode))return 54;screen.draw(output_width,output_height,target.framebuffer());if(mode<5){const auto deadline=std::chrono::steady_clock::now()+std::chrono::seconds(10);while(!museum::ScreenInspection::trophy_feedback_image_ready(screen)&&std::chrono::steady_clock::now()<deadline)settle(3);if(!museum::ScreenInspection::trophy_feedback_image_ready(screen))return 55;}capture(names[mode]);}
        if(!museum::ScreenInspection::actual_native_only_trophy_preview(screen))return 59;
        screen.draw(output_width,output_height,target.framebuffer());
        {const auto deadline=std::chrono::steady_clock::now()+std::chrono::seconds(10);while(!museum::ScreenInspection::actual_native_only_trophy_ready(screen)&&std::chrono::steady_clock::now()<deadline)settle(3);if(!museum::ScreenInspection::actual_native_only_trophy_ready(screen))return 60;}
        capture("feedback-actual-persisted-unlock-native-only");
        screen.shutdown();target.destroy();eglMakeCurrent(display,EGL_NO_SURFACE,EGL_NO_SURFACE,EGL_NO_CONTEXT);eglDestroyContext(display,gl);eglTerminate(display);return 0;
    }

    if(cover_probe){
        if(!museum::ScreenInspection::cover_probe(screen,argv[2]))return 43;
        const auto deadline=std::chrono::steady_clock::now()+std::chrono::seconds(12);
        while(!museum::ScreenInspection::cover_probe_ready(screen)&&std::chrono::steady_clock::now()<deadline){settle(2);screen.draw(output_width,output_height,target.framebuffer());}
        if(!museum::ScreenInspection::cover_probe_ready(screen))return 44;
        capture(argc>3?argv[3]:"cover-probe");
        screen.shutdown();target.destroy();eglMakeCurrent(display,EGL_NO_SURFACE,EGL_NO_SURFACE,EGL_NO_CONTEXT);eglDestroyContext(display,gl);eglTerminate(display);return 0;
    }
    if(music_layout){
        if(!museum::ScreenInspection::refinement_preview(screen,3))return 42;
        capture(argc>2?argv[2]:"music-layout");
        screen.shutdown();target.destroy();eglMakeCurrent(display,EGL_NO_SURFACE,EGL_NO_SURFACE,EGL_NO_CONTEXT);eglDestroyContext(display,gl);eglTerminate(display);return 0;
    }
    if(argc>1&&std::string(argv[1])=="search"){
        if(!museum::ScreenInspection::verify_search(screen))return 24;
        capture("search-results");museum::ScreenInspection::search_keyboard_preview(screen);capture("search-keyboard");
        screen.shutdown();target.destroy();eglMakeCurrent(display,EGL_NO_SURFACE,EGL_NO_SURFACE,EGL_NO_CONTEXT);eglDestroyContext(display,gl);eglTerminate(display);return 0;
    }
    if(argc>1&&std::string(argv[1])=="playlist"){
        const bool passed=museum::ScreenInspection::verify_playlist(screen,target.framebuffer(),output_width,output_height);
        screen.shutdown();target.destroy();eglMakeCurrent(display,EGL_NO_SURFACE,EGL_NO_SURFACE,EGL_NO_CONTEXT);eglDestroyContext(display,gl);eglTerminate(display);return passed?0:16;
    }
    if(argc>1&&std::string(argv[1])=="story-audit"){
        const bool passed=museum::ScreenInspection::verify_story_scenes(screen);
        screen.shutdown();target.destroy();eglMakeCurrent(display,EGL_NO_SURFACE,EGL_NO_SURFACE,EGL_NO_CONTEXT);eglDestroyContext(display,gl);eglTerminate(display);return passed?0:19;
    }
    if(argc>2&&std::string(argv[1])=="illustrated-story"){
        const int count=museum::ScreenInspection::illustrated_story_preview(screen,argv[2],0);
        if(count<1)return 26;
        // Optional single-card target for bounded editorial visual reviews.
        const int first=argc>3?std::atoi(argv[3]):0;
        const int end=argc>3?first+1:count;
        if(first<0||first>=count)return 26;
        for(int card=first;card<end;++card){
            if(museum::ScreenInspection::illustrated_story_preview(screen,argv[2],card)!=count)return 26;
            const auto deadline=std::chrono::steady_clock::now()+std::chrono::seconds(10);
            while(!museum::ScreenInspection::story_photo_ready(screen)&&std::chrono::steady_clock::now()<deadline){
                screen.update(1.f/60);std::this_thread::sleep_for(std::chrono::milliseconds(10));
            }
            if(!museum::ScreenInspection::story_photo_ready(screen)){
                std::fprintf(stderr,"Illustrated story photograph did not become resident: card %d\n",card);return 26;
            }
            if(!museum::ScreenInspection::story_photo_evidence(screen))return 26;
            capture((std::string("story-")+argv[2]+"-"+std::to_string(card)).c_str());
        }
        screen.shutdown();target.destroy();eglMakeCurrent(display,EGL_NO_SURFACE,EGL_NO_SURFACE,EGL_NO_CONTEXT);eglDestroyContext(display,gl);eglTerminate(display);return 0;
    }
    if(argc>1&&std::string(argv[1])=="onboarding"){
        for(int mode:{1,5}){if(!museum::ScreenInspection::design_preview(screen,mode))return 14;capture(mode==1?"onboarding-navigation":"onboarding-media");}
        screen.shutdown();target.destroy();eglMakeCurrent(display,EGL_NO_SURFACE,EGL_NO_SURFACE,EGL_NO_CONTEXT);eglDestroyContext(display,gl);eglTerminate(display);return 0;
    }
    if(argc>1&&std::string(argv[1])=="double-timeline"){
        if(!museum::ScreenInspection::verify_history(screen))return 21;
        if(!museum::ScreenInspection::history_preview(screen,false))return 21;
        if(!await_object())return 21;
        capture("world-timeline-gaming");
        hui::ui::Feedback route_feedback;hui::InputFrame route_input;route_input.connected=true;route_input.nav=hui::Direction::up;
        screen.handle(route_input,route_feedback);settle(15);capture_frame("world-timeline-transition");
        capture("world-timeline-culture");
        if(!museum::ScreenInspection::history_preview(screen,true,1833))return 21;
        capture("world-timeline-origins");
        screen.preview(4);capture("museum-options");screen.preview(5);capture("museum-credits");
        screen.shutdown();target.destroy();eglMakeCurrent(display,EGL_NO_SURFACE,EGL_NO_SURFACE,EGL_NO_CONTEXT);eglDestroyContext(display,gl);eglTerminate(display);return 0;
    }
    if(argc>3&&std::string(argv[1])=="feature"){
        screen.select(argv[2]);settle(220);
        for(int paragraph=0;paragraph<4;++paragraph){
            if(!museum::ScreenInspection::focus_feature(screen,argv[3],paragraph))return 20;
            capture((std::string("feature-")+argv[2]+"-"+std::to_string(paragraph)).c_str());
        }
        screen.shutdown();target.destroy();eglMakeCurrent(display,EGL_NO_SURFACE,EGL_NO_SURFACE,EGL_NO_CONTEXT);eglDestroyContext(display,gl);eglTerminate(display);return 0;
    }
    if(argc>1&&std::string(argv[1])=="refinements"){
        if(!museum::ScreenInspection::verify_story_scenes(screen))return 19;
        const char*names[]={"awards-archive","experience-inverse-card","music-invitation","listening-room","video-loading"};
        for(int mode=0;mode<5;++mode){if(!museum::ScreenInspection::refinement_preview(screen,mode))return 18;settle(90);capture(names[mode]);}
        screen.shutdown();target.destroy();eglMakeCurrent(display,EGL_NO_SURFACE,EGL_NO_SURFACE,EGL_NO_CONTEXT);eglDestroyContext(display,gl);eglTerminate(display);return 0;
    }
    if(argc>1&&std::string(argv[1])=="experiences"){
        if(!museum::ScreenInspection::verify_playlist(screen,target.framebuffer(),output_width,output_height))return 16;
        if(!museum::ScreenInspection::verify_experiences(screen,target.framebuffer(),output_width,output_height))return 15;
        museum::ScreenInspection::experience_preview(screen,0,3);capture("experiences-library");
        museum::ScreenInspection::experience_preview(screen,1,8);capture("experience-introduction");
        museum::ScreenInspection::experience_preview(screen,2,8);capture("experience-momentum");
        museum::ScreenInspection::experience_preview(screen,2,14);capture("experience-raycast");
        screen.shutdown();target.destroy();eglMakeCurrent(display,EGL_NO_SURFACE,EGL_NO_SURFACE,EGL_NO_CONTEXT);eglDestroyContext(display,gl);eglTerminate(display);return 0;
    }
    if(argc>1&&std::string(argv[1])=="today"){
        museum::ScreenInspection::today(screen);settle(300);capture("on-this-day");screen.preview(1);capture("on-this-day-story");
        screen.shutdown();target.destroy();eglMakeCurrent(display,EGL_NO_SURFACE,EGL_NO_SURFACE,EGL_NO_CONTEXT);eglDestroyContext(display,gl);eglTerminate(display);return 0;
    }
    if(onboarding_locales){
        if(!museum::ScreenInspection::verify_first_visit(screen))return 22;
        for(const auto*locale:{"en","it","es","fr","de"}){
            for(int step=0;step<=museum::ScreenInspection::onboarding_card_count();++step){
                if(!museum::ScreenInspection::localized_onboarding_preview(screen,locale,step))return 22;
                capture((std::string("onboarding-")+locale+"-"+std::to_string(step)).c_str());
            }
            museum::ScreenInspection::reordered_options_preview(screen);
            capture((std::string("reordered-options-")+locale).c_str());
        }
        screen.shutdown();target.destroy();eglMakeCurrent(display,EGL_NO_SURFACE,EGL_NO_SURFACE,EGL_NO_CONTEXT);eglDestroyContext(display,gl);eglTerminate(display);return 0;
    }
    if(design){
        const char*names[]={"onboarding-welcome","onboarding-navigation","onboarding-start","year-atlas","pixel-workshop","onboarding-media","onboarding-music"};
        for(int mode=0;mode<7;++mode){if(!museum::ScreenInspection::design_preview(screen,mode))return 14;if(mode==3){if(!await_object())return 13;museum::ScreenInspection::design_year_atlas(screen);}capture(names[mode]);}
        screen.shutdown();target.destroy();eglMakeCurrent(display,EGL_NO_SURFACE,EGL_NO_SURFACE,EGL_NO_CONTEXT);eglDestroyContext(display,gl);eglTerminate(display);return 0;
    }
    if(argc>1&&std::string(argv[1])=="scenes"){
        screen.select(argc>2?argv[2]:"karateka");settle(220);
        if(!museum::ScreenInspection::verify_scene(screen,target.framebuffer(),output_width,output_height))return 12;
        screen.preview(1);capture("slice-story");screen.preview(2);capture("slice-photo-fullscreen");screen.preview(0);
        for(const auto*id:{"carol-shaw","game-boy","nintendo-3ds"}){screen.select(id);museum::ScreenInspection::freeze_object(screen);screen.preview(0);if(std::string(id)=="carol-shaw")settle(350);else if(!await_object())return 13;capture((std::string("slice-")+id).c_str());screen.preview(1);capture((std::string("slice-")+id+"-story").c_str());screen.preview(0);}
        screen.shutdown();target.destroy();eglMakeCurrent(display,EGL_NO_SURFACE,EGL_NO_SURFACE,EGL_NO_CONTEXT);eglDestroyContext(display,gl);eglTerminate(display);return 0;
    }
    if(argc>2&&std::string(argv[1])=="model"){
        screen.select(argv[2]);museum::ScreenInspection::freeze_object(screen);if(!await_object())return 13;if(!museum::ScreenInspection::verify_model_controls(screen))return 11;capture(argv[2]);screen.preview(1);capture("model-story");
        screen.shutdown();target.destroy();eglMakeCurrent(display,EGL_NO_SURFACE,EGL_NO_SURFACE,EGL_NO_CONTEXT);eglDestroyContext(display,gl);eglTerminate(display);return 0;
    }
    std::string hero;for(const auto&e:screen.catalog().entries)if(e.title.find("PlayStation")!=std::string::npos){hero=e.id;break;}if(hero.empty())for(const auto&e:screen.catalog().entries)if(e.year>=1989&&!e.images.empty()){hero=e.id;break;}if(!hero.empty())screen.select(hero);
    settle(650);capture("timeline");screen.preview(1);capture("exhibit");screen.preview(2);capture("image-viewer");screen.preview(0);screen.preview(4);capture("options");screen.preview(5);capture("credits");screen.preview(0);
    for(const auto&e:screen.catalog().entries)if(e.id=="carol-shaw"&&!e.images.empty()){screen.select(e.id);settle(350);screen.preview(1);capture("portrait");break;}
    for(const auto&e:screen.catalog().entries)if(e.id=="game-boy"){screen.select(e.id);screen.preview(0);if(e.models.empty()){settle(350);capture("game-boy-png");}else{museum::ScreenInspection::freeze_object(screen);if(!await_object())return 13;capture("object-3d");}break;}
    screen.shutdown();target.destroy();eglMakeCurrent(display,EGL_NO_SURFACE,EGL_NO_SURFACE,EGL_NO_CONTEXT);eglDestroyContext(display,gl);eglTerminate(display);return 0;
}
