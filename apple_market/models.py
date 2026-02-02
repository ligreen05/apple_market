from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin

db = SQLAlchemy()

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True)
    password = db.Column(db.String(200))
    is_admin = db.Column(db.Boolean, default=False)

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    model = db.Column(db.String(50))
    price = db.Column(db.Float)
    condition = db.Column(db.String(20))
    battery = db.Column(db.Integer)
    memory = db.Column(db.Integer)
    color = db.Column(db.String(30))
    package = db.Column(db.String(30))
    description = db.Column(db.Text)
    images = db.relationship('ProductImage', backref='product')

class ProductImage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(200))
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'))
