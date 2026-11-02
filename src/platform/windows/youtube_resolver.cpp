#if defined(_WIN32)
// Pixel Museum - Windows fallback to the official yt-dlp EJS player solver.
// SPDX-License-Identifier: GPL-3.0-or-later
#ifndef WIN32_LEAN_AND_MEAN
#define WIN32_LEAN_AND_MEAN
#endif
#ifndef NOMINMAX
#define NOMINMAX
#endif
#include <windows.h>

#include "platform/windows/youtube_resolver.hpp"
#include "museum/collection_sha256.hpp"
#include "third_party/yyjson/yyjson.h"
#include "yt/http.hpp"
#include "yt/log.hpp"

#include <algorithm>
#include <array>
#include <chrono>
#include <cstdlib>
#include <cwchar>
#include <filesystem>
#include <map>
#include <mutex>
#include <string_view>
#include <utility>
#include <vector>

namespace hui::windows
{
namespace
{
namespace fs = std::filesystem;
constexpr std::size_t kPlayerLimit = 3u << 20;
constexpr std::size_t kOutputLimit = 256u << 10;
constexpr auto kSolverTimeout = std::chrono::seconds(20);
constexpr const wchar_t *kDeno = L"tools/windows-media/deno-2.9.8/deno.exe";
constexpr const wchar_t *kCore = L"tools/windows-media/ejs-0.8.0/yt.solver.core.min.js";
constexpr const wchar_t *kLib = L"tools/windows-media/ejs-0.8.0/yt.solver.lib.min.js";

struct Handle
{
    HANDLE value = INVALID_HANDLE_VALUE;
    Handle() = default;
    explicit Handle(HANDLE handle) : value(handle) {}
    ~Handle() { close(); }
    Handle(const Handle &) = delete;
    Handle &operator=(const Handle &) = delete;
    void close()
    {
        if (value != INVALID_HANDLE_VALUE && value != nullptr) CloseHandle(value);
        value = INVALID_HANDLE_VALUE;
    }
    bool valid() const { return value != INVALID_HANDLE_VALUE && value != nullptr; }
};

bool ordinary_file(const fs::path &path)
{
    const DWORD attr = GetFileAttributesW(path.c_str());
    return attr != INVALID_FILE_ATTRIBUTES &&
        !(attr & (FILE_ATTRIBUTE_DIRECTORY | FILE_ATTRIBUTE_REPARSE_POINT));
}

fs::path tools_root(const std::string &install_root)
{
    std::vector<fs::path> roots;
    if (!install_root.empty()) roots.emplace_back(std::u8string(
        reinterpret_cast<const char8_t *>(install_root.data()), install_root.size()));
    std::array<wchar_t, 32768> module{};
    const DWORD length = GetModuleFileNameW(nullptr, module.data(), static_cast<DWORD>(module.size()));
    if (length != 0 && length < module.size())
    {
        fs::path directory = fs::path(std::wstring(module.data(), length)).parent_path();
        // Development executables live in build/<check-name>; installed apps
        // resolve the first directory. Never search PATH for executables.
        for (unsigned i = 0; i < 4 && !directory.empty(); ++i)
        {
            roots.push_back(directory);
            const auto parent = directory.parent_path();
            if (parent == directory) break;
            directory = parent;
        }
    }
    for (const auto &root : roots)
        if (ordinary_file(root / kDeno) && ordinary_file(root / kCore) && ordinary_file(root / kLib))
            return root;
    return {};
}

bool read_script(const fs::path &path, std::size_t limit, const char *expected_hash, std::string *text)
{
    Handle file(CreateFileW(path.c_str(), GENERIC_READ, FILE_SHARE_READ, nullptr,
        OPEN_EXISTING, FILE_FLAG_OPEN_REPARSE_POINT | FILE_FLAG_SEQUENTIAL_SCAN, nullptr));
    LARGE_INTEGER size{};
    BY_HANDLE_FILE_INFORMATION info{};
    if (!file.valid() || !GetFileInformationByHandle(file.value, &info) ||
        (info.dwFileAttributes & (FILE_ATTRIBUTE_DIRECTORY | FILE_ATTRIBUTE_REPARSE_POINT)) ||
        !GetFileSizeEx(file.value, &size) || size.QuadPart <= 0 ||
        static_cast<unsigned long long>(size.QuadPart) > limit) return false;
    std::string data(static_cast<std::size_t>(size.QuadPart), '\0');
    DWORD read = 0;
    if (!ReadFile(file.value, data.data(), static_cast<DWORD>(data.size()), &read, nullptr) ||
        read != data.size()) return false;
    museum::CollectionSha256 hash;
    hash.update(data.data(), data.size());
    if (hash.finish() != expected_hash) return false;
    *text = std::move(data);
    return true;
}

std::wstring quoted(const std::wstring &argument)
{
    std::wstring out = L"\"";
    std::size_t slashes = 0;
    for (const wchar_t ch : argument)
    {
        if (ch == L'\\') { ++slashes; continue; }
        out.append(slashes * (ch == L'"' ? 2 : 1), L'\\');
        slashes = 0;
        if (ch == L'"') out += L'\\';
        out += ch;
    }
    out.append(slashes * 2, L'\\');
    return out + L'"';
}

bool drain_pipe(HANDLE pipe, std::size_t limit, std::string *output)
{
    for (;;)
    {
        DWORD available = 0;
        if (!PeekNamedPipe(pipe, nullptr, 0, nullptr, &available, nullptr))
            return GetLastError() == ERROR_BROKEN_PIPE;
        if (available == 0) return true;
        if (available > limit - std::min(limit, output->size())) return false;
        std::array<char, 8192> bytes{};
        DWORD read = 0;
        if (!ReadFile(pipe, bytes.data(), std::min<DWORD>(available, bytes.size()), &read, nullptr))
            return GetLastError() == ERROR_BROKEN_PIPE;
        output->append(bytes.data(), read);
    }
}

bool child_environment(std::vector<wchar_t> *block)
{
    wchar_t *environment = GetEnvironmentStringsW();
    if (!environment) return false;
    std::vector<std::wstring> values;
    for (const wchar_t *entry = environment; *entry; entry += std::wcslen(entry) + 1)
    {
        if (_wcsnicmp(entry, L"DENO_", 5) == 0 || _wcsnicmp(entry, L"NPM_CONFIG_", 11) == 0 ||
            _wcsnicmp(entry, L"NODE_OPTIONS=", 13) == 0 || _wcsnicmp(entry, L"NO_COLOR=", 9) == 0)
            continue;
        values.emplace_back(entry);
    }
    FreeEnvironmentStringsW(environment);
    // The runtime itself otherwise checks for newer versions independently
    // of script network permissions. Do not change the parent's environment.
    values.emplace_back(L"DENO_NO_UPDATE_CHECK=1");
    values.emplace_back(L"DENO_NO_PROMPT=1");
    values.emplace_back(L"NO_COLOR=1");
    std::sort(values.begin(), values.end(), [](const auto &left, const auto &right) {
        return CompareStringOrdinal(left.c_str(), -1, right.c_str(), -1, TRUE) == CSTR_LESS_THAN;
    });
    for (const auto &value : values)
    {
        block->insert(block->end(), value.begin(), value.end());
        block->push_back(L'\0');
    }
    block->push_back(L'\0');
    return true;
}

bool run_deno(const fs::path &executable, const std::string &script,
              const std::function<bool()> &cancelled, std::string *output, std::string *error)
{
    if (cancelled && cancelled()) { *error = "cancelled"; return false; }
    SECURITY_ATTRIBUTES inheritable{sizeof(SECURITY_ATTRIBUTES), nullptr, TRUE};
    // A delete-on-close stdin file avoids a blocking pipe writer when a child
    // exits early or stalls. It is private, bounded and never persistent.
    std::array<wchar_t, 32768> temp_directory{}, temp_name{};
    const DWORD temp_length = GetTempPathW(static_cast<DWORD>(temp_directory.size()), temp_directory.data());
    if (!temp_length || temp_length >= temp_directory.size() ||
        !GetTempFileNameW(temp_directory.data(), L"pmj", 0, temp_name.data()))
    { *error = "cannot create player solver input"; return false; }
    Handle input(CreateFileW(temp_name.data(), GENERIC_READ | GENERIC_WRITE, FILE_SHARE_READ,
        &inheritable, OPEN_EXISTING, FILE_ATTRIBUTE_TEMPORARY | FILE_FLAG_DELETE_ON_CLOSE, nullptr));
    if (!input.valid())
    {
        DeleteFileW(temp_name.data());
        *error = "cannot open player solver input"; return false;
    }
    DWORD written = 0;
    LARGE_INTEGER zero{};
    if (!WriteFile(input.value, script.data(), static_cast<DWORD>(script.size()), &written, nullptr) ||
        written != script.size() || !SetFilePointerEx(input.value, zero, nullptr, FILE_BEGIN))
    { *error = "cannot write player solver input"; return false; }
    Handle stdout_read, stdout_write, stderr_read, stderr_write;
    if (!CreatePipe(&stdout_read.value, &stdout_write.value, &inheritable, 0) ||
        !CreatePipe(&stderr_read.value, &stderr_write.value, &inheritable, 0) ||
        !SetHandleInformation(stdout_read.value, HANDLE_FLAG_INHERIT, 0) ||
        !SetHandleInformation(stderr_read.value, HANDLE_FLAG_INHERIT, 0))
    { *error = "cannot create player solver output"; return false; }
    Handle job(CreateJobObjectW(nullptr, nullptr));
    JOBOBJECT_EXTENDED_LIMIT_INFORMATION limits{};
    limits.BasicLimitInformation.LimitFlags = JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE | JOB_OBJECT_LIMIT_PROCESS_MEMORY;
    limits.ProcessMemoryLimit = std::size_t(1) << 30;
    if (!job.valid() || !SetInformationJobObject(job.value, JobObjectExtendedLimitInformation, &limits, sizeof(limits)))
    { *error = "cannot bound player solver process"; return false; }
    SIZE_T attribute_bytes = 0;
    InitializeProcThreadAttributeList(nullptr, 1, 0, &attribute_bytes);
    std::vector<unsigned char> attributes(attribute_bytes);
    auto *attribute_list = reinterpret_cast<LPPROC_THREAD_ATTRIBUTE_LIST>(attributes.data());
    if (!InitializeProcThreadAttributeList(attribute_list, 1, 0, &attribute_bytes))
    { *error = "cannot initialize player solver handles"; return false; }
    struct AttributeCleanup
    {
        LPPROC_THREAD_ATTRIBUTE_LIST list;
        ~AttributeCleanup() { DeleteProcThreadAttributeList(list); }
    } attribute_cleanup{attribute_list};
    HANDLE handles[] = {input.value, stdout_write.value, stderr_write.value};
    if (!UpdateProcThreadAttribute(attribute_list, 0, PROC_THREAD_ATTRIBUTE_HANDLE_LIST,
        handles, sizeof(handles), nullptr, nullptr))
    { *error = "cannot restrict player solver handles"; return false; }
    STARTUPINFOEXW startup{};
    startup.StartupInfo.cb = sizeof(startup);
    startup.StartupInfo.dwFlags = STARTF_USESTDHANDLES | STARTF_USESHOWWINDOW;
    startup.StartupInfo.wShowWindow = SW_HIDE;
    startup.StartupInfo.hStdInput = input.value;
    startup.StartupInfo.hStdOutput = stdout_write.value;
    startup.StartupInfo.hStdError = stderr_write.value;
    startup.lpAttributeList = attribute_list;
    PROCESS_INFORMATION process{};
    std::vector<wchar_t> environment;
    if (!child_environment(&environment)) { *error = "cannot prepare player runtime environment"; return false; }
    std::wstring command = quoted(executable.wstring()) +
        L" run --ext=js --no-code-cache --no-prompt --no-remote --no-npm --cached-only"
        L" --no-lock --node-modules-dir=none --no-config -";
    if (!CreateProcessW(executable.c_str(), command.data(), nullptr, nullptr, TRUE,
        CREATE_NO_WINDOW | CREATE_SUSPENDED | EXTENDED_STARTUPINFO_PRESENT | CREATE_UNICODE_ENVIRONMENT,
        environment.data(), nullptr, &startup.StartupInfo, &process))
    { *error = "cannot start bundled JavaScript runtime"; return false; }
    Handle child(process.hProcess), thread(process.hThread);
    if (!AssignProcessToJobObject(job.value, child.value) || ResumeThread(thread.value) == DWORD(-1))
    {
        TerminateProcess(child.value, 1);
        WaitForSingleObject(child.value, 2000);
        *error = "cannot start bounded player solver"; return false;
    }
    stdout_write.close(); stderr_write.close();
    std::string diagnostic;
    const auto deadline = std::chrono::steady_clock::now() + kSolverTimeout;
    bool finished = false;
    for (;;)
    {
        if (!drain_pipe(stdout_read.value, kOutputLimit, output) ||
            !drain_pipe(stderr_read.value, 16384, &diagnostic))
        { *error = "player solver output exceeded its limit"; break; }
        if (cancelled && cancelled()) { *error = "cancelled"; break; }
        const DWORD state = WaitForSingleObject(child.value, 20);
        if (state == WAIT_OBJECT_0) { finished = true; break; }
        if (state == WAIT_FAILED) { *error = "player solver process wait failed"; break; }
        if (std::chrono::steady_clock::now() >= deadline) { *error = "player solver timed out"; break; }
    }
    if (!finished)
    {
        TerminateJobObject(job.value, 1);
        WaitForSingleObject(child.value, 2000);
        return false;
    }
    if (!drain_pipe(stdout_read.value, kOutputLimit, output) ||
        !drain_pipe(stderr_read.value, 16384, &diagnostic))
    { *error = "player solver output exceeded its limit"; return false; }
    DWORD exit_code = 1;
    GetExitCodeProcess(child.value, &exit_code);
    if (exit_code != 0)
    {
        // Do not expose a fetched player script or signed URL in UI errors.
        yt::log::line("windows solver: Deno exit=%lu diagnostic=%.*s", exit_code,
                      static_cast<int>(std::min<std::size_t>(diagnostic.size(), 2048)), diagnostic.c_str());
        *error = "bundled JavaScript runtime could not resolve this player"; return false;
    }
    return true;
}

int unhex(char ch)
{
    if (ch >= '0' && ch <= '9') return ch - '0';
    if (ch >= 'a' && ch <= 'f') return ch - 'a' + 10;
    if (ch >= 'A' && ch <= 'F') return ch - 'A' + 10;
    return -1;
}
std::string decoded(std::string_view value)
{
    std::string out;
    for (std::size_t i = 0; i < value.size(); ++i)
    {
        if (value[i] == '%' && i + 2 < value.size() && unhex(value[i + 1]) >= 0 && unhex(value[i + 2]) >= 0)
        { out += static_cast<char>(unhex(value[i + 1]) * 16 + unhex(value[i + 2])); i += 2; }
        else out += value[i];
    }
    return out;
}
std::string encoded(std::string_view value)
{
    constexpr char hex[] = "0123456789ABCDEF";
    std::string out;
    for (const unsigned char ch : value)
    {
        if ((ch >= 'a' && ch <= 'z') || (ch >= 'A' && ch <= 'Z') ||
            (ch >= '0' && ch <= '9') || ch == '-' || ch == '_' || ch == '.' || ch == '~') out += ch;
        else { out += '%'; out += hex[ch >> 4]; out += hex[ch & 15]; }
    }
    return out;
}
struct Parameter
{
    std::size_t offset = std::string::npos, length = 0;
    std::string value;
};
Parameter throttle(const std::string &url)
{
    Parameter out;
    for (const std::string_view prefix : {"?n=", "&n=", "/n/"})
    {
        const auto start = url.find(prefix);
        if (start == std::string::npos) continue;
        out.offset = start + prefix.size();
        const auto end = url.find_first_of(prefix == "/n/" ? "/?#" : "&#", out.offset);
        out.length = (end == std::string::npos ? url.size() : end) - out.offset;
        out.value = decoded(std::string_view(url).substr(out.offset, out.length));
        return out;
    }
    return out;
}
void add_unique(std::vector<std::string> *values, const std::string &value)
{
    if (!value.empty() && std::find(values->begin(), values->end(), value) == values->end()) values->push_back(value);
}
bool safe_player_url(const std::string &url)
{
    return url.rfind("https://www.youtube.com/s/player/", 0) == 0 && url.size() < 4096 &&
        url.find_first_of("\r\n\0", 0, 3) == std::string::npos;
}
std::string json_text(yyjson_val *object, const char *key)
{
    yyjson_val *value = yyjson_obj_get(object, key);
    return yyjson_is_str(value) ? std::string(yyjson_get_str(value), yyjson_get_len(value)) : std::string();
}
bool solve(const fs::path &root, const std::string &player_url,
           const std::vector<std::string> &n_values, const std::vector<std::string> &s_values,
           const std::function<bool()> &cancelled,
           std::map<std::string, std::string> *n_results, std::map<std::string, std::string> *s_results,
           std::string *error)
{
    static std::mutex cache_mutex;
    static std::string cached_url, cached_player;
    using Key = std::pair<std::string, std::string>;
    static std::map<Key, std::string> cached_n, cached_s;
    static std::map<std::string, std::string> unsupported_players;
    {
        std::lock_guard<std::mutex> lock(cache_mutex);
        const auto unsupported = unsupported_players.find(player_url);
        if (unsupported != unsupported_players.end()) { *error = unsupported->second; return false; }
        bool complete = true;
        for (unsigned kind = 0; kind < 2; ++kind)
        {
            const auto &values = kind == 0 ? n_values : s_values;
            const auto &cache = kind == 0 ? cached_n : cached_s;
            auto &results = kind == 0 ? *n_results : *s_results;
            for (const auto &value : values)
            {
                const auto found = cache.find({player_url, value});
                if (found == cache.end()) complete = false;
                else results.emplace(value, found->second);
            }
        }
        if (complete) return true;
    }
    std::string lib, core;
    if (!read_script(root / kCore, 128u << 10, "18da6ce0758b416e7ae645084f4f8801f9f9d59d6c477c05eaa0ff94ebd8cc00", &core) ||
        !read_script(root / kLib, 512u << 10, "c55987fe697e5b9ee18830163f7af85327e9bb5c3e674b969d38c8d205eaa577", &lib))
    { *error = "bundled YouTube solver is damaged; repair Pixel Museum Setup"; return false; }
    // Keep only the latest player script. Each Service request's HTTP is
    // cancellable; no disk cache, cookies or browser state are consulted.
    std::string player;
    { std::lock_guard<std::mutex> lock(cache_mutex); if (cached_url == player_url) player = cached_player; }
    if (player.empty())
    {
        yt::http::Request request;
        request.url = player_url;
        request.timeout_s = 12;
        request.max_bytes = kPlayerLimit;
        request.cancelled = cancelled;
        auto response = yt::http::perform(request);
        if (!response.http_ok() || response.body.empty())
        { *error = "cannot load public YouTube player script: " + (response.error.empty() ? std::to_string(response.status) : response.error); return false; }
        player = std::move(response.body);
        std::lock_guard<std::mutex> lock(cache_mutex);
        cached_url = player_url; cached_player = player;
    }
    yyjson_mut_doc *document = yyjson_mut_doc_new(nullptr);
    yyjson_mut_val *data = yyjson_mut_obj(document), *requests = yyjson_mut_arr(document);
    yyjson_mut_doc_set_root(document, data);
    yyjson_mut_obj_add_str(document, data, "type", "player");
    yyjson_mut_obj_add_str(document, data, "player", player.c_str());
    yyjson_mut_obj_add_bool(document, data, "output_preprocessed", false);
    yyjson_mut_obj_add_val(document, data, "requests", requests);
    for (unsigned kind = 0; kind < 2; ++kind)
    {
        const auto &values = kind == 0 ? n_values : s_values;
        if (values.empty()) continue;
        auto *request = yyjson_mut_obj(document), *challenges = yyjson_mut_arr(document);
        yyjson_mut_obj_add_str(document, request, "type", kind == 0 ? "n" : "sig");
        for (const auto &value : values) yyjson_mut_arr_add_str(document, challenges, value.c_str());
        yyjson_mut_obj_add_val(document, request, "challenges", challenges);
        yyjson_mut_arr_add_val(requests, request);
    }
    char *json = yyjson_mut_write(document, 0, nullptr);
    std::string script = std::move(lib);
    script += "\nObject.assign(globalThis, lib);\n";
    script += core;
    script += "\nconsole.log(JSON.stringify(jsc(";
    if (json) script += json;
    script += ")));\n";
    const bool serialized = json != nullptr;
    std::free(json);
    yyjson_mut_doc_free(document);
    if (!serialized) { *error = "cannot allocate YouTube solver input"; return false; }
    std::string output;
    if (!run_deno(root / kDeno, script, cancelled, &output, error)) return false;
    yyjson_doc *parsed = yyjson_read(output.data(), output.size(), 0);
    if (!parsed) { *error = "YouTube solver returned invalid JSON"; return false; }
    yyjson_val *result = yyjson_doc_get_root(parsed);
    yyjson_val *responses = yyjson_obj_get(result, "responses");
    bool ok = json_text(result, "type") != "error" && yyjson_is_arr(responses);
    std::size_t response_index = 0;
    for (unsigned kind = 0; ok && kind < 2; ++kind)
    {
        const auto &values = kind == 0 ? n_values : s_values;
        auto &results = kind == 0 ? *n_results : *s_results;
        if (values.empty()) continue;
        auto *response = yyjson_arr_get(responses, response_index++);
        if (json_text(response, "type") == "error") { ok = false; break; }
        auto *mapped = yyjson_obj_get(response, "data");
        for (const auto &value : values)
        {
            std::string transformed = json_text(mapped, value.c_str());
            if (transformed.empty() || transformed.size() > 8192 || transformed.rfind("enhanced_except_", 0) == 0)
            { ok = false; break; }
            results.emplace(value, std::move(transformed));
        }
    }
    yyjson_doc_free(parsed);
    {
        std::lock_guard<std::mutex> lock(cache_mutex);
        if (!ok)
        {
            *error = "official YouTube solver does not support this player";
            unsupported_players.emplace(player_url, *error);
            if (unsupported_players.size() > 32) unsupported_players.erase(unsupported_players.begin());
        }
        else
        {
            for (const auto &[value, transformed] : *n_results) cached_n[{player_url, value}] = transformed;
            for (const auto &[value, transformed] : *s_results) cached_s[{player_url, value}] = transformed;
            while (cached_n.size() > 256) cached_n.erase(cached_n.begin());
            while (cached_s.size() > 256) cached_s.erase(cached_s.begin());
        }
    }
    return ok;
}
}

bool transform_youtube_streams(const std::string &install_root, const std::string &player_js_url,
                               const yt::Format &video, const yt::Format *audio,
                               const std::function<bool()> &cancelled,
                               std::string *video_url, std::string *audio_url, std::string *error)
{
    if (!video_url || !audio_url || !error) return false;
    if (!safe_player_url(player_js_url)) { *error = "no supported public YouTube player script"; return false; }
    const auto root = tools_root(install_root);
    if (root.empty()) { *error = "bundled YouTube runtime is missing; repair Pixel Museum Setup"; return false; }
    std::vector<std::string> n_values, s_values;
    for (const yt::Format *format : {&video, audio})
    {
        if (!format) continue;
        if (format->url.size() > 32768 || format->cipher_s.size() > 8192)
        { *error = "YouTube stream parameters exceed their limit"; return false; }
        const auto n = throttle(format->url);
        if (n.value.size() > 8192) { *error = "YouTube player parameter exceeds its limit"; return false; }
        add_unique(&n_values, n.value);
        if (format->ciphered) add_unique(&s_values, format->cipher_s);
    }
    std::map<std::string, std::string> n_results, s_results;
    if (!solve(root, player_js_url, n_values, s_values, cancelled, &n_results, &s_results, error)) return false;
    const auto transform = [&](const yt::Format &format, std::string *url)
    {
        *url = format.url;
        const auto n = throttle(*url);
        if (!n.value.empty()) url->replace(n.offset, n.length, encoded(n_results.at(n.value)));
        if (format.ciphered)
        {
            const auto signature = s_results.find(format.cipher_s);
            if (signature == s_results.end()) return false;
            *url += url->find('?') == std::string::npos ? '?' : '&';
            *url += encoded(format.cipher_sp.empty() ? "signature" : format.cipher_sp) + '=' + encoded(signature->second);
        }
        return !url->empty();
    };
    if (!transform(video, video_url) || (audio && !transform(*audio, audio_url)))
    { *error = "YouTube player returned incomplete stream parameters"; return false; }
    yt::log::line("windows solver: official EJS 0.8.0 + Deno 2.9.8 transformed n=%u sig=%u",
                  static_cast<unsigned>(n_values.size()), static_cast<unsigned>(s_values.size()));
    return true;
}
}
#endif
