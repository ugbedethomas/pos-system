from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List


# Product schemas
class ProductBase(BaseModel):
    name: str
    description: Optional[str] = None
    price: float
    stock_quantity: int = 0
    category: Optional[str] = "Uncategorized"
    sku: str


class ProductCreate(ProductBase):
    pass


class ProductUpdate(BaseModel):
    name: Optional[str] = None
    price: Optional[float] = None
    stock_quantity: Optional[int] = None
    category: Optional[str] = None


class Product(ProductBase):
    id: int
    is_active: bool
    created_at: datetime

    class Config:
        orm_mode = True


# Customer schemas
class CustomerBase(BaseModel):
    name: str
    phone: Optional[str] = None
    email: Optional[str] = None


class CustomerCreate(CustomerBase):
    pass


class Customer(CustomerBase):
    id: int
    created_at: datetime

    class Config:
        orm_mode = True


# Sale Item schemas
class SaleItemBase(BaseModel):
    product_id: int
    quantity: int


class SaleItemCreate(SaleItemBase):
    pass


class SaleItem(SaleItemBase):
    id: int
    unit_price: float
    subtotal: float
    sale_id: int

    class Config:
        orm_mode = True


# Sale schemas
class SaleBase(BaseModel):
    customer_id: Optional[int] = None
    payment_method: str = "cash"
    items: List[SaleItemCreate]


class SaleCreate(SaleBase):
    pass


class Sale(SaleBase):
    id: int
    receipt_number: str
    total_amount: float
    tax_amount: float
    discount_amount: float
    payment_status: str
    created_at: datetime
    items: List[SaleItem]

    class Config:
        orm_mode = True


# User schemas
class UserBase(BaseModel):
    username: str
    full_name: str
    email: str
    role: str


class UserCreate(UserBase):
    password: str


class UserLogin(BaseModel):
    username: str
    password: str


class User(UserBase):
    id: int
    is_active: bool
    created_at: datetime
    last_login: Optional[datetime]

    class Config:
        orm_mode = True


class Token(BaseModel):
    access_token: str
    token_type: str
    user: User


# Inventory schemas
class StockMovementBase(BaseModel):
    product_id: int
    quantity: int
    movement_type: str  # 'purchase', 'sale', 'adjustment', 'return'
    reference: Optional[str] = None
    notes: Optional[str] = None
    created_by: Optional[str] = "system"


class StockMovementCreate(StockMovementBase):
    pass


class StockMovement(StockMovementBase):
    id: int
    created_at: datetime

    class Config:
        orm_mode = True


class InventoryReport(BaseModel):
    product_id: int
    product_name: str
    current_stock: int
    min_stock_level: int = 10
    total_value: float
    status: str  # 'OK', 'LOW', 'OUT'
    last_movement: Optional[datetime] = None