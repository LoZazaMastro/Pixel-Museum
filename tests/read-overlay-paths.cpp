// Read-overlay path identity must survive SDL's trailing directory separator.
// SPDX-License-Identifier: GPL-3.0-or-later
#include "core/save_file.hpp"
#include <filesystem>
#include <fstream>
#include <iostream>
#include <string>
#include <vector>

int main(int argc, char** argv) {
    if (argc != 2) return 2;
    namespace fs = std::filesystem;
    const auto path = [](const std::string& text) { return fs::path(std::u8string(text.begin(), text.end())); };
    const fs::path fixture = fs::absolute(path(argv[1]));
    if (fs::exists(fixture)) return 3;
    fs::create_directories(fixture / "content");
    const auto generic = fixture.generic_u8string();
    const std::string root(generic.begin(), generic.end());
    const std::string baseline = root + "/content/catalog.json";
    const std::string blob = root + "/verified-blob";
    { std::ofstream file(path(baseline), std::ios::binary); file << "bundled revision 1"; }
    { std::ofstream file(path(blob), std::ios::binary); file << "verified revision 2"; }
    hui::save::set_read_overlay({{baseline, blob}});
    const std::vector<std::string> requests = {
        root + "/content/catalog.json",
        root + "//content/catalog.json", // SDL_GetBasePath already ends in '/'.
        root + "///content//catalog.json",
        root + "\\content\\catalog.json",
        root + "\\\\content//catalog.json",
    };
    for (const auto& request : requests) {
        std::string text;
        if (hui::save::resolve_read_path(request) != blob ||
            !hui::save::read_file(request, &text, 100) || text != "verified revision 2") {
            std::cerr << "FAIL overlay alias: " << request << '\n';
            return 1;
        }
    }
    // Registration and lookup use the same normalization, including PS5 paths.
    hui::save::set_read_overlay({{root + "//content\\catalog.json", blob},
                                {"/app0//content/catalog.json", blob}});
    if (hui::save::resolve_read_path(baseline) != blob ||
        hui::save::resolve_read_path("/app0/content//catalog.json") != blob) return 4;
    if (hui::save::resolve_read_path(baseline + ".bak") != baseline + ".bak") return 5;
    hui::save::set_read_overlay({});
    std::string bundled;
    if (!hui::save::read_file(baseline, &bundled, 100) || bundled != "bundled revision 1") return 6;
    std::cout << "PASS overlay: SDL trailing slash, repeated separators, Windows separators, PS5 spelling, normalized registration, exact siblings, clearing restores baseline\n";
}
