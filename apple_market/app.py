import os
from flask import Flask, render_template, request, redirect, url_for, flash, abort
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from flask_migrate import Migrate

# ================== Настройки ==================
app = Flask(__name__)
app.config['SECRET_KEY'] = 'supersecretkey'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///apple_market.db'
app.config['UPLOAD_FOLDER'] = 'static/uploads'

db = SQLAlchemy(app)
migrate = Migrate(app, db)
login_manager = LoginManager(app)
login_manager.login_view = "login"

# ================== Разрешённые модели ==================
ALLOWED_MODELS = [
    "iPhone 8", "iPhone 8 Plus",
    "iPhone X", "iPhone XR", "iPhone XS", "iPhone XS Max",
    "iPhone 11", "iPhone 11 Pro", "iPhone 11 Pro Max",
    "iPhone 12", "iPhone 12 Mini", "iPhone 12 Pro", "iPhone 12 Pro Max",
    "iPhone 13", "iPhone 13 Mini", "iPhone 13 Pro", "iPhone 13 Pro Max",
    "iPhone 14", "iPhone 14 Plus", "iPhone 14 Pro", "iPhone 14 Pro Max",
    "iPhone 15", "iPhone 15 Plus", "iPhone 15 Pro", "iPhone 15 Pro Max",
    "iPhone 16", "iPhone 16 Plus", "iPhone 16 Pro", "iPhone 16 Pro Max",
    "iPhone 17", "iPhone 17 Plus", "iPhone 17 Pro", "iPhone 17 Pro Max"
]

# ================== Модели БД ==================
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    model = db.Column(db.String(50))
    price = db.Column(db.Float)
    condition = db.Column(db.String(50))
    battery = db.Column(db.Integer)
    memory = db.Column(db.String(50))
    color = db.Column(db.String(50))
    package = db.Column(db.String(50))
    description = db.Column(db.Text)
    images = db.relationship('ProductImage', backref='product', lazy=True)

class ProductImage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(100))
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'))

class ChatMessage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.Text, nullable=False)
    sender = db.Column(db.String(10), nullable=False)  # 'admin' или 'user'
    user_id = db.Column(db.Integer, nullable=False)

# ================== Flask-Login ==================
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# ================== Декоратор для админа ==================
def admin_required(f):
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_admin:
            abort(403)
        return f(*args, **kwargs)
    return decorated_function

# ================== Главная ==================
@app.route('/', methods=['GET'])
def index():
    selected_model = request.args.get('model')

    if selected_model and selected_model in ALLOWED_MODELS:
        products = Product.query.filter_by(model=selected_model).all()
    else:
        products = Product.query.all()

    return render_template(
        'index.html',
        products=products,
        allowed_models=ALLOWED_MODELS,
        selected_model=selected_model
    )

# ================== Регистрация ==================
@app.route('/register', methods=['GET','POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if User.query.filter_by(username=username).first():
            flash("Пользователь с таким именем уже существует", "danger")
            return redirect('/register')

        user = User(
            username=username,
            password=generate_password_hash(password),
            is_admin=False
        )
        db.session.add(user)
        db.session.commit()
        flash("Регистрация прошла успешно", "success")
        return redirect('/login')
    return render_template('register.html')

# ================== Вход ==================
@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        user = User.query.filter_by(username=request.form['username']).first()
        if user and check_password_hash(user.password, request.form['password']):
            login_user(user)
            return redirect('/')
        flash("Неверный логин или пароль", "danger")
    return render_template('login.html')

# ================== Выход ==================
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect('/')

# ================== Добавление телефона ==================
@app.route('/admin/add', methods=['GET', 'POST'])
@login_required
@admin_required
def add_product():
    if request.method == 'POST':
        # создаём продукт напрямую из данных формы
        product = Product(
            model=request.form.get('model'),        # <--- сюда приходит выбранная модель
            price=request.form.get('price'),
            condition=request.form.get('condition'),
            battery=request.form.get('battery'),
            memory=request.form.get('memory'),
            color=request.form.get('color'),
            package=request.form.get('package'),
            description=request.form.get('description')
        )

        db.session.add(product)
        db.session.commit()  # нужно сначала создать продукт для получения product.id

        # Загружаем несколько изображений
        files = request.files.getlist('images')
        for file in files:
            if file.filename:
                filename = secure_filename(file.filename)
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                img = ProductImage(filename=filename, product_id=product.id)
                db.session.add(img)

        db.session.commit()
        return redirect('/')

    return render_template('add_product.html', allowed_models=ALLOWED_MODELS)

# ================== Чат ==================

@app.route('/admin/delete/<int:product_id>', methods=['POST'])
@login_required
@admin_required
def delete_product(product_id):
    product = Product.query.get_or_404(product_id)

    # удаляем картинки с диска
    for img in product.images:
        path = os.path.join(app.config['UPLOAD_FOLDER'], img.filename)
        if os.path.exists(path):
            os.remove(path)

    # удаляем из базы
    db.session.delete(product)
    db.session.commit()

    flash("Телефон удалён", "success")
    return redirect(url_for('index'))


@app.route('/chat/<int:user_id>', methods=['GET','POST'])
@login_required
def chat(user_id):
    if not current_user.is_admin and current_user.id != user_id:
        abort(403)

    if request.method == 'POST':
        msg = ChatMessage(
            text=request.form['text'],
            sender='admin' if current_user.is_admin else 'user',
            user_id=user_id
        )
        db.session.add(msg)
        db.session.commit()

    messages = ChatMessage.query.filter_by(user_id=user_id).all()
    return render_template('chat.html', messages=messages, user_id=user_id)

# ================== Запуск ==================
if __name__ == '__main__':
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    # 🔹 контекст приложения для работы с БД
    with app.app_context():
        db.create_all()
        # Создание админа по умолчанию
        if not User.query.filter_by(username='Admin_Biznes').first():
            admin = User(
                username='Admin_Biznes',
                password=generate_password_hash('LadaXray2019'),
                is_admin=True
            )
            db.session.add(admin)
            db.session.commit()
            print("✅ Админ создан: Admin_Biznes / LadaXray2019")

    app.run(debug=True)

