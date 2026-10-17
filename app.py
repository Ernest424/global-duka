import os
from flask import Flask, request, redirect, session, send_from_directory

app = Flask(__name__)
app.secret_key = 'global-duka-secret-123'

IS_POSTGRES = False
try:
    import psycopg2
    if os.environ.get('DATABASE_URL'):
        IS_POSTGRES = True
    else:
        # Check if we can use postgres locally too
        IS_POSTGRES = False
except:
    IS_POSTGRES = False

import sqlite3

STYLE = """
<style>
body{font-family:Arial;background:#f5f5f5;margin:0;padding:0}
.card{background:white;padding:20px;border-radius:10px;box-shadow:0 2px 10px rgba(0,0,0,0.1)}
input,button{padding:10px;margin:5px;width:90%;border-radius:5px;border:1px solid #ccc}
button{background:#0ea5e9;color:white;border:none;cursor:pointer}
</style>
"""

def get_db():
    # Try Postgres if DATABASE_URL exists
    db_url = os.environ.get('DATABASE_URL')
    if db_url:
        import psycopg2
        conn = psycopg2.connect(db_url)
        cur = conn.cursor()
        return conn, cur
    else:
        conn = sqlite3.connect('duka.db')
        cur = conn.cursor()
        return conn, cur

@app.route('/')
def home():
    return redirect('/login')

@app.route('/login', methods=['GET', 'POST'])
def login():
    conn, cur = get_db()
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        try:
            if os.environ.get('DATABASE_URL'):
                cur.execute("SELECT username, shop_id FROM users WHERE username=%s AND password=%s", (username, password))
            else:
                cur.execute("SELECT username, shop_id FROM users WHERE username=? AND password=?", (username, password))
        except:
            cur.execute("SELECT username, shop_id FROM users WHERE username=? AND password=?", (username, password))
        u = cur.fetchone()
        if u:
            session['user'] = u[0]
            session['shop_id'] = u[1]
            return redirect('/dashboard')
    return STYLE + "<div class='card' style='max-width:400px;margin:80px auto'><h2>Login</h2><form method='POST'><input name='username' placeholder='username'><input name='password' type='password' placeholder='password'><button>Login</button></form></div>"

@app.route('/dashboard')
def dashboard():
    if 'user' not in session:
        return redirect('/login')
    conn, cur = get_db()
    try:
        if os.environ.get('DATABASE_URL'):
            cur.execute("SELECT shop_name, country, town, phone, currency_symbol, profile_picture FROM shops WHERE id=%s", (session['shop_id'],))
        else:
            cur.execute("SELECT shop_name, country, town, phone, currency_symbol, profile_picture FROM shops WHERE id=?", (session['shop_id'],))
    except:
        cur.execute("SELECT shop_name, country, town, phone, currency_symbol, profile_picture FROM shops WHERE id=?", (session['shop_id'],))
    
    r = cur.fetchone()
    shop_name = r[0] if r else 'My Shop'
    country = r[1] if r and len(r)>1 else ''
    town = r[2] if r and len(r)>2 else ''
    phone = r[3] if r and len(r)>3 else ''
    profile_pic = r[5] if r and len(r)>5 and r[5] else ''
    
    if profile_pic:
        pic_html = f"<img src='{profile_pic}' style='width:120px;height:120px;border-radius:50%;object-fit:cover;border:3px solid #0ea5e9'><br>"
    else:
        pic_html = "<p>No profile picture yet</p>"
    
    return STYLE + f"""
    <div class='card' style='max-width:600px;margin:30px auto;text-align:center'>
        <h2>✅ ONLINE! {shop_name}</h2>
        {pic_html}
        <p>Country: {country}</p>
        <p>Town: {town}</p>
        <p>Phone: {phone}</p>
        <hr>
        <h3>Upload Profile Picture</h3>
        <form action='/upload-profile' method='POST' enctype='multipart/form-data'>
            <input type='file' name='profile' accept='image/*' required>
            <button type='submit'>Upload Picture</button>
        </form>
    </div>
    """

@app.route('/upload-profile', methods=['POST'])
def upload_profile():
    if 'user' not in session:
        return redirect('/login')
    conn, cur = get_db()
    if 'profile' not in request.files:
        return 'No file selected'
    file = request.files['profile']
    if file.filename == '':
        return 'No file selected'
    
    filename = file.filename.replace(' ', '_')
    os.makedirs('uploads', exist_ok=True)
    file.save(os.path.join('uploads', filename))
    image_path = f'/uploads/{filename}'
    
    try:
        if os.environ.get('DATABASE_URL'):
            cur.execute("UPDATE shops SET profile_picture = %s WHERE id = %s", (image_path, session['shop_id']))
        else:
            cur.execute("UPDATE shops SET profile_picture = ? WHERE id = ?", (image_path, session['shop_id']))
    except:
        cur.execute("UPDATE shops SET profile_picture = ? WHERE id = ?", (image_path, session['shop_id']))
    
    conn.commit()
    return redirect('/dashboard')

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory('uploads', filename)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
