// Pixel Museum - Shared native Windows HTTPS configuration.
// Copyright (C) 2026 Andrea Sgarro
// SPDX-License-Identifier: GPL-3.0-or-later

#pragma once

#include <curl/curl.h>

namespace hui::windows
{

inline bool ensure_curl()
{
    // Function-local initialization is shared by the API and media workers.
    // Cleanup belongs to process shutdown, after all native worker threads.
    static const CURLcode result = curl_global_init(CURL_GLOBAL_DEFAULT);
    return result == CURLE_OK;
}

inline void configure_curl(CURL *handle)
{
    (void)curl_easy_setopt(handle, CURLOPT_NOSIGNAL, 1L);
    // Bundled OpenSSL builds can use the Windows trust store too. Keep both
    // peer and hostname verification enabled and honor managed Windows roots.
#ifdef CURLSSLOPT_NATIVE_CA
    (void)curl_easy_setopt(handle, CURLOPT_SSL_OPTIONS,
                           static_cast<long>(CURLSSLOPT_NATIVE_CA));
#endif
    (void)curl_easy_setopt(handle, CURLOPT_SSL_VERIFYPEER, 1L);
    (void)curl_easy_setopt(handle, CURLOPT_SSL_VERIFYHOST, 2L);
}

} // namespace hui::windows
