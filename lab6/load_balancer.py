from flask import Flask, jsonify, request, redirect, render_template
import requests
import threading
import time

app = Flask(__name__)

# Начальный пул серверов
server_pool = [
    {"url": "http://localhost:5001", "weight": 1, "active": True},
    {"url": "http://localhost:5002", "weight": 1, "active": True},
    {"url": "http://localhost:5003", "weight": 1, "active": True}
]

current_index = 0

def health_check(server):
    try:
        response = requests.get(f"{server['url']}/health", timeout=3)
        if response.status_code == 200:
            return True
    except requests.exceptions.RequestException:
        pass
    return False

def background_health_check():
    while True:
        active_count = 0
        for server in server_pool:
            is_healthy = health_check(server)
            server['active'] = is_healthy
            status = "Доступен" if is_healthy else "Недоступен"
            if is_healthy:
                active_count += 1
            print(f"{server['url']}: {status}")
        print(f"Активных серверов: {active_count}/{len(server_pool)}")
        time.sleep(5)

def get_next_server():
    global current_index
    start_index = current_index
    
    for i in range(len(server_pool)):
        server = server_pool[current_index]
        current_index = (current_index + 1) % len(server_pool)
        
        if server['active']:
            print(f"Выбран сервер: {server['url']}")
            return server
            
        if current_index == start_index:
            break
            
    return None

# Запускаем поток с проверкой здоровья
health_thread = threading.Thread(target=background_health_check, daemon=True)
health_thread.start()

@app.route('/health', methods=['GET'])
def lb_health():
    server_statuses = []
    for server in server_pool:
        server_statuses.append({
            "url": server['url'],
            "active": server['active']
        })
    return jsonify({"server_pool": server_statuses})

@app.route('/process', methods=['GET', 'POST'])
def lb_process():
    target_server = get_next_server()
    if not target_server:
        return jsonify({"error": "Нет доступных серверов"}), 503

    try:
        response = requests.request(
            method=request.method,
            url=f"{target_server['url']}/process",
            headers={key: value for (key, value) in request.headers if key != 'Host'},
            data=request.get_data(),
            params=request.args,
            cookies=request.cookies,
            allow_redirects=False
        )
        return (response.content, response.status_code, response.headers.items())
    except requests.exceptions.RequestException as e:
        return jsonify({"error": f"Ошибка подключения к серверу: {str(e)}"}), 502

# Web UI для управления пулом инстансов
@app.route('/', methods=['GET'])
def web_ui():
    active_count = sum(1 for server in server_pool if server['active'])
    return render_template(
        'admin.html', 
        servers=server_pool,
        active_count=active_count,
        total_count=len(server_pool),
        current_index=current_index
    )

# Добавление нового инстанса в пул
@app.route('/add_instance', methods=['POST'])
def add_instance():
    ip = request.form.get('ip', 'localhost').strip()
    port = request.form.get('port', '').strip()
    
    if not port:
        return "Ошибка: Порт обязателен для заполнения", 400
    
    new_server_url = f"http://{ip}:{port}"
    
    for server in server_pool:
        if server['url'] == new_server_url:
            return "Ошибка: Сервер уже существует в пуле", 400
    
    is_healthy = health_check({"url": new_server_url})
    
    new_server = {
        "url": new_server_url,
        "weight": 1,
        "active": is_healthy
    }
    server_pool.append(new_server)
    
    print(f"Добавлен новый сервер: {new_server_url} (Активен: {is_healthy})")
    return redirect('/')

# Удаление инстанса из пула
@app.route('/remove_instance', methods=['POST'])
def remove_instance():
    try:
        index = int(request.form.get('index'))
        if 0 <= index < len(server_pool):
            removed_server = server_pool.pop(index)
            
            global current_index
            if current_index >= len(server_pool) and len(server_pool) > 0:
                current_index = current_index % len(server_pool)
            
            print(f"Удален сервер: {removed_server['url']}")
            return redirect('/')
        else:
            return "Ошибка: Неверный индекс сервера", 400
    except ValueError:
        return "Ошибка: Неверный формат индекса", 400

# Универсальный обработчик для перехвата всех других запросов
@app.route('/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE', 'PATCH'])
def catch_all(path):
    target_server = get_next_server()
    if not target_server:
        return jsonify({"error": "Нет доступных серверов"}), 503
    
    try:
        response = requests.request(
            method=request.method,
            url=f"{target_server['url']}/{path}",
            headers={key: value for (key, value) in request.headers if key != 'Host'},
            data=request.get_data(),
            params=request.args,
            cookies=request.cookies,
            allow_redirects=False
        )
        return (response.content, response.status_code, response.headers.items())
    except requests.exceptions.RequestException as e:
        return jsonify({"error": f"Ошибка подключения к серверу: {str(e)}"}), 502

if __name__ == '__main__':
    print("Балансировщик нагрузки запущен на http://localhost:5000")
    print("Доступные эндпоинты:")
    print("   - http://localhost:5000/ (Web интерфейс)")
    print("   - http://localhost:5000/health (Проверка состояния)")
    print("   - http://localhost:5000/process (Тест балансировки)")
    print("\nНачальный пул серверов:")
    for i, server in enumerate(server_pool):
        print(f"   {i+1}. {server['url']}")
    app.run(port=5000, debug=True)
    