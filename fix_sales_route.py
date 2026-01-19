# fix_sales_route.py
import os

print("🔧 Fixing sales/complete endpoint...")

# Check if route exists in web_server.py
web_server_path = 'web_server.py'
if os.path.exists(web_server_path):
    with open(web_server_path, 'r', encoding='utf-8') as f:
        content = f.read()

    if "@app.route('/sales/complete'" in content or '@app.route("/sales/complete"' in content:
        print("✅ /sales/complete route exists")
    else:
        print("❌ /sales/complete route NOT found")

        # Add the route
        route_code = '''@app.route('/sales/complete', methods=['POST'])
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
        amount_paid = float(data.get('amount_paid', total))  # Default to total if not specified

        if amount_paid < total:
            return jsonify({
                'success': False,
                'message': f'Insufficient payment. Total: ₦{total:,.2f}'
            }), 400

        change_given = amount_paid - total if amount_paid > total else 0
        receipt_number = f'REC-{datetime.now().strftime("%Y%m%d%H%M%S")}'

        # Create sale
        sale = models.Sale(
            receipt_number=receipt_number,
            total_amount=total,
            tax_amount=tax,
            discount_amount=discount_amount,
            amount_paid=amount_paid,
            change_amount=change_given,
            payment_method=payment_method,
            payment_status="completed",
            customer_id=data.get('customer_id'),
            user_id=session.get('user_id')
        )

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
        session.pop('cart', None)

        return jsonify({
            'success': True,
            'message': 'Sale completed!',
            'sale_id': sale.id,
            'receipt_number': receipt_number,
            'total': total,
            'change': change_given
        })

    except Exception as e:
        db.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        db.close()'''

        # Find where to insert (before the last routes)
        lines = content.split('\n')
        inserted = False
        for i, line in enumerate(lines):
            if "if __name__ ==" in line and "'__main__'" in line:
                lines.insert(i, route_code)
                inserted = True
                break

        if not inserted:
            # Insert before the last few lines
            lines.insert(-5, route_code)

        with open(web_server_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))

        print("✅ Added /sales/complete route")
else:
    print("❌ web_server.py not found")

print("\n✅ Fix applied. Restart your server.")