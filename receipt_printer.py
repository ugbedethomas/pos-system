import os
from datetime import datetime


def print_receipt_nigeria(sale, company_settings, products_db):
    """
    Generate receipt text for Nigerian thermal printer
    """
    receipt = []

    # Company header
    receipt.append(" " * 16 + company_settings["name"])
    receipt.append("=" * 48)
    receipt.append(company_settings["address"])
    receipt.append(f"Tel: {company_settings['phone']}")
    receipt.append(f"Email: {company_settings['email']}")
    receipt.append(f"Tax ID: {company_settings['tax_id']}")
    receipt.append("=" * 48)

    # Sale info
    receipt.append(f"Receipt: {sale.receipt_number}")
    receipt.append(f"Date: {sale.created_at.strftime('%d/%m/%Y %H:%M:%S')}")
    receipt.append(f"Cashier: {sale.cashier or 'System'}")
    receipt.append("-" * 48)

    # Items
    receipt.append(f"{'Item':<20} {'Qty':>6} {'Price':>10} {'Total':>10}")
    receipt.append("-" * 48)

    for item in sale.items:
        product = next((p for p in products_db if p.id == item.product_id), None)
        name = product.name[:20] if product else f"Product {item.product_id}"
        receipt.append(
            f"{name:<20} {item.quantity:>6} {format_naira(item.unit_price):>10} {format_naira(item.subtotal):>10}")

    receipt.append("-" * 48)

    # Totals
    receipt.append(f"{'Subtotal:':<36} {format_naira(sale.total_amount - sale.tax_amount):>10}")
    receipt.append(f"{'VAT (7.5%):':<36} {format_naira(sale.tax_amount):>10}")
    receipt.append(f"{'Total:':<36} {format_naira(sale.total_amount):>10}")

    # Payment
    receipt.append(f"Payment: {sale.payment_method.upper()}")
    if sale.payment_method == 'transfer' and sale.transfer_reference:
        receipt.append(f"Ref: {sale.transfer_reference}")

    receipt.append("=" * 48)

    # Footer
    receipt.append(company_settings["receipt_footer"])
    receipt.append(" " * 16 + "*** THANK YOU ***")

    return "\n".join(receipt)


def format_naira(amount):
    """Format amount as Nigerian Naira"""
    return f"₦{amount:,.2f}"


def save_receipt_to_file(receipt_text, filename=None):
    """Save receipt to file (can be sent to printer)"""
    if not filename:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"receipts/receipt_{timestamp}.txt"

    os.makedirs("receipts", exist_ok=True)

    with open(filename, 'w', encoding='utf-8') as f:
        f.write(receipt_text)

    print(f"✅ Receipt saved to: {filename}")
    return filename