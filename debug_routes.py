# debug_routes.py
from flask import Flask, render_template_string, jsonify
import sys
import os

# Add the current directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

app = Flask(__name__)


@app.route('/')
def index():
    return "Debug server is running"


@app.route('/minimal-test')
def minimal_test():
    """Minimal test to check template rendering"""
    # Test data - IMPORTANT: Use a different key name than 'items'
    receipt_data = {
        'receipt_number': 'TEST-001',
        'items_list': [  # Changed from 'items' to 'items_list'
            {'name': 'Item 1', 'quantity': 1, 'price': 10.0, 'total': 10.0},
            {'name': 'Item 2', 'quantity': 2, 'price': 5.0, 'total': 10.0}
        ]
    }

    # Simple template string to test
    template = """
    <!DOCTYPE html>
    <html>
    <body>
        <h1>Testing iteration</h1>
        <ul>
        {% for item in receipt_data.items_list %}
            <li>{{ item.name }} - {{ item.quantity }} x ${{ item.price }}</li>
        {% endfor %}
        </ul>
        <p>Total items: {{ receipt_data.items_list|length }}</p>
    </body>
    </html>
    """

    return render_template_string(template, receipt_data=receipt_data)


@app.route('/test-issue')
def test_issue():
    """Test to demonstrate the 'items' conflict"""
    # The issue: 'items' is a built-in dictionary method!
    test_dict = {'key': 'value'}
    print(f"Type of dict.items: {type(test_dict.items)}")
    print(f"Dict.items is callable: {callable(test_dict.items)}")

    # This is what's happening in your template
    receipt = {
        'receipt_number': 'TEST-001',
        'items': [  # This conflicts with dict.items() method!
            {'name': 'Item 1', 'quantity': 1}
        ]
    }

    template = """
    <html>
    <body>
        <h1>Understanding the Issue</h1>
        <p>In Python, dictionaries have an .items() method.</p>
        <p>When Jinja2 sees 'receipt.items', it might access the method, not your data.</p>
        <p>Type of receipt.items in template: {{ receipt.items.__class__.__name__ }}</p>
        <p>Is it callable? {{ receipt.items is callable }}</p>

        <h2>Solution 1: Use a different key name</h2>
        {% for item in receipt.item_list %}
            <li>{{ item.name }}</li>
        {% endfor %}

        <h2>Solution 2: Access as dictionary key</h2>
        {% for item in receipt['items'] %}
            <li>{{ item.name }}</li>
        {% endfor %}
    </body>
    </html>
    """

    # Use bracket notation in the data
    receipt_fixed = {
        'receipt_number': 'TEST-001',
        'item_list': [{'name': 'Item 1', 'quantity': 1}],
        'items': [{'name': 'Item 2', 'quantity': 2}]  # Still has conflict
    }

    return render_template_string(template, receipt=receipt_fixed)


@app.route('/working-receipt')
def working_receipt():
    """A working receipt example"""
    receipt = {
        'receipt_number': 'WORKING-001',
        'receipt_items': [  # Different key name!
            {'name': 'Product A', 'quantity': 2, 'price': 25.0, 'total': 50.0},
            {'name': 'Product B', 'quantity': 1, 'price': 15.5, 'total': 15.5}
        ],
        'total_amount': 65.5,
        'payment_method': 'cash'
    }

    template = """
    <!DOCTYPE html>
    <html>
    <head><title>Working Receipt</title></head>
    <body>
        <h1>Receipt: {{ receipt.receipt_number }}</h1>
        <table border="1">
            <tr>
                <th>Item</th>
                <th>Qty</th>
                <th>Price</th>
                <th>Total</th>
            </tr>
            {% for item in receipt.receipt_items %}
            <tr>
                <td>{{ item.name }}</td>
                <td>{{ item.quantity }}</td>
                <td>${{ item.price }}</td>
                <td>${{ item.total }}</td>
            </tr>
            {% endfor %}
        </table>
        <h3>Total: ${{ receipt.total_amount }}</h3>
        <p>Payment: {{ receipt.payment_method }}</p>
    </body>
    </html>
    """

    return render_template_string(template, receipt=receipt)


@app.route('/debug-all-routes')
def debug_all_routes():
    """Show all registered routes"""
    routes = []
    for rule in app.url_map.iter_rules():
        routes.append({
            'endpoint': rule.endpoint,
            'rule': str(rule),
            'methods': list(rule.methods - {'OPTIONS', 'HEAD'})
        })
    return jsonify(routes)


if __name__ == '__main__':
    print("Starting debug server on http://localhost:5001")
    print("Test these URLs:")
    print("  http://localhost:5001/minimal-test")
    print("  http://localhost:5001/test-issue")
    print("  http://localhost:5001/working-receipt")
    app.run(debug=True, port=5001)