// Installer contract tests; real authenticated transport is tested separately.
// SPDX-License-Identifier: GPL-3.0-or-later
#include "platform/collection_writer.hpp"
#include "third_party/nlohmann/json.hpp"
#include <cerrno>
#include <cstdlib>
#include <fcntl.h>
#include <fstream>
#include <sys/stat.h>
#include <unistd.h>
thread_local bool pm_writer_test_sink=false;
namespace {
std::string setting(const char*key){const auto*value=std::getenv(key);return value?value:"";}
void event(const char*name,std::uint64_t bytes=0){const auto root=setting("PM_WRITER_TEST_ROOT");if(root.empty())return;std::ofstream file(root+"/writer-events.jsonl",std::ios::app);file<<nlohmann::json({{"event",name},{"bytes",bytes}}).dump()<<'\n';}
}
namespace museum {
CollectionWriter::~CollectionWriter(){stop();}
bool CollectionWriter::start(const std::vector<Pack>&packs,std::string&error){packs_=packs;event("start");if(setting("PM_SERVICE_TEST_MODE")=="unavailable"){error_=error="simulated loader unavailable";errno=ECONNREFUSED;return false;}authenticated_=true;return true;}
bool CollectionWriter::open(std::size_t index,std::uint64_t&actual,std::string&error){
 if(!authenticated_||opened_||index>=packs_.size()){error_=error="invalid test service open";errno=EINVAL;return false;}
 const auto path=setting("PM_WRITER_TEST_ROOT")+"/collection/downloads/"+packs_[index].sha+".tar.part";fd_=::open(path.c_str(),O_WRONLY|O_CREAT|O_APPEND|O_NOFOLLOW,0600);if(fd_<0){error_=error="test service open failed";return false;}
 if(setting("PM_SERVICE_TEST_MODE")=="rewind"&&index==0)assert(!ftruncate(fd_,0));
 struct stat info{};assert(!fstat(fd_,&info));actual=offset_=info.st_size;expected_=packs_[index].bytes;opened_=true;event("open",actual);return true;
}
std::ptrdiff_t CollectionWriter::write(const void*data,std::size_t bytes){
 if(!opened_||bytes>expected_-offset_){errno=EINVAL;error_="invalid test service write";return -1;}
 pm_writer_test_sink=true;const auto written=::write(fd_,data,bytes);const auto code=errno;pm_writer_test_sink=false;if(written<0){error_="test service storage write failed";errno=code;return -1;}offset_+=written;event("write",written);return written;
}
bool CollectionWriter::finish(std::string&error){
 if(!opened_){error_=error="test service has no open pack";errno=EINVAL;return false;}
 const bool flushed=fsync(fd_)==0;const auto code=errno;const bool closed=::close(fd_)==0;fd_=-1;opened_=false;event("finish",offset_);
 if(!flushed||!closed){error_=error="test service sync failed";errno=code;return false;}if(setting("PM_SERVICE_TEST_MODE")=="finish-fail"){error_=error="simulated lost durable acknowledgement";errno=EIO;return false;}return true;
}
void CollectionWriter::stop(){if(fd_>=0){fsync(fd_);::close(fd_);fd_=-1;}if(authenticated_||!packs_.empty())event("stop");opened_=authenticated_=false;packs_.clear();}
}
