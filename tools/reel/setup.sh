#!/usr/bin/env bash
# One-time setup for the reel kit: light Python deps + the kokoro voice model (shared with the story kit).
set -e
cd "$(dirname "$0")"
pip install --break-system-packages -q kokoro-onnx soundfile scipy numpy pillow 2>/dev/null \
  || pip install -q kokoro-onnx soundfile scipy numpy pillow
models=../story/models
mkdir -p "$models"
base=https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0
[ -s $models/kokoro-v1.0.onnx ] || curl -sSL -o $models/kokoro-v1.0.onnx $base/kokoro-v1.0.onnx
[ -s $models/voices-v1.0.bin ] || curl -sSL -o $models/voices-v1.0.bin $base/voices-v1.0.bin
command -v ffmpeg >/dev/null || echo "ffmpeg is missing: install it (apt install ffmpeg)"
fc-match -f '%{file}\n' Poppins:Bold | grep -qi poppins || echo "Poppins font not found: captions will fall back to another font"
python -c "import kokoro_onnx, PIL; print('reel kit ready')"
