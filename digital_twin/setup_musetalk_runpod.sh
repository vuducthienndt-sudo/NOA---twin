#!/usr/bin/env bash
# Cai MuseTalk 1.5 vao Network Volume (/workspace) voi dung bo phien ban upstream.
# Can ~20GB trong, volume 30GB phai trong (xoa venv cu truoc khi chay). Chay 1 lan. Phan cai dat KHONG can GPU: chay tren Pod CPU re hoac Pod GPU,
# Chay duoc tren moi template Pod (Python 3.10 va torch 2.0.1 duoc cai rieng trong venv).
set -euo pipefail

ROOT=/workspace
APP="$ROOT/MuseTalk"
VENV="$ROOT/venv-musetalk"

apt-get update -qq && apt-get install -y -qq ffmpeg git build-essential curl >/dev/null
# Python 3.10 lay bang uv, khong phu thuoc image/Ubuntu cua Pod
python3 -m pip install -q --break-system-packages uv 2>/dev/null || python3 -m pip install -q uv

[ -d "$APP" ] || git clone --depth 1 https://github.com/TMElyralab/MuseTalk.git "$APP"

[ -d "$VENV" ] || python3 -m uv venv --python 3.10 --seed "$VENV"
# shellcheck disable=SC1091
source "$VENV/bin/activate"
python -m pip install -q -U pip "setuptools<70" wheel

# Dung thu tu va phien ban theo README upstream
pip install torch==2.0.1 torchvision==0.15.2 torchaudio==2.0.2 \
  --index-url https://download.pytorch.org/whl/cu118
pip install -r "$APP/requirements.txt"
pip install --no-cache-dir -U openmim
mim install mmengine
mim install "mmcv==2.0.1"
mim install "mmdet==3.1.0"
mim install "mmpose==1.1.0"

# Cac goi sau bi pip nang nham/hong khi cai, ep ve dung ban da kiem chung chay duoc
pip install huggingface_hub==0.30.2
pip install --force-reinstall --no-deps opencv-python==4.9.0.80
apt-get install -y -qq libgl1 libglib2.0-0 >/dev/null

# Trong luong model (khong can GPU)
cd "$APP"
sh ./download_weights.sh

# Kiem tra: in phien ban + file model can thiet. Khong chay inference.
python - <<'PY'
import torch, mmcv, mmpose, cv2, os
print("torch", torch.__version__, "cuda build", torch.version.cuda,
      "cuda available", torch.cuda.is_available())
print("mmcv", mmcv.__version__, "mmpose", mmpose.__version__)
need = ["models/musetalkV15/unet.pth", "models/musetalkV15/musetalk.json",
        "models/whisper/pytorch_model.bin", "models/sd-vae/diffusion_pytorch_model.bin",
        "models/dwpose/dw-ll_ucoco_384.pth", "models/face-parse-bisent/79999_iter.pth"]
missing = [f for f in need if not os.path.isfile(f)]
print("MISSING:", missing if missing else "none")
raise SystemExit(1 if missing else 0)
PY
echo "SETUP OK. Dung Pod nay ngay neu chi cai dat (khong can GPU)."
