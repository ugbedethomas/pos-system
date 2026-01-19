# fix_modal_scroll.py
import os

print("🔧 Fixing product modal scroll issue...")

# Path to products.html
products_path = 'templates/products.html'

if not os.path.exists(products_path):
    print(f"❌ {products_path} not found")
    exit(1)

with open(products_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Add CSS for modal scrolling
css_fix = '''
<style>
/* Modal scroll fix */
#addProductModal .modal-dialog {
    max-width: 800px;
    margin: 30px auto;
}

#addProductModal .modal-content {
    max-height: 85vh;
    overflow-y: auto;
}

#addProductModal .modal-body {
    max-height: 65vh;
    overflow-y: auto;
    padding-right: 15px;
}

/* Make form more compact */
#addProductModal .form-group {
    margin-bottom: 10px;
}

#addProductModal .form-control {
    padding: 6px 10px;
    font-size: 14px;
}

#addProductModal label {
    font-size: 13px;
    margin-bottom: 3px;
    font-weight: 500;
}

/* Save button always visible */
#addProductModal .modal-footer {
    position: sticky;
    bottom: 0;
    background: white;
    border-top: 1px solid #dee2e6;
    padding: 10px 15px;
}
</style>
'''

# Add the CSS fix before closing </head> tag
if '</head>' in content:
    new_content = content.replace('</head>', css_fix + '\n</head>')

    with open(products_path, 'w', encoding='utf-8') as f:
        f.write(new_content)

    print("✅ Added modal scroll CSS fix")

    # Also add JavaScript for auto-scroll
    js_fix = '''
    <script>
    // Auto-scroll to save button when modal opens
    $(document).ready(function() {
        $('#addProductModal').on('shown.bs.modal', function() {
            var $modal = $(this);
            var $body = $modal.find('.modal-body');

            // Scroll to bottom after short delay
            setTimeout(function() {
                $body.scrollTop($body[0].scrollHeight);

                // Or focus on save button
                $modal.find('.btn-primary').focus();
            }, 300);
        });

        // Keyboard shortcut: Ctrl+Enter to save
        $(document).on('keydown', '#addProductModal input, #addProductModal textarea', function(e) {
            if (e.ctrlKey && e.keyCode === 13) { // Ctrl+Enter
                $('#addProductModal .btn-primary').click();
                e.preventDefault();
            }
        });
    });
    </script>
    '''

    # Add JavaScript before closing </body> tag
    if '</body>' in new_content:
        new_content_with_js = new_content.replace('</body>', js_fix + '\n</body>')

        with open(products_path, 'w', encoding='utf-8') as f:
            f.write(new_content_with_js)

        print("✅ Added auto-scroll JavaScript")
else:
    print("⚠️ Could not find </head> tag")

print("\n✅ Fix applied. Refresh the products page.")
print("\n💡 Tip: Press Ctrl+Enter in any form field to save quickly!")