import os, json
from flask import Flask, request, redirect, session
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'global_duka_online_2026'

# Use Postgres locally, SQLite online (Render)
try:
    import psycopg2
    conn = psycopg2.connect(dbname="duka_db", user="postgres", password="mkame2026", host="localhost")
    conn.autocommit = True
    cur = conn.cursor()
    IS_POSTGRES = True
    print("Using Postgres local")
except:
    import sqlite3
    conn = sqlite3.connect('duka.db', check_same_thread=False)
    cur = conn.cursor()
    IS_POSTGRES = False
    print("Using SQLite online")

PHONE_CODES = {
"Kenya": ("+254","KE","KSh"),"Tanzania": ("+255","TZ","TSh"),"Uganda": ("+256","UG","USh"),"Rwanda": ("+250","RW","FRw"),"Burundi": ("+257","BI","FBu"),
"Ethiopia": ("+251","ET","Br"),"Somalia": ("+252","SO","Sh"),"South Sudan": ("+211","SS","£"),"Nigeria": ("+234","NG","₦"),"Ghana": ("+233","GH","₵"),
"South Africa": ("+27","ZA","R"),"Egypt": ("+20","EG","E£"),"USA": ("+1","US","$"),"UK": ("+44","GB","£"),"Canada": ("+1","CA","C$"),
"Germany": ("+49","DE","€"),"France": ("+33","FR","€"),"China": ("+86","CN","¥"),"India": ("+91","IN","₹"),"UAE": ("+971","AE","AED"),
"Other": ("+1","OT","$")
}
WORLD_REGIONS = {
"Kenya": ["Laikipia","Nairobi","Mombasa","Kiambu","Nakuru","Kisumu","Meru","Uasin Gishu","Kakamega","Machakos","Narok","Kajiado"],
"Tanzania": ["Dar es Salaam","Arusha","Mwanza","Dodoma","Mbeya","Kilimanjaro"],
"Uganda": ["Kampala","Gulu","Mbarara","Jinja","Wakiso"],
"Nigeria": ["Lagos","Abuja","Kano","Rivers","Oyo","Kaduna"],
"Ghana": ["Greater Accra","Ashanti","Western"],
"South Africa": ["Gauteng","Western Cape","KwaZulu-Natal"],
"USA": ["California","Texas","Florida","New York","Washington"],
"UK": ["London","Manchester","Birmingham"],
"India": ["Maharashtra","Delhi","Karnataka","Tamil Nadu"],
"Other": ["Main Region"]
}
TOWNS_PER_REGION = {
"Laikipia": ["Nanyuki","Nyahururu","Rumuruti","Doldol","Timau","Ol Jabet"],
"Nairobi": ["Westlands","CBD","Eastleigh","Embakasi","Kibera","Kasarani"],
"Lagos": ["Ikeja","Lekki","Victoria Island","Surulere"],
"California": ["Los Angeles","San Francisco","San Diego"],
}

if IS_POSTGRES:
    cur.execute("""
    CREATE TABLE IF NOT EXISTS shops (id SERIAL PRIMARY KEY, shop_name VARCHAR(100), owner_name VARCHAR(100), country VARCHAR(100), currency_code VARCHAR(10), currency_symbol VARCHAR(10), town VARCHAR(100), phone VARCHAR(50), created_at TIMESTAMP);
    CREATE TABLE IF NOT EXISTS users (id SERIAL PRIMARY KEY, username VARCHAR(50) UNIQUE, password VARCHAR(100), role VARCHAR(20), shop_id INT);
    CREATE TABLE IF NOT EXISTS products (id SERIAL PRIMARY KEY, name VARCHAR(100), buying_price FLOAT, selling_price FLOAT, stock INT, category VARCHAR(50), shop_id INT, barcode VARCHAR(50));
    CREATE TABLE IF NOT EXISTS sales (id SERIAL PRIMARY KEY, product_name VARCHAR(100), quantity INT, total FLOAT, profit FLOAT, date TIMESTAMP, seller VARCHAR(50), shop_id INT, payment_method VARCHAR(20), customer_phone VARCHAR(20), receipt_no VARCHAR(20));
    """)
else:
    cur.execute("CREATE TABLE IF NOT EXISTS shops (id INTEGER PRIMARY KEY AUTOINCREMENT, shop_name TEXT, owner_name TEXT, country TEXT, currency_code TEXT, currency_symbol TEXT, town TEXT, phone TEXT, created_at TEXT)")
    cur.execute("CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE, password TEXT, role TEXT, shop_id INTEGER)")
    cur.execute("CREATE TABLE IF NOT EXISTS products (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, buying_price REAL, selling_price REAL, stock INTEGER, category TEXT, shop_id INTEGER, barcode TEXT)")
    cur.execute("CREATE TABLE IF NOT EXISTS sales (id INTEGER PRIMARY KEY AUTOINCREMENT, product_name TEXT, quantity INTEGER, total REAL, profit REAL, date TEXT, seller TEXT, shop_id INTEGER, payment_method TEXT, customer_phone TEXT, receipt_no TEXT)")
    conn.commit()

STYLE = "<style>body{font-family:Arial;background:#f4f6f9;margin:0}.card{background:white;padding:18px;margin:12px;border-radius:10px;box-shadow:0 2px 5px rgba(0,0,0,0.1)}.btn{padding:12px;border:none;border-radius:6px;cursor:pointer;font-weight:bold}.btn-g{background:#27ae60;color:white;width:100%} input,select{padding:11px;width:96%;margin:6px 0;border:1px solid #ccc;border-radius:6px}.box{padding:12px;border-radius:8px;margin:10px 0}.blue{background:#eaf7ff;border:1px solid #3498db}.yellow{background:#fff9e6;border:1px solid #f1c40f}.green{background:#eafaf1;border:1px solid #27ae60}.phone-group{display:flex;gap:5px}.phone-group select{width:35%}.phone-group input{width:65%}</style>"

@app.route('/register-shop', methods=['GET','POST'])
def register_shop():
    msg=""
    if request.method=='POST':
        country=request.form['country']; region=request.form.get('region',''); town=request.form.get('town','')
        if town=='OTHER': town=request.form.get('town_custom','Town')
        full=f"{region} - {town}"; code,flag,sym=PHONE_CODES.get(country, ("+254","KE","KSh")); dial=request.form.get('dial_code',code); phone_number=request.form.get('phone_number',''); full_phone=f"{dial} {phone_number}"
        if IS_POSTGRES:
            cur.execute("INSERT INTO shops (shop_name,owner_name,country,currency_code,currency_symbol,town,phone,created_at) VALUES (%s,%s,%s,%s,%s,%s,%s,%s) RETURNING id",(request.form['shop_name'],request.form['owner'],country,country,sym,full,full_phone,datetime.now()))
            sid=cur.fetchone()[0]
            cur.execute("INSERT INTO users (username,password,role,shop_id) VALUES (%s,%s,'admin',%s)",(request.form['username'],request.form['password'],sid))
        else:
            cur.execute("INSERT INTO shops (shop_name,owner_name,country,currency_code,currency_symbol,town,phone,created_at) VALUES (?,?,?,?,?,?,?,?)",(request.form['shop_name'],request.form['owner'],country,country,sym,full,full_phone,str(datetime.now())))
            sid=cur.lastrowid
            cur.execute("INSERT INTO users (username,password,role,shop_id) VALUES (?,?,?,?)",(request.form['username'],request.form['password'],'admin',sid))
            conn.commit()
        msg=f"✅ Shop created! {country} {flag} {full} | Phone: {full_phone} | Currency: {sym}"
    c_opts="".join([f"<option value='{c}'>{flag} {c} ({code} - {sym})</option>" for c,(code,flag,sym) in sorted(PHONE_CODES.items())])
    dial_opts="".join([f"<option value='{v[0]}'>{v[1]} {v[0]}</option>" for k,v in sorted(PHONE_CODES.items())])
    return STYLE + f"""
    <div class='card' style='max-width:700px;margin:20px auto'>
    <h2>🌍 World Duka - Online Global Registration</h2>
    <p style='color:green;font-weight:bold'>{msg}</p>
    <p style='background:#d4efdf;padding:10px;border-radius:6px'>✅ ONLINE READY! Country codes + Counties + Receipt + M-Pesa!</p>
    <form method='POST'>
    Shop Name<br><input name='shop_name' required placeholder='Nga-ra Duka'><br>
    Owner<br><input name='owner' required value="Ernest"><br>
    Country<br><select name='country' id='country' onchange='updateAll()' required><option value=''>-- Select --</option>{c_opts}</select><br>
    Region / County<br><select name='region' id='region' onchange='loadTowns()' required><option>Select Country First</option></select><br>
    Town<br><select name='town' id='town' required><option>Select Region First</option></select><br>
    <input name='town_custom' placeholder='Custom town if OTHER'><br>
    Phone with Country Code<br><div class='phone-group'><select name='dial_code' id='dial_code' required>{dial_opts}</select><input name='phone_number' id='phone_number' required placeholder='712 345 678'></div><br>
    Username<br><input name='username' required><br>
    Password<br><input type='password' name='password' required><br><br>
    <button class='btn btn-g'>CREATE SHOP ONLINE</button>
    </form><br><a href='/shops'>View All Shops Worldwide</a> | <a href='/login'>Login</a>
    </div>
    <script>const regions={json.dumps(WORLD_REGIONS)}; const towns={json.dumps(TOWNS_PER_REGION)}; const phoneCodes={json.dumps(PHONE_CODES)}; function updateAll(){{const c=document.getElementById('country').value; const r=document.getElementById('region'); r.innerHTML=''; (regions[c]||regions['Other']).forEach(x=>{{let o=document.createElement('option');o.value=x;o.textContent=x;r.appendChild(o)}}); if(phoneCodes[c]){{document.getElementById('dial_code').value=phoneCodes[c][0];}} loadTowns();}} function loadTowns(){{const reg=document.getElementById('region').value; const t=document.getElementById('town'); t.innerHTML=''; const list=towns[reg]||[reg+' Main Town']; list.forEach(x=>{{let o=document.createElement('option');o.value=x;o.textContent=x;t.appendChild(o)}}); let o=document.createElement('option');o.value='OTHER';o.textContent='OTHER';t.appendChild(o);}} document.getElementById('country').value='Kenya'; updateAll(); setTimeout(()=>{{document.getElementById('region').value='Laikipia'; loadTowns(); document.getElementById('town').value='Nanyuki'}},300);</script>
    """

@app.route('/shops')
def shops():
    if IS_POSTGRES:
        cur.execute("SELECT shop_name,country,town,phone,currency_symbol FROM shops ORDER BY id DESC")
        rows=cur.fetchall()
    else:
        cur.execute("SELECT shop_name,country,town,phone,currency_symbol FROM shops ORDER BY id DESC")
        rows=cur.fetchall()
    html="".join([f"<tr><td>{r[0]}</td><td>{r[1]}</td><td>{r[2]}</td><td><b>{r[3]}</b></td><td>{r[4]}</td></tr>" for r in rows])
    return STYLE + f"<div class='card'><h2>🌍 All Shops Worldwide Online</h2><table border='1' style='width:100%;border-collapse:collapse'><tr><th>Shop</th><th>Country</th><th>County-Town</th><th>Phone Code</th><th>Curr</th></tr>{html}</table><br><a href='/register-shop'>Add Shop</a> | <a href='/login'>Login</a></div>"

@app.route('/')
def home():
    return redirect('/register-shop')

@app.route('/login', methods=['GET','POST'])
def login():
    if request.method=='POST':
        if IS_POSTGRES:
            cur.execute("SELECT username,shop_id FROM users WHERE username=%s AND password=%s",(request.form['username'], request.form['password']))
            u=cur.fetchone()
        else:
            cur.execute("SELECT username,shop_id FROM users WHERE username=? AND password=?",(request.form['username'], request.form['password']))
            u=cur.fetchone()
        if u:
            session['user']=u[0]; session['shop_id']=u[1]
            return redirect('/dashboard')
    return STYLE + "<div class='card' style='max-width:400px;margin:80px auto'><h2>Login</h2><form method='POST'><input name='username' placeholder='Username' required><br><input type='password' name='password' required><br><br><button class='btn btn-g'>Login</button></form><br><a href='/register-shop'>Register with Phone Code</a></div>"

@app.route('/dashboard')
def dashboard():
    if 'user' not in session: return redirect('/login')
    if IS_POSTGRES:
        cur.execute("SELECT shop_name,country,town,phone,currency_symbol FROM shops WHERE id=%s",(session.get('shop_id'),))
    else:
        cur.execute("SELECT shop_name,country,town,phone,currency_symbol FROM shops WHERE id=?",(session.get('shop_id'),))
    r=cur.fetchone()
    return STYLE + f"<div class='card'><h2>✅ ONLINE! {r[0] if r else ''}</h2><p>Country: {r[1] if r else ''}<br>Location: {r[2] if r else ''}<br>Phone: <b style='color:green'>{r[3] if r else ''}</b><br>Currency: {r[4] if r else ''}</p><p>🎉 Your shop is LIVE online! Share link to customers!</p><a href='/shops'>View All Shops</a></div>" if r else STYLE+"<div class='card'>No shop</div>"

if __name__=='__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)