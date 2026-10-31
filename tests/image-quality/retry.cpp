// Pixel Museum - real worker HTTP recovery, visibility, cooldown and stop checks.
// SPDX-License-Identifier: GPL-3.0-or-later
#include "platform/media.hpp"
#include "platform/media_retry.hpp"
#include "gfx/renderer.hpp"
#include "yt/http.hpp"
#include <cassert>
#include <chrono>
#include <cstdio>
#include <map>
#include <mutex>
#include <string>
#include <thread>
namespace {
using Clock=std::chrono::steady_clock;
std::mutex calls_mutex;
std::map<std::string,unsigned> calls;
std::map<std::string,Clock::time_point> first_call;
unsigned count(const std::string&url){std::lock_guard<std::mutex>lock(calls_mutex);return calls[url];}
std::string png(){FILE*f=std::fopen("build/photo-fixtures/small.png","rb");assert(f);std::fseek(f,0,SEEK_END);std::string b(std::ftell(f),'\0');std::rewind(f);assert(std::fread(b.data(),1,b.size(),f)==b.size());std::fclose(f);return b;}
template<class Predicate>void until(Predicate done,unsigned timeout=8500){const auto start=Clock::now();while(!done()){assert(Clock::now()-start<std::chrono::milliseconds(timeout));std::this_thread::sleep_for(std::chrono::milliseconds(2));}}
}
namespace yt::http {
Response perform(const Request&r){unsigned n;{std::lock_guard<std::mutex>lock(calls_mutex);n=++calls[r.url];if(n==1)first_call[r.url]=Clock::now();}
    Response out;out.status=200;
    if(r.url.find("permanent")!=std::string::npos)out.status=404;
    else if(r.url.find("document")!=std::string::npos||r.url.find("steady")!=std::string::npos)out.status=503;
    else if(r.url.find("recovery")!=std::string::npos&&n==1)out.status=429;
    else if(r.url.find("hidden")!=std::string::npos&&n==1)out.status=503;
    out.body=r.url.find("corrupt")!=std::string::npos?"not an image":png();return out;
}}
namespace hui::gfx {
Renderer::~Renderer()=default;GlBatch::~GlBatch()=default;Backdrop::~Backdrop()=default;Canvas::~Canvas()=default;
std::uint32_t GlBatch::create_texture(int,int,const std::uint8_t*){assert(false&&"This worker-only test must not upload GL textures");return 0;}
}
int main(){
    using museum::media::detail::ImageRetry;ImageRetry policy;
    for(long permanent:{0L,200L,400L,401L,403L,404L,501L,505L,511L,599L}){policy.failed(permanent,10);assert(!policy.eligible(true,true,1000000));}
    for(long temporary:{429L,500L,502L,503L,504L}){
        policy.reset();std::uint64_t now=100;
        for(auto delay:{5000u,20000u,60000u}){policy.failed(temporary,now);assert(policy.due==now+delay);assert(!policy.eligible(true,true,now+delay-1));assert(policy.eligible(true,true,now+delay));assert(!policy.eligible(true,false,now+delay));assert(!policy.eligible(false,true,now+delay));now+=delay;}
        policy.failed(temporary,now);assert(policy.failures==4&&policy.due==ImageRetry::never);
        for(unsigned i=0;i<10000;++i)assert(!policy.eligible(true,true,now+i+100000));
    }
    policy.reset();assert(policy.failures==0);assert(ImageRetry::after(ImageRetry::never-1,5000)==ImageRetry::never);
    const std::string a="https://rate.test/recovery",b="https://rate.test/after-rate-limit",h="https://hidden.test/hidden",p="https://permanent.test/permanent",d="https://document.test/document",s="https://steady.test/steady",bad="https://corrupt.test/corrupt",independent="https://another.test/healthy";
    museum::media::RemoteCache cache;
    const auto root="build/photo-retry-cache-"+std::to_string(Clock::now().time_since_epoch().count());assert(cache.start(root));
    cache.set_visible({a,p,d,s,bad});cache.request(a);
    until([&]{return cache.get(a).state==museum::media::State::failed;});
    cache.request(b);cache.request(h);cache.request(p);cache.request(d,false);cache.request(s);cache.request(bad);cache.request(independent);
    until([&]{return count(independent)==1&&cache.get(h).state==museum::media::State::failed&&cache.get(s).state==museum::media::State::failed;});
    assert(count(b)==0); // Another URL on the rate-limited origin must also wait.
    for(unsigned i=0;i<10000;++i){cache.request(a);cache.request(h);cache.request(p);cache.request(d,false);cache.request(bad);cache.set_visible({a,p,d,s,bad});}
    assert(count(a)==1&&count(h)==1&&count(p)==1&&count(d)==1&&count(bad)==1);
    until([&]{return cache.get(a).state==museum::media::State::ready&&count(s)==2&&count(b)==1;});
    assert(count(a)==2&&count(h)==1&&count(p)==1&&count(d)==1&&count(bad)==1);
    {std::lock_guard<std::mutex>lock(calls_mutex);assert(first_call[b]-first_call[a]>=std::chrono::milliseconds(4950));}
    cache.set_visible({});
    for(unsigned i=0;i<10000;++i)cache.request(h);
    std::this_thread::sleep_for(std::chrono::milliseconds(100));assert(count(h)==1);
    cache.set_visible({h});until([&]{return cache.get(h).state==museum::media::State::ready;});assert(count(h)==2);
    cache.set_visible({s});const auto stop=Clock::now();cache.stop();assert(Clock::now()-stop<std::chrono::milliseconds(500));
    puts("PASS: HTTP429/5xx recovery; 5/20/60s policy and three-retry ceiling; visible-only dispatch; shared host cooldown; permanent/decode/document exclusion; 10000 repeated requests do not storm; stop interrupts timer");
}
