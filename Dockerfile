FROM alpine:latest

RUN apk add --no-cache wget cmake build-base git

WORKDIR /app

# clone و کامپایل llama.cpp
RUN git clone https://github.com/ggerganov/llama.cpp.git && \
    cd llama.cpp && \
    mkdir build && cd build && \
    cmake .. && \
    make -j2

# دانلود مدل
RUN mkdir -p models && \
    wget -O models/SmolLM2-135M-Instruct.Q4_K_M.gguf \
    "https://huggingface.co/QuantFactory/SmolLM2-135M-Instruct-GGUF/resolve/main/SmolLM2-135M-Instruct.Q4_K_M.gguf"

EXPOSE 8080

CMD ["./llama.cpp/build/bin/llama-server", \
     "-m", "models/SmolLM2-135M-Instruct.Q4_K_M.gguf", \
     "--host", "0.0.0.0", \
     "--port", "8080", \
     "--ctx-size", "512"]
