from flask import Flask
from lab3 import lab3

app = Flask(__name__)

app.register_blueprint(lab3)

@app.route("/")
@app.route("/index")
def labs():
    return '''<!DOCTYPE html>
<body >
    <main>
        <div>
        <a href="/number/">Лабораторная работа 3</a><br>
        </div>
    </main>
</body>
</html>
'''
