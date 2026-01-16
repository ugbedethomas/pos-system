"""
Company settings for Nigerian POS System
Update these with your actual business details
"""

COMPANY_SETTINGS = {
    "name": "Your Business Name",
    "address": "123 Business Street, Lagos, Nigeria",
    "phone": "+234 812 345 6789",
    "email": "info@yourbusiness.com",
    "tax_id": "VAT-123456789",
    "currency": "₦",
    "currency_code": "NGN",
    "tax_rate": 0.075,  # 7.5% VAT in Nigeria
    "receipt_footer": "Thank you for your patronage!\nGoods sold are not returnable\nVAT Inclusive: 7.5%",
    "bank_details": {
        "name": "Your Business Name",
        "bank": "Access Bank",
        "account_number": "1234567890",
        "account_type": "Current"
    }
}

# Payment methods for Nigeria
PAYMENT_METHODS = [
    {"id": "cash", "name": "Cash", "icon": "fa-money-bill-wave"},
    {"id": "transfer", "name": "Bank Transfer", "icon": "fa-university"},
    {"id": "pos", "name": "POS Card", "icon": "fa-credit-card"},
    {"id": "mobile", "name": "Mobile Money", "icon": "fa-mobile-alt"}
]

# Thermal printer settings (if using)
PRINTER_SETTINGS = {
    "enabled": False,
    "port": "COM3",  # or "/dev/ttyUSB0" on Linux
    "baudrate": 9600,
    "receipt_width": 48,
    "company_logo": None  # Path to logo file
}