#!/usr/bin/env bash

set -e

mkdir -p models

if [ ! -f models/SmolLM2-135M-Instruct.Q8_0.gguf ]; then
    echo "Downloading model..."
    wget -O models/SmolLM2-135M-Instruct.Q8_0.gguf \
    "https://huggingface.co/unsloth/SmolLM2-135M-Instruct-GGUF/resolve/main/SmolLM2-135M-Instruct.Q8_0.gguf"
fi

echo "Starting llama-server..."

./llama.cpp/build/bin/llama-server \
  -m models/SmolLM2-135M-Instruct.Q8_0.gguf \
  --host 0.0.0.0 \
  --port ${PORT:-8080}
