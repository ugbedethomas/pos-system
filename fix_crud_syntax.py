# fix_crud_syntax.py
import os

print("🔧 Fixing crud.py syntax error...")

crud_path = 'app/crud.py'
if os.path.exists(crud_path):
    with open(crud_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    # Look for line 361 (actually line 360 in zero-index)
    for i, line in enumerate(lines):
        if i >= 358 and i <= 363:  # Check around line 361
            print(f"Line {i + 1}: {line.rstrip()}")

    # Find and fix the issue
    for i in range(len(lines)):
        if 'models.Product.stock_quantity <= models.Product.reorder_level' in lines[i]:
            # Check if it has a comma
            if not lines[i].strip().endswith(','):
                print(f"\n⚠️ Found syntax error at line {i + 1}")
                print(f"Before: {lines[i].rstrip()}")
                lines[i] = lines[i].rstrip() + ',\n'
                print(f"After:  {lines[i].rstrip()}")

                with open(crud_path, 'w', encoding='utf-8') as f:
                    f.writelines(lines)

                print("✅ Added missing comma!")
                break

    print("\n✅ Syntax should be fixed now.")
else:
    print(f"❌ Could not find {crud_path}")