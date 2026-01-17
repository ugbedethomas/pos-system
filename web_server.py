# web_server.py
from flask import Flask, render_template, jsonify, request, redirect, url_for, session
from app.database import SessionLocal
from app import crud, schemas, models
from app.models import Sale, SaleItem, Product, Customer, User, StockMovement
from datetime import datetime, timedelta
import secrets
from app.auth import authenticate_user, get_password_hash
import json
from markupsafe import Markup
import sqlite3
import os

app = Flask(__name__, template_folder="templates")
app.secret_key = secrets.token_hex(32)


def escapejs(value):
    """Custom escapejs filter for Jinja2"""
    if value is None:
        return ''
    value = str(value)
    # Escape characters that could break JavaScript strings
    replacements = {
        '\\': '\\\\',
        "'": "\\'",
        '"': '\\"',
        '\n': '\\n',
        '\r': '\\r',
        '\t': '\\t',
        '<': '\\u003C',
        '>': '\\u003E',
        '&': '\\u0026'
    }
    for find, replace in replacements.items():
        value = value.replace(find, replace)
    return Markup(value)


# Register the custom filter with Jinja2
app.jinja_env.filters['escapejs'] = escapejs


# Auto-initialize database on startup
def initialize_database_on_startup():
    try:
        from app.database import Base, engine, SessionLocal
        from app.auth import get_password_hash
        from app.models import User

        print("🔍 Checking if database needs initialization...")

        # Try to connect to database
        db = SessionLocal()
        try:
            # Test if users table exists
            db.execute("SELECT 1 FROM users LIMIT 1")
            print("✅ Database already initialized")
            db.close()
            return
        except Exception:
            print("🔄 Database not found. Creating tables...")
            db.close()

        # Create all tables
        Base.metadata.create_all(bind=engine)

        # Create default users
        db = SessionLocal()

        users_to_create = [
            ("admin", "admin123", "admin", "System Administrator"),
            ("cashier", "cashier123", "cashier", "Cashier User"),
            ("inventory", "inventory123", "inventory", "Inventory Manager")
        ]

        for username, password, role, full_name in users_to_create:
            existing = db.query(User).filter(User.username == username).first()
            if not existing:
                user = User(
                    username=username,
                    email=f"{username}@pos.com",
                    hashed_password=get_password_hash(password),
                    role=role,
                    full_name=full_name,
                    is_active=True
                )
                db.add(user)
                print(f"  ✅ Created user: {username}")

        db.commit()
        db.close()
        print("🎉 Database initialized successfully on startup!")

    except Exception as e:
        print(f"⚠️ Startup initialization failed: {e}")
        import traceback
        print(traceback.format_exc())


# Call this function when the app starts
# initialize_database_on_startup()

@app.route('/force-init-db')
def force_init_db():
    """Initialize database WITHOUT login requirement"""
    try:
        from app.database import Base, engine
        from app.auth import get_password_hash

        print("🚀 FORCE Creating database tables...")

        # Create all tables
        Base.metadata.create_all(bind=engine)

        # Create users
        from app.models import User
        from app.database import SessionLocal

        db = SessionLocal()

        # Create admin if not exists
        admin = db.query(User).filter(User.username == "admin").first()
        if not admin:
            admin_user = User(
                username="admin",
                email="admin@pos.com",
                hashed_password=get_password_hash("admin123"),
                role="admin",
                full_name="Administrator",
                is_active=True
            )
            db.add(admin_user)
            print("✅ Admin user created")

        db.commit()
        db.close()

        return '''
        <h1>✅ SUCCESS! Database Initialized</h1>
        <p>Database tables created successfully!</p>
        <p>Admin user created: admin/admin123</p>
        <p><a href="/login">Go to Login</a></p>
        '''
    except Exception as e:
        return f"<h1>Error:</h1><pre>{str(e)}</pre>"


# Simple currency formatting function
def format_naira(amount):
    """Format amount as Nigerian Naira"""
    if amount is None:
        return "₦0.00"
    try:
        amount = float(amount)
        return f"₦{amount:,.2f}"
    except (ValueError, TypeError):
        return "₦0.00"


def format_number(num):
    """Format number with commas"""
    if num is None:
        return "0"
    try:
        num = float(num)
        return f"{num:,.0f}"
    except (ValueError, TypeError):
        return "0"


# Default company settings
COMPANY_SETTINGS = {
    "name": "Your Business POS",
    "address": "123 Business Street, Lagos, Nigeria",
    "phone": "+234 812 345 6789",
    "email": "info@yourbusiness.com",
    "tax_id": "VAT-123456789",
    "currency": "₦",
    "currency_code": "NGN",
    "tax_rate": 0.075,
    "receipt_footer": "Thank you for your patronage!\nGoods sold are not returnable",
    "bank_details": {
        "name": "Your Business Name",
        "bank": "Access Bank",
        "account_number": "1234567890"
    }
}

# Nigerian payment methods
PAYMENT_METHODS = [
    {"id": "cash", "name": "Cash", "icon": "fa-money-bill-wave"},
    {"id": "transfer", "name": "Bank Transfer", "icon": "fa-university"},
    {"id": "pos", "name": "POS Card", "icon": "fa-credit-card"},
    {"id": "mobile", "name": "Mobile Money", "icon": "fa-mobile-alt"}
]


# Check user permissions
def check_permission(required_role=None):
    user_role = session.get('role')

    if required_role is None:
        return True

    # Admin has all permissions
    if user_role == 'admin':
        return True

    # Check specific role
    if user_role == required_role:
        return True

    # Role hierarchy
    role_hierarchy = {
        'admin': ['admin', 'cashier', 'inventory'],
        'inventory': ['inventory'],
        'cashier': ['cashier']
    }

    # Check if user's role has permission
    allowed_roles = role_hierarchy.get(required_role, [])
    return user_role in allowed_roles


# Helper function to get top selling products
def get_top_selling_products(db, limit=5):
    """Get top selling products by quantity sold"""
    try:
        from sqlalchemy import func
        result = db.query(
            models.Product.id,
            models.Product.name,
            models.Product.sku,
            models.Product.category,
            func.sum(models.SaleItem.quantity).label('total_sold'),
            func.sum(models.SaleItem.subtotal).label('total_revenue')
        ).join(
            models.SaleItem, models.SaleItem.product_id == models.Product.id
        ).join(
            models.Sale, models.Sale.id == models.SaleItem.sale_id
        ).group_by(
            models.Product.id,
            models.Product.name,
            models.Product.sku,
            models.Product.category
        ).order_by(
            func.sum(models.SaleItem.quantity).desc()
        ).limit(limit).all()

        # Format the result
        top_products = []
        for row in result:
            top_products.append({
                'id': row.id,
                'name': row.name,
                'sku': row.sku,
                'category': row.category,
                'total_sold': row.total_sold or 0,
                'total_revenue': float(row.total_revenue or 0)
            })

        return top_products
    except Exception as e:
        print(f"Error getting top products: {e}")
        return []


# Check if user is logged in
@app.before_request
def require_login():
    # Routes that don't require login
    public_routes = [
        'login',
        'setup_admin',
        'static',
        'health',
        'force_init_db',
        'init_now'  # ← ADD THIS LINE
    ]

    # Also allow any route that starts with /force- or /init-
    if request.endpoint in public_routes:
        return

    if request.path.startswith('/force-') or request.path.startswith('/init-'):
        return

    # Check for login
    if 'user_id' not in session:
        return redirect('/login')


# Login page
@app.route('/login', methods=['GET', 'POST'])
def login():
    # ADD THE PING ENDPOINT HERE
    @app.route('/ping')
    def ping():
        """Ultra-lightweight ping endpoint to keep app awake"""
        return 'pong', 200

    # Try to auto-initialize database if needed
    try:
        db = SessionLocal()
        # Test if users table exists by trying a simple query
        db.execute("SELECT 1 FROM users LIMIT 1")
        db.close()
    except Exception as e:
        # Database not initialized - auto-initialize it
        print(f"⚠️ Database not initialized. Auto-initializing... Error: {e}")
        try:
            from app.database import Base, engine, SessionLocal
            from app.auth import get_password_hash
            import traceback

            print("🔄 Creating database tables...")
            Base.metadata.create_all(bind=engine)

            # Create default users
            db = SessionLocal()
            from app.models import User

            users_to_create = [
                ("admin", "admin123", "admin", "System Administrator"),
                ("cashier", "cashier123", "cashier", "Cashier User"),
                ("inventory", "inventory123", "inventory", "Inventory Manager")
            ]

            for username, password, role, full_name in users_to_create:
                existing = db.query(User).filter(User.username == username).first()
                if not existing:
                    user = User(
                        username=username,
                        email=f"{username}@pos.com",
                        hashed_password=get_password_hash(password),
                        role=role,
                        full_name=full_name,
                        is_active=True
                    )
                    db.add(user)

            db.commit()
            db.close()
            print("✅ Database auto-initialized successfully!")

        except Exception as init_error:
            print(f"❌ Auto-initialization failed: {init_error}")
            print(traceback.format_exc())
            # Continue to login page - user will see error if they try to login

    # Now handle the login request normally
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        db = SessionLocal()
        user = authenticate_user(db, username, password)

        if user:
            session['user_id'] = user.id
            session['username'] = user.username
            session['role'] = user.role
            session['full_name'] = user.full_name

            user.last_login = datetime.now()
            db.commit()
            db.close()

            return redirect('/')
        else:
            db.close()
            return render_template('login.html', error='Invalid username or password')

    return render_template('login.html')


@app.route('/create-inventory-test-user')
def create_inventory_test_user():
    db = SessionLocal()
    try:
        # Check if user already exists
        existing = db.query(models.User).filter(models.User.username == 'inventory').first()

        if existing:
            return f"User already exists: {existing.username} (Role: {existing.role})"

        # Create new inventory manager
        new_user = models.User(
            username='inventory',
            full_name='Inventory Manager',
            hashed_password=get_password_hash('inventory123'),
            role='inventory',
            email='inventory@pos.com',
            created_at=datetime.now()
        )

        db.add(new_user)
        db.commit()
        return """
        <h1>✅ Inventory User Created!</h1>
        <p><strong>Username:</strong> inventory</p>
        <p><strong>Password:</strong> inventory123</p>
        <p><strong>Role:</strong> inventory</p>
        <p><a href="/login">Go to Login</a></p>
        """
    except Exception as e:
        return f"<h1>Error:</h1><p>{str(e)}</p>"
    finally:
        db.close()


# Logout
@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')


# Create first admin user (run once)
@app.route('/setup-admin')
def setup_admin():
    db = SessionLocal()
    try:
        # Check if admin exists
        admin = db.query(models.User).filter(models.User.role == 'admin').first()

        if not admin:
            admin_user = models.User(
                username='admin',
                full_name='System Administrator',
                email='admin@pos.com',
                hashed_password=get_password_hash('admin123'),
                role='admin'
            )
            db.add(admin_user)

            # Add sample cashier
            cashier_user = models.User(
                username='cashier',
                full_name='John Cashier',
                email='cashier@pos.com',
                hashed_password=get_password_hash('cashier123'),
                role='cashier'
            )
            db.add(cashier_user)

            # Add sample inventory officer
            inventory_user = models.User(
                username='inventory',
                full_name='Jane Inventory',
                email='inventory@pos.com',
                hashed_password=get_password_hash('inventory123'),
                role='inventory'
            )
            db.add(inventory_user)

            db.commit()
            return '''
            <h2>Users Created Successfully!</h2>
            <p><strong>Admin:</strong> username: admin, password: admin123</p>
            <p><strong>Cashier:</strong> username: cashier, password: cashier123</p>
            <p><strong>Inventory Officer:</strong> username: inventory, password: inventory123</p>
            <p><a href="/login">Go to Login Page</a></p>
            '''
        else:
            return '''
            <h2>Users Already Exist</h2>
            <p>Admin user already exists in the system.</p>
            <p><a href="/login">Go to Login Page</a></p>
            '''
    finally:
        db.close()


# Dashboard
@app.route('/')
def dashboard():
    # Allow ALL logged-in users: admin, cashier, inventory
    if 'user_id' not in session:
        return redirect('/login')

    db = SessionLocal()
    try:
        products = crud.get_products(db)
        customers = crud.get_customers(db)
        sales = crud.get_sales(db)

        # Calculate stats
        today = datetime.now().date()
        today_sales = sum(sale.total_amount for sale in sales if sale.created_at.date() == today)
        inventory_value = sum(p.stock_quantity * p.price for p in products)
        low_stock = crud.get_low_stock_products(db)
        recent_sales = sorted(sales, key=lambda x: x.created_at, reverse=True)[:5]

        # Get top selling products
        top_products = get_top_selling_products(db)

        return render_template('dashboard.html',
                               total_products=len(products),
                               total_customers=len(customers),
                               today_sales=today_sales,
                               inventory_value=inventory_value,
                               low_stock_products=low_stock,
                               low_stock_count=len(low_stock),
                               recent_sales=recent_sales,
                               top_products=top_products,
                               company=COMPANY_SETTINGS,
                               payment_methods=PAYMENT_METHODS,
                               format_naira=format_naira,
                               format_number=format_number
                               )
    finally:
        db.close()


# POS Page - Only cashiers and admin
@app.route('/pos')
def pos():
    if not check_permission('cashier'):
        return "Access Denied: Only cashiers and admin can access POS", 403

    db = SessionLocal()
    try:
        products = crud.get_products(db)
        categories = list(set(p.category for p in products if p.category))

        return render_template('pos.html',
                               products=products,
                               categories=categories,
                               company=COMPANY_SETTINGS,
                               payment_methods=PAYMENT_METHODS,
                               format_naira=format_naira,
                               format_number=format_number
                               )
    finally:
        db.close()


# Products Page - Only inventory and admin
@app.route('/products')
def products():
    if not check_permission('inventory'):
        return "Access Denied: Only inventory officers and admin can manage products", 403

    db = SessionLocal()
    try:
        products = crud.get_products(db)
        return render_template('products.html',
                               products=products,
                               format_naira=format_naira,
                               format_number=format_number
                               )
    finally:
        db.close()


# Inventory Page - Only inventory and admin
@app.route('/inventory')
def inventory():
    if not check_permission('inventory'):
        return "Access Denied: Only inventory officers and admin can view inventory", 403

    db = SessionLocal()
    try:
        products = crud.get_products(db)
        report = crud.get_inventory_report(db)
        low_stock = crud.get_low_stock_products(db)

        return render_template('inventory.html',
                               inventory_report=report,
                               low_stock_products=low_stock,
                               products=products,
                               format_naira=format_naira,
                               format_number=format_number
                               )
    finally:
        db.close()


# Sales Page - Only cashiers and admin
@app.route('/sales')
def sales_page():
    if not check_permission('cashier'):
        return "Access Denied: Only cashiers and admin can view sales", 403

    db = SessionLocal()
    try:
        sales_list = crud.get_sales(db)

        # Calculate statistics
        today = datetime.now().date()
        today_sales = sum(
            sale.total_amount for sale in sales_list
            if sale.created_at.date() == today
        )
        total_sales = sum(sale.total_amount for sale in sales_list)
        total_transactions = len(sales_list)
        average_sale = total_sales / total_transactions if total_transactions > 0 else 0

        return render_template('sales.html',
                               sales=sales_list,
                               today_sales=today_sales,
                               total_sales=total_sales,
                               total_transactions=total_transactions,
                               average_sale=average_sale,
                               company=COMPANY_SETTINGS,
                               format_naira=format_naira,
                               format_number=format_number
                               )
    finally:
        db.close()


# API Endpoints
@app.route('/api/products')
def api_products():
    db = SessionLocal()
    try:
        products = crud.get_products(db)
        result = []
        for p in products:
            result.append({
                'id': p.id,
                'name': p.name,
                'price': float(p.price),
                'stock_quantity': p.stock_quantity,
                'category': p.category,
                'sku': p.sku,
                'description': p.description
            })
        return jsonify(result)
    finally:
        db.close()


@app.route('/api/products', methods=['POST'])
def api_create_product():
    if not check_permission('inventory'):
        return jsonify({'error': 'Access denied'}), 403

    db = SessionLocal()
    try:
        data = request.get_json()

        # Validate required fields
        if not data.get('name') or not data.get('sku') or not data.get('price'):
            return jsonify({'error': 'Name, SKU, and price are required'}), 400

        # Create product
        product_data = schemas.ProductCreate(
            name=data['name'],
            sku=data['sku'],
            price=float(data['price']),
            stock_quantity=int(data.get('stock_quantity', 0)),
            category=data.get('category', 'Uncategorized'),
            description=data.get('description', '')
        )

        product = crud.create_product(db, product_data)

        return jsonify({
            'id': product.id,
            'name': product.name,
            'sku': product.sku,
            'price': float(product.price),
            'stock_quantity': product.stock_quantity,
            'category': product.category,
            'description': product.description
        })
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': f'Server error: {str(e)}'}), 500
    finally:
        db.close()


@app.route('/products/create', methods=['POST'])
def web_create_product():
    if not check_permission('inventory'):
        return "Access Denied", 403

    db = SessionLocal()
    try:
        # Get form data
        name = request.form.get('name')
        sku = request.form.get('sku')
        price = request.form.get('price')

        if not name or not sku or not price:
            return redirect('/products?error=Missing+required+fields')

        product_data = schemas.ProductCreate(
            name=name,
            sku=sku,
            price=float(price),
            stock_quantity=int(request.form.get('stock_quantity', 0)),
            category=request.form.get('category', 'Uncategorized'),
            description=request.form.get('description', '')
        )

        product = crud.create_product(db, product_data)
        return redirect('/products?success=Product+added')
    except ValueError as e:
        return redirect(f'/products?error={str(e).replace(" ", "+")}')
    except Exception as e:
        return redirect(f'/products?error={str(e).replace(" ", "+")}')
    finally:
        db.close()


# Product Edit Endpoints
@app.route('/products/edit/<int:product_id>', methods=['GET', 'POST'])
def edit_product(product_id):
    if not check_permission('inventory'):
        return "Access Denied", 403

    db = SessionLocal()
    try:
        if request.method == 'GET':
            # Get product for editing
            product = db.query(models.Product).filter(models.Product.id == product_id).first()
            if not product:
                return redirect('/products?error=Product+not+found')

            return render_template('edit_product.html',
                                   product=product,
                                   format_naira=format_naira)
        else:  # POST - Update product
            # Get form data
            name = request.form.get('name')
            sku = request.form.get('sku')
            price = request.form.get('price')

            if not name or not sku or not price:
                return redirect(f'/products/edit/{product_id}?error=Missing+required+fields')

            # Update product
            product = db.query(models.Product).filter(models.Product.id == product_id).first()
            if not product:
                return redirect('/products?error=Product+not+found')

            # Check if SKU is being changed and already exists
            if sku != product.sku:
                existing = db.query(models.Product).filter(
                    models.Product.sku == sku,
                    models.Product.id != product_id
                ).first()
                if existing:
                    return redirect(f'/products/edit/{product_id}?error=SKU+already+exists')

            # Update fields
            product.name = name
            product.sku = sku
            product.price = float(price)
            product.cost_price = float(request.form.get('cost_price', 0))
            product.category = request.form.get('category', 'Uncategorized')
            product.description = request.form.get('description', '')
            product.stock_quantity = int(request.form.get('stock_quantity', 0))
            product.reorder_level = int(request.form.get('reorder_level', 10))

            db.commit()
            return redirect('/products?success=Product+updated')
    except Exception as e:
        db.rollback()
        return redirect(f'/products?error={str(e).replace(" ", "+")}')
    finally:
        db.close()


@app.route('/products/delete/<int:product_id>', methods=['POST'])
def delete_product(product_id):
    if not check_permission('inventory'):
        return jsonify({'success': False, 'message': 'Access denied'}), 403

    db = SessionLocal()
    try:
        product = db.query(models.Product).filter(models.Product.id == product_id).first()
        if not product:
            return jsonify({'success': False, 'message': 'Product not found'}), 404

        # Check if product is in any sales
        sale_items = db.query(models.SaleItem).filter(models.SaleItem.product_id == product_id).first()
        if sale_items:
            return jsonify({'success': False, 'message': 'Cannot delete product with sales history'}), 400

        db.delete(product)
        db.commit()
        return jsonify({'success': True, 'message': 'Product deleted'})
    except Exception as e:
        db.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        db.close()


# Cart Management Endpoints
@app.route('/api/cart/add', methods=['POST'])
def api_add_to_cart():
    """Add item to cart"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not authenticated'}), 401

    try:
        data = request.get_json()
        product_id = data.get('product_id')
        quantity = int(data.get('quantity', 1))

        db = SessionLocal()
        product = crud.get_product(db, product_id)

        if not product:
            db.close()
            return jsonify({'success': False, 'message': 'Product not found'}), 404

        # Initialize cart in session if not exists
        if 'cart' not in session:
            session['cart'] = []

        cart = session['cart']

        # Check if product already in cart
        item_index = next((i for i, item in enumerate(cart) if item['product_id'] == product_id), -1)

        if item_index >= 0:
            # Update quantity
            new_quantity = cart[item_index]['quantity'] + quantity
            if new_quantity < 1:
                # Remove item if quantity would be 0 or negative
                cart.pop(item_index)
            else:
                # Check stock
                if new_quantity > product.stock_quantity:
                    db.close()
                    return jsonify({
                        'success': False,
                        'message': f'Only {product.stock_quantity} in stock'
                    }), 400

                cart[item_index]['quantity'] = new_quantity
                cart[item_index]['subtotal'] = new_quantity * float(product.price)
        else:
            # Add new item
            if quantity > product.stock_quantity:
                db.close()
                return jsonify({
                    'success': False,
                    'message': f'Only {product.stock_quantity} in stock'
                }), 400

            cart.append({
                'product_id': product_id,
                'name': product.name,
                'price': float(product.price),
                'quantity': quantity,
                'subtotal': quantity * float(product.price),
                'sku': product.sku
            })

        session['cart'] = cart
        session.modified = True
        db.close()

        return jsonify({
            'success': True,
            'message': 'Cart updated',
            'cart_count': len(cart),
            'cart_total': sum(item['subtotal'] for item in cart),
            'cart_items': cart
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/api/cart', methods=['GET'])
def api_get_cart():
    """Get current cart contents"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not authenticated'}), 401

    cart = session.get('cart', [])
    cart_total = sum(item['subtotal'] for item in cart)

    return jsonify({
        'success': True,
        'cart_items': cart,
        'cart_total': cart_total,
        'cart_count': len(cart)
    })


@app.route('/api/cart/clear', methods=['POST'])
def api_clear_cart():
    """Clear the cart"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not authenticated'}), 401

    session.pop('cart', None)
    session.modified = True

    return jsonify({
        'success': True,
        'message': 'Cart cleared'
    })


@app.route('/api/cart/remove/<int:product_id>', methods=['POST'])
def api_remove_from_cart(product_id):
    """Remove item from cart"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not authenticated'}), 401

    if 'cart' in session:
        cart = session['cart']
        session['cart'] = [item for item in cart if item['product_id'] != product_id]
        session.modified = True

    new_cart = session.get('cart', [])

    return jsonify({
        'success': True,
        'message': 'Item removed from cart',
        'cart_count': len(new_cart),
        'cart_total': sum(item['subtotal'] for item in new_cart),
        'cart_items': new_cart
    })


# Complete Sale Endpoint
@app.route('/sales/complete', methods=['POST'])
def complete_sale():
    """Complete the sale"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not authenticated'}), 401

    if not check_permission('cashier'):
        return jsonify({'success': False, 'message': 'Access denied'}), 403

    db = SessionLocal()
    try:
        data = request.get_json()

        if not data:
            return jsonify({'success': False, 'message': 'No data provided'}), 400

        cart = session.get('cart', [])
        if not cart:
            return jsonify({'success': False, 'message': 'Cart is empty'}), 400

        # Calculate totals
        subtotal = sum(item['subtotal'] for item in cart)
        tax_rate = COMPANY_SETTINGS.get('tax_rate', 0.075)
        tax = subtotal * tax_rate
        discount_amount = float(data.get('discount_amount', 0))
        total = subtotal + tax - discount_amount

        payment_method = data.get('payment_method', 'cash')
        amount_paid = float(data.get('amount_paid', 0))
        customer_id = data.get('customer_id')

        # Check if amount_paid is sufficient
        if amount_paid < total:
            return jsonify({
                'success': False,
                'message': f'Insufficient payment. Total: {format_naira(total)}'
            }), 400

        change_given = amount_paid - total if amount_paid > total else 0

        # Generate receipt number
        today = datetime.now()
        receipt_number = f'REC-{today.strftime("%Y%m%d%H%M%S")}'

        # Create sale
        sale = models.Sale(
            receipt_number=receipt_number,
            total_amount=total,
            tax_amount=tax,
            discount_amount=discount_amount,
            payment_method=payment_method,
            payment_status="completed",
            customer_id=customer_id
        )

        db.add(sale)
        db.flush()  # Get the sale ID

        # Add sale items
        for item in cart:
            sale_item = models.SaleItem(
                sale_id=sale.id,
                product_id=item['product_id'],
                quantity=item['quantity'],
                unit_price=item['price'],
                subtotal=item['subtotal']
            )
            db.add(sale_item)

            # Update product stock
            product = db.query(models.Product).filter(models.Product.id == item['product_id']).first()
            if product:
                product.stock_quantity = max(0, product.stock_quantity - item['quantity'])

        db.commit()

        # Clear cart from session
        session.pop('cart', None)
        session.modified = True

        return jsonify({
            'success': True,
            'message': 'Sale completed successfully!',
            'sale_id': sale.id,
            'receipt_number': sale.receipt_number,
            'receipt_data': {
                'receipt_number': sale.receipt_number,
                'subtotal': subtotal,
                'tax': tax,
                'discount': discount_amount,
                'total': total,
                'amount_paid': amount_paid,
                'change': change_given,
                'payment_method': payment_method,
                'date': sale.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                'cashier': session.get('full_name', session.get('username', 'Cashier')),
                'company': COMPANY_SETTINGS,
                'items': cart
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        db.close()


@app.route('/api/sales', methods=['POST'])
def api_create_sale():
    if not check_permission('cashier'):
        return jsonify({'error': 'Access denied'}), 403

    db = SessionLocal()
    try:
        data = request.get_json()

        sale_data = schemas.SaleCreate(
            customer_id=data.get('customer_id'),
            payment_method=data.get('payment_method', 'cash'),
            items=[schemas.SaleItemCreate(**item) for item in data['items']]
        )

        sale = crud.create_sale(db, sale_data)

        return jsonify({
            'id': sale.id,
            'receipt_number': sale.receipt_number,
            'total_amount': float(sale.total_amount),
            'tax_amount': float(sale.tax_amount),
            'created_at': sale.created_at.isoformat(),
            'items': [{
                'product_id': item.product_id,
                'quantity': item.quantity,
                'unit_price': float(item.unit_price),
                'subtotal': float(item.subtotal)
            } for item in sale.items]
        })
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    finally:
        db.close()


@app.route('/api/inventory/report')
def api_inventory_report():
    if not check_permission('inventory'):
        return jsonify({'error': 'Access denied'}), 403

    db = SessionLocal()
    try:
        report = crud.get_inventory_report(db)
        return jsonify(report)
    finally:
        db.close()


# Settings Page - Only admin
@app.route('/settings')
def settings():
    if not check_permission('admin'):
        return "Access Denied: Only admin can access settings", 403

    return render_template('settings.html',
                           company=COMPANY_SETTINGS,
                           format_naira=format_naira
                           )


@app.route('/api/sales/<receipt_number>')
def get_sale_by_receipt(receipt_number):
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401

    db = SessionLocal()
    try:
        # Get sale
        sale = db.query(models.Sale).filter(models.Sale.receipt_number == receipt_number).first()

        if not sale:
            return jsonify({'error': 'Receipt not found'}), 404

        # Get sale items with product names
        items = []
        for item in sale.items:
            product = db.query(models.Product).filter(models.Product.id == item.product_id).first()
            items.append({
                'product_id': item.product_id,
                'product_name': product.name if product else 'Unknown Product',
                'quantity': item.quantity,
                'unit_price': float(item.unit_price),
                'subtotal': float(item.subtotal)
            })

        return jsonify({
            'receipt_number': sale.receipt_number,
            'total_amount': float(sale.total_amount),
            'tax_amount': float(sale.tax_amount or 0),
            'discount_amount': float(sale.discount_amount or 0),
            'payment_method': sale.payment_method,
            'created_at': sale.created_at.isoformat(),
            'items': items
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        db.close()


# API to update settings
@app.route('/api/settings', methods=['POST'])
def update_settings():
    if not check_permission('admin'):
        return jsonify({'success': False, 'message': 'Access denied'}), 403

    try:
        data = request.get_json()

        # Update COMPANY_SETTINGS
        if 'name' in data:
            COMPANY_SETTINGS['name'] = data['name']
        if 'address' in data:
            COMPANY_SETTINGS['address'] = data['address']
        if 'phone' in data:
            COMPANY_SETTINGS['phone'] = data['phone']
        if 'email' in data:
            COMPANY_SETTINGS['email'] = data['email']
        if 'tax_id' in data:
            COMPANY_SETTINGS['tax_id'] = data['tax_id']
        if 'tax_rate' in data:
            COMPANY_SETTINGS['tax_rate'] = float(data['tax_rate'])
        if 'receipt_footer' in data:
            COMPANY_SETTINGS['receipt_footer'] = data['receipt_footer']
        if 'bank_details' in data:
            COMPANY_SETTINGS['bank_details'] = data['bank_details']

        return jsonify({
            'success': True,
            'message': 'Settings updated successfully',
            'settings': COMPANY_SETTINGS
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


# Health check
@app.route('/health')
def health():
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat()
    })


# Add this route to see all users and their roles
@app.route('/debug-users')
def debug_users():
    if 'user_id' not in session or session.get('role') != 'admin':
        return "Admin access required"

    db = SessionLocal()
    users = db.query(models.User).all()
    db.close()

    result = "<h1>All Users</h1>"
    for user in users:
        result += f"<p>ID: {user.id}, Username: {user.username}, Role: {user.role}, Full Name: {user.full_name}</p>"
    return result


# Sales data management
@app.route('/api/sales/clear-all', methods=['POST'])
def clear_all_sales():
    """Clear all sales data from database"""
    try:
        data = request.get_json()

        if not data or not data.get('confirmed'):
            return jsonify({
                'success': False,
                'message': 'Confirmation required. Please confirm this action.'
            }), 400

        # Connect to database
        conn = sqlite3.connect('pos.db')
        cursor = conn.cursor()

        print(f"[{datetime.now()}] Starting to clear sales data...")

        # Get sales-related tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [table[0] for table in cursor.fetchall()]

        sales_tables = []
        sales_keywords = ['sale', 'transaction', 'receipt', 'order']

        for table in tables:
            table_lower = table.lower()
            if any(keyword in table_lower for keyword in sales_keywords):
                sales_tables.append(table)

        # Clear each sales table
        cleared_tables = []
        for table in sales_tables:
            try:
                cursor.execute(f'SELECT COUNT(*) FROM "{table}"')
                count_before = cursor.fetchone()[0]

                cursor.execute(f'DELETE FROM "{table}"')
                cleared_tables.append({
                    'name': table,
                    'rows_cleared': count_before
                })
                print(f"Cleared table: {table} ({count_before} rows)")
            except Exception as e:
                print(f"Error clearing table {table}: {e}")

        conn.commit()
        conn.close()

        # Calculate total rows cleared
        total_rows = sum(t['rows_cleared'] for t in cleared_tables)

        return jsonify({
            'success': True,
            'message': f'✅ Successfully cleared {total_rows} sales records!',
            'cleared_tables': [t['name'] for t in cleared_tables],
            'rows_cleared': total_rows,
            'timestamp': datetime.now().isoformat(),
            'cleared_by': session.get('username', 'admin')
        })
    except Exception as e:
        print(f"Error clearing sales data: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Error: {str(e)}'
        }), 500


@app.route('/api/sales/backup', methods=['POST'])
def backup_sales():
    """Create a backup of sales data"""
    try:
        import json
        from datetime import datetime

        conn = sqlite3.connect('pos.db')
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Get all tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';")
        tables = [row[0] for row in cursor.fetchall()]

        # Create backup data
        backup_data = {
            'timestamp': datetime.now().isoformat(),
            'tables': {}
        }

        # Backup each table
        for table in tables:
            cursor.execute(f'SELECT * FROM "{table}"')
            rows = cursor.fetchall()
            backup_data['tables'][table] = [dict(row) for row in rows]

        conn.close()

        # Save to file
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_filename = f'sales_backup_{timestamp}.json'

        with open(backup_filename, 'w') as f:
            json.dump(backup_data, f, indent=2)

        return jsonify({
            'success': True,
            'message': f'Backup created: {backup_filename}',
            'filename': backup_filename,
            'row_count': sum(len(rows) for rows in backup_data['tables'].values())
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Backup failed: {str(e)}'
        }), 500


# Receipt printing
@app.route('/receipt/<int:sale_id>/print')
def print_receipt(sale_id):
    """Print receipt for a specific sale"""
    if not check_permission('cashier'):
        return "Access Denied", 403

    from app.database import SessionLocal
    from sqlalchemy.orm import joinedload
    import traceback

    db = SessionLocal()
    try:
        # Get sale with all relationships
        sale = db.query(models.Sale).options(
            joinedload(models.Sale.customer),
            joinedload(models.Sale.items).joinedload(models.SaleItem.product)
        ).filter(models.Sale.id == sale_id).first()

        if not sale:
            return "Sale not found", 404

        # Convert items to a proper list
        items_list = []
        for item in sale.items:
            items_list.append({
                'name': item.product.name if item.product else 'Unknown Product',
                'quantity': item.quantity,
                'price': float(item.unit_price),
                'total': float(item.quantity * item.unit_price)
            })

        # Create receipt data
        receipt_data = {
            'receipt_number': sale.receipt_number or f"REC-{sale.id:06d}",
            'created_at': sale.created_at.strftime('%Y-%m-%d %H:%M:%S') if sale.created_at else 'N/A',
            'receipt_items': items_list,
            'subtotal': float(sale.total_amount - (sale.tax_amount or 0)),
            'tax_amount': float(sale.tax_amount or 0),
            'discount_amount': float(sale.discount_amount or 0),
            'total_amount': float(sale.total_amount),
            'amount_paid': float(sale.total_amount),
            'change_amount': 0.0,
            'payment_method': sale.payment_method or 'cash',
            'customer': sale.customer.name if sale.customer else 'Walk-in Customer'
        }

        return render_template('receipt_print.html',
                               receipt=receipt_data,
                               company=COMPANY_SETTINGS,
                               format_naira=format_naira)
    except Exception as e:
        error_msg = f"Error: {str(e)}\n\nTraceback:\n{traceback.format_exc()}"
        print(error_msg)
        return f"<pre>{error_msg}</pre>", 500
    finally:
        db.close()


@app.route('/api/sales/<int:sale_id>')
def get_sale_details(sale_id):
    """Get detailed sale information for modal"""
    if not check_permission('cashier'):
        return jsonify({'error': 'Access denied'}), 403

    db = SessionLocal()
    try:
        sale = crud.get_sale(db, sale_id)
        if not sale:
            return jsonify({'error': 'Sale not found'}), 404

        # Get sale items with product info
        from sqlalchemy.orm import joinedload
        sale_items = db.query(models.SaleItem).options(
            joinedload(models.SaleItem.product)
        ).filter(models.SaleItem.sale_id == sale_id).all()

        # Format sale data for JSON response
        sale_data = {
            'id': sale.id,
            'receipt_number': sale.receipt_number or f"REC-{sale.id:06d}",
            'created_at': sale.created_at.isoformat() if sale.created_at else None,
            'customer': {
                'name': sale.customer.name if sale.customer else None,
                'phone': sale.customer.phone if sale.customer else None
            } if sale.customer else None,
            'items': [
                {
                    'product_name': item.product.name if item.product else 'Unknown Product',
                    'quantity': item.quantity,
                    'price': float(item.unit_price),
                    'total': float(item.quantity * item.unit_price)
                }
                for item in sale_items
            ],
            'subtotal': float(sale.total_amount - (sale.tax_amount or 0)),
            'tax_amount': float(sale.tax_amount or 0),
            'discount_amount': float(sale.discount_amount or 0),
            'total_amount': float(sale.total_amount),
            'amount_paid': float(sale.total_amount),
            'change_amount': 0.0,
            'payment_method': sale.payment_method or 'cash',
            'notes': sale.notes if hasattr(sale, 'notes') else None
        }

        return jsonify(sale_data)
    except Exception as e:
        print(f"Error getting sale details: {str(e)}")
        return jsonify({'error': str(e)}), 500
    finally:
        db.close()


# Database initialization route - FIXED SINGLE VERSION
@app.route('/init-now')
def init_now():
    """Initialize database silently and redirect to login"""
    try:
        from app.database import Base, engine, SessionLocal
        from app.auth import get_password_hash

        # 1. Create tables
        Base.metadata.create_all(bind=engine)

        # 2. Create users (only if they don't exist)
        db = SessionLocal()

        users_to_create = [
            ("admin", "admin123", "admin", "System Administrator"),
            ("cashier", "cashier123", "cashier", "Cashier User"),
            ("inventory", "inventory123", "inventory", "Inventory Manager")
        ]

        for username, password, role, full_name in users_to_create:
            existing = db.query(models.User).filter(models.User.username == username).first()
            if not existing:
                user = models.User(
                    username=username,
                    email=f"{username}@pos.com",
                    hashed_password=get_password_hash(password),
                    role=role,
                    full_name=full_name,
                    is_active=True
                )
                db.add(user)

        db.commit()
        db.close()

        # Log to console only (not shown to user)
        print(f"✅ [{datetime.now()}] Database initialized via /init-now")

        # IMMEDIATE REDIRECT to login
        return redirect('/login')

    except Exception as e:
        # Only show error if something goes wrong
        return f'''
        <h1>Error</h1>
        <p>Database initialization failed.</p>
        <p><a href="/login">Try to login anyway</a></p>
        <details>
            <summary>Technical Details</summary>
            <pre>{str(e)}</pre>
        </details>
        '''


# Additional initialization endpoint for backward compatibility
@app.route('/init-db')
def initialize_database():
    """Initialize database tables (run once after deployment)"""
    try:
        from app.database import Base, engine
        from app import models

        # Create all tables
        Base.metadata.create_all(bind=engine)

        return jsonify({
            'success': True,
            'message': 'Database tables created successfully',
            'tables_created': list(Base.metadata.tables.keys())
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# Production configuration
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=2)
app.config['SESSION_COOKIE_SECURE'] = os.environ.get('FLASK_ENV') == 'production'
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

if __name__ == '__main__':
    # Get port from environment variable (Render sets PORT)
    port = int(os.environ.get('PORT', 5000))

    # Determine if we're in development or production
    debug_mode = os.environ.get('FLASK_ENV') != 'production'

    print(f"🚀 Starting POS System on port {port}")
    print(f"🔧 Debug mode: {debug_mode}")
    print(f"🌍 Environment: {os.environ.get('FLASK_ENV', 'development')}")

    if os.environ.get('DATABASE_URL'):
        print(f"🗄️ Database: PostgreSQL (Render)")
    else:
        print(f"🗄️ Database: SQLite (local)")

    print("\n🔗 Available URLs:")
    print(f"   http://localhost:{port}/login")
    print(f"   http://localhost:{port}/init-now (first time only)")
    print(f"   http://localhost:{port}/force-init-db")
    print(f"   http://localhost:{port}/health")

    app.run(
        host='0.0.0.0',
        port=port,
        debug=debug_mode,
        threaded=True
    )