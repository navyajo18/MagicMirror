import cv2
import numpy as np
import mediapipe as mp
from flask import Response, Flask, render_template
import os

UPLOAD_FOLDER = 'uploads'

app = Flask(__name__)

mp_pose = mp.solutions.pose
pose = mp_pose.Pose()

def overlay_transparent(background, overlay, x, y):
    overlay_h, overlay_w = overlay.shape[:2]
    if x + overlay_w > background.shape[1] or y + overlay_h > background.shape[0]:
        return background
    overlay_rgb = overlay[:, :, :3]
    alpha_mask = overlay[:, :, 3] / 255.0
    roi = background[y:y+overlay_h, x:x+overlay_w]
    for c in range(3):  
        roi[:, :, c] = (1 - alpha_mask) * roi[:, :, c] + alpha_mask * overlay_rgb[:, :, c]
    background[y:y+overlay_h, x:x+overlay_w] = roi
    return background

def generate_frames():
    cap = cv2.VideoCapture(0)
    while True:
        ret, frame = cap.read()
        if not ret:
            continue

        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = pose.process(frame_rgb)

        if results.pose_landmarks:
            landmarks = results.pose_landmarks.landmark

            # Use landmarks to position clothing as before
            # Add your t-shirt and pants overlay logic here...

        frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
        _, buffer = cv2.imencode('.jpg', frame)
        frame = buffer.tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

    cap.release()


def load_clothing_images():
    # Load clothing images from the uploads directory
    images = {}
    for filename in os.listdir(UPLOAD_FOLDER):
        if filename.endswith(('.png', '.jpg', '.jpeg')):
            filepath = os.path.join(UPLOAD_FOLDER, filename)
            image = cv2.imread(filepath, cv2.IMREAD_UNCHANGED)
            if image is not None:
                images[filename] = image
    return images

clothing_images = load_clothing_images()

# You can now use `clothing_images` to access the uploaded clothing items.

if __name__ == '__main__':
    app.run(debug=True)
