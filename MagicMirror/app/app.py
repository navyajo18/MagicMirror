import sqlite3
import os
from flask import Flask, request, render_template, redirect, url_for
from werkzeug.utils import secure_filename

app = Flask(__name__)

# Directory to store uploaded images
UPLOAD_FOLDER = 'uploads'
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
            save_clothing_item(type, filepath)
            return redirect(url_for('uploaded_file', filename=filename))
    return render_template('upload.html')

def save_clothing_item(type, image_path):
    with get_db_connection() as conn:
        conn.execute('INSERT INTO clothing (type, image_path) VALUES (?, ?)', (type, image_path))
        conn.commit()

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    """Display the uploaded file."""
    return f"File uploaded successfully: {filename}"

@app.route('/clothing/<type>')
def show_clothing(type):
    items = []
    with get_db_connection() as conn:
        items = conn.execute('SELECT * FROM clothing WHERE type = ?', (type,)).fetchall()
    return render_template('show_clothing.html', items=items)

if __name__ == '__main__':
    app.run(debug=True)
