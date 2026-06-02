from flask import Flask, request, jsonify
from llama_cpp import Llama
import os
import urllib.request

app = Flask(__name__)

# آدرس مدل تو
MODEL_URL = "https://huggingface.co/Akakkskssk/model/resolve/main/smollm-135m-instruct-q4_k_m-imat.gguf"
MODEL_PATH = "model.gguf"

# دانلود مدل (فقط اولین بار)
if not os.path.exists(MODEL_PATH):
    print("Downloading model from HuggingFace...")
    urllib.request.urlretrieve(MODEL_URL, MODEL_PATH)
    print("Model downloaded!")

# لود مدل با llama-cpp-python
print("Loading model...")
llm = Llama(
    model_path=MODEL_PATH,
    n_ctx=512,          # context window (کمتر = رم کمتر)
    n_threads=2,        # تعداد تردها
    verbose=False
)
print("Model loaded!")

@app.route('/generate', methods=['POST'])
def generate():
    data = request.json
    prompt = data.get('prompt', '')
    
    # تولید پاسخ
    output = llm(
        prompt,
        max_tokens=100,
        temperature=0.7,
        stop=["</s>", "\n\n"]
    )
    
    response = output['choices'][0]['text']
    return jsonify({'response': response})

@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'ok'})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)
