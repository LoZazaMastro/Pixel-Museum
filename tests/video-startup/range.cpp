#include "platform/ps5/range_stream.hpp"
#include "platform/ps5/console_curl.h"
extern "C" {
#include <libavutil/error.h>
}
#include <chrono>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <thread>
extern "C" void console_curl_setup(CURL* c){curl_easy_setopt(c,CURLOPT_NOSIGNAL,1L);}
namespace yt::log {void line(const char*,...) {}}
int main(int argc,char** argv){
 if(argc!=3)return 2;
 const int expected=std::atoi(argv[2]);
 auto before=std::chrono::steady_clock::now();
 hui::ps5::RangeStream stream(argv[1],"fixture",nullptr,nullptr);std::string error;
 int result=stream.start(&error);
 if(expected==403||expected==401||expected==429){
  if(result!=(expected==429?AVERROR_HTTP_OTHER_4XX:expected==403?AVERROR_HTTP_FORBIDDEN:AVERROR_HTTP_UNAUTHORIZED))return 3;
  if(std::chrono::steady_clock::now()-before>std::chrono::milliseconds(500))return 4;
 }else{
  unsigned char bytes[8]={};if(result!=0||stream.read(bytes,4)!=4||std::memcmp(bytes,"RIFF",4)!=0)return 5;
 }
 // Give the detached, already-notified worker time to exit after scope.
 return 0;
}
