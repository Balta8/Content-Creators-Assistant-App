from flask import Flask, render_template, request, jsonify, send_file
from ibm_watson import TextToSpeechV1
from ibm_cloud_sdk_core.authenticators import IAMAuthenticator

def generate_speech(text, language_choice , gender):
    apikey = 'your api'
    url = 'your url'
    authenticator = IAMAuthenticator(apikey)
    tts = TextToSpeechV1(authenticator=authenticator)
    tts.set_service_url(url)

    # Choose voice based on language preference
    if language_choice == 'Fr':
        if gender == 'Male':
            voice = 'fr-FR_ReneeV3Voice'
        else:
            voice = 'fr-FR_ReneeV3Voice'
    elif language_choice == 'En':
        if gender == 'Male':
            voice = 'en-AU_JackExpressive'
        else:
            voice = 'en-US_AllisonV3Voice'

    # Convert the user text to speech
    file_path = r'.\user_voice.mp3'  
    with open(file_path, 'wb') as audio_file:
        res = tts.synthesize(text, accept='audio/mp3', voice=voice).get_result()
        audio_file.write(res.content)
    return file_path


app = Flask(__name__)


def get_received_text():
    try:
        data = request.form if request.form else request.get_json()
        text1 = data.get('text1')
        text2 = data.get('text2')
        text3 = data.get('text3')

        return text1, text2, text3

    except Exception as e:
        response = {'status': 'error', 'message': str(e)}
        return jsonify(response), 400


def generate_music_from_text(text1, text2, text3):
    try:
        
        text_input=text1
        language_choice_input=text2
        gender_input=text3
        generated_music =generate_speech(text_input, language_choice_input,gender_input)

        return generated_music
    except Exception as e:
        response = {'status': 'error', 'message': str(e)}
        return jsonify(response), 500


@app.route('/')
def index():
    return render_template('index.html', image_data=None)


@app.route('/generate_music', methods=['POST'])
def generate_image():
    try:
        text1, text2, text3 = get_received_text()
        print(text3)
        print(text2)
        print(text1)
        music_data = generate_music_from_text(text1, text2, text3)
        return send_file(music_data, as_attachment=True)
    except Exception as e:
        response = {'status': 'error', 'message': str(e)}
        return jsonify(response), 500


if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0")
