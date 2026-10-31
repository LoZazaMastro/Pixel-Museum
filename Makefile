# Pixel Museum - Native PS5 and same-renderer host preview entry points.
# Copyright (C) 2026 Andrea Sgarro
# SPDX-License-Identifier: GPL-3.0-or-later
SHELL := /bin/bash
.DEFAULT_GOAL := app
-include .env
APP_DEFINITIONS ?= GL_GLEXT_PROTOTYPES=1
APP_INCLUDE_PATHS ?= src . .deps/ps5-opengl/current/include
APP_STATIC_ARCHIVES ?= .deps/ps5-opengl/libps5opengl-group.a
APP_IMPORT_STUBS ?= .deps/ps5-opengl/current/lib/libSceAgc.so .deps/ps5-opengl/current/lib/libSceAgcDriver.so tooling/stubs/libSceVideodec2.so
APP_RUNTIME_MODULES ?=
PACBREW_PACKAGES ?=
PACBREW_INCLUDE_PATHS ?= include
PACBREW_STATIC_ARCHIVES ?= lib/libcurl.a lib/libpsl.a lib/libssl.a lib/libcrypto.a lib/libzstd.a lib/libz.a lib/libavformat.a lib/libavfilter.a lib/libavcodec.a lib/libavutil.a lib/libswscale.a lib/libswresample.a lib/libpostproc.a lib/libiconv.a lib/liblzma.a lib/libx264.a lib/libharfbuzz.a lib/libfreetype.a lib/libbz2.a lib/libpng16.a lib/libfribidi.a lib/libass.a lib/libfontconfig.a lib/libexpat.a
PS5_OPENGL_PREFIX ?=
BUILD_JOBS ?= 6
USE_CCACHE ?= 0
export APP_DEFINITIONS APP_INCLUDE_PATHS APP_STATIC_ARCHIVES APP_IMPORT_STUBS APP_RUNTIME_MODULES
export PACBREW_PACKAGES PACBREW_INCLUDE_PATHS PACBREW_STATIC_ARCHIVES PS5_OPENGL_PREFIX BUILD_JOBS USE_CCACHE
.PHONY: app preview deps package
app:
	@bash tools/prepare-opengl.sh
	@bash tools/build.sh Folder
preview:
	@bash tools/preview.sh
deps:
	@bash tools/setup-native-dependencies.sh
	@bash tools/setup-pacbrew-dependencies.sh --environment
	@bash tools/prepare-opengl.sh
package: app
	@python3 tools/package-museum.py
