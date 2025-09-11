from flask import Flask, request, jsonify
import psycopg2

app = Flask(__name__)

def get_db_connection():
    conn = psycopg2.connect(
        host="localhost",
        database="rpp_database",
        user="postgres",
        password="postgres"
    )
    return conn

conn = get_db_connection()
cur = conn.cursor()


@app.route('/load', methods=['POST'])
def load_currency():
    data = request.json
    currency_name = data.get('currency_name')
    rate = data.get('rate')

    if not currency_name or not rate:
        return jsonify({"error": "currency_name and rate are required"}), 400

    try:
        cur.execute("SELECT 1 FROM currencies WHERE currency_name = %s", (currency_name,))
        if cur.fetchone():
            return jsonify({"error": "Currency already exists"}), 400

        cur.execute(
            "INSERT INTO currencies (currency_name, rate) VALUES (%s, %s)",
            (currency_name, rate)
        )
        conn.commit()
        return jsonify({"message": "Currency added successfully"}), 200
    except:
        conn.rollback()
        return jsonify({"error": "Internal server error"}), 500


@app.route('/update_currency', methods=['POST'])
def update_currency():
    data = request.json
    currency_name = data.get('currency_name')
    new_rate = data.get('new_rate')

    if not currency_name or not new_rate:
        return jsonify({"error": "currency_name and new_rate are required"}), 400

    try:
        cur.execute("SELECT 1 FROM currencies WHERE currency_name = %s", (currency_name,))
        if not cur.fetchone():
            return jsonify({"error": "Currency not found"}), 404

        cur.execute(
            "UPDATE currencies SET rate = %s WHERE currency_name = %s",
            (new_rate, currency_name)
        )
        conn.commit()
        return jsonify({"message": "Currency updated successfully"}), 200
    except:
        conn.rollback()
        return jsonify({"error": "Internal server error"}), 500


@app.route('/delete', methods=['POST'])
def delete_currency():
    data = request.json
    currency_name = data.get('currency_name')

    if not currency_name:
        return jsonify({"error": "currency_name is required"}), 400

    try:
        cur.execute("SELECT 1 FROM currencies WHERE currency_name = %s", (currency_name,))
        if not cur.fetchone():
            return jsonify({"error": "Currency not found"}), 404

        cur.execute("DELETE FROM currencies WHERE currency_name = %s", (currency_name,))
        conn.commit()
        return jsonify({"message": "Currency deleted successfully"}), 200
    except:
        conn.rollback()
        return jsonify({"error": "Internal server error"}), 500


if __name__ == '__main__':
    app.run(port=5001)
    cur.close()
    conn.close()
