import json
import os
from flask import Flask, request, jsonify
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

# Инициализация Flask-приложения
app = Flask(__name__)

# Инициализация Flask-Limiter
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["100 per day"]
)

# Файл для хранения данных
DATA_FILE = 'data.json'

# Загрузка данных из файла при старте
def load_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return {}
    return {}

# Функция сохранения данных в файл
def save_data(data_dict):
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data_dict, f, ensure_ascii=False, indent=4)

# Инициализация хранилища
data_store = load_data()

# Главная страница - информационная
@app.route('/')
def index():
    loaded_keys = len(data_store)
    return f"""
    <html>
    <head><title>Key-Value Storage API</title></head>
    <body>
        <h1>Key-Value Storage API</h1>
        <p>Данные загружены из файла: {DATA_FILE}</p>
        <p>Загружено ключей: {loaded_keys}</p>
        <p>Доступные эндпоинты:</p>
        <ul>
            <li>POST /set - сохранить ключ-значение</li>
            <li>GET /get/&lt;key&gt; - получить значение по ключу</li>
            <li>DELETE /delete/&lt;key&gt; - удалить ключ</li>
            <li>GET /exists/&lt;key&gt; - проверить наличие ключа</li>
        </ul>
    </body>
    </html>
    """

# 1. POST /set - сохранение ключа и значения
@app.route('/set', methods=['POST'])
@limiter.limit("10 per minute")
def set_key():
    if not request.is_json:
        return jsonify({"error": "Request must be JSON"}), 400

    content = request.get_json()
    key = content.get('key')
    value = content.get('value')

    if key is None or value is None:
        return jsonify({"error": "Both 'key' and 'value' are required"}), 400

    data_store[key] = value
    save_data(data_store)

    return jsonify({"status": "success", "key": key, "value": value}), 201

# 2. GET /get/<key> - получение значения по ключу
@app.route('/get/<key>', methods=['GET'])
def get_key(key):
    value = data_store.get(key)
    if value is None:
        return jsonify({"error": f"Key '{key}' not found"}), 404
    return jsonify({"key": key, "value": value}), 200

# 3. DELETE /delete/<key> - удаление ключа
@app.route('/delete/<key>', methods=['DELETE'])
@limiter.limit("10 per minute")
def delete_key(key):
    if key not in data_store:
        return jsonify({"error": f"Key '{key}' not found"}), 404

    value = data_store.pop(key)
    save_data(data_store)

    return jsonify({"status": "deleted", "key": key, "value": value}), 200

# 4. GET /exists/<key> - проверка существования ключа
@app.route('/exists/<key>', methods=['GET'])
def exists_key(key):
    exists = key in data_store
    return jsonify({"key": key, "exists": exists}), 200

if __name__ == '__main__':
    print(f"Файл данных: {DATA_FILE}")
    print(f"Загружено ключей: {len(data_store)}")
    print(f"Сервер запущен: http://127.0.0.1:5000")
    app.run(debug=True, port=5000)
    