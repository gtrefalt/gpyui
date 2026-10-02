#!/usr/bin/env bash
# Run a native capture command on the current display, or a free Xvfb display.
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p artifacts/docs-captures
if [[ -d /workspace/native/sysroot ]]; then
    source scripts/workspace-env.sh
    python - <<'PY'
import json, os
from pathlib import Path
root = Path(os.environ['GPYUI_SYSROOT'])
driver = json.loads((root/'usr/share/vulkan/icd.d/lvp_icd.json').read_text())
driver['ICD']['library_path'] = str(root/'usr/lib/x86_64-linux-gnu/libvulkan_lvp.so')
Path('artifacts/docs-captures/driver.json').write_text(json.dumps(driver))
PY
    export VK_DRIVER_FILES="$PWD/artifacts/docs-captures/driver.json"
fi
export XDG_RUNTIME_DIR="${XDG_RUNTIME_DIR:-$PWD/artifacts/docs-captures/runtime}"
mkdir -p "$XDG_RUNTIME_DIR"
chmod 700 "$XDG_RUNTIME_DIR"
if [[ -z "${DISPLAY:-}" ]]; then
    rm -f artifacts/docs-captures/display
    Xvfb -displayfd 3 -screen 0 1600x1100x24 -nolisten tcp 3>artifacts/docs-captures/display >artifacts/docs-captures/xvfb.log 2>&1 &
    gpyui_docs_xvfb_pid=$!
    trap 'kill "$gpyui_docs_xvfb_pid" 2>/dev/null || true' EXIT
    for _ in {1..100}; do
        [[ -s artifacts/docs-captures/display ]] && break
        sleep 0.1
    done
    gpyui_docs_display="$(cat artifacts/docs-captures/display)"
    [[ "$gpyui_docs_display" =~ ^[0-9]+$ ]] || { cat artifacts/docs-captures/xvfb.log >&2; exit 1; }
    export DISPLAY=":$gpyui_docs_display"
fi
"$@"
