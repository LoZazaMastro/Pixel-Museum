#if defined(_WIN32)
#ifndef WIN32_LEAN_AND_MEAN
#define WIN32_LEAN_AND_MEAN
#endif
#include <winsock2.h>
#include <ws2tcpip.h>
#include "yt/http.hpp"
#include <atomic>
#include <chrono>
#include <cstdio>
#include <thread>

int main()
{
    WSADATA data{};
    if (WSAStartup(MAKEWORD(2,2), &data) != 0) return 2;
    const SOCKET listener = socket(AF_INET, SOCK_STREAM, IPPROTO_TCP);
    sockaddr_in address{}; address.sin_family = AF_INET;
    address.sin_addr.s_addr = htonl(INADDR_LOOPBACK);
    int address_bytes = sizeof(address);
    if (listener == INVALID_SOCKET || bind(listener, reinterpret_cast<sockaddr *>(&address), sizeof(address)) ||
        listen(listener, 1) || getsockname(listener, reinterpret_cast<sockaddr *>(&address), &address_bytes)) return 2;
    u_long nonblocking = 1;
    if (ioctlsocket(listener, FIONBIO, &nonblocking)) return 2;
    std::atomic<bool> stop{false}, accepted{false};
    std::thread fixture([&]() {
        SOCKET peer = INVALID_SOCKET;
        const auto deadline = std::chrono::steady_clock::now() + std::chrono::seconds(5);
        while (!stop && peer == INVALID_SOCKET && std::chrono::steady_clock::now() < deadline)
        {
            peer = accept(listener, nullptr, nullptr);
            if (peer == INVALID_SOCKET) std::this_thread::sleep_for(std::chrono::milliseconds(5));
        }
        if (peer != INVALID_SOCKET)
        {
            accepted = true;
            // Deliberately withhold all TLS/header/body bytes; trust settings
            // stay enabled and no certificate bypass is used by this fixture.
            while (!stop) std::this_thread::sleep_for(std::chrono::milliseconds(10));
            closesocket(peer);
        }
    });
    yt::http::Request request;
    request.url = "https://127.0.0.1:" + std::to_string(ntohs(address.sin_port));
    request.timeout_s = 60;
    const auto start = std::chrono::steady_clock::now();
    request.cancelled = [&]() { return std::chrono::steady_clock::now() - start > std::chrono::milliseconds(150); };
    auto response = yt::http::perform(request);
    const auto elapsed = std::chrono::duration_cast<std::chrono::milliseconds>(std::chrono::steady_clock::now() - start).count();
    stop = true; closesocket(listener); fixture.join(); WSACleanup();
    if (!accepted || response.error != "cancelled" || response.status != 0 || !response.body.empty() || elapsed > 3000)
    { std::printf("FAIL delayed TLS cancel error=%s status=%ld bytes=%zu ms=%lld\n",response.error.c_str(),response.status,response.body.size(),static_cast<long long>(elapsed)); return 1; }
    std::printf("PASS transport cancellation before headers/body: %lldms (request timeout 60s)\n", static_cast<long long>(elapsed));
    return 0;
}
#endif
