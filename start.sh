#!/usr/bin/env bash
set -e

# نصب ابزارهای لازم (Render اوبونتو مینیمال داره)
apt-get update && apt-get install -y git cmake build-essential wget

# دانلود مدل در اولین اجرا
mkdir -p models

if [ ! -f models/SmolLM2-135M-Instruct.Q8_0.gguf ]; then
    wget -O models/SmolLM2-135M-Instruct.Q8_0.gguf \
    "https://huggingface.co/unsloth/SmolLM2-135M-Instruct-GGUF/resolve/main/SmolLM2-135M-Instruct.Q8_0.gguf"
fi

# دانلود llama.cpp (اگر وجود نداشت)
if [ ! -d llama.cpp ]; then
    git clone https://github.com/ggml-org/llama.cpp.git
fi

cd llama.cpp

# کامپایل (با تعداد ترد کمتر برای رم کمتر)
mkdir -p build
cd build
cmake ..
make -j2

# برگرد به پوشه قبلی و اجرا
cd ../..
./llama.cpp/build/bin/llama-server \
  -m models/SmolLM2-135M-Instruct.Q8_0.gguf \
  --host 0.0.0.0 \
  --port ${PORT:-8080} \
  --ctx-size 512
