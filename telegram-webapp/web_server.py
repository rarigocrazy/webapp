# web_server.py
from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, emit
import sqlite3
import threading
import time
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY') or '4899cd0d1d863eadb332bb38fbb3b2cb'
socketio = SocketIO(app, cors_allowed_origins="*")

# Инициализация базы данных
def init_db():
    conn = sqlite3.connect('bot_data.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_choices (
            user_id INTEGER,
            username TEXT,
            selected_number INTEGER,
            timestamp TEXT,
            PRIMARY KEY (user_id)
        )
    ''')
    conn.commit()
    conn.close()

init_db()

# Функция для получения данных из базы
def get_user_choice(user_id):
    conn = sqlite3.connect('bot_data.db')
    cursor = conn.cursor()
    cursor.execute('SELECT selected_number, username FROM user_choices WHERE user_id = ?', (user_id,))
    result = cursor.fetchone()
    conn.close()
    return result

def get_all_choices():
    conn = sqlite3.connect('bot_data.db')
    cursor = conn.cursor()
    cursor.execute('SELECT user_id, username, selected_number FROM user_choices')
    results = cursor.fetchall()
    conn.close()
    return [{'user_id': row[0], 'username': row[1], 'number': row[2]} for row in results]

# Мониторинг изменений в базе данных
def monitor_database():
    last_data = {}
    while True:
        try:
            current_data = {row['user_id']: row for row in get_all_choices()}
            
            # Проверяем изменения
            if current_data != last_data:
                with app.app_context():
                    socketio.emit('data_update', {'choices': list(current_data.values())})
                last_data = current_data.copy()
            
            time.sleep(2)
        except Exception as e:
            print(f"Error in database monitoring: {e}")
            time.sleep(5)

@app.route('/')
def home():
    return "Server is running! Go to /webapp to see the application."

@app.route('/webapp')
def webapp():
    user_id = request.args.get('user_id', '')
    return render_template('index.html', user_id=user_id)

@app.route('/api/user/<int:user_id>')
def get_user_data(user_id):
    choice = get_user_choice(user_id)
    if choice:
        return jsonify({'user_id': user_id, 'number': choice[0], 'username': choice[1]})
    return jsonify({'error': 'User not found'}), 404

@app.route('/api/all_choices')
def get_all_data():
    return jsonify({'choices': get_all_choices()})

@app.route('/health')
def health():
    return jsonify({'status': 'ok'})

if __name__ == '__main__':
    # Запускаем мониторинг в отдельном потоке
    monitor_thread = threading.Thread(target=monitor_database, daemon=True)
    monitor_thread.start()
    
    # Для Render
    port = int(os.environ.get('PORT', 5000))
    socketio.run(app, host='0.0.0.0', port=port, debug=False)