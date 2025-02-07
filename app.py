from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
db = SQLAlchemy(app)

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Float, nullable=False)

with app.app_context():
    db.create_all()

# GET: Отримання всіх продуктів
@app.route('/products', methods=['GET'])
def get_products():
    products = Product.query.all()
    return jsonify([{'id': p.id, 'name': p.name, 'price': p.price} for p in products])

# POST: Додавання нового продукту
@app.route('/products', methods=['POST'])
def add_product():
    data = request.json
    new_product = Product(name=data['name'], price=data['price'])
    db.session.add(new_product)
    db.session.commit()
    return jsonify({'message': 'Product added', 'product': {'id': new_product.id, 'name': new_product.name, 'price': new_product.price}}), 201

# PATCH: Оновлення продукту
@app.route('/products/<int:product_id>', methods=['PATCH'])
def update_product(product_id):
    product = Product.query.get_or_404(product_id)
    data = request.json
    if 'name' in data:
        product.name = data['name']
    if 'price' in data:
        product.price = data['price']
    db.session.commit()
    return jsonify({'message': 'Product updated', 'product': {'id': product.id, 'name': product.name, 'price': product.price}})

# DELETE: Видалення продукту
@app.route('/products/<int:product_id>', methods=['DELETE'])
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
