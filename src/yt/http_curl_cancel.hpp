// Optional cooperative cancellation for the two native curl transports.
// SPDX-License-Identifier: GPL-3.0-or-later
#pragma once
#include "yt/http.hpp"
#include <curl/curl.h>

namespace yt::http::detail
{
inline CURLcode perform_with_cancellation(CURL *handle, const Request &request)
{
    if (!request.cancelled) return curl_easy_perform(handle);
    if (request.cancelled()) return CURLE_ABORTED_BY_CALLBACK;
    CURLM *multi = curl_multi_init();
    if (!multi) return CURLE_OUT_OF_MEMORY;
    if (curl_multi_add_handle(multi, handle) != CURLM_OK)
    { curl_multi_cleanup(multi); return CURLE_FAILED_INIT; }
    struct Cleanup
    {
        CURLM *multi;
        CURL *easy;
        ~Cleanup() { curl_multi_remove_handle(multi, easy); curl_multi_cleanup(multi); }
    } cleanup{multi, handle};
    for (;;)
    {
        if (request.cancelled()) return CURLE_ABORTED_BY_CALLBACK;
        int running = 0;
        CURLMcode code;
        do { code = curl_multi_perform(multi, &running); }
        while (code == CURLM_CALL_MULTI_PERFORM);
        if (code != CURLM_OK) return CURLE_RECV_ERROR;
        if (!running)
        {
            int remaining = 0;
            while (CURLMsg *message = curl_multi_info_read(multi, &remaining))
                if (message->msg == CURLMSG_DONE && message->easy_handle == handle)
                    return message->data.result;
            return CURLE_FAILED_INIT;
        }
        // The easy progress callback may not run during a stalled TLS
        // handshake. Bound that wait too, without changing ordinary requests.
        if (curl_multi_poll(multi, nullptr, 0, 100, nullptr) != CURLM_OK)
            return CURLE_RECV_ERROR;
    }
}
}
