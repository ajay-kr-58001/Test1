import os
from flask import Flask, request, jsonify, session, send_from_directory, render_template
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import sqlite3

app = Flask(__name__, static_folder='sky', static_url_path='')
app.secret_key = 'super_secret_key_for_assessment'

DATABASE = 'database.db'

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with app.app_context():
        db = get_db()
        db.execute('''
            CREATE TABLE IF NOT EXISTS admin (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                full_name TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL
            )
        ''')
        db.execute('''
            CREATE TABLE IF NOT EXISTS opportunity (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                admin_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                duration TEXT NOT NULL,
                start_date TEXT NOT NULL,
                description TEXT NOT NULL,
                skills TEXT NOT NULL,
                category TEXT NOT NULL,
                future_opportunities TEXT NOT NULL,
                max_applicants TEXT,
                FOREIGN KEY (admin_id) REFERENCES admin (id)
            )
        ''')
        db.commit()

init_db()

@app.route('/')
def index():
    return app.send_static_file('admin.html')

@app.route('/api/signup', methods=['POST'])
def signup():
    data = request.json
    full_name = data.get('full_name')
    email = data.get('email')
    password = data.get('password')
    confirm_password = data.get('confirm_password')

    if not full_name or not email or not password or not confirm_password:
        return jsonify({'error': 'All fields are required.'}), 400
    if password != confirm_password:
        return jsonify({'error': 'Passwords do not match.'}), 400
    if len(password) < 8:
        return jsonify({'error': 'Password must be at least 8 characters.'}), 400

    db = get_db()
    existing_user = db.execute('SELECT * FROM admin WHERE email = ?', (email,)).fetchone()
    if existing_user:
        return jsonify({'error': 'Account already exists.'}), 400

    hashed_pw = generate_password_hash(password)
    db.execute('INSERT INTO admin (full_name, email, password) VALUES (?, ?, ?)', (full_name, email, hashed_pw))
    db.commit()
    return jsonify({'success': 'Account created successfully.'})

@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    email = data.get('email')
    password = data.get('password')
    remember_me = data.get('remember_me', False)

    db = get_db()
    user = db.execute('SELECT * FROM admin WHERE email = ?', (email,)).fetchone()
    
    if user and check_password_hash(user['password'], password):
        session.clear()
        session['admin_id'] = user['id']
        session['email'] = user['email']
        
        if remember_me:
            session.permanent = True
            app.permanent_session_lifetime = timedelta(days=30)
        else:
            session.permanent = False
            
        return jsonify({'success': 'Login successful.', 'email': user['email']})
    
    return jsonify({'error': 'Invalid email or password.'}), 401

@app.route('/api/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({'success': 'Logged out.'})

@app.route('/api/forgot_password', methods=['POST'])
def forgot_password():
    data = request.json
    email = data.get('email')
    # Always show success as per requirements
    return jsonify({'success': 'Reset link sent to your email.'})

@app.route('/api/check_session', methods=['GET'])
def check_session():
    if 'admin_id' in session:
        return jsonify({'logged_in': True, 'email': session['email']})
    return jsonify({'logged_in': False})

@app.route('/api/opportunities', methods=['GET'])
def get_opportunities():
    if 'admin_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    db = get_db()
    opportunities = db.execute('SELECT * FROM opportunity WHERE admin_id = ? ORDER BY id DESC', (session['admin_id'],)).fetchall()
    
    return jsonify([dict(opp) for opp in opportunities])

@app.route('/api/opportunities', methods=['POST'])
def add_opportunity():
    if 'admin_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    data = request.json
    required_fields = ['name', 'duration', 'start_date', 'description', 'skills', 'category', 'future_opportunities']
    for field in required_fields:
        if not data.get(field):
            return jsonify({'error': f'{field} is required.'}), 400
            
    db = get_db()
    cursor = db.cursor()
    cursor.execute('''
        INSERT INTO opportunity (admin_id, name, duration, start_date, description, skills, category, future_opportunities, max_applicants)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (session['admin_id'], data['name'], data['duration'], data['start_date'], data['description'], 
          data['skills'], data['category'], data['future_opportunities'], data.get('max_applicants', '')))
    db.commit()
    
    return jsonify({'success': 'Opportunity added.', 'id': cursor.lastrowid})

@app.route('/api/opportunities/<int:opp_id>', methods=['PUT'])
def edit_opportunity(opp_id):
    if 'admin_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
        
    data = request.json
    required_fields = ['name', 'duration', 'start_date', 'description', 'skills', 'category', 'future_opportunities']
    for field in required_fields:
        if not data.get(field):
            return jsonify({'error': f'{field} is required.'}), 400

    db = get_db()
    # Check if opportunity belongs to admin
    opp = db.execute('SELECT * FROM opportunity WHERE id = ? AND admin_id = ?', (opp_id, session['admin_id'])).fetchone()
    if not opp:
        return jsonify({'error': 'Not found or unauthorized.'}), 404
        
    db.execute('''
        UPDATE opportunity 
        SET name=?, duration=?, start_date=?, description=?, skills=?, category=?, future_opportunities=?, max_applicants=?
        WHERE id=? AND admin_id=?
    ''', (data['name'], data['duration'], data['start_date'], data['description'], data['skills'], 
          data['category'], data['future_opportunities'], data.get('max_applicants', ''), opp_id, session['admin_id']))
    db.commit()
    
    return jsonify({'success': 'Opportunity updated.'})

@app.route('/api/opportunities/<int:opp_id>', methods=['DELETE'])
def delete_opportunity(opp_id):
    if 'admin_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
        
    db = get_db()
    opp = db.execute('SELECT * FROM opportunity WHERE id = ? AND admin_id = ?', (opp_id, session['admin_id'])).fetchone()
    if not opp:
        return jsonify({'error': 'Not found or unauthorized.'}), 404
        
    db.execute('DELETE FROM opportunity WHERE id = ? AND admin_id = ?', (opp_id, session['admin_id']))
    db.commit()
    return jsonify({'success': 'Opportunity deleted.'})

if __name__ == '__main__':
    app.run(debug=True, port=5000)
