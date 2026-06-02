# server.py
from flask import Flask, request, jsonify
from transformers import AutoModelForCausalLM, AutoTokenizer

app = Flask(__name__)

# مدل رو با تنظیمات کم‌رم لود کن
model = AutoModelForCausalLM.from_pretrained(
    "unsloth/SmolLM2-135M-Instruct",
    torch_dtype="auto",
    device_map="cpu",
    low_cpu_mem_usage=True
)
tokenizer = AutoTokenizer.from_pretrained("unsloth/SmolLM2-135M-Instruct")

@app.route('/generate', methods=['POST'])
def generate():
    prompt = request.json['prompt']
    inputs = tokenizer(prompt, return_tensors="pt")
    outputs = model.generate(**inputs, max_new_tokens=50)
    return jsonify({'response': tokenizer.decode(outputs[0])})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
