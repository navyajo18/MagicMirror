import sqlite3
import os
from flask import Flask, request, render_template, redirect, url_for, flash, send_from_directory, Response
from werkzeug.utils import secure_filename
import cv2
import mediapipe as mp
import numpy as np

app = Flask(__name__)
app.secret_key = 'supersecretkey'  # Needed for flashing messages

# Base directory for uploads
UPLOAD_FOLDER = os.path.join(app.root_path, 'uploads')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Create specific folders for 'SHIRTS' and 'PANTS'
SHIRT_FOLDER = os.path.join(UPLOAD_FOLDER, 'SHIRTS')
PANTS_FOLDER = os.path.join(UPLOAD_FOLDER, 'PANTS')
os.makedirs(SHIRT_FOLDER, exist_ok=True)
os.makedirs(PANTS_FOLDER, exist_ok=True)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

DATABASE = 'virtual_try_on.db'

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_db_connection() as conn:
        conn.execute('''CREATE TABLE IF NOT EXISTS clothing (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        type TEXT NOT NULL,
                        image_path TEXT NOT NULL)''')
        conn.commit()

init_db()  # Ensure the database and table are created

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        file = request.files['clothingImage']
        clothing_type = request.form['clothingType']
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            if clothing_type == 'shirt':
                filepath = os.path.join(SHIRT_FOLDER, filename)
            elif clothing_type == 'pant':
                filepath = os.path.join(PANTS_FOLDER, filename)
            else:
                filepath = os.path.join(UPLOAD_FOLDER, filename)  # Default case for other types
            file.save(filepath)
            save_clothing_item(clothing_type, filepath)  # Save path in DB might need updating
            flash(f"You've uploaded a {clothing_type}!")
    return render_template('upload.html')

def save_clothing_item(clothing_type, filepath):
    with get_db_connection() as conn:
        conn.execute('INSERT INTO clothing (type, image_path) VALUES (?, ?)', (clothing_type, os.path.relpath(filepath, UPLOAD_FOLDER)))
        conn.commit()

@app.route('/uploads/<path:filename>')
def uploaded_file(filename):
    print("Trying to serve:", filename)  # Debugging
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/clothing/<type>')
def show_clothing(type):
    with get_db_connection() as conn:
        items = conn.execute('SELECT * FROM clothing WHERE type = ?', (type,)).fetchall()
    return render_template('show_clothing.html', items=items)

@app.route('/wardrobe')
def wardrobe():
    with get_db_connection() as conn:
        items = conn.execute('SELECT * FROM clothing').fetchall()
    wardrobe = {}
    for item in items:
        wardrobe.setdefault(item['type'], []).append(item)
    return render_template('wardrobe.html', wardrobe=wardrobe)

@app.route('/delete/<int:item_id>', methods=['POST'])
def delete_item(item_id):
    with get_db_connection() as conn:
        item = conn.execute('SELECT image_path FROM clothing WHERE id = ?', (item_id,)).fetchone()
        if item:
            image_path = os.path.join(app.config['UPLOAD_FOLDER'], item['image_path'])
            if os.path.exists(image_path):
                os.remove(image_path)
            conn.execute('DELETE FROM clothing WHERE id = ?', (item_id,))
            conn.commit()
            flash('Item removed from wardrobe.')
    return redirect(url_for('wardrobe'))

# Video feed setup
camera = cv2.VideoCapture(1)

# Initialize MediaPipe Pose
mp_pose = mp.solutions.pose
pose = mp_pose.Pose()

# Function to overlay transparent images (clothing)
def overlay_transparent(background, overlay, x, y):
    overlay_h, overlay_w = overlay.shape[:2]

    # Ensure overlay does not exceed frame size
    if x + overlay_w > background.shape[1] or y + overlay_h > background.shape[0]:
        return background

    overlay_rgb = overlay[:, :, :3]  # Extract RGB channels
    alpha_mask = overlay[:, :, 3] / 255.0  # Normalize alpha (0 to 1)

    roi = background[y:y+overlay_h, x:x+overlay_w]

    # Blend overlay with background using the alpha channel
    for c in range(3):  
        roi[:, :, c] = (1 - alpha_mask) * roi[:, :, c] + alpha_mask * overlay_rgb[:, :, c]

    background[y:y+overlay_h, x:x+overlay_w] = roi
    return background

def generate_frames():
    # Load t-shirt and pants images (replace with correct paths)
    tshirt_path = "MagicMirror/app/uploads/SHIRTS/image_1.png"
    pants_path = "MagicMirror/app/uploads/PANTS/image-2.png"
    
    tshirt = cv2.imread(tshirt_path, cv2.IMREAD_UNCHANGED)  # Load transparent t-shirt image
    pants = cv2.imread(pants_path, cv2.IMREAD_UNCHANGED)  # Load transparent pants image

    if tshirt is None or pants is None:
        print(f"Error: Could not load clothing images. Check the file paths.")
        return

    while True:
        # Read the camera frame in BGR (OpenCV default)
        success, frame = camera.read()
        if not success:
            break
        
        # Convert the frame to RGB for pose detection only
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = pose.process(frame_rgb)

        if results.pose_landmarks:
            landmarks = results.pose_landmarks.landmark

            # T-shirt: Using shoulder landmarks (LEFT_SHOULDER, RIGHT_SHOULDER)
            left_shoulder = landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER]
            right_shoulder = landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER]

            img_h, img_w, _ = frame.shape
            x1, y1 = int(left_shoulder.x * img_w), int(left_shoulder.y * img_h)
            x2, y2 = int(right_shoulder.x * img_w), int(right_shoulder.y * img_h)

            tshirt_width = max(int(abs(x2 - x1) * 1.4), 1)  
            tshirt_height = max(int(tshirt.shape[0] * (tshirt_width / tshirt.shape[1])), 1)

            tshirt_resized = cv2.resize(tshirt, (tshirt_width, tshirt_height))

            x_center = (x1 + x2) // 2
            x_pos = x_center - (tshirt_width // 2)

            y_pos = min(y1, y2) - tshirt_height // 8

            frame = overlay_transparent(frame, tshirt_resized, x_pos, y_pos)

            # Pants: Using hip landmarks (LEFT_HIP, RIGHT_HIP)
            left_hip = landmarks[mp_pose.PoseLandmark.LEFT_HIP]
            right_hip = landmarks[mp_pose.PoseLandmark.RIGHT_HIP]

            x1, y1 = int(left_hip.x * img_w), int(left_hip.y * img_h)
            x2, y2 = int(right_hip.x * img_w), int(right_hip.y * img_h)

            pants_width = max(int(abs(x2 - x1) * 1.8), 1)  
            pants_height = max(int(pants.shape[0] * (pants_width / pants.shape[1])), 1)

            pants_resized = cv2.resize(pants, (pants_width, pants_height))

            x_center = (x1 + x2) // 2
            x_pos = x_center - (pants_width // 2)

            y_pos = min(y1, y2)  # Position pants just below the hips

            frame = overlay_transparent(frame, pants_resized, x_pos, y_pos)

        # Convert the frame back to BGR (to preserve the original colors) and send to the browser
        ret, buffer = cv2.imencode('.jpg', frame)
        frame = buffer.tobytes()

        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/try_it_on')
def try_it_on():
    return render_template('try_it_on.html')

if __name__ == '__main__':
    app.run(debug=True)
