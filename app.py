from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
import os
from dotenv import load_dotenv

app = Flask(__name__)

# Load environment variables from .env file
load_dotenv()

# Configure the database connection URL.
app.config['SQLALCHEMY_DATABASE_URI'] = (
    f"mysql://{os.getenv('MYSQL_DATABASE_USER')}:{os.getenv('MYSQL_DATABASE_PASSWORD')}@{os.getenv('MYSQL_DATABASE_HOST')}/{os.getenv('MYSQL_DATABASE_DB')}"
)

# Initialize the SQLAlchemy object.
db = SQLAlchemy(app)

# Define the data model for Menu Items.
# In the case of the MenuItem class, SQLAlchemy will automatically create a table named menu_item in your database.
class MenuItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.String(500))
    price = db.Column(db.Float, nullable=False)
    availability = db.Column(db.Boolean, default=True)
    sold_count = db.Column(db.Integer, default=0)


# Create the database if it doesn't exist.
with app.app_context():
    db.create_all()


@app.route('/', methods=['GET'])
def hello_world():
    return 'Hello, World!'


# Route to add a new menu item.
@app.route('/menu/add', methods=['POST'])
def add_menu_item():
    try:
        # Extract data from the request.
        data = request.get_json()
        name = data['name']
        description = data['description']
        price = data['price']
        availability = data['availability']
        sold_count = data['sold_count']

        # Create a new Menu Item object.
        new_item = MenuItem(name=name, description=description,
                            price=price, availability=availability, sold_count=sold_count)

        # Add the new item to the database.
        db.session.add(new_item)
        db.session.commit()

        return jsonify({"message": "Menu item added successfully"}), 201

    except Exception as e:
        return jsonify({"error": str(e)}), 400


@app.route('/menu', methods=['GET'])
def get_menu_items():
    try:
        # Retrieve and return a list of menu items from the database.
        menu_items = MenuItem.query.all()

        # Convert menu items to a list of dictionaries.
        menu_items_list = []
        for item in menu_items:
            menu_item = {
                'id': item.id,
                'name': item.name,
                'description': item.description,
                'price': item.price,
                'availability': item.availability,
                'sold_count': item.sold_count
            }

            menu_items_list.append(menu_item)

        return jsonify(menu_items_list), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/menu/update/<int:item_id>', methods=['PUT'])
def update_menu_item(item_id):
    try:
        # Extract and validate request data.
        data = request.get_json()
        name = data['name']
        description = data['description']
        price = data['price']
        availability = data['availability']
        sold_count = data['sold_count']

        # Find the menu item by ID.
        menu_item = MenuItem.query.get(item_id)

        if not menu_item:
            return jsonify({'error': 'Menu item not found'}), 404

        # Update the menu item attributes.
        menu_item.name = name
        menu_item.description = description
        menu_item.price = price
        menu_item.availability = availability
        menu_item.sold_count = sold_count

        # Commit the changes to the database.
        db.session.commit()

        return jsonify({'message': 'Menu item updated successfully'}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 400


@app.route('/menu/delete/<int:item_id>', methods=['DELETE'])
def delete_menu_item(item_id):
    try:
        # Find the menu item by ID.
        menu_item = MenuItem.query.get(item_id)

        if not menu_item:
            return jsonify({'error': 'Menu item not found'}), 404

        # Delete the menu item from the database.
        db.session.delete(menu_item)
        db.session.commit()

        return jsonify({'message': 'Menu item deleted successfully'}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 400


# Define the data model for orders.
class FoodOrder(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    customer_name = db.Column(db.String(255), nullable=False)
    # Store item IDs as a comma-separated string.
    dish_ids = db.Column(db.String(255), nullable=False)
    total_price = db.Column(db.Integer, nullable=False)
    order_status = db.Column(db.String(50), nullable=False, default='received')
    # Add any other relevant order details here.


# Route to create a new order
@app.route('/orders', methods=['POST'])
def create_order():
    # Get data from the request JSON
    data = request.get_json()

    # Convert the list of dish IDs to a string with comma separation
    dish_ids_str = ','.join(data['dish_ids'])

    # Extract customer name and item IDs from the JSON
    customer_name = data['customer_name']
    dish_ids = dish_ids_str,  # Store as a string
    total_price = data['total_price'],
    order_status = 'received'
    # Check if customer name and item IDs are provided
    if not customer_name or not dish_ids:
        return jsonify({'error': 'Customer name and item IDs are required'}), 400

    # Create a new order with the received data
    new_order = FoodOrder(customer_name=customer_name,
                          dish_ids=dish_ids, total_price=total_price, order_status=order_status)

    try:
        # Add the order to the database
        db.session.add(new_order)
        db.session.commit()
        return jsonify({'message': 'Order created successfully'}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


# Route to update order status by order ID
@app.route('/orders/<int:order_id>', methods=['PUT'])
def update_order_status(order_id):
    # Get the new order status from the request JSON
    data = request.get_json()
    new_status = data.get('order_status')

    # Find the order by its ID
    order = FoodOrder.query.get(order_id)

    if not order:
        return jsonify({'error': 'Order not found'}), 404

    # Update the order status
    order.order_status = new_status

    try:
        db.session.commit()
        return jsonify({'message': 'Order status updated successfully'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to update order status'}), 500


# Route to retrieve orders by customer name
@app.route('/orders/customer/<string:customer_name>', methods=['GET'])
def get_orders_by_customer(customer_name):
    # Query orders by customer name
    orders = FoodOrder.query.filter_by(customer_name=customer_name).all()

    if not orders:
        return jsonify({'message': 'No orders found for this customer'}), 200

    # Serialize the orders to JSON
    orders_data = [{'id': order.id, 'customer_name': order.customer_name, 'order_status': order.order_status}
                   for order in orders]

    return jsonify({'orders': orders_data}), 200


# Route to retrieve orders by order status
@app.route('/orders/status/<string:order_status>', methods=['GET'])
def get_orders_by_status(order_status):
    if order_status is not None:
        # Query orders by order status
        orders = FoodOrder.query.filter_by(order_status=order_status).all()
    else:
        # If order_status is not specified, retrieve all orders
        orders = FoodOrder.query.all()

    if not orders:
        return jsonify({'message': 'No orders found with this status'}), 200

    # Serialize the orders to JSON
    orders_data = [{'id': order.id, 'customer_name': order.customer_name, 'order_status': order.order_status}
                   for order in orders]

    return jsonify({'orders': orders_data}), 200


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
