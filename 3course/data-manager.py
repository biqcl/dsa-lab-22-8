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


@app.route('/convert', methods=['GET'])
def convert_currency():
    currency_name = request.args.get('currency')
    amount = request.args.get('amount')

    if not currency_name or not amount:
        return jsonify({"error": "currency and amount parameters are required"}), 400

    try:
        amount = float(amount)
    except:
        return jsonify({"error": "amount must be a number"}), 400

    try:
        cur.execute("SELECT rate FROM currencies WHERE currency_name = %s", (currency_name.upper(),))
        result = cur.fetchone()

        if not result:
            return jsonify({"error": "Currency not found"}), 404

        rate = float(result[0])
        converted_amount = amount * rate

        return jsonify({
            "original_amount": amount,
            "currency": currency_name.upper(),
            "converted_amount": round(converted_amount, 2),
            "target_currency": "RUB"
        }), 200
    except:
        return jsonify({"error": "Internal server error"}), 500


@app.route('/currencies', methods=['GET'])
def get_all_currencies():
    try:
        cur.execute("SELECT currency_name, rate FROM currencies ORDER BY currency_name")
        currencies = cur.fetchall()
        result = [{"currency": curr[0], "rate": float(curr[1])} for curr in currencies]
        return jsonify({"currencies": result}), 200
    except:
        return jsonify({"error": "Internal server error"}), 500


if __name__ == '__main__':
    app.run(port=5002)
    cur.close()
    conn.close()
