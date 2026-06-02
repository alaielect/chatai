FROM alpine:latest

RUN apk add --no-cache wget unzip libstdc++

WORKDIR /app

# دانلود باینری آماده llama.cpp (نیاز به کامپایل نداره!)
RUN wget https://github.com/ggerganov/llama.cpp/releases/download/b4110/llama-b4110-bin-ubuntu-x64.zip && \
    unzip llama-b4110-bin-ubuntu-x64.zip && \
    rm llama-b4110-bin-ubuntu-x64.zip && \
    chmod +x llama-server

# دانلود مدل (نسخه Q4_K_M برای رم کمتر)
RUN mkdir -p models && \
    wget -O models/SmolLM2-135M-Instruct.Q4_K_M.gguf \
    "https://huggingface.co/QuantFactory/SmolLM2-135M-Instruct-GGUF/resolve/main/SmolLM2-135M-Instruct.Q4_K_M.gguf"

EXPOSE 8080

CMD ["./llama-server", \
     "-m", "models/SmolLM2-135M-Instruct.Q4_K_M.gguf", \
     "--host", "0.0.0.0", \
     "--port", "8080", \
     "--ctx-size", "512"]
