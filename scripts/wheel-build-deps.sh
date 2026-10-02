#!/usr/bin/env bash
# Native development libraries for the manylinux_2_28 build container.
set -euo pipefail

dnf install -y dnf-plugins-core
dnf config-manager --set-enabled powertools
dnf install -y \
    clang-devel fontconfig-devel freetype-devel libX11-devel libX11-xcb \
    libxcb-devel libxkbcommon-devel libxkbcommon-x11-devel wayland-devel \
    vulkan-loader-devel
