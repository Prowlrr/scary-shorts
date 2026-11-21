#!/usr/bin/env bash
# One-time setup in a fresh session: installs deps and downloads the free Kokoro TTS model.
set -e
cd "$(dirname "$0")"
command -v ffmpeg >/dev/null || (apt-get update -qq && apt-get install -y -qq ffmpeg)
pip install --break-system-packages -q kokoro-onnx soundfile pillow numpy
mkdir -p models
B=https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0
[ -s models/kokoro-v1.0.int8.onnx ] || curl -sSL -o models/kokoro-v1.0.int8.onnx $B/kokoro-v1.0.int8.onnx
[ -s models/kokoro-v1.0.onnx ] || curl -sSL -o models/kokoro-v1.0.onnx $B/kokoro-v1.0.onnx   # full-precision model: more natural voice
[ -s models/voices-v1.0.bin ] || curl -sSL -o models/voices-v1.0.bin $B/voices-v1.0.bin
echo "setup ok"
