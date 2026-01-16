from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_, func
from typing import List, Optional
from datetime import datetime, date

from app import models, schemas


# Product CRUD operations
def get_product(db: Session, product_id: int):
    return db.query(models.Product).filter(models.Product.id == product_id).first()


def get_products(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Product).filter(models.Product.is_active == True).offset(skip).limit(limit).all()


def create_product(db: Session, product: schemas.ProductCreate):
    # Check if SKU already exists
    existing = db.query(models.Product).filter(models.Product.sku == product.sku).first()
    if existing:
        raise ValueError(f"Product with SKU {product.sku} already exists")

    db_product = models.Product(
        name=product.name,
        description=product.description,
        price=product.price,
        stock_quantity=product.stock_quantity,
        category=product.category,
        sku=product.sku
    )
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    return db_product


def update_product(db: Session, product_id: int, product_update: schemas.ProductUpdate):
    db_product = get_product(db, product_id)
    if not db_product:
        return None

    # Update only provided fields
    if product_update.name is not None:
        db_product.name = product_update.name
    if product_update.price is not None:
        db_product.price = product_update.price
    if product_update.stock_quantity is not None:
        db_product.stock_quantity = product_update.stock_quantity
    if product_update.category is not None:
        db_product.category = product_update.category

    db.commit()
    db.refresh(db_product)
    return db_product


def delete_product(db: Session, product_id: int):
    db_product = get_product(db, product_id)
    if db_product:
        db_product.is_active = False  # Soft delete
        db.commit()
    return db_product


def search_products(db: Session, query: str):
    return db.query(models.Product).filter(
        or_(
            models.Product.name.ilike(f"%{query}%"),
            models.Product.description.ilike(f"%{query}%"),
            models.Product.sku.ilike(f"%{query}%")
        )
    ).filter(models.Product.is_active == True).all()


# Customer CRUD
def create_customer(db: Session, customer: schemas.CustomerCreate):
    db_customer = models.Customer(
        name=customer.name,
        phone=customer.phone,
        email=customer.email
    )
    db.add(db_customer)
    db.commit()
    db.refresh(db_customer)
    return db_customer


def get_customer(db: Session, customer_id: int):
    return db.query(models.Customer).filter(models.Customer.id == customer_id).first()


def get_customers(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Customer).offset(skip).limit(limit).all()


# Sales CRUD - FIXED AND UPDATED
def get_sale_items(db: Session, sale_id: int):
    """Get all items for a specific sale"""
    return db.query(models.SaleItem).filter(models.SaleItem.sale_id == sale_id).all()


def get_sale_with_items(db: Session, sale_id: int):
    """Get a sale with all its items"""
    return db.query(models.Sale) \
        .options(joinedload(models.Sale.items)) \
        .filter(models.Sale.id == sale_id) \
        .first()


def get_sales(db: Session, skip: int = 0, limit: int = 100):
    """Get all sales with customer information"""
    return db.query(models.Sale) \
        .options(joinedload(models.Sale.customer)) \
        .order_by(models.Sale.created_at.desc()) \
        .offset(skip) \
        .limit(limit) \
        .all()


def get_sale(db: Session, sale_id: int):
    """Get a specific sale with customer and items"""
    return db.query(models.Sale) \
        .options(joinedload(models.Sale.customer), joinedload(models.Sale.items)) \
        .filter(models.Sale.id == sale_id) \
        .first()


def get_sales_by_date(db: Session, sale_date: date):
    """Get sales for a specific date"""
    start_date = datetime.combine(sale_date, datetime.min.time())
    end_date = datetime.combine(sale_date, datetime.max.time())

    return db.query(models.Sale) \
        .filter(models.Sale.created_at.between(start_date, end_date)) \
        .options(joinedload(models.Sale.customer)) \
        .order_by(models.Sale.created_at.desc()) \
        .all()


def get_today_sales(db: Session):
    """Get today's sales"""
    today = date.today()
    return get_sales_by_date(db, today)


def create_sale(db: Session, sale_data: dict, items_data: List[dict]):
    """Create a new sale with items"""
    # Generate receipt number
    from datetime import datetime as dt
    import uuid

    today_str = dt.now().strftime('%Y%m%d')
    receipt_number = f"REC-{today_str}-{uuid.uuid4().hex[:8].upper()}"

    # Calculate totals
    subtotal = sum(item['subtotal'] for item in items_data)
    tax_amount = subtotal * 0.075  # 7.5% tax
    total_amount = subtotal + tax_amount

    # Create sale
    db_sale = models.Sale(
        receipt_number=receipt_number,
        customer_id=sale_data.get('customer_id'),
        subtotal=subtotal,
        tax_amount=tax_amount,
        discount_amount=sale_data.get('discount_amount', 0),
        total_amount=total_amount,
        amount_paid=sale_data.get('amount_paid', total_amount),
        change_given=sale_data.get('change_given', 0),
        payment_method=sale_data.get('payment_method', 'cash'),
        payment_status='completed',
        user_id=sale_data.get('user_id', 1)  # Default to admin user
    )

    db.add(db_sale)
    db.flush()  # Get the sale ID without committing

    # Create sale items
    for item in items_data:
        sale_item = models.SaleItem(
            sale_id=db_sale.id,
            product_id=item['product_id'],
            product_name=item.get('product_name', 'Product'),
            quantity=item['quantity'],
            unit_price=item['unit_price'],
            subtotal=item['subtotal']
        )
        db.add(sale_item)

        # Update product stock
        product = get_product(db, item['product_id'])
        if product:
            product.stock_quantity -= item['quantity']

    db.commit()
    db.refresh(db_sale)
    return db_sale


def get_sale_by_receipt_number(db: Session, receipt_number: str):
    """Get a sale by receipt number"""
    return db.query(models.Sale) \
        .options(joinedload(models.Sale.customer), joinedload(models.Sale.items)) \
        .filter(models.Sale.receipt_number == receipt_number) \
        .first()


def get_sales_summary(db: Session):
    """Get sales summary (total sales, today's sales, etc.)"""
    today = date.today()
    start_of_day = datetime.combine(today, datetime.min.time())
    end_of_day = datetime.combine(today, datetime.max.time())

    # Total sales
    total_sales_result = db.query(func.sum(models.Sale.total_amount)).scalar() or 0

    # Today's sales
    today_sales_result = db.query(func.sum(models.Sale.total_amount)) \
                             .filter(models.Sale.created_at.between(start_of_day, end_of_day)) \
                             .scalar() or 0

    # Total transactions
    total_transactions = db.query(func.count(models.Sale.id)).scalar() or 0

    # Today's transactions
    today_transactions = db.query(func.count(models.Sale.id)) \
                             .filter(models.Sale.created_at.between(start_of_day, end_of_day)) \
                             .scalar() or 0

    # Average sale
    average_sale = total_sales_result / total_transactions if total_transactions > 0 else 0

    return {
        'total_sales': total_sales_result,
        'today_sales': today_sales_result,
        'total_transactions': total_transactions,
        'today_transactions': today_transactions,
        'average_sale': average_sale
    }


def void_sale(db: Session, sale_id: int, void_reason: str = None):
    """Void a sale (mark as cancelled)"""
    sale = get_sale(db, sale_id)
    if not sale:
        return None

    # Check if sale is already voided
    if sale.payment_status == 'voided':
        return sale

    # Update sale status
    sale.payment_status = 'voided'
    sale.voided_at = datetime.now()
    sale.void_reason = void_reason

    # Restore product stock
    for item in sale.items:
        product = get_product(db, item.product_id)
        if product:
            product.stock_quantity += item.quantity

    db.commit()
    db.refresh(sale)
    return sale


# Inventory CRUD
def create_stock_movement(db: Session, movement: schemas.StockMovementCreate):
    # Update product stock
    product = get_product(db, movement.product_id)
    if not product:
        raise ValueError(f"Product {movement.product_id} not found")

    # Update stock quantity
    product.stock_quantity += movement.quantity

    # Create movement record
    db_movement = models.StockMovement(
        product_id=movement.product_id,
        quantity=movement.quantity,
        movement_type=movement.movement_type,
        reference=movement.reference,
        notes=movement.notes,
        created_by=movement.created_by
    )
    db.add(db_movement)
    db.commit()
    db.refresh(db_movement)
    return db_movement


def get_stock_movements(db: Session, product_id: Optional[int] = None, skip: int = 0, limit: int = 100):
    query = db.query(models.StockMovement)
    if product_id:
        query = query.filter(models.StockMovement.product_id == product_id)

    return query.order_by(models.StockMovement.created_at.desc()).offset(skip).limit(limit).all()


def get_low_stock_products(db: Session):
    return db.query(models.Product).filter(
        models.Product.stock_quantity <= models.Product.min_stock_level,
        models.Product.is_active == True
    ).all()


def get_inventory_report(db: Session):
    products = db.query(models.Product).filter(models.Product.is_active == True).all()

    report = []
    for product in products:
        # Get latest movement
        latest_movement = db.query(models.StockMovement).filter(
            models.StockMovement.product_id == product.id
        ).order_by(models.StockMovement.created_at.desc()).first()

        # Determine status
        if product.stock_quantity <= 0:
            status = "OUT"
        elif product.stock_quantity <= product.min_stock_level:
            status = "LOW"
        else:
            status = "OK"

        report.append({
            "product_id": product.id,
            "product_name": product.name,
            "current_stock": product.stock_quantity,
            "min_stock_level": product.min_stock_level,
            "total_value": product.stock_quantity * product.price,
            "status": status,
            "last_movement": latest_movement.created_at if latest_movement else None
        })

    return report


def update_stock_level(db: Session, product_id: int, new_min_level: int):
    product = get_product(db, product_id)
    if not product:
        return None

    product.min_stock_level = new_min_level
    db.commit()
    db.refresh(product)
    return product


# User CRUD
def create_user(db: Session, user: schemas.UserCreate):
    from app.auth import get_password_hash

    hashed_password = get_password_hash(user.password)
    db_user = models.User(
        username=user.username,
        full_name=user.full_name,
        email=user.email,
        hashed_password=hashed_password,
        role=user.role
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def get_user(db: Session, user_id: int):
    return db.query(models.User).filter(models.User.id == user_id).first()


def get_user_by_username(db: Session, username: str):
    return db.query(models.User).filter(models.User.username == username).first()


def get_users(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.User).offset(skip).limit(limit).all()


# Add the missing create_sale_with_items function (fixed version)
def create_sale_with_items(db: Session, sale_data: dict, cart_items: List[dict]):
    """Create a sale with all items"""
    # Generate receipt number
    today = datetime.now()
    receipt_prefix = today.strftime('REC-%Y%m%d-')

    # Get last receipt number for today
    last_sale = db.query(models.Sale).filter(
        models.Sale.receipt_number.like(f'{receipt_prefix}%')
    ).order_by(models.Sale.receipt_number.desc()).first()

    if last_sale:
        last_num = int(last_sale.receipt_number.split('-')[-1])
        receipt_number = f'{receipt_prefix}{last_num + 1:04d}'
    else:
        receipt_number = f'{receipt_prefix}0001'

    # Calculate totals
    subtotal = sum(item['subtotal'] for item in cart_items)
    tax_rate = 0.075  # 7.5%
    tax_amount = subtotal * tax_rate
    total_amount = subtotal + tax_amount

    # Get payment details
    amount_paid = sale_data.get('amount_paid', total_amount)
    change_given = amount_paid - total_amount if amount_paid > total_amount else 0

    # Create sale
    sale = models.Sale(
        receipt_number=receipt_number,
        user_id=sale_data.get('user_id', 1),
        customer_id=sale_data.get('customer_id'),
        subtotal=subtotal,
        tax_amount=tax_amount,
        discount_amount=sale_data.get('discount_amount', 0),
        total_amount=total_amount,
        amount_paid=amount_paid,
        change_given=change_given,
        payment_method=sale_data.get('payment_method', 'cash'),
        status='completed'
    )

    db.add(sale)
    db.flush()  # Get the sale ID without committing

    # Add sale items
    for item in cart_items:
        sale_item = models.SaleItem(
            sale_id=sale.id,
            product_id=item['product_id'],
            quantity=item['quantity'],
            unit_price=item['price'],
            subtotal=item['subtotal']
        )
        db.add(sale_item)

        # Update product stock
        product = get_product(db, item['product_id'])
        if product:
            product.stock_quantity -= item['quantity']

    db.commit()
    db.refresh(sale)
    return sale