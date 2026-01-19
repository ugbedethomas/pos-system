# fix_product_modal.py
import os
import re

print("🔧 Applying comprehensive modal scroll fix...")

products_path = 'templates/products.html'
if not os.path.exists(products_path):
    print(f"❌ {products_path} not found")
    exit(1)

with open(products_path, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Find and replace the modal
modal_pattern = r'<!-- Add Product Modal -->.*?</div>\s*</div>\s*</div>'
new_modal = '''<!-- Add Product Modal -->
<div class="modal fade" id="addProductModal" tabindex="-1" role="dialog" aria-labelledby="addProductModalLabel" aria-hidden="true">
    <div class="modal-dialog modal-dialog-scrollable modal-lg" role="document">
        <div class="modal-content">
            <div class="modal-header bg-primary text-white">
                <h5 class="modal-title" id="addProductModalLabel">
                    <i class="fas fa-plus-circle mr-2"></i>Add New Product
                </h5>
                <button type="button" class="close text-white" data-dismiss="modal" aria-label="Close">
                    <span aria-hidden="true">&times;</span>
                </button>
            </div>

            <form id="addProductForm" method="POST" action="/products/create">
                <div class="modal-body" style="max-height: 65vh; overflow-y: auto;">
                    <div class="row">
                        <div class="col-md-6">
                            <h6 class="text-primary mb-3 border-bottom pb-2">
                                <i class="fas fa-info-circle mr-1"></i> Basic Information
                            </h6>

                            <div class="form-group">
                                <label for="productName" class="font-weight-bold">
                                    Product Name <span class="text-danger">*</span>
                                </label>
                                <input type="text" class="form-control" id="productName" name="name" required>
                            </div>

                            <div class="form-group">
                                <label for="productSKU" class="font-weight-bold">
                                    SKU <span class="text-danger">*</span>
                                </label>
                                <input type="text" class="form-control" id="productSKU" name="sku" required>
                            </div>

                            <div class="form-group">
                                <label for="productBarcode" class="font-weight-bold">
                                    Barcode <small class="text-muted">(Optional)</small>
                                </label>
                                <input type="text" class="form-control" id="productBarcode" name="barcode">
                            </div>

                            <div class="form-group">
                                <label for="productCategory" class="font-weight-bold">Category</label>
                                <input type="text" class="form-control" id="productCategory" name="category" value="Uncategorized">
                            </div>
                        </div>

                        <div class="col-md-6">
                            <h6 class="text-primary mb-3 border-bottom pb-2">
                                <i class="fas fa-money-bill-wave mr-1"></i> Pricing & Stock
                            </h6>

                            <div class="form-group">
                                <label for="productPrice" class="font-weight-bold">
                                    Selling Price (₦) <span class="text-danger">*</span>
                                </label>
                                <input type="number" class="form-control" id="productPrice" name="price" step="0.01" required>
                            </div>

                            <div class="form-group">
                                <label for="productCost" class="font-weight-bold">
                                    Cost Price (₦) <small class="text-muted">(Optional)</small>
                                </label>
                                <input type="number" class="form-control" id="productCost" name="cost_price" step="0.01" value="0">
                            </div>

                            <div class="form-group">
                                <label for="productStock" class="font-weight-bold">Initial Stock</label>
                                <input type="number" class="form-control" id="productStock" name="stock_quantity" value="0">
                            </div>

                            <div class="form-group">
                                <label for="productReorder" class="font-weight-bold">Reorder Level</label>
                                <input type="number" class="form-control" id="productReorder" name="reorder_level" value="10">
                            </div>
                        </div>
                    </div>

                    <div class="row mt-3">
                        <div class="col-12">
                            <h6 class="text-primary mb-3 border-bottom pb-2">
                                <i class="fas fa-align-left mr-1"></i> Additional Information
                            </h6>

                            <div class="form-group">
                                <label for="productDescription" class="font-weight-bold">Description</label>
                                <textarea class="form-control" id="productDescription" name="description" rows="3"></textarea>
                            </div>
                        </div>
                    </div>
                </div>

                <div class="modal-footer sticky-bottom bg-light border-top">
                    <button type="button" class="btn btn-secondary" data-dismiss="modal">
                        <i class="fas fa-times mr-1"></i> Cancel
                    </button>
                    <button type="submit" class="btn btn-primary">
                        <i class="fas fa-save mr-1"></i> Save Product
                    </button>
                </div>
            </form>
        </div>
    </div>
</div>'''

# Replace the modal
if re.search(modal_pattern, content, re.DOTALL):
    content = re.sub(modal_pattern, new_modal, content, flags=re.DOTALL)
    print("✅ Updated modal structure")
else:
    print("⚠️ Could not find existing modal, adding new one")
    # Insert before closing body tag
    if '</body>' in content:
        content = content.replace('</body>', new_modal + '\n</body>')

# 2. Add CSS
css_fix = '''
<style>
/* Modal Scroll Fix */
.modal-dialog-scrollable .modal-content { max-height: 85vh; display: flex; flex-direction: column; }
.modal-dialog-scrollable .modal-body { overflow-y: auto; flex: 1 1 auto; }
.modal-footer.sticky-bottom { position: sticky; bottom: 0; background: white; z-index: 1050; }
@media (max-width: 768px) { .modal-body { max-height: 60vh !important; } }
</style>
'''

if '</head>' in content:
    content = content.replace('</head>', css_fix + '\n</head>')
    print("✅ Added CSS fixes")

# 3. Add minimal JavaScript
js_fix = '''
<script>
$(document).ready(function() {
    $('#addProductModal').on('shown.bs.modal', function() {
        $('#productName').focus();
        if (!$('#productSKU').val()) {
            $('#productSKU').val('PROD-' + Date.now().toString().slice(-6));
        }
    });

    // Ctrl+Enter to save
    $(document).on('keydown', '#addProductModal input, #addProductModal textarea', function(e) {
        if (e.ctrlKey && e.keyCode === 13) {
            e.preventDefault();
            $('#addProductForm').submit();
        }
    });
});
</script>
'''

if '</body>' in content:
    content = content.replace('</body>', js_fix + '\n</body>')
    print("✅ Added JavaScript enhancements")

# Save the file
with open(products_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("\n🎉 COMPREHENSIVE FIX APPLIED!")
print("\n✅ The modal now has:")
print("   - Scrollable content area")
print("   - Always-visible save button (sticky footer)")
print("   - Two-column layout for better organization")
print("   - Responsive design")
print("   - Keyboard shortcuts (Ctrl+Enter to save)")
print("\n🔄 Refresh the products page to see changes!")