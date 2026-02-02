from app import app
from models import db, User
from werkzeug.security import generate_password_hash

with app.app_context():
    # Удаляем старого админа, если есть
    User.query.filter_by(username='Admin_Biznes').delete()
    db.session.commit()

    # Создаём нового админа
    admin = User(username='Admin_Biznes',
                 password=generate_password_hash('LadaXray2019'),
                 is_admin=True)
    db.session.add(admin)
    db.session.commit()

    print("✅ Новый админ создан")
