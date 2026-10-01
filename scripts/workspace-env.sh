#!/usr/bin/env bash
# Optional environment for this cloud workspace's locally extracted Debian libs.
# Normal desktops should install the packages listed in README.md instead.
export CARGO_HOME="${GPYUI_CARGO_HOME:-/workspace/.cargo}"
export RUSTUP_HOME="${GPYUI_RUSTUP_HOME:-/workspace/.rustup}"
export PATH="$CARGO_HOME/bin:$PATH"
export UV_CACHE_DIR="${UV_CACHE_DIR:-/tmp/gpyui-uv-cache}"
export UV_LINK_MODE=copy
export CARGO_BUILD_JOBS="${CARGO_BUILD_JOBS:-3}"
export GPYUI_SYSROOT="${GPYUI_SYSROOT:-/workspace/native/sysroot}"
export PKG_CONFIG_PATH="$GPYUI_SYSROOT/usr/lib/x86_64-linux-gnu/pkgconfig:$GPYUI_SYSROOT/usr/share/pkgconfig:${PKG_CONFIG_PATH:-}"
export LIBRARY_PATH="$GPYUI_SYSROOT/usr/lib/x86_64-linux-gnu:${LIBRARY_PATH:-}"
export LIBCLANG_PATH="$GPYUI_SYSROOT/usr/lib/llvm-19/lib"
export LD_LIBRARY_PATH="$GPYUI_SYSROOT/usr/lib/x86_64-linux-gnu:${LD_LIBRARY_PATH:-}"
export PATH="$GPYUI_SYSROOT/usr/bin:$PATH"
