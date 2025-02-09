import sqlite3
import os
from flask import Flask, request, render_template, redirect, url_for, flash, send_from_directory
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'supersecretkey'  # Needed for flashing messages

# Directory to store uploaded images (inside app folder)
UPLOAD_FOLDER = os.path.join(app.root_path, 'uploads')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Ensure the upload folder exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

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
        type = request.form['clothingType']
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            save_clothing_item(type, filename)  # Save only the filename
            flash(f"You've uploaded a {type}!")
    return render_template('upload.html')

def save_clothing_item(type, image_path):
    with get_db_connection() as conn:
        conn.execute('INSERT INTO clothing (type, image_path) VALUES (?, ?)', (type, image_path))
        conn.commit()

@app.route('/uploads/<filename>')
def uploaded_file(filename):
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

from flask import Response

@app.route('/video_feed')
def video_feed():
    from virtual import generate_frames
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/try_it_on')
def try_it_on():
    return render_template('try_it_on.html')

if __name__ == '__main__':
    app.run(debug=True)
