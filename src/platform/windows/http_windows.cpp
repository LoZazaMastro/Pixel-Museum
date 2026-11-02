#if defined(_WIN32)

// Pixel Museum - Native Windows HTTP transport and DNS diagnostics.
// Copyright (C) 2026 BlackBearReloaded
// Copyright (C) 2026 Andrea Sgarro
// SPDX-License-Identifier: GPL-3.0-or-later

#ifndef WIN32_LEAN_AND_MEAN
#define WIN32_LEAN_AND_MEAN
#endif
#include <winsock2.h>
#include <ws2tcpip.h>

#include "yt/http.hpp"
#include "yt/http_curl_cancel.hpp"
#include "platform/windows/curl_windows.hpp"

#include <algorithm>
#include <array>
#include <limits>
#include <memory>
#include <mutex>
#include <string>
#include <vector>

namespace yt::http
{
namespace
{

struct Sink
{
    std::string *body = nullptr;
    std::size_t limit = 0;
    const std::function<bool(std::string_view)> *stream = nullptr;
    bool limit_reached = false;
};

std::size_t on_write(char *data, std::size_t size, std::size_t count, void *opaque)
{
    auto &sink = *static_cast<Sink *>(opaque);
    if (size != 0 && count > std::numeric_limits<std::size_t>::max() / size)
        return 0;
    const std::size_t bytes = size * count;
    if (bytes == 0)
        return 0;
    // libcurl callbacks may not unwind through C. A failed allocation or a
    // consumer exception is reported as the same transport write failure.
    try
    {
        if (sink.stream != nullptr && *sink.stream)
            return (*sink.stream)(std::string_view(data, bytes)) ? bytes : 0;
        const std::size_t used = sink.body->size();
        const std::size_t room = sink.limit > used ? sink.limit - used : 0;
        const std::size_t take = std::min(bytes, room);
        sink.body->append(data, take);
        sink.limit_reached = take != bytes;
        return take == bytes ? bytes : 0;
    }
    catch (...)
    {
        return 0;
    }
}

const char *describe(CURLcode code)
{
    switch (code)
    {
    case CURLE_OPERATION_TIMEDOUT: return "timeout";
    case CURLE_COULDNT_RESOLVE_HOST:
    case CURLE_COULDNT_RESOLVE_PROXY: return "resolve";
    case CURLE_COULDNT_CONNECT: return "connect";
    case CURLE_SSL_CONNECT_ERROR:
    case CURLE_PEER_FAILED_VERIFICATION:
    case CURLE_SSL_CERTPROBLEM: return "tls";
    case CURLE_WRITE_ERROR: return "write";
    case CURLE_READ_ERROR: return "read";
    case CURLE_SEND_ERROR: return "send";
    case CURLE_RECV_ERROR: return "recv";
    case CURLE_GOT_NOTHING: return "empty";
    case CURLE_TOO_MANY_REDIRECTS: return "redirect";
    case CURLE_OUT_OF_MEMORY: return "memory";
    case CURLE_ABORTED_BY_CALLBACK: return "cancelled";
    default: return curl_easy_strerror(code);
    }
}

int on_progress(void *opaque, curl_off_t, curl_off_t, curl_off_t, curl_off_t)
{
    const auto &request = *static_cast<const Request *>(opaque);
    return request.cancelled && request.cancelled() ? 1 : 0;
}

// Each request owns a handle exclusively. Idle handles preserve TLS sessions
// and HTTP/2 connections between thumbnail, metadata and authentication calls.
struct HandlePool
{
    std::mutex mutex;
    std::vector<CURL *> idle;
    ~HandlePool()
    {
        for (CURL *handle : idle)
            curl_easy_cleanup(handle);
    }
};

HandlePool &handle_pool()
{
    static HandlePool pool;
    return pool;
}

CURL *take_handle()
{
    auto &pool = handle_pool();
    std::lock_guard<std::mutex> lock(pool.mutex);
    if (pool.idle.empty())
        return curl_easy_init();
    CURL *handle = pool.idle.back();
    pool.idle.pop_back();
    curl_easy_reset(handle);
    return handle;
}

void give_back(CURL *handle, CURLcode result)
{
    if (result == CURLE_OK)
    {
        auto &pool = handle_pool();
        std::lock_guard<std::mutex> lock(pool.mutex);
        if (pool.idle.size() < 8)
        {
            pool.idle.push_back(handle);
            return;
        }
    }
    curl_easy_cleanup(handle);
}

} // namespace

std::string describe_lookup(const std::string &host)
{
    if (!hui::windows::ensure_curl())
        return "Windows DNS: network initialization failed";
    addrinfo hints{};
    hints.ai_family = AF_UNSPEC;
    hints.ai_socktype = SOCK_STREAM;
    addrinfo *addresses = nullptr;
    const int result = getaddrinfo(host.c_str(), nullptr, &hints, &addresses);
    if (result != 0)
        return "Windows DNS " + host + ": lookup failed (" + std::to_string(result) + ")";
    std::unique_ptr<addrinfo, decltype(&freeaddrinfo)> owner(addresses, &freeaddrinfo);
    std::vector<std::string> resolved;
    for (const addrinfo *entry = addresses; entry != nullptr && resolved.size() < 4;
         entry = entry->ai_next)
    {
        const void *address = nullptr;
        if (entry->ai_family == AF_INET)
            address = &reinterpret_cast<const sockaddr_in *>(entry->ai_addr)->sin_addr;
        else if (entry->ai_family == AF_INET6)
            address = &reinterpret_cast<const sockaddr_in6 *>(entry->ai_addr)->sin6_addr;
        char text[INET6_ADDRSTRLEN]{};
        if (address != nullptr && inet_ntop(entry->ai_family, address, text, sizeof(text)) != nullptr &&
            std::find(resolved.begin(), resolved.end(), text) == resolved.end())
            resolved.emplace_back(text);
    }
    std::string description = "Windows DNS " + host + ": ";
    for (std::size_t index = 0; index < resolved.size(); ++index)
    {
        if (index != 0)
            description += ", ";
        description += resolved[index];
    }
    return description + (resolved.empty() ? "no addresses" : "");
}

Response perform(const Request &request)
{
    Response response;
    if (!hui::windows::ensure_curl())
    {
        response.error = "init";
        return response;
    }
    CURL *handle = take_handle();
    if (handle == nullptr)
    {
        response.error = "init";
        return response;
    }
    hui::windows::configure_curl(handle);
    Sink sink{&response.body, request.max_bytes, &request.on_body};
    curl_slist *headers = nullptr;
    for (const Header &header : request.headers)
    {
        const std::string line = header.name + ": " + header.value;
        curl_slist *updated = curl_slist_append(headers, line.c_str());
        if (updated == nullptr)
        {
            curl_slist_free_all(headers);
            curl_easy_cleanup(handle);
            response.error = "memory";
            return response;
        }
        headers = updated;
    }
    const long timeout = request.timeout_s > 0 ? request.timeout_s : 20L;
    (void)curl_easy_setopt(handle, CURLOPT_URL, request.url.c_str());
    (void)curl_easy_setopt(handle, CURLOPT_FOLLOWLOCATION, 1L);
    (void)curl_easy_setopt(handle, CURLOPT_PROTOCOLS_STR, "https");
    (void)curl_easy_setopt(handle, CURLOPT_REDIR_PROTOCOLS_STR, "https");
    (void)curl_easy_setopt(handle, CURLOPT_MAXREDIRS, 5L);
    (void)curl_easy_setopt(handle, CURLOPT_TIMEOUT, timeout);
    (void)curl_easy_setopt(handle, CURLOPT_CONNECTTIMEOUT, std::min(timeout, 15L));
    (void)curl_easy_setopt(handle, CURLOPT_ACCEPT_ENCODING, "");
    (void)curl_easy_setopt(handle, CURLOPT_WRITEFUNCTION, &on_write);
    (void)curl_easy_setopt(handle, CURLOPT_WRITEDATA, &sink);
    if (request.cancelled)
    {
        (void)curl_easy_setopt(handle, CURLOPT_XFERINFOFUNCTION, &on_progress);
        (void)curl_easy_setopt(handle, CURLOPT_XFERINFODATA, &request);
        (void)curl_easy_setopt(handle, CURLOPT_NOPROGRESS, 0L);
    }
    if (headers != nullptr)
        (void)curl_easy_setopt(handle, CURLOPT_HTTPHEADER, headers);
    if (request.method == "POST")
    {
        (void)curl_easy_setopt(handle, CURLOPT_POST, 1L);
        (void)curl_easy_setopt(handle, CURLOPT_POSTFIELDS, request.body.data());
        (void)curl_easy_setopt(handle, CURLOPT_POSTFIELDSIZE_LARGE,
                               static_cast<curl_off_t>(request.body.size()));
    }
    else if (request.method == "HEAD")
        (void)curl_easy_setopt(handle, CURLOPT_NOBODY, 1L);
    else if (request.method != "GET")
    {
        (void)curl_easy_setopt(handle, CURLOPT_CUSTOMREQUEST, request.method.c_str());
        if (!request.body.empty())
        {
            (void)curl_easy_setopt(handle, CURLOPT_POSTFIELDS, request.body.data());
            (void)curl_easy_setopt(handle, CURLOPT_POSTFIELDSIZE_LARGE,
                                   static_cast<curl_off_t>(request.body.size()));
        }
    }
    const CURLcode result = detail::perform_with_cancellation(handle, request);
    (void)curl_easy_getinfo(handle, CURLINFO_RESPONSE_CODE, &response.status);
    if (result != CURLE_OK)
        response.error = sink.limit_reached ? "response too large" : describe(result);
    // Reset/destroy the handle before the local header list disappears.
    (void)curl_easy_setopt(handle, CURLOPT_HTTPHEADER, nullptr);
    curl_slist_free_all(headers);
    give_back(handle, result);
    return response;
}

} // namespace yt::http

#endif // _WIN32
