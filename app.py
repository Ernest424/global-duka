import os
from flask import Flask, request, redirect, session, render_template, send_from_directory
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'shopkeeper-secret-123'

UPLOAD_FOLDER = 'uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Database setup
try:
    import psycopg2
    DATABASE_URL = os.environ.get('DATABASE_URL')
    USE_POSTGRES = True if DATABASE_URL else False
except:
    USE_POSTGRES = False
    import sqlite3

def get_db():
    if USE_POSTGRES:
        conn = psycopg2.connect(os.environ.get('DATABASE_URL'))
        return conn
    else:
        conn = sqlite3.connect('shopkeeper.db')
        return conn

def init_db():
    conn = get_db()
    cur = conn.cursor()
    if USE_POSTGRES:
        cur.execute('''CREATE TABLE IF NOT EXISTS shops 
                     (id SERIAL PRIMARY KEY, username TEXT, password TEXT, shop_name TEXT, profile_picture TEXT)''')
    else:
        cur.execute('''CREATE TABLE IF NOT EXISTS shops 
                     (id INTEGER PRIMARY KEY, username TEXT, password TEXT, shop_name TEXT, profile_picture TEXT)''')
    conn.commit()
    conn.close()

init_db()

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = get_db()
        cur = conn.cursor()
        if USE_POSTGRES:
            cur.execute("SELECT * FROM shops WHERE username = %s AND password = %s", (username, password))
        else:
            cur.execute("SELECT * FROM shops WHERE username = ? AND password = ?", (username, password))
        user = cur.fetchone()
        conn.close()
        if user:
            session['user_id'] = user[0]
            session['username'] = username
            return redirect('/dashboard')
        else:
            return "Invalid login"
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        shop_name = request.form.get('shop_name', 'Shopkeeper')
        conn = get_db()
        cur = conn.cursor()
        if USE_POSTGRES:
            cur.execute("INSERT INTO shops (username, password, shop_name) VALUES (%s, %s, %s)", (username, password, shop_name))
        else:
            cur.execute("INSERT INTO shops (username, password, shop_name) VALUES (?, ?, ?)", (username, password, shop_name))
        conn.commit()
        conn.close()
        return redirect('/login')
    return render_template('register.html')

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect('/login')
    conn = get_db()
    cur = conn.cursor()
    if USE_POSTGRES:
        cur.execute("SELECT * FROM shops WHERE id = %s", (session['user_id'],))
    else:
        cur.execute("SELECT * FROM shops WHERE id = ?", (session['user_id'],))
    shop = cur.fetchone()
    conn.close()
    return render_template('dashboard.html', shop=shop)

@app.route('/upload_profile', methods=['POST'])
def upload_profile():
    if 'user_id' not in session:
        return redirect('/login')
    if 'profile_picture' not in request.files:
        return redirect('/dashboard')
    file = request.files['profile_picture']
    if file.filename == '':
        return redirect('/dashboard')
    if file:
        filename = secure_filename(file.filename)
        image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(image_path)
        conn = get_db()
        cur = conn.cursor()
        try:
            if USE_POSTGRES:
                cur.execute("UPDATE shops SET profile_picture = %s WHERE id = %s", (image_path, session['user_id']))
            else:
                cur.execute("UPDATE shops SET profile_picture = ? WHERE id = ?", (image_path, session['user_id']))
        except:
            if USE_POSTGRES:
                cur.execute("UPDATE shops SET profile_picture = %s WHERE id = %s", (image_path, session['user_id']))
            else:
                cur.execute("UPDATE shops SET profile_picture = ? WHERE id = ?", (image_path, session['user_id']))
        conn.commit()
        conn.close()
        return redirect('/dashboard')

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory('uploads', filename)

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
