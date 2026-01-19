# fix_modal_scroll_simple.py
import os

print("🔧 Fixing modal scroll while keeping your layout...")

products_path = 'templates/products.html'
if not os.path.exists(products_path):
    print(f"❌ {products_path} not found")
    exit(1)

with open(products_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Add minimal CSS fix
css_fix = '''
<style>
/* Simple modal scroll fix - keeps your existing layout */
#addProductModal .modal-dialog {
    max-width: 700px;
}

#addProductModal .modal-content {
    max-height: 90vh;
}

#addProductModal .modal-body {
    max-height: 70vh;
    overflow-y: auto;
    padding-right: 15px; /* Space for scrollbar */
}

/* Make sure footer is visible */
#addProductModal .modal-footer {
    position: sticky;
    bottom: 0;
    background: white;
    border-top: 1px solid #dee2e6;
    padding: 15px;
}
</style>
'''

# Add minimal JavaScript
js_fix = '''
<script>
// Simple fix: scroll to bottom when modal opens
$(document).ready(function() {
    $('#addProductModal').on('shown.bs.modal', function() {
        var $body = $(this).find('.modal-body');
        setTimeout(function() {
            $body.scrollTop($body[0].scrollHeight);
        }, 100);
    });

    // Quick save with Ctrl+Enter
    $(document).on('keydown', '#addProductModal input', function(e) {
        if (e.ctrlKey && e.key === 'Enter') {
            $('#addProductModal .btn-primary').click();
        }
    });
});
</script>
'''

# Insert CSS before </head>
if '</head>' in content:
    content = content.replace('</head>', css_fix + '\n</head>')
    print("✅ Added CSS scroll fix")

# Insert JS before </body>
if '</body>' in content:
    content = content.replace('</body>', js_fix + '\n</body>')
    print("✅ Added JavaScript helpers")

# Also update modal-dialog to be scrollable
if 'class="modal-dialog"' in content:
    content = content.replace('class="modal-dialog"', 'class="modal-dialog modal-dialog-scrollable"')
    print("✅ Added scrollable class to modal")

with open(products_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("\n✅ FIX APPLIED!")
print("Your modal will now:")
print("1. Scroll when content is too tall")
print("2. Keep Save button visible at bottom")
print("3. Auto-scroll to bottom when opened")
print("4. Allow Ctrl+Enter to save quickly")
print("\n🔄 Refresh the Products page!")