import requests
from flask import Flask, request, jsonify
from pose_format import Pose
from pose_format.pose_visualizer import PoseVisualizer
import imageio
import numpy as np
from dotenv import load_dotenv
import os
import cloudinary
import cloudinary.uploader

# Load environment variables
load_dotenv()
app = Flask(__name__)

# Access environment variables
CLOUD_NAME = os.getenv('CLOUD_NAME')
API_KEY = os.getenv('API_KEY')
API_SECRET = os.getenv('API_SECRET')

# Configure Cloudinary
cloudinary.config(
    cloud_name=CLOUD_NAME,
    api_key=API_KEY,
    api_secret=API_SECRET
)

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
    if not request.is_json:
        return jsonify({"error": "Missing JSON in request"}), 400
    data = request.get_json()
    text = data.get('text', 'hello') 
    pose_data = fetch_pose_from_api(text)
    pose = Pose.read(pose_data)
    v = PoseVisualizer(pose)
    gif_frames = [frame.astype(np.uint8) for frame in v.draw()]

    gif_path = f"{text}.gif"
    imageio.mimsave(gif_path, gif_frames, format='GIF', fps=10)

    # Upload to Cloudinary
    upload_response = cloudinary.uploader.upload(
        gif_path,
        resource_type='image',
        format='gif'
    )
    os.remove(gif_path)
    
    # Obtain the URL of the uploaded GIF
    gif_url = upload_response.get('url')
    return jsonify({'gif_url': gif_url})

if __name__ == '__main__':
    app.run(debug=True, port=5000)
