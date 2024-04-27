import requests
from flask import Flask, request, jsonify
from pose_format import Pose
from pose_format.pose_visualizer import PoseVisualizer
import imageio
import numpy as np
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()
app = Flask(__name__)

# Access environment variables
VERCEL_TOKEN = os.getenv('VERCEL_TOKEN')
PROJECT_ID = os.getenv('PROJECT_ID')
TEAM_ID = os.getenv('TEAM_ID')

app = Flask(__name__)


def fetch_pose_from_api(text):
    url = "https://us-central1-sign-mt.cloudfunctions.net/spoken_text_to_signed_pose"
    params = {'text': text, 'spoken': 'en', 'signed': 'ase'}
    response = requests.get(url, params=params)
    if response.status_code == 200:
        return response.content
    else:
        raise Exception(f"Failed to fetch pose data: Status code {response.status_code}, {response.text}")

@app.route('/get_pose_gif', methods=['GET'])
def get_pose_gif():
    text = request.args.get('text', 'hello')
    pose_data = fetch_pose_from_api(text)
    pose = Pose.read(pose_data)
    v = PoseVisualizer(pose)
    gif_frames = [frame.astype(np.uint8) for frame in v.draw()]

    gif_path = "pose_animation.gif"
    imageio.mimsave(gif_path, gif_frames, format='GIF', fps=10)

    blob_url = upload_to_vercel_blob(gif_path)
    return jsonify({'gif_url': blob_url})

def upload_to_vercel_blob(file_path):
    url = f"https://api.vercel.com/v8/projects/{PROJECT_ID}/blobs"
    headers = {'Authorization': f'Bearer {VERCEL_TOKEN}'}
    files = {'file': open(file_path, 'rb')}
    response = requests.post(url, headers=headers, files=files)

    if response.status_code == 200:
        blob_id = response.json()['id']
        return f"https://api.vercel.com/v8/projects/{PROJECT_ID}/blobs/{blob_id}"
    else:
        raise Exception(f"Failed to upload blob: {response.status_code}, {response.text}")

if __name__ == '__main__':
    app.run(debug=True, port=5000)
