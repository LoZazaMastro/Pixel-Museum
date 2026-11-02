#if !defined(_WIN32)
#include "museum/database_updater.hpp"
#include "museum/collection_sha256.hpp"
#include "yt/http.hpp"
#include "third_party/nlohmann/json.hpp"
#include <atomic>
#include <cerrno>
#include <chrono>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <sys/stat.h>
#include <thread>
#include <unistd.h>

// Emulate the PS5 SDK import failure without changing the production platform
// macros or intercepting the proven open/fstat path.
static std::atomic<unsigned> lstat_calls{0};
extern "C" int __wrap_lstat(const char*,struct stat*) {
    ++lstat_calls;errno=ENOSYS;return -1;
}
namespace {
using Json=nlohmann::json;
const std::string payload=R"({"entries":[{"id":"descriptor-proof","title":"Proof","year":2000}]})";
std::string digest() {
    museum::CollectionSha256 hash;hash.update(payload.data(),payload.size());return hash.finish();
}
std::string read(const std::filesystem::path&path) {
    std::ifstream file(path,std::ios::binary);return std::string(std::istreambuf_iterator<char>(file),{});
}
void write(const std::filesystem::path&path,const std::string&text) {
    std::ofstream file(path,std::ios::binary);file<<text;
}
bool wait(museum::DatabaseUpdater&updater) {
    const auto end=std::chrono::steady_clock::now()+std::chrono::seconds(4);
    while(std::chrono::steady_clock::now()<end) {
        const auto phase=updater.snapshot().phase;
        if(phase!=museum::DatabaseUpdater::Phase::checking&&phase!=museum::DatabaseUpdater::Phase::downloading)return true;
        std::this_thread::sleep_for(std::chrono::milliseconds(2));
    }
    return false;
}
bool install(museum::DatabaseUpdater&updater,const std::filesystem::path&app,const std::filesystem::path&data) {
    return updater.configure(app.string(),data.string(),"http://127.0.0.1:8181/feed")&&updater.check()&&wait(updater)&&updater.snapshot().phase==museum::DatabaseUpdater::Phase::available&&updater.install()&&wait(updater);
}
}
namespace yt::http {
Response perform(const Request&request) {
    Response response;response.status=200;
    if(request.url.ends_with("/feed")) {
        response.body=Json({{"schema_version",1},{"database_id","pixel-museum"},{"revision",9},{"version","descriptor-stat-proof"},{"files",Json::array({{{"path","content/catalog.json"},{"url","http://127.0.0.1:8181/catalog"},{"sha256",digest()},{"bytes",payload.size()}}})}}).dump();
    } else if(!request.on_body||!request.on_body(payload))response.error="fixture body rejected";
    return response;
}
}
int main(int argc,char**argv) {
    if(argc!=2)return 2;
    namespace fs=std::filesystem;using Phase=museum::DatabaseUpdater::Phase;
    const auto root=fs::absolute(argv[1]);if(fs::exists(root))return 3;
    fs::create_directories(root/"app");fs::create_directory(root/"plain");
    museum::DatabaseUpdater updater;
    if(!install(updater,root/"app",root/"plain")||updater.snapshot().phase!=Phase::ready) {
        std::cerr<<"FAIL ordinary storage with lstat=ENOSYS: "<<updater.snapshot().error<<" calls="<<lstat_calls<<'\n';return 4;
    }
    if(read(root/"plain/database/blobs"/digest())!=payload)return 5;
    updater.shutdown();
    museum::DatabaseUpdater reader;
    if(!reader.configure((root/"app").string(),(root/"plain").string(),"http://127.0.0.1:8181/feed")||reader.snapshot().current_revision!=9)return 6;
    reader.shutdown();
    fs::create_directory(root/"outside");write(root/"outside/sentinel","unchanged");
    fs::create_directory(root/"linked");fs::create_directory_symlink(root/"outside",root/"linked/database");
    if(!install(updater,root/"app",root/"linked")||updater.snapshot().phase!=Phase::failed||fs::exists(root/"outside/blobs")||read(root/"outside/sentinel")!="unchanged")return 7;
    updater.shutdown();fs::create_directory(root/"fifo");
    if(::mkfifo((root/"fifo/database").c_str(),0600)!=0)return 8;
    if(!install(updater,root/"app",root/"fifo")||updater.snapshot().phase!=Phase::failed)return 9;
    updater.shutdown();fs::create_directories(root/"leaf/database/blobs");
    fs::create_symlink(root/"outside/sentinel",root/"leaf/database/blobs"/digest());
    if(!install(updater,root/"app",root/"leaf")||updater.snapshot().phase!=Phase::ready||read(root/"outside/sentinel")!="unchanged"||read(root/"leaf/database/blobs"/digest())!=payload)return 10;
    updater.shutdown();
    if(lstat_calls.load()!=0)return 11;
    std::cout<<"PASS lstat=ENOSYS: verified install+next-configure activation; directory symlink rejected; FIFO rejected without blocking; blob symlink never followed; lstat calls=0\n";
}
#endif
