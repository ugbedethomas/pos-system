# fix_templates.py
import os

print("=" * 60)
print("🛠️  Fixing Template Files")
print("=" * 60)

# Fix all template files
template_dir = 'templates'
files_to_fix = ['inventory.html', 'products.html', 'dashboard.html']

for filename in files_to_fix:
    filepath = os.path.join(template_dir, filename)
    if os.path.exists(filepath):
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()

            if 'min_stock_level' in content:
                new_content = content.replace('min_stock_level', 'reorder_level')
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(new_content)
                print(f"✅ Fixed {filename}")
            else:
                print(f"✓ {filename} already uses reorder_level")
        except UnicodeDecodeError:
            # Try with different encoding
            try:
                with open(filepath, 'r', encoding='latin-1') as f:
                    content = f.read()

                if 'min_stock_level' in content:
                    new_content = content.replace('min_stock_level', 'reorder_level')
                    with open(filepath, 'w', encoding='utf-8') as f:
                        f.write(new_content)
                    print(f"✅ Fixed {filename} (latin-1 encoding)")
                else:
                    print(f"✓ {filename} already uses reorder_level")
            except Exception as e:
                print(f"⚠️ Could not read {filename}: {e}")
    else:
        print(f"⚠️ {filename} not found")

# Also fix crud.py with proper encoding
print("\n📝 Fixing crud.py...")
crud_path = 'app/crud.py'
if os.path.exists(crud_path):
    try:
        with open(crud_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except UnicodeDecodeError:
        with open(crud_path, 'r', encoding='latin-1') as f:
            content = f.read()

    if 'min_stock_level' in content:
        new_content = content.replace('min_stock_level', 'reorder_level')
        with open(crud_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print("✅ Fixed crud.py")
    else:
        print("✓ crud.py already uses reorder_level")
else:
    print("⚠️ crud.py not found")

print("\n" + "=" * 60)
print("🎉 Template fixes complete! Restart your server.")
print("=" * 60)