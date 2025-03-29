# === SERVER CODE ===
# Dependencies: Flask, SQLite
# Install Flask using: pip install flask

from flask import Flask, request, jsonify
import sqlite3
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # Allow cross-origin requests from the client

DB_NAME = 'users.db'

# Utility function to execute DB queries
def query_db(query, args=(), one=False, commit=False):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(query, args)
    if commit:
        conn.commit()
        result = None
    else:
        result = cursor.fetchall()
    conn.close()
    return (result[0] if result else None) if one else result

# Initialize database tables
@app.route('/init', methods=['POST'])
def init_db():
    query_db('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL
        );
    ''', commit=True)

    query_db('''
        CREATE TABLE IF NOT EXISTS meetings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            meeting_name TEXT NOT NULL UNIQUE,
            meeting_password TEXT,
            max_participants INTEGER,
            creator_username TEXT NOT NULL,
            waiting_room_enabled INTEGER DEFAULT 0
        );
    ''', commit=True)

    return jsonify({"status": "Database initialized"})

# Sign up
@app.route('/signup', methods=['POST'])
def signup():
    data = request.json
    username = data['username']
    password = data['password']
    existing = query_db('SELECT * FROM users WHERE username = ?', (username,), one=True)
    if existing:
        return jsonify({"success": False, "message": "Username already exists."})
    query_db('INSERT INTO users (username, password) VALUES (?, ?)', (username, password), commit=True)
    return jsonify({"success": True})

# Login
@app.route('/login', methods=['POST'])
def login():
    data = request.json
    username = data['username']
    password = data['password']
    user = query_db('SELECT * FROM users WHERE username = ? AND password = ?', (username, password), one=True)
    if user:
        return jsonify({"success": True})
    return jsonify({"success": False, "message": "Invalid username or password."})

# Create meeting
@app.route('/create_meeting', methods=['POST'])
def create_meeting():
    data = request.json
    query_db('''INSERT INTO meetings (meeting_name, meeting_password, max_participants, creator_username, waiting_room_enabled) 
                VALUES (?, ?, ?, ?, ?)''',
             (data['meeting_name'], data['meeting_password'], data['max_participants'], data['creator_username'], data['waiting_room_enabled']),
             commit=True)
    return jsonify({"success": True})

# Join meeting
@app.route('/join_meeting', methods=['POST'])
def join_meeting():
    data = request.json
    if data['meeting_password']:
        meeting = query_db('SELECT * FROM meetings WHERE meeting_name = ? AND meeting_password = ?',
                           (data['meeting_name'], data['meeting_password']), one=True)
    else:
        meeting = query_db('SELECT * FROM meetings WHERE meeting_name = ?', (data['meeting_name'],), one=True)
    if meeting:
        return jsonify({"success": True, "meeting": {
            "meeting_name": meeting[1],
            "meeting_password": meeting[2],
            "max_participants": meeting[3],
            "creator_username": meeting[4],
            "waiting_room_enabled": meeting[5]
        }})
    return jsonify({"success": False, "message": "Invalid meeting name or password."})

# Delete meeting (used on exit)
@app.route('/delete_meeting', methods=['POST'])
def delete_meeting():
    data = request.json
    query_db('DELETE FROM meetings WHERE creator_username = ?', (data['creator_username'],), commit=True)
    return jsonify({"success": True})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
