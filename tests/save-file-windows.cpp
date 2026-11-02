#if defined(_WIN32)
// Windows binary/bounded reads under the production UTF-8 process manifest.
// SPDX-License-Identifier: GPL-3.0-or-later
#include "core/save_file.hpp"
#include <cassert>
#include <cstdio>
#include <filesystem>
#include <fstream>
#include <string>
#include <windows.h>

namespace fs=std::filesystem;
std::string utf8(const fs::path&path){const auto bytes=path.generic_u8string();return {bytes.begin(),bytes.end()};}
int main(int argc,char**argv){
    assert(argc==2&&GetACP()==CP_UTF8);
    const auto root=fs::u8path(argv[1]);
    assert(root.is_absolute()&&!fs::exists(root));fs::create_directories(root);
    const auto path=root/fs::path(u8"Pixel Ω 日本.bin");
    std::string expected;expected.reserve(131077);
    for(unsigned n=0;n<131077;++n)expected.push_back(char(n%256));
    expected.replace(65534,5,"\r\n\x1a\r\n",5);
    {std::ofstream file(path,std::ios::binary);file.write(expected.data(),std::streamsize(expected.size()));assert(file);}
    std::string actual="unchanged";
    assert(hui::save::read_file(utf8(path),&actual,expected.size())&&actual==expected);
    actual="unchanged";
    assert(!hui::save::read_file(utf8(path),&actual,expected.size()-1)&&actual=="unchanged");
    assert(!hui::save::read_file(utf8(root/"missing.bin"),&actual,100)&&actual=="unchanged");
    assert(!hui::save::read_file(utf8(path),&actual,0)&&actual=="unchanged");
    {std::ofstream file(root/"empty.bin",std::ios::binary);assert(file);}
    assert(hui::save::read_file(utf8(root/"empty.bin"),&actual,0)&&actual.empty());
    {std::ofstream file(root/"boundary.bin",std::ios::binary);file.write(expected.data(),65536);assert(file);}
    assert(hui::save::read_file(utf8(root/"boundary.bin"),&actual,65536)&&actual==expected.substr(0,65536));
    assert(!hui::save::read_file(utf8(root),&actual,expected.size()));
    std::puts("PASS Windows read_file: binary CRLF/Ctrl-Z, Unicode filename under UTF-8 manifest, exact/oversize/zero limits, chunk boundary, missing file and directory");
}
#endif // _WIN32
