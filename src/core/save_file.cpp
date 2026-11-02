// ps5-homebrew-ui - Checked save container and atomic file writes.
// Copyright (C) 2026 BlackBearReloaded
// SPDX-License-Identifier: GPL-3.0-or-later

#include "core/save_file.hpp"

#include <cerrno>
#include <dirent.h>
#include <cstring>
#include <fcntl.h>
#include <sys/stat.h>
#include <unistd.h>
#include <mutex>
#include <algorithm>
#if defined(_WIN32)
#include <cstdio>
#ifndef NOMINMAX
#define NOMINMAX
#endif
#include <windows.h>
#endif

namespace hui::save
{

namespace
{

std::mutex overlay_mutex;
std::map<std::string, std::string> read_overlay;
std::string normalized_read_path(std::string value) {
    std::replace(value.begin(), value.end(), '\\', '/');
    std::string normalized;
    normalized.reserve(value.size());
    std::size_t at = 0;
#if defined(_WIN32)
    // Keep the UNC prefix distinct from a local rooted path.
    if (value.size() > 1 && value[0] == '/' && value[1] == '/') {
        normalized = "//";
        at = 2;
    }
#endif
    for (; at < value.size(); ++at) {
        const char ch = value[at];
        if (ch != '/' || normalized.empty() || normalized.back() != '/')
            normalized.push_back(ch);
    }
    return normalized;
}

constexpr char kMagic[4] = {'H', 'U', 'I', 'L'};
constexpr std::size_t kHeader = 12;
constexpr std::size_t kTrailer = 4;

void put_u16(std::string &out, std::uint16_t value)
{
    out.push_back(static_cast<char>(value & 0xff));
    out.push_back(static_cast<char>(value >> 8));
}

void put_u32(std::string &out, std::uint32_t value)
{
    for (int shift = 0; shift < 32; shift += 8)
        out.push_back(static_cast<char>((value >> shift) & 0xff));
}

std::uint32_t get_u32(std::string_view data, std::size_t offset)
{
    std::uint32_t value = 0;
    for (int i = 3; i >= 0; --i)
        value =
            (value << 8) | static_cast<unsigned char>(data[offset + static_cast<std::size_t>(i)]);
    return value;
}

std::uint16_t get_u16(std::string_view data, std::size_t offset)
{
    return static_cast<std::uint16_t>(static_cast<unsigned char>(data[offset]) |
                                      (static_cast<unsigned char>(data[offset + 1]) << 8));
}

std::string errno_text(const char *operation)
{
    return std::string(operation) + ": " + std::strerror(errno);
}

} // namespace

std::uint32_t crc32(std::string_view data)
{
    std::uint32_t crc = 0xffffffffu;
    for (char c : data)
    {
        crc ^= static_cast<unsigned char>(c);
        for (int bit = 0; bit < 8; ++bit)
            crc = (crc >> 1) ^ (0xedb88320u & (0u - (crc & 1u)));
    }
    return ~crc;
}

std::string encode(Kind kind, std::uint16_t version, std::string_view payload)
{
    std::string out(kMagic, sizeof(kMagic));
    put_u16(out, version);
    put_u16(out, static_cast<std::uint16_t>(kind));
    put_u32(out, static_cast<std::uint32_t>(payload.size()));
    out.append(payload);
    put_u32(out, crc32(out));
    return out;
}

Decoded decode(Kind kind, std::string_view data)
{
    Decoded result;
    if (data.size() < kHeader + kTrailer || std::memcmp(data.data(), kMagic, 4) != 0)
    {
        result.error = "not a ps5-homebrew-ui save";
        return result;
    }
    if (get_u16(data, 6) != static_cast<std::uint16_t>(kind))
    {
        result.error = "unexpected save kind";
        return result;
    }
    const std::uint32_t size = get_u32(data, 8);
    if (data.size() != kHeader + size + kTrailer)
    {
        result.error = "save size mismatch";
        return result;
    }
    if (crc32(data.substr(0, kHeader + size)) != get_u32(data, kHeader + size))
    {
        result.error = "save checksum mismatch";
        return result;
    }
    result.ok = true;
    result.version = get_u16(data, 4);
    result.payload.assign(data.substr(kHeader, size));
    return result;
}

std::string write_atomic(const std::string &path, std::string_view data)
{
    const std::string temporary = path + ".tmp";
    int flags = O_WRONLY | O_CREAT | O_TRUNC;
#if defined(_WIN32)
    flags |= O_BINARY;
#endif
    const int fd = ::open(temporary.c_str(), flags, 0644);
    if (fd < 0)
        return errno_text("open");
    std::size_t written = 0;
    while (written < data.size())
    {
        const ssize_t result = ::write(fd, data.data() + written, data.size() - written);
        if (result < 0)
        {
            if (errno == EINTR)
                continue;
            const std::string error = errno_text("write");
            ::close(fd);
            ::unlink(temporary.c_str());
            return error;
        }
        written += static_cast<std::size_t>(result);
    }
    if (::fsync(fd) != 0)
    {
        const std::string error = errno_text("fsync");
        ::close(fd);
        ::unlink(temporary.c_str());
        return error;
    }
    if (::close(fd) != 0)
    {
        ::unlink(temporary.c_str());
        return errno_text("close");
    }
#if defined(_WIN32)
    const auto utf16=[](const std::string& value){
        const int n=MultiByteToWideChar(CP_UTF8,MB_ERR_INVALID_CHARS,value.data(),int(value.size()),nullptr,0);
        if(n<=0)return std::wstring();
        std::wstring text(std::size_t(n),L'\0');
        MultiByteToWideChar(CP_UTF8,MB_ERR_INVALID_CHARS,value.data(),int(value.size()),text.data(),n);
        return text;
    };
    const auto from=utf16(temporary),to=utf16(path);
    if(from.empty()||to.empty()||!MoveFileExW(from.c_str(),to.c_str(),MOVEFILE_REPLACE_EXISTING|MOVEFILE_WRITE_THROUGH)){
        const auto code=GetLastError();::unlink(temporary.c_str());
        return "atomic replacement: Windows error "+std::to_string(code);
    }
#else
    if (::rename(temporary.c_str(), path.c_str()) != 0)
    {
        // Some filesystems refuse to replace an existing file.
        ::unlink(path.c_str());
        if (::rename(temporary.c_str(), path.c_str()) != 0)
        {
            const std::string error = errno_text("rename");
            ::unlink(temporary.c_str());
            return error;
        }
    }
#endif
    return {};
}

void set_read_overlay(std::map<std::string, std::string> files) {
    std::map<std::string, std::string> normalized;
    for (auto& file : files)
        normalized.emplace(normalized_read_path(file.first), std::move(file.second));
    std::lock_guard<std::mutex> lock(overlay_mutex);
    read_overlay = std::move(normalized);
}

std::string resolve_read_path(const std::string& path) {
    std::lock_guard<std::mutex> lock(overlay_mutex);
    const auto it = read_overlay.find(normalized_read_path(path));
    return it == read_overlay.end() ? path : it->second;
}

bool read_file(const std::string &requested_path, std::string *data, std::size_t max_bytes)
{
    const std::string path = resolve_read_path(requested_path);
#if defined(_WIN32)
    // Explicit binary mode preserves asset bytes independently of the CRT's
    // process default. Buffered reads avoid thousands of small descriptor
    // reads for baked fonts and the catalogue on Windows file systems.
    std::FILE *file = std::fopen(path.c_str(), "rb");
    if (file == nullptr)
        return false;
    std::string buffer;
    char chunk[64u << 10];
    for (;;)
    {
        const std::size_t count = std::fread(chunk, 1, sizeof(chunk), file);
        if (count > max_bytes - buffer.size())
        {
            std::fclose(file);
            return false;
        }
        buffer.append(chunk, count);
        if (count < sizeof(chunk))
        {
            const bool complete = std::feof(file) != 0 && std::ferror(file) == 0;
            const int closed = std::fclose(file);
            if (!complete || closed != 0)
                return false;
            *data = std::move(buffer);
            return true;
        }
    }
#else
    const int fd = ::open(path.c_str(), O_RDONLY);
    if (fd < 0)
        return false;
    std::string buffer;
    char chunk[4096];
    for (;;)
    {
        const ssize_t result = ::read(fd, chunk, sizeof(chunk));
        if (result < 0)
        {
            if (errno == EINTR)
                continue;
            ::close(fd);
            return false;
        }
        if (result == 0)
            break;
        buffer.append(chunk, static_cast<std::size_t>(result));
        if (buffer.size() > max_bytes)
        {
            ::close(fd);
            return false;
        }
    }
    ::close(fd);
    *data = std::move(buffer);
    return true;
#endif
}

bool ensure_directory(const std::string &path)
{
    if (::mkdir(path.c_str(), 0755) == 0 || errno == EEXIST)
    {
        struct stat info
        {
        };
        return ::stat(path.c_str(), &info) == 0 && S_ISDIR(info.st_mode);
    }
    return false;
}

std::vector<std::string> list_files(const std::string &directory)
{
    std::vector<std::string> names;
    std::string index;
    if (read_file(directory + "/index.txt", &index, 1u << 20))
    {
        std::size_t start = 0;
        while (start < index.size())
        {
            std::size_t end = index.find('\n', start);
            if (end == std::string::npos)
                end = index.size();
            std::string name = index.substr(start, end - start);
            if (!name.empty() && name.back() == '\r')
                name.pop_back();
            if (!name.empty() && name.find('/') == std::string::npos && name != "index.txt")
                names.push_back(std::move(name));
            start = end + 1;
        }
        return names;
    }
    if (DIR *dir = ::opendir(directory.c_str()))
    {
        while (const dirent *entry = ::readdir(dir))
        {
            const std::string name = entry->d_name;
            if (name != "." && name != ".." && name != "index.txt")
                names.push_back(name);
        }
        ::closedir(dir);
    }
    return names;
}

} // namespace hui::save
