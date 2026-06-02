#!/usr/bin/env bash

set -e

# دانلود مدل در اولین اجرا
mkdir -p models

if [ ! -f models/SmolLM2-135M-Instruct.Q8_0.gguf ]; then
    wget -O models/SmolLM2-135M-Instruct.Q8_0.gguf \
    "https://huggingface.co/unsloth/SmolLM2-135M-Instruct-GGUF/resolve/main/SmolLM2-135M-Instruct.Q8_0.gguf"
fi

# دانلود llama.cpp
if [ ! -d llama.cpp ]; then
    git clone https://github.com/ggml-org/llama.cpp.git
fi

cd llama.cpp

cmake -B build
cmake --build build -j

./build/bin/llama-server \
  -m ../models/SmolLM2-135M-Instruct.Q8_0.gguf \
  --host 0.0.0.0 \
  --port $PORT
