from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(String(500))
    price = Column(Float, nullable=False)
    stock_quantity = Column(Integer, default=0)
    category = Column(String(100), default="Uncategorized")
    sku = Column(String(50), unique=True)
    created_at = Column(DateTime, default=func.now())
    is_active = Column(Boolean, default=True)
    min_stock_level = Column(Integer, default=10)

    # Relationship to sale items
    sale_items = relationship("SaleItem", back_populates="product")


class Customer(Base):
    __tablename__ = "customers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255))
    phone = Column(String(50))
    email = Column(String(255))
    created_at = Column(DateTime, default=func.now())

    # Relationship to sales
    sales = relationship("Sale", back_populates="customer")


class Sale(Base):
    __tablename__ = "sales"

    id = Column(Integer, primary_key=True, index=True)
    receipt_number = Column(String(100), unique=True, index=True)
    total_amount = Column(Float, nullable=False)
    tax_amount = Column(Float, default=0)
    discount_amount = Column(Float, default=0)
    payment_method = Column(String(50))  # cash, card, mobile
    payment_status = Column(String(50), default="completed")  # completed, pending, cancelled
    customer_id = Column(Integer, ForeignKey("customers.id"))
    created_at = Column(DateTime, default=func.now())

    # Relationships
    customer = relationship("Customer", back_populates="sales")
    items = relationship("SaleItem", back_populates="sale")


class SaleItem(Base):
    __tablename__ = "sale_items"

    id = Column(Integer, primary_key=True, index=True)
    sale_id = Column(Integer, ForeignKey("sales.id"))
    product_id = Column(Integer, ForeignKey("products.id"))
    quantity = Column(Integer, nullable=False)
    unit_price = Column(Float, nullable=False)
    subtotal = Column(Float, nullable=False)

    # Relationships
    sale = relationship("Sale", back_populates="items")
    product = relationship("Product", back_populates="sale_items")


class StockMovement(Base):
    __tablename__ = "stock_movements"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"))
    quantity = Column(Integer, nullable=False)  # Positive = added, Negative = sold
    movement_type = Column(String(50))  # 'purchase', 'sale', 'adjustment', 'return'
    reference = Column(String(100))  # sale_id, purchase_order, etc.
    notes = Column(String(500))
    created_at = Column(DateTime, default=func.now())
    created_by = Column(String(100), default="system")

    # Relationship
    product = relationship("Product")


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False)
    full_name = Column(String(100))
    email = Column(String(100), unique=True)
    hashed_password = Column(String(255), nullable=False)
    role = Column(String(20))  # admin, cashier, inventory
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=func.now())
    last_login = Column(DateTime)