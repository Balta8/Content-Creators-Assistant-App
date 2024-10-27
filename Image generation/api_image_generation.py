
from flask import Flask, render_template, request, jsonify
import os
import io
import base64
from PIL import Image
from diffusers import StableDiffusionPipeline
import torch
auth_token = " your hugging face token"
model_id= "your id"
device = "cuda"
pipe = StableDiffusionPipeline.from_pretrained(model_id, torch_dtype=torch.float16,safety_checker = None,requires_safety_checker = False)
pipe.to(device)

app = Flask(__name__)

def get_received_text():
    try:
        data = request.form if request.form else request.get_json()
        text = data.get('text')
        return text

    except Exception as e:
        response = {'status': 'error', 'message': str(e)}
        return jsonify(response), 400

def generate_image_from_text(text):
    try:
        image_data= pipe(text).images[0]


        buffered = io.BytesIO()
        image_data.save(buffered, format="PNG")
        image_data_base64 = base64.b64encode(buffered.getvalue()).decode('utf-8')

        return image_data_base64
    except Exception as e:
        response = {'status': 'error', 'message': str(e)}
        return jsonify(response), 500

@app.route('/')
def index():
    return render_template('index.html', image_data=None)

@app.route('/generate_image', methods=['POST'])
def generate_image():
    try:
        text = get_received_text()
        image_data = generate_image_from_text(text)
        return jsonify({'image_data': image_data}), 200
    except Exception as e:
        response = {'status': 'error', 'message': str(e)}
        return jsonify(response), 500

if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0")
