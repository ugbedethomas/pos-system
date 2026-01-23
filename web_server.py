# web_server.py - CORRECTED VERSION
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


# AUTO-SETUP DATABASE ON STARTUP
def setup_database():
    """Auto-setup database on first run"""
    try:
        from app.database import Base, engine, SessionLocal
        from app.auth import get_password_hash
        from sqlalchemy import inspect

        # Check if tables exist
        inspector = inspect(engine)
        existing_tables = inspector.get_table_names()

        if not existing_tables:
            print("🔄 First run: Creating database tables...")
            Base.metadata.create_all(bind=engine)

            # Create default users
            db = SessionLocal()

            default_users = [
                ("admin", "admin123", "admin", "System Administrator"),
                ("cashier", "cashier123", "cashier", "Cashier User"),
                ("inventory", "inventory123", "inventory", "Inventory Manager")
            ]

            for username, password, role, full_name in default_users:
                user = models.User(
                    username=username,
                    email=f"{username}@pos.com",
                    hashed_password=get_password_hash(password),
                    role=role,
                    full_name=full_name,
                    is_active=True
                )
                db.add(user)
                print(f"✅ Created user: {username}")

            db.commit()
            db.close()

            print("🎉 First-time setup complete!")
            print("🔑 Default credentials:")
            print("   • admin / admin123")
            print("   • cashier / cashier123")
            print("   • inventory / inventory123")
            print("⚠️ Change passwords immediately after login!")

            return True  # First time setup
        else:
            print(f"✅ Database ready with {len(existing_tables)} tables")
            return False  # Already set up

    except Exception as e:
        print(f"❌ Database setup error: {e}")
        return False


# Run setup when app starts
with app.app_context():
    setup_database()


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
        'init_now',
        'ping'
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
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        if not username or not password:
            return render_template('login.html', error='Username and password are required')

        db = SessionLocal()
        try:
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
        except Exception as e:
            db.close()
            print(f"Login error: {e}")
            return render_template('login.html', error='Login failed. Please try again.')

    return render_template('login.html')


@app.route('/ping')
def ping():
    """Ultra-lightweight ping endpoint to keep app awake"""
    return 'pong', 200


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
        categories = list(set(p.category for p in products if p.category))

        return render_template('products.html',
                               products=products,
                               categories=categories,
                               company=COMPANY_SETTINGS,
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
                'description': p.description,
                'barcode': p.barcode if hasattr(p, 'barcode') else None
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
            description=data.get('description', ''),
            barcode=data.get('barcode')
        )

        product = crud.create_product(db, product_data)

        return jsonify({
            'id': product.id,
            'name': product.name,
            'sku': product.sku,
            'price': float(product.price),
            'stock_quantity': product.stock_quantity,
            'category': product.category,
            'description': product.description,
            'barcode': product.barcode
        })
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': f'Server error: {str(e)}'}), 500
    finally:
        db.close()


# PRODUCT CREATE PAGE - COMBINED GET & POST - ONLY ONE FUNCTION!
@app.route('/products/create', methods=['GET', 'POST'])
def web_create_product():
    """Handle both GET (display form) and POST (create product)"""
    if not check_permission('inventory'):
        return "Access Denied", 403

    db = SessionLocal()
    try:
        # Get categories for dropdown (needed for both GET and error cases)
        products = crud.get_products(db)
        categories = list(set(p.category for p in products if p.category))

        if request.method == 'GET':
            # Display the form
            return render_template('create_product.html',
                                   categories=categories,
                                   company=COMPANY_SETTINGS,
                                   format_naira=format_naira)

        else:  # POST method - Create product
            # Get form data
            name = request.form.get('name')
            sku = request.form.get('sku')
            price = request.form.get('price')
            barcode = request.form.get('barcode', '').strip() or None

            if not name or not sku or not price:
                # Show error on the same page
                return render_template('create_product.html',
                                       categories=categories,
                                       company=COMPANY_SETTINGS,
                                       format_naira=format_naira,
                                       error='Missing required fields')

            # Check if barcode already exists
            if barcode:
                existing = db.query(models.Product).filter(
                    models.Product.barcode == barcode
                ).first()
                if existing:
                    return render_template('create_product.html',
                                           categories=categories,
                                           company=COMPANY_SETTINGS,
                                           format_naira=format_naira,
                                           error=f'Barcode {barcode} already exists')

            # Create product
            product_data = schemas.ProductCreate(
                name=name,
                sku=sku,
                price=float(price),
                stock_quantity=int(request.form.get('stock_quantity', 0)),
                category=request.form.get('category', 'Uncategorized'),
                description=request.form.get('description', ''),
                barcode=barcode
            )

            product = crud.create_product(db, product_data)

            # Redirect to products page with success message
            return redirect('/products?success=Product+added+successfully')

    except ValueError as e:
        return render_template('create_product.html',
                               categories=categories,
                               company=COMPANY_SETTINGS,
                               format_naira=format_naira,
                               error=str(e))
    except Exception as e:
        return render_template('create_product.html',
                               categories=categories,
                               company=COMPANY_SETTINGS,
                               format_naira=format_naira,
                               error=f'Error: {str(e)}')
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
            barcode = request.form.get('barcode', '').strip() or None

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

            # Check if barcode is being changed and already exists
            if barcode != product.barcode:
                existing_barcode = db.query(models.Product).filter(
                    models.Product.barcode == barcode,
                    models.Product.id != product_id
                ).first()
                if existing_barcode:
                    return redirect(f'/products/edit/{product_id}?error=Barcode+{barcode}+already+exists')

            # Update fields
            product.name = name
            product.sku = sku
            product.barcode = barcode
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
    """Add item to cart by product_id OR barcode"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not authenticated'}), 401

    try:
        data = request.get_json()
        product_id = data.get('product_id')
        barcode = data.get('barcode')
        quantity = int(data.get('quantity', 1))

        if not product_id and not barcode:
            return jsonify({'success': False, 'message': 'Either product_id or barcode is required'}), 400

        db = SessionLocal()
        product = None

        # First try to find product by ID if provided
        if product_id:
            product = crud.get_product(db, product_id)
        elif barcode:
            # Try to find product by barcode
            product = db.query(models.Product).filter(models.Product.barcode == barcode).first()

            if not product:
                # Search for product with barcode in name or SKU (fallback)
                products = db.query(models.Product).filter(
                    (models.Product.name.ilike(f'%{barcode}%')) |
                    (models.Product.sku.ilike(f'%{barcode}%'))
                ).first()

                if not products:
                    db.close()
                    return jsonify({
                        'success': False,
                        'message': f'Product with barcode "{barcode}" not found'
                    }), 404
                product = products

        if not product:
            db.close()
            return jsonify({'success': False, 'message': 'Product not found'}), 404

        # Check stock availability
        if product.stock_quantity < quantity:
            db.close()
            return jsonify({
                'success': False,
                'message': f'Only {product.stock_quantity} in stock'
            }), 400

        # Initialize cart in session if not exists
        if 'cart' not in session:
            session['cart'] = []

        cart = session['cart']

        # Check if product already in cart
        item_index = next((i for i, item in enumerate(cart) if item['product_id'] == product.id), -1)

        if item_index >= 0:
            # Update quantity
            new_quantity = cart[item_index]['quantity'] + quantity
            if new_quantity < 1:
                # Remove item if quantity would be 0 or negative
                cart.pop(item_index)
            else:
                # Check stock for new total quantity
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
            cart.append({
                'product_id': product.id,
                'name': product.name,
                'price': float(product.price),
                'quantity': quantity,
                'subtotal': quantity * float(product.price),
                'sku': product.sku,
                'barcode': product.barcode if hasattr(product, 'barcode') else None
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
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/api/cart', methods=['GET'])
def api_get_cart():
    """Get current cart"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not authenticated'}), 401

    try:
        cart = session.get('cart', [])

        return jsonify({
            'success': True,
            'cart_count': len(cart),
            'cart_total': sum(item.get('subtotal', 0) for item in cart),
            'cart_items': cart
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/api/cart/update', methods=['POST'])
def api_update_cart():
    """Update cart item quantity"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not authenticated'}), 401

    try:
        data = request.get_json()
        product_id = data.get('product_id')
        quantity_change = int(data.get('quantity_change', 0))

        if not product_id:
            return jsonify({'success': False, 'message': 'product_id is required'}), 400

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
            # Calculate new quantity
            new_quantity = cart[item_index]['quantity'] + quantity_change

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
            # Adding new item with quantity_change as initial quantity
            if quantity_change < 1:
                db.close()
                return jsonify({'success': False, 'message': 'Quantity must be positive'}), 400

            if quantity_change > product.stock_quantity:
                db.close()
                return jsonify({
                    'success': False,
                    'message': f'Only {product.stock_quantity} in stock'
                }), 400

            cart.append({
                'product_id': product_id,
                'name': product.name,
                'price': float(product.price),
                'quantity': quantity_change,
                'subtotal': quantity_change * float(product.price),
                'sku': product.sku,
                'barcode': product.barcode if hasattr(product, 'barcode') else None
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


@app.route('/api/cart/remove/<int:product_id>', methods=['POST'])
def api_remove_from_cart(product_id):
    """Remove item from cart"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not authenticated'}), 401

    try:
        # Initialize cart in session if not exists
        if 'cart' not in session:
            session['cart'] = []

        cart = session['cart']

        # Find and remove item
        initial_length = len(cart)
        cart = [item for item in cart if item['product_id'] != product_id]

        if len(cart) == initial_length:
            return jsonify({'success': False, 'message': 'Item not found in cart'}), 404

        session['cart'] = cart
        session.modified = True

        return jsonify({
            'success': True,
            'message': 'Item removed from cart',
            'cart_count': len(cart),
            'cart_total': sum(item['subtotal'] for item in cart),
            'cart_items': cart
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/api/cart/clear', methods=['POST'])
def api_clear_cart():
    """Clear all items from cart"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not authenticated'}), 401

    try:
        session['cart'] = []
        session.modified = True

        return jsonify({
            'success': True,
            'message': 'Cart cleared',
            'cart_count': 0,
            'cart_total': 0,
            'cart_items': []
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


# Barcode Search Endpoint
@app.route('/api/products/barcode/<barcode>', methods=['GET'])
def api_get_product_by_barcode(barcode):
    """Get product by barcode"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not authenticated'}), 401

    try:
        db = SessionLocal()

        # First try exact barcode match
        product = db.query(models.Product).filter(models.Product.barcode == barcode).first()

        if not product:
            # Try partial matches
            product = db.query(models.Product).filter(
                (models.Product.barcode.ilike(f'%{barcode}%')) |
                (models.Product.sku.ilike(f'%{barcode}%')) |
                (models.Product.name.ilike(f'%{barcode}%'))
            ).first()

        if product:
            result = {
                'success': True,
                'product': {
                    'id': product.id,
                    'name': product.name,
                    'sku': product.sku,
                    'barcode': product.barcode if hasattr(product, 'barcode') else None,
                    'price': float(product.price),
                    'cost_price': float(product.cost_price) if hasattr(product,
                                                                       'cost_price') and product.cost_price else None,
                    'stock_quantity': product.stock_quantity,
                    'reorder_level': product.reorder_level if hasattr(product, 'reorder_level') else 10,
                    'category': product.category,
                    'description': product.description
                }
            }
            db.close()
            return jsonify(result)
        else:
            db.close()
            return jsonify({
                'success': False,
                'message': f'Product with barcode "{barcode}" not found'
            }), 404

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'message': str(e)}), 500


# Settings Page - Only admin
@app.route('/settings')
def settings():
    if not check_permission('admin'):
        return "Access Denied: Only admin can access settings", 403

    return render_template('settings.html',
                           company=COMPANY_SETTINGS,
                           format_naira=format_naira
                           )


# Settings API endpoints
@app.route('/api/settings', methods=['GET'])
def api_get_settings():
    """Get company settings"""
    if not check_permission('admin'):
        return jsonify({'error': 'Access denied'}), 403

    return jsonify({
        'success': True,
        'settings': COMPANY_SETTINGS
    })


@app.route('/api/settings', methods=['POST'])
def api_save_settings():
    """Save company settings"""
    if not check_permission('admin'):
        return jsonify({'error': 'Access denied'}), 403

    try:
        data = request.get_json()

        if not data:
            return jsonify({'success': False, 'message': 'No data provided'}), 400

        # Update COMPANY_SETTINGS with new values
        for key, value in data.items():
            if key in COMPANY_SETTINGS:
                if key == 'bank_details' and isinstance(value, dict):
                    # Update nested bank_details
                    for bank_key, bank_value in value.items():
                        if bank_key in COMPANY_SETTINGS['bank_details']:
                            COMPANY_SETTINGS['bank_details'][bank_key] = bank_value
                else:
                    # Update regular settings
                    if key == 'tax_rate':
                        COMPANY_SETTINGS[key] = float(value)
                    else:
                        COMPANY_SETTINGS[key] = value

        return jsonify({
            'success': True,
            'message': 'Settings saved successfully',
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
            'notes': sale.notes if hasattr(sale, 'notes') else None,
            'status': sale.status if hasattr(sale, 'status') else 'completed'
        }

        return jsonify(sale_data)
    except Exception as e:
        print(f"Error getting sale details: {str(e)}")
        return jsonify({'error': str(e)}), 500
    finally:
        db.close()


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
        amount_paid = float(data.get('amount_paid', total))

        if amount_paid < total:
            return jsonify({
                'success': False,
                'message': f'Insufficient payment. Total: ₦{total:,.2f}'
            }), 400

        change_given = amount_paid - total if amount_paid > total else 0
        receipt_number = f'REC-{datetime.now().strftime("%Y%m%d%H%M%S")}'

        # Create sale - check if status field exists
        sale_kwargs = {
            'receipt_number': receipt_number,
            'total_amount': total,
            'tax_amount': tax,
            'discount_amount': discount_amount,
            'amount_paid': amount_paid,
            'change_amount': change_given,
            'payment_method': payment_method,
            'payment_status': "completed",
            'customer_id': data.get('customer_id'),
            'user_id': session.get('user_id'),
            'created_at': datetime.now()
        }

        # Add status field if it exists in the model
        if hasattr(models.Sale, 'status'):
            sale_kwargs['status'] = 'completed'

        sale = models.Sale(**sale_kwargs)

        db.add(sale)
        db.flush()

        # Add sale items and update stock
        for item in cart:
            sale_item = models.SaleItem(
                sale_id=sale.id,
                product_id=item['product_id'],
                quantity=item['quantity'],
                unit_price=item['price'],
                subtotal=item['subtotal']
            )
            db.add(sale_item)

            product = db.query(models.Product).filter(models.Product.id == item['product_id']).first()
            if product:
                product.stock_quantity = max(0, product.stock_quantity - item['quantity'])

        db.commit()

        # Clear the cart from session
        if 'cart' in session:
            session.pop('cart', None)
            session.modified = True

        return jsonify({
            'success': True,
            'message': 'Sale completed successfully!',
            'sale_id': sale.id,
            'receipt_number': receipt_number,
            'total': total,
            'change': change_given,
            'amount_paid': amount_paid,
            'items_count': len(cart)
        })

    except Exception as e:
        db.rollback()
        import traceback
        print(f"Error completing sale: {str(e)}")
        print(traceback.format_exc())
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        db.close()


# Database initialization route - SMART VERSION (Preserves existing users/passwords)
@app.route('/init-now')
def init_now():
    """Initialize database safely - creates missing tables/users only"""
    try:
        from app.database import Base, engine, SessionLocal
        from app.auth import get_password_hash
        from sqlalchemy import inspect

        # 1. Check if tables already exist
        inspector = inspect(engine)
        existing_tables = inspector.get_table_names()
        was_first_time = False

        if not existing_tables:
            # First time setup - create all tables
            Base.metadata.create_all(bind=engine)
            was_first_time = True
            print(f"✅ [{datetime.now()}] Created database tables (first time)")
        else:
            print(f"✅ [{datetime.now()}] Database already exists - preserving all data")

        # 2. Create default users ONLY if they don't exist
        db = SessionLocal()

        users_to_create = [
            ("admin", "admin123", "admin", "System Administrator"),
            ("cashier", "cashier123", "cashier", "Cashier User"),
            ("inventory", "inventory123", "inventory", "Inventory Manager")
        ]

        created_users = []
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
                created_users.append(username)
                print(f"✅ Created user: {username}")
            else:
                print(f"✅ User already exists: {username}")

        db.commit()
        db.close()

        # 3. Show different message based on whether it was first time
        if was_first_time:
            print(f"✅ [{datetime.now()}] Database initialized with default users")
            return '''
            <!DOCTYPE html>
            <html>
            <head>
                <title>Database Initialized</title>
                <meta http-equiv="refresh" content="3;url=/login">
                <style>
                    body { font-family: Arial; padding: 40px; text-align: center; }
                    .success { color: green; font-size: 24px; }
                    .warning { color: orange; background: #fff8e1; padding: 15px; border-radius: 5px; margin: 20px; }
                    .info { background: #e3f2fd; padding: 15px; border-radius: 5px; margin: 20px; }
                </style>
            </head>
            <body>
                <div class="success">✅ Database Initialized Successfully!</div>

                <div class="info">
                    <h3>Default Users Created:</h3>
                    <p><strong>Admin:</strong> admin / admin123</p>
                    <p><strong>Cashier:</strong> cashier / cashier123</p>
                    <p><strong>Inventory:</strong> inventory / inventory123</p>
                </div>

                <div class="warning">
                    <h3>⚠️ IMPORTANT:</h3>
                    <p><strong>Change these passwords immediately after login!</strong></p>
                    <p>Use the "Change Password" option in your profile.</p>
                </div>

                <p>Redirecting to login in 3 seconds...</p>
                <p><a href="/login">Click here if not redirected</a></p>
            </body>
            </html>
            '''
        else:
            print(f"✅ [{datetime.now()}] Database checked - existing users preserved")
            return '''
            <!DOCTYPE html>
            <html>
            <head>
                <title>Database Already Initialized</title>
                <meta http-equiv="refresh" content="3;url=/login">
                <style>
                    body { font-family: Arial; padding: 40px; text-align: center; }
                    .info { color: blue; font-size: 24px; }
                    .success { background: #e8f5e9; padding: 15px; border-radius: 5px; margin: 20px; }
                </style>
            </head>
            <body>
                <div class="info">✅ Database Already Initialized</div>

                <div class="success">
                    <h3>All User Data Preserved</h3>
                    <p>Your existing users, passwords, and all data are safe.</p>
                    <p><strong>Use your current passwords to login.</strong></p>
                    <p><em>New users created: ''' + (
                ', '.join(created_users) if created_users else 'None (all users already exist)') + '''</em></p>
                </div>

                <p>Redirecting to login in 3 seconds...</p>
                <p><a href="/login">Click here if not redirected</a></p>
            </body>
            </html>
            '''

    except Exception as e:
        # Error handling
        print(f"❌ [{datetime.now()}] Database initialization failed: {str(e)}")
        return f'''
        <!DOCTYPE html>
        <html>
        <head>
            <title>Error</title>
            <style>
                body {{ font-family: Arial; padding: 40px; }}
                .error {{ color: red; font-size: 20px; }}
                .details {{ background: #ffebee; padding: 15px; border-radius: 5px; margin: 20px 0; }}
            </style>
        </head>
        <body>
            <div class="error">❌ Database Initialization Failed</div>

            <p>The database could not be initialized. This could be because:</p>
            <ul>
                <li>Database connection issue</li>
                <li>Permission problems</li>
                <li>Existing database with different structure</li>
            </ul>

            <div class="details">
                <strong>Technical Error:</strong>
                <pre>{str(e)}</pre>
            </div>

            <p><a href="/login">Try to login anyway</a> • <a href="/" onclick="location.reload()">Retry initialization</a></p>
        </body>
        </html>
        '''


@app.route('/api/change-password', methods=['POST'])
def api_change_password():
    """API endpoint to change password"""
    try:
        data = request.json
        username = data.get('username')
        current_password = data.get('current_password')
        new_password = data.get('new_password')

        if not all([username, current_password, new_password]):
            return jsonify({"success": False, "error": "All fields are required"}), 400

        from app.database import SessionLocal
        from app.auth import verify_password, get_password_hash

        db = SessionLocal()
        user = db.query(models.User).filter(models.User.username == username).first()

        if not user:
            db.close()
            return jsonify({"success": False, "error": "User not found"}), 404

        # Verify current password
        if not verify_password(current_password, user.hashed_password):
            db.close()
            return jsonify({"success": False, "error": "Current password is incorrect"}), 401

        # Update to new password
        user.hashed_password = get_password_hash(new_password)
        db.commit()
        db.close()

        print(f"✅ [{datetime.now()}] Password changed for user: {username}")

        return jsonify({
            "success": True,
            "message": "Password updated successfully"
        })

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/adjust-stock', methods=['POST'])
def adjust_stock():
    """Stock adjustment API - SIMPLE WORKING VERSION"""
    try:
        data = request.json
        product_id = data.get('product_id')
        quantity = data.get('quantity')

        if not product_id or quantity is None:
            return jsonify({"success": False, "error": "Missing product or quantity"}), 400

        from app.database import SessionLocal
        db = SessionLocal()

        # Get product
        product = db.query(models.Product).filter(models.Product.id == product_id).first()

        if not product:
            db.close()
            return jsonify({"success": False, "error": "Product not found"}), 404

        # Store product name BEFORE any updates
        product_name = product.name
        current_stock = product.stock_quantity
        new_stock = current_stock + quantity

        if new_stock < 0:
            db.close()
            return jsonify({"success": False, "error": "Stock cannot go below zero"}), 400

        # Update product
        product.stock_quantity = new_stock

        # Create movement
        movement = models.StockMovement(
            product_id=product_id,
            quantity=quantity,
            movement_type=data.get('adjustment_type', 'adjustment'),
            reference=data.get('reference', 'Stock adjustment'),
            created_at=datetime.now(),
            created_by=session.get('username', 'Anonymous')
        )
        db.add(movement)

        db.commit()
        db.close()

        # Log using stored variables
        print(f"✅ Stock updated: {product_name} ({quantity:+d}) = {new_stock}")

        return jsonify({
            "success": True,
            "message": f"Updated {product_name}",
            "new_stock": new_stock,
            "product_name": product_name
        })

    except Exception as e:
        print(f"❌ Error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


def check_database_status():
    """Check database status on startup"""
    try:
        from app.database import engine
        from sqlalchemy import inspect

        inspector = inspect(engine)
        tables = inspector.get_table_names()

        if tables:
            print(f"✅ Database ready with {len(tables)} tables")

            # Check if admin user exists
            from app.database import SessionLocal
            db = SessionLocal()
            admin = db.query(models.User).filter(models.User.username == 'admin').first()
            db.close()

            if admin:
                print(f"✅ Admin user exists")
            else:
                print(f"⚠️  Admin user not found - visit /init-now")

        else:
            print(f"⚠️  Database not initialized - visit /init-now for first-time setup")

    except Exception as e:
        print(f"⚠️  Database check failed: {e}")


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

    # Check database status
    with app.app_context():
        check_database_status()

    app.run(
        host='0.0.0.0',
        port=port,
        debug=debug_mode,
        threaded=True
    )