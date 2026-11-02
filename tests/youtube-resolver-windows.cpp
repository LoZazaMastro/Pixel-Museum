#if defined(_WIN32)
// Exercise the private, bounded child-process boundary without YouTube/network.
// This fixture compiles the implementation once rather than exposing test API.
#include "platform/windows/youtube_resolver.cpp"
#include <cstdio>

int main(int argc, char **argv)
{
    if (argc != 2) return 2;
    const auto root = std::filesystem::path(std::u8string(
        reinterpret_cast<const char8_t *>(argv[1])));
    const auto runtime = root / L"tools/windows-media/deno-2.9.8/deno.exe";
    std::string output, error;
    if (!hui::windows::run_deno(runtime, "console.log('ready')", {}, &output, &error) || output != "ready\n")
    { std::printf("FAIL normal: %s %s\n", error.c_str(), output.c_str()); return 1; }
    output.clear(); error.clear();
    const auto permissions = "try { await fetch('https://example.invalid'); console.log('unexpected'); }"
        " catch(e) { console.log(e.name); }";
    if (!hui::windows::run_deno(runtime, permissions, {}, &output, &error) || output.find("NotCapable") == std::string::npos)
    { std::printf("FAIL permissions: %s %s\n", error.c_str(), output.c_str()); return 1; }
    output.clear(); error.clear();
    const auto start = std::chrono::steady_clock::now();
    const auto cancel = [&]() { return std::chrono::steady_clock::now() - start > std::chrono::milliseconds(150); };
    if (hui::windows::run_deno(runtime, "setInterval(()=>{},10)", cancel, &output, &error) ||
        error != "cancelled" || std::chrono::steady_clock::now() - start > std::chrono::seconds(3))
    { std::printf("FAIL cancellation: %s\n", error.c_str()); return 1; }
    const auto cancelled_ms = std::chrono::duration_cast<std::chrono::milliseconds>(std::chrono::steady_clock::now() - start).count();
    output.clear(); error.clear();
    if (hui::windows::run_deno(runtime, "console.log('x'.repeat(300000))", {}, &output, &error) ||
        error != "player solver output exceeded its limit")
    { std::printf("FAIL output cap: %s\n", error.c_str()); return 1; }
    output.clear(); error.clear();
    const auto timeout_start = std::chrono::steady_clock::now();
    if (hui::windows::run_deno(runtime, "while(true){}", {}, &output, &error) ||
        error != "player solver timed out" ||
        std::chrono::steady_clock::now() - timeout_start > std::chrono::seconds(23))
    { std::printf("FAIL wall timeout: %s\n", error.c_str()); return 1; }
    std::printf("PASS hidden bounded runtime: normal JSON, no network permission, cancellation %lldms, 256KiB output cap, 20s wall timeout\n", static_cast<long long>(cancelled_ms));
    return 0;
}
#endif
