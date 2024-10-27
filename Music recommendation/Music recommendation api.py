from flask import Flask, render_template, request, jsonify, send_file
import os
import librosa
import numpy as np
import tensorflow as tf
import pandas as pd
from sklearn.preprocessing import LabelEncoder
from keras.models import load_model
from keras.utils import to_categorical

app = Flask(__name__)

def find_matching_music(text):
    x = "asdas"
    model = load_model(r"model_final55555.h5")
    extracted_features_df = pd.read_csv(r"extracted_features_df.csv")
    y = np.array(extracted_features_df["class"].tolist())
    label_encoder = LabelEncoder()
    y = to_categorical(label_encoder.fit_transform(y))

    def predict_genre(audio_path):
        audio, sample_rate = librosa.load(audio_path, res_type='kaiser_fast')
        mfccs_features = librosa.feature.mfcc(y=audio, sr=sample_rate, n_mfcc=40)
        mfccs_scaled_features = np.mean(mfccs_features.T, axis=0)
        mfccs_scaled_features = mfccs_scaled_features.reshape(1, -1)
        Z = model.predict(mfccs_scaled_features)
        predicted_label = tf.argmax(Z, axis=1)
        prediction_class = label_encoder.inverse_transform(predicted_label)
        return prediction_class[0]

    def find_matching_music_genre(predicted_genre):
        music_files = []
        music_directory = r"Music_Meta_Data"
        
        for root, dirs, files in os.walk(music_directory):
            for file in files:
                if file.endswith(".mp3") or file.endswith(".wav"):
                    file_path = os.path.join(root, file)
                    predicted_text = predict_genre(file_path)
                    if predicted_genre == predicted_text:
                        music_files.append(file_path)
                        break
            if music_files:
                break
                    
        return music_files

    def select_music_file(text):
        user_input = text
        predicted_genre = user_input.lower()  

        # Find matching music files
        matching_music = find_matching_music_genre(predicted_genre)
        if matching_music:
            chosen_music_index = 0  # Select the first matching music file
            chosen_music_path = matching_music[chosen_music_index]
            return chosen_music_path
        else:
            return x  # Return None if no matching music is found

    text = text
    chosen_music_path = select_music_file(text)
    print(chosen_music_path)
    if chosen_music_path:
        print(chosen_music_path)
    return chosen_music_path

def get_received_text():
    try:
        data = request.form if request.form else request.get_json()
        text = data.get('text')
        return text

    except Exception as e:
        response = {'status': 'error', 'message': str(e)}
        return jsonify(response), 400

def generate_music_from_text(text):
    try:
        text_user = text
        chosen_music_path = find_matching_music(text_user)
        if chosen_music_path:
            generated_music = chosen_music_path
        return generated_music
    except Exception as e:
        response = {'status': 'error', 'message': str(e)}
        return jsonify(response), 500

@app.route('/')
def index():
    return render_template('index.html', image_data=None)

@app.route('/generate_music', methods=['POST'])
def generate_music():
    try:
        text = get_received_text()
        music_data = generate_music_from_text(text)
        print(music_data + "Aa")
        return (send_file(music_data, as_attachment=True))
    except Exception as e:
        response = {'status': 'error', 'message': str(e)}
        return jsonify(response), 500

if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0")
