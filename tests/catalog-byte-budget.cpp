// Growing editorial and soundtrack data must fit the bounded native reader.
#include "museum/catalog.hpp"
#include <cassert>
#include <cstdio>
#include <fstream>

int main(int argc,char** argv){
    static_assert(museum::kCatalogByteLimit==(32u<<20));
    museum::Catalog catalog;
    std::string data=R"({"entries":[{"id":"budget","title":"Budget","year":1980}]})";
    data.resize(museum::kCatalogByteLimit,' ');
    assert(catalog.parse(data)&&catalog.find_entry("budget"));
    const char* path="build/research/catalog-byte-budget.json";
    {std::ofstream out(path,std::ios::binary);out.write(data.data(),data.size());assert(out.good());}
    assert(catalog.load(path)&&catalog.find_entry("budget"));
    data.push_back(' ');
    assert(!catalog.parse(data)&&catalog.find_entry("budget"));
    {std::ofstream out(path,std::ios::binary);out.write(data.data(),data.size());assert(out.good());}
    assert(!catalog.load(path)&&catalog.find_entry("budget"));
    assert(std::remove(path)==0);
    if(argc>1){
        assert(catalog.load(argv[1])&&!catalog.entries.empty());
        std::printf("Actual runtime catalogue PASS: %zu entries.\n",catalog.entries.size());
    }
    std::puts("Catalog byte budget PASS: exact32MiB parse/file load, over-limit rejection, previous collection preserved.");
}
