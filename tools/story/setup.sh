#!/usr/bin/env bash
# One-time setup for the story kit: Python deps (Blender as a module, TTS) + kokoro voice model.
set -e
cd "$(dirname "$0")"
pip install --break-system-packages -q bpy kokoro-onnx soundfile scipy numpy pillow 2>/dev/null \
  || pip install -q bpy kokoro-onnx soundfile scipy numpy pillow
mkdir -p models cache
base=https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0
[ -s models/kokoro-v1.0.onnx ] || curl -sSL -o models/kokoro-v1.0.onnx $base/kokoro-v1.0.onnx
[ -s models/voices-v1.0.bin ] || curl -sSL -o models/voices-v1.0.bin $base/voices-v1.0.bin
command -v ffmpeg >/dev/null || echo "ffmpeg is missing: install it (apt install ffmpeg)"
python -c "import bpy, kokoro_onnx; print('story kit ready, blender', bpy.app.version_string)"
