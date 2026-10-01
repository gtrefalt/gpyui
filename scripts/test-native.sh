#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
if [[ -d /workspace/native/sysroot ]]; then
    source scripts/workspace-env.sh
    mkdir -p artifacts
    python - <<'PY'
import json, os
from pathlib import Path
root = Path(os.environ['GPYUI_SYSROOT'])
manifest = json.loads((root/'usr/share/vulkan/icd.d/lvp_icd.json').read_text())
manifest['ICD']['library_path'] = str(root/'usr/lib/x86_64-linux-gnu/libvulkan_lvp.so')
Path('artifacts/lvp-icd.json').write_text(json.dumps(manifest))
PY
    export VK_DRIVER_FILES="$PWD/artifacts/lvp-icd.json"
fi
mkdir -p artifacts
export XDG_RUNTIME_DIR="$PWD/artifacts/runtime"
mkdir -p "$XDG_RUNTIME_DIR"
chmod 700 "$XDG_RUNTIME_DIR"
if [[ -z "${DISPLAY:-}" ]]; then
    # -displayfd asks Xvfb to select a free display, avoiding fixed-port collisions.
    rm -f artifacts/display
    Xvfb -displayfd 3 -screen 0 1024x768x24 -nolisten tcp 3>artifacts/display >artifacts/xvfb.log 2>&1 &
    gpyui_xvfb_pid=$!
    trap 'kill "$gpyui_xvfb_pid" 2>/dev/null || true' EXIT
    for _ in {1..100}; do
        [[ -s artifacts/display ]] && break
        sleep 0.1
    done
    gpyui_display_number="$(cat artifacts/display)"
    if [[ ! "$gpyui_display_number" =~ ^[0-9]+$ ]]; then
        cat artifacts/xvfb.log >&2
        exit 1
    fi
    export DISPLAY=":$gpyui_display_number"
fi
export GPYUI_NATIVE_TESTS=1
.venv/bin/python -m pytest -q tests/test_native.py "$@"
