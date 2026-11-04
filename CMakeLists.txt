cmake_minimum_required(VERSION 3.24)
project(PixelMuseum VERSION 0.2.0 LANGUAGES C CXX)
set(PIXEL_MUSEUM_APP_VERSION "0.2.0-preview" CACHE STRING "Published Windows application version")
if(NOT PIXEL_MUSEUM_APP_VERSION MATCHES "^[0-9]+\\.[0-9]+\\.[0-9]+([-+][A-Za-z0-9.+-]+)?$")
  message(FATAL_ERROR "PIXEL_MUSEUM_APP_VERSION must be a semantic version")
endif()
file(GENERATE OUTPUT "${CMAKE_BINARY_DIR}/application-version.json"
  CONTENT "{\"schema_version\":1,\"version\":\"${PIXEL_MUSEUM_APP_VERSION}\"}\n")

if(NOT WIN32)
  message(FATAL_ERROR "This CMake target builds the Windows edition. Use Makefile for PS5/host previews.")
endif()
set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
find_package(SDL3 CONFIG REQUIRED)
find_package(GLEW REQUIRED)
find_package(OpenGL REQUIRED)
find_package(CURL REQUIRED)
find_package(OpenSSL REQUIRED)
find_package(ZLIB REQUIRED)
find_package(PkgConfig REQUIRED)
pkg_check_modules(FFMPEG REQUIRED IMPORTED_TARGET libavcodec libavformat libavutil libavfilter libswscale libswresample)
pkg_check_modules(ZSTD REQUIRED IMPORTED_TARGET libzstd)
find_package(Threads REQUIRED)

file(GLOB_RECURSE COMMON CONFIGURE_DEPENDS src/*.cpp)
list(FILTER COMMON EXCLUDE REGEX "/platform/(ps5|windows)/")
list(FILTER COMMON EXCLUDE REGEX "/runtime/|/third_party/|/main\\.cpp$")
file(GLOB_RECURSE VENDORED CONFIGURE_DEPENDS src/third_party/*.c)
add_executable(pixelmuseum WIN32 ${COMMON} ${VENDORED}
  src/platform/windows/main.cpp src/platform/windows/desktop_input.cpp
  src/platform/windows/desktop_audio.cpp src/platform/windows/desktop_display.cpp
  src/platform/windows/dualsense_bluetooth.cpp
  src/platform/windows/player_ffmpeg.cpp src/platform/windows/range_stream.cpp
  src/platform/windows/http_windows.cpp src/platform/windows/system_windows.cpp
  src/platform/windows/youtube_resolver.cpp
  host/trophy_notification_stub.cpp src/platform/windows/pixelmuseum.rc)
set_target_properties(pixelmuseum PROPERTIES OUTPUT_NAME "Pixel Museum")
target_include_directories(pixelmuseum BEFORE PRIVATE src/platform/windows/include src .)
target_compile_definitions(pixelmuseum PRIVATE MUSEUM_DESKTOP=1 MUSEUM_WINDOWS=1 MUSEUM_APP_VERSION="${PIXEL_MUSEUM_APP_VERSION}" NOMINMAX WIN32_LEAN_AND_MEAN JSON_NOEXCEPTION=1 __USE_MINGW_ANSI_STDIO=1)
target_compile_options(pixelmuseum PRIVATE $<$<COMPILE_LANGUAGE:CXX>:-include${CMAKE_CURRENT_SOURCE_DIR}/src/platform/windows/compat.hpp> -Wall -Wextra -Wno-misleading-indentation)
target_link_libraries(pixelmuseum PRIVATE SDL3::SDL3 GLEW::GLEW OpenGL::GL CURL::libcurl OpenSSL::SSL OpenSSL::Crypto ZLIB::ZLIB PkgConfig::FFMPEG PkgConfig::ZSTD Threads::Threads hid ws2_32)
if(MINGW)
  target_link_options(pixelmuseum PRIVATE -static-libgcc -static-libstdc++)
endif()
install(TARGETS pixelmuseum RUNTIME DESTINATION .)
