#!/usr/bin/env bash
# Cai LatentSync 1.6 (ByteDance, Apache-2.0 code) vao Network Volume /workspace.
# Can ~15GB trong tren volume. Chay 1 lan, KHONG can GPU de cai.
# Dung thu tu va phien ban theo requirements.txt cua repo goc (torch 2.5.1 + cu121).
set -euo pipefail

ROOT=/workspace
APP="$ROOT/LatentSync"
VENV="$ROOT/venv-latentsync"

FREE_GB=$(df -BG --output=avail "$ROOT" | tail -1 | tr -dc '0-9')
if [ "$FREE_GB" -lt 15 ]; then
  echo "THIEU CHO: chi con ${FREE_GB}GB tren $ROOT, can >= 15GB. Tang volume hoac xoa venv cu."
  exit 1
fi

apt-get update -qq && apt-get install -y -qq ffmpeg git libgl1 libglib2.0-0 build-essential curl >/dev/null
python3 -m pip install -q --break-system-packages uv 2>/dev/null || python3 -m pip install -q uv

[ -d "$APP" ] || git clone --depth 1 https://github.com/bytedance/LatentSync.git "$APP"
[ -d "$VENV" ] || python3 -m uv venv --python 3.10 --seed "$VENV"
# shellcheck disable=SC1091
source "$VENV/bin/activate"
python -m pip install -q -U pip wheel

cd "$APP"
pip install -r requirements.txt

# Checkpoints (whisper tiny + unet 1.6)
python - <<'PY'
from huggingface_hub import hf_hub_download
for f in ("whisper/tiny.pt", "latentsync_unet.pt"):
    p = hf_hub_download("ByteDance/LatentSync-1.6", f, local_dir="checkpoints")
    print("OK", p)
PY

python - <<'PY'
import os, torch, cv2, mediapipe
print("torch", torch.__version__, "cuda build", torch.version.cuda, "gpu", torch.cuda.is_available())
need = ["checkpoints/latentsync_unet.pt", "checkpoints/whisper/tiny.pt", "configs/unet/stage2_512.yaml"]
missing = [f for f in need if not os.path.isfile(f)]
print("MISSING:", missing if missing else "none")
raise SystemExit(1 if missing else 0)
PY
echo "SETUP OK (LatentSync). Stop Pod ngay neu chi cai dat."
