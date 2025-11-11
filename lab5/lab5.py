from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash

# Инициализация приложения Flask
app = Flask(__name__)
app.config['SECRET_KEY'] = 'lab5-secret-key-2024'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Инициализация расширений
db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'


# Модель пользователя на основе UserMixin
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    name = db.Column(db.String(100), nullable=False)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# Создание таблиц в базе данных
with app.app_context():
    db.create_all()


# Маршрут для корневой страницы
@app.route('/')
def index():
    if current_user.is_authenticated:
        return render_template('index.html', user=current_user)
    else:
        return redirect(url_for('login'))


# Маршрут для страницы входа (GET и POST)
@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    
    if request.method == 'POST':
        # Получение данных из формы
        email = request.form.get('email')
        password = request.form.get('password')
        
        # Проверка обязательных полей
        if not email or not password:
            error = 'Все поля обязательны для заполнения'
            return render_template('login.html', error=error)
        
        # Поиск пользователя по email
        user = User.query.filter_by(email=email).first()
        
        # Проверка существования пользователя
        if not user:
            error = 'Пользователь с таким email не найден'
            return render_template('login.html', error=error)
        
        # Проверка пароля
        if not check_password_hash(user.password, password):
            error = 'Неверный пароль'
            return render_template('login.html', error=error)
        
        # Успешная авторизация
        login_user(user)
        return redirect(url_for('index'))
    
    # GET запрос - отображение формы входа
    return render_template('login.html', error=error)


# Маршрут для страницы регистрации (GET и POST)
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    error = None
    success = None
    
    if request.method == 'POST':
        # Получение данных из формы
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        
        # Проверка обязательных полей
        if not name or not email or not password:
            error = 'Все поля обязательны для заполнения'
            return render_template('signup.html', error=error)
        
        # Проверка существования пользователя с таким email
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            error = 'Пользователь с таким email уже существует'
            return render_template('signup.html', error=error)
        
        # Создание нового пользователя с хешированным паролем
        new_user = User(
            name=name,
            email=email,
            password=generate_password_hash(password, method='pbkdf2:sha256')
        )
        
        # Сохранение пользователя в базе данных
        db.session.add(new_user)
        db.session.commit()
        
        success = 'Регистрация успешна! Теперь вы можете войти.'
        return render_template('signup.html', success=success)
    
    # GET запрос - отображение формы регистрации
    return render_template('signup.html', error=error, success=success)


# Маршрут для выхода из системы
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))


# Запуск приложения
if __name__ == '__main__':
    app.run(debug=True)
