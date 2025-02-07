import json
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from functools import wraps

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['JWT_SECRET_KEY'] = 'supersecret'  # Змінити на більш безпечний ключ

db = SQLAlchemy(app)
jwt = JWTManager(app)

# Модель користувача
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(80), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # 'Admin' або 'User'

# Модель продукту
class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Float, nullable=False)

with app.app_context():
    db.create_all()

# Декоратор для перевірки ролі

def role_required(role):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            identity = json.loads(get_jwt_identity())  # ✅ Розпарсити JSON-рядок у словник
            user_role = identity.get("role")
            if user_role != role:
                return jsonify({"message": "Access denied"}), 403
            return func(*args, **kwargs)
        return wrapper
    return decorator

# Реєстрація нового користувача
@app.route('/register', methods=['POST'])
def register():
    data = request.json
    if User.query.filter_by(username=data['username']).first():
        return jsonify({"message": "User already exists"}), 400

    new_user = User(username=data['username'], password=data['password'], role=data['role'])
    db.session.add(new_user)
    db.session.commit()
    return jsonify({"message": "User registered successfully"}), 201

# Логін і отримання токена
@app.route('/login', methods=['POST'])
def login():
    data = request.json
    user = User.query.filter_by(username=data['username'], password=data['password']).first()
    if not user:
        return jsonify({"message": "Invalid credentials"}), 401

    access_token = create_access_token(identity=json.dumps({"username": user.username, "role": user.role}))  # ✅ Фіксований токен
    return jsonify(access_token=access_token)

# GET: Отримання всіх продуктів (доступно всім користувачам)
@app.route('/products', methods=['GET'])
@jwt_required()
def get_products():
    products = Product.query.all()
    return jsonify([{'id': p.id, 'name': p.name, 'price': p.price} for p in products])

# POST: Додавання нового продукту (лише Admin)
@app.route('/products', methods=['POST'])
@jwt_required()
@role_required('Admin')
def add_product():
    data = request.json
    new_product = Product(name=data['name'], price=data['price'])
    db.session.add(new_product)
    db.session.commit()
    return jsonify({'message': 'Product added', 'product': {'id': new_product.id, 'name': new_product.name, 'price': new_product.price}}), 201

# PATCH: Оновлення продукту (лише Admin)
@app.route('/products/<int:product_id>', methods=['PATCH'])
@jwt_required()
@role_required('Admin')
def update_product(product_id):
    product = Product.query.get_or_404(product_id)
    data = request.json
    if 'name' in data:
        product.name = data['name']
    if 'price' in data:
        product.price = data['price']
    db.session.commit()
    return jsonify({'message': 'Product updated', 'product': {'id': product.id, 'name': product.name, 'price': product.price}})

# DELETE: Видалення продукту (лише Admin)
@app.route('/products/<int:product_id>', methods=['DELETE'])
@jwt_required()
@role_required('Admin')
def delete_product(product_id):
    product = Product.query.get_or_404(product_id)
    db.session.delete(product)
    db.session.commit()
    return jsonify({'message': 'Product deleted'})

@app.route('/')
def home():
    return jsonify({"message": "Welcome to the API"}), 200

if __name__ == '__main__':
    app.run(debug=True)