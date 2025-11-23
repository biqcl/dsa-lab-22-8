from flask import Flask, jsonify
import sys

# Создаем экземпляр Flask приложения
app = Flask(__name__)

# Получаем порт из аргументов командной строки
if len(sys.argv) > 1:
    port = int(sys.argv[1])
else:
    port = 5000  # Порт по умолчанию

# Генерируем уникальный ID для этого экземпляра на основе порта
instance_id = f"instance-{port}"

# Эндпоинт для проверки состояния
@app.route('/health', methods=['GET'])
def health():
    return jsonify({
        "status": "healthy",
        "instance_id": instance_id
    })

# Эндпоинт для обработки запросов
@app.route('/process', methods=['GET', 'POST'])
def process():
    return jsonify({
        "message": "Request processed successfully",
        "instance_id": instance_id
    })

if __name__ == '__main__':
    # Запускаем приложение на указанном порту
    app.run(port=port, debug=True)
    