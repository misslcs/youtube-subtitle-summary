from flask import Flask, request, jsonify, render_template, send_file, Response
from youtube_transcript_api import YouTubeTranscriptApi
from urllib.parse import urlparse, parse_qs
import requests
import os

app = Flask(__name__, static_url_path='/static')

SILICONFLOW_API_URL = "https://api.siliconflow.cn/v1/chat/completions"
SILICONFLOW_API_KEY = "sk-ewlxwjyjfjfmejneffzbdcuqvocyszwpmyjdhhmvtpautvsf"

def get_video_id(url):
    parsed_url = urlparse(url)
    if parsed_url.hostname == 'youtu.be':
        return parsed_url.path[1:]
    elif parsed_url.hostname in ('www.youtube.com', 'youtube.com'):
        if parsed_url.path == '/watch':
            return parse_qs(parsed_url.query)['v'][0]
        elif parsed_url.path.startswith('/embed/'):
            return parsed_url.path.split('/')[2]
        elif parsed_url.path.startswith('/v/'):
            return parsed_url.path.split('/')[2]
        elif parsed_url.path.startswith('/shorts/'):
            return parsed_url.path.split('/')[2]
    return None

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/get_transcript', methods=['GET', 'POST'])
def get_transcript():
    video_url = request.args.get('url') if request.method == 'GET' else request.form['url']
    video_id = get_video_id(video_url)
    if not video_id:
        return jsonify({'error': '无法解析视频 ID，请检查 URL 是否正确'}), 400
    try:
        transcript = YouTubeTranscriptApi.get_transcript(video_id)
        transcript_text = "\n".join([item['text'] for item in transcript])
        return Response(transcript_text, mimetype='text/plain')
    except Exception as e:
        import traceback
        error_message = traceback.format_exc()
        return jsonify({'error': str(e), 'traceback': error_message}), 500

@app.route('/ask_gpt', methods=['POST'])
def ask_gpt():
    data = request.get_json()
    prompt = data['prompt']
    payload = {
        "model": "Qwen/Qwen2-7B-Instruct",
        "messages": [
            {
                "role": "user",
                "content": prompt
            }
        ]
    }
    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "authorization": f"Bearer {SILICONFLOW_API_KEY}"
    }
    try:
        response = requests.post(SILICONFLOW_API_URL, json=payload, headers=headers)
        response.raise_for_status()
        result = response.json()
        return jsonify({'response': result['choices'][0]['message']['content'].strip()})
    except requests.exceptions.RequestException as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)

