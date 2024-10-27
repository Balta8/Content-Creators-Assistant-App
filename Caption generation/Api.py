import mimetypes

from flask import Flask, render_template, request, jsonify, send_file
import os
import os
import moviepy.editor as mp
from ibm_watson import SpeechToTextV1
from ibm_cloud_sdk_core.authenticators import IAMAuthenticator
from moviepy.editor import TextClip, CompositeVideoClip
from base64 import b64encode
from IPython.display import HTML
import pysrt
# Ensure ImageMagick is properly set up for TextClip
os.environ["IMAGEMAGICK_BINARY"] = r"C:\Program Files\ImageMagick-7.1.1-Q16-HDRI\magick.exe"
# IBM Watson credentials
apikey = '8Ge1q5zWxotlJ_xFnPhqgLepcaCO4GlkH0cDIYCP0V7C'
url = 'https://api.au-syd.speech-to-text.watson.cloud.ibm.com/instances/cee8c40b-dabb-4067-8b98-54697a00858e'

# Set up IBM Watson Speech to Text
authenticator = IAMAuthenticator(apikey)
speech_to_text = SpeechToTextV1(authenticator=authenticator)
speech_to_text.set_service_url(url)

def add_subtitles_to_video(language_choice, video_path):
    language_mapping = {
        "1": "en-US",  # English
        "2": "ar-AR",  # Arabic
    }

    if language_choice not in language_mapping:
        print("Invalid language selection. Please choose 1 for English or 2 for Arabic.")
        return None

    try:
        # Load the video and extract audio
        video = mp.VideoFileClip(video_path)
        audio = video.audio

        # Save the audio as a temporary WAV file
        audio_path = r"C:\Users\Moatsem\Videos\temp_audio.wav"
        audio.write_audiofile(audio_path, codec="pcm_s16le")

        # Recognize speech in the chosen language using IBM Watson
        with open(audio_path, 'rb') as audio_file:
            response = speech_to_text.recognize(
                audio=audio_file,
                content_type='audio/wav',
                model=f"{language_mapping[language_choice]}_BroadbandModel",
                timestamps=True,
                max_alternatives=1
            ).get_result()

        # Extract and format recognized text with timestamps
        srt_path = os.path.splitext(video_path)[0] + ".srt"
        with open(srt_path, "w") as srt_file:
            index = 1
            for result in response['results']:
                for alternative in result['alternatives']:
                    transcript = alternative['transcript']
                    timestamps = alternative['timestamps']
                    start_time = timestamps[0][1]
                    end_time = timestamps[-1][2]
                    start_time_str = format_timestamp(start_time)
                    end_time_str = format_timestamp(end_time)
                    srt_file.write(f"{index}\n{start_time_str} --> {end_time_str}\n{transcript}\n\n")
                    index += 1

        # Create subtitle clips
        subtitles = pysrt.open(srt_path)
        subtitle_clips = create_subtitle_clips(subtitles, video.size)

        # Add subtitles to the video
        final_video = CompositeVideoClip([video] + subtitle_clips)

        # Write output video file
        output_video_path = os.path.splitext(video_path)[0] + "_subtitled.mp4"
        final_video.write_videofile(output_video_path, codec="libx264")

        # Display the video with subtitles
        mp4 = open(output_video_path, 'rb').read()
        data_url = "data:video/mp4;base64," + b64encode(mp4).decode()
        display_video = HTML(f"""
        <video width=500 controls>
              <source src="{data_url}" type="video/mp4">
        </video>
        """)

        return output_video_path

    except Exception as e:
        print("An error occurred:", str(e))
        return None

def format_timestamp(seconds):
    try:
        seconds = float(seconds)
    except ValueError as e:
        print(f"Invalid timestamp value: {seconds}, error: {e}")
        raise
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    seconds = int(seconds % 60)
    milliseconds = int((seconds % 1) * 1000)
    return f"{hours:02}:{minutes:02}:{seconds:02},{milliseconds:03}"

def time_to_seconds(time_obj):
    return time_obj.hours * 3600 + time_obj.minutes * 60 + time_obj.seconds + time_obj.milliseconds / 1000

def create_subtitle_clips(subtitles, videosize, fontsize=36, font='Roboto', color='white', stroke_color='black', stroke_width=2):
    subtitle_clips = []

    for subtitle in subtitles:
        start_time = time_to_seconds(subtitle.start)
        end_time = time_to_seconds(subtitle.end)
        duration = end_time - start_time

        video_width, video_height = videosize

        text_clip = TextClip(
            subtitle.text,
            fontsize=fontsize,
            font='Roboto',
            color=color,
            bg_color='black',  # Change background color to gray
            stroke_color='yellow',  # Remove stroke
            stroke_width=2,
            size=(video_width * 3 / 4, None),
            method='caption'
        ).set_start(start_time).set_duration(duration)

        subtitle_x_position = 'center'
        subtitle_y_position = video_height * 4 / 5

        text_position = (subtitle_x_position, subtitle_y_position)
        subtitle_clips.append(text_clip.set_position(text_position))

    return subtitle_clips

# Test the function
#language_choice = "1"  # Choose 1 for English, 2 for Arabic
#video_path = r"C:\Users\Moatsem\Videos\STT.mp4"  # Provide the path to the video file here
#add_subtitles_to_video(language_choice, video_path)
#############################################################################


app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False

# Define the path to the static folder
static_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static')


def guess_mimetype(file_path):
    mime, encoding = mimetypes.guess_type(file_path)
    return mime or 'application/octet-stream'


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/videos')
def get_videos():
    videos = []
    for filename in os.listdir(static_folder):
        filepath = os.path.join(static_folder, filename)
        videos.append({
            'filename': filename,
            'mimetype': guess_mimetype(filepath),
            'size': os.path.getsize(filepath),
        })

    return jsonify(videos)


@app.route('/upload', methods=['POST'])
def upload():
    if 'video' not in request.files:
        return jsonify({'error': 'No video part in the request'})

    video_file = request.files['video']

    if video_file.filename == '':
        return jsonify({'error': 'No selected video file'})

    # Ensure that the uploaded file has an allowed extension (e.g., mp4, avi, mkv)
    allowed_extensions = {'mp4', 'avi', 'mkv'}
    if '.' in video_file.filename and video_file.filename.rsplit('.', 1)[1].lower() not in allowed_extensions:
        return jsonify({'error': 'Invalid file type'})

    # Save the video to the static folder
    video_path = os.path.join(static_folder, video_file.filename)
    video_file.save(video_path)

    def process_video(video_path):
        language_choice = "1"  # Choose 1 for English, 2 for Arabic
        #video_path = r"C:\Users\Moatsem\Videos\STT.mp4"  # Provide the path to the video file here
        fahmy=add_subtitles_to_video(language_choice, video_path)
        
        return fahmy
    ahmed=process_video(video_path)
    #video_path = os.path.join(static_folder, ahmed.filename)
    #video_file.save(ahmed)


    return send_file(ahmed, as_attachment=True)
    #return send_file(balta_path, as_attachment=True, download_name=video_file.filename, mimetype='video/mp4')


if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0")
