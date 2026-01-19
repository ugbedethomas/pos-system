# fix_duplicate_route.py
import os

print("🔧 Fixing duplicate complete_sale route...")

web_server_path = 'web_server.py'
if not os.path.exists(web_server_path):
    print("❌ web_server.py not found")
    exit(1)

with open(web_server_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Find all complete_sale definitions
complete_sale_lines = []
for i, line in enumerate(lines):
    if 'def complete_sale' in line:
        complete_sale_lines.append(i)
    if '@app.route' in line and 'complete' in line and 'sales' in line:
        print(f"Route at line {i + 1}: {line.strip()}")

print(f"\nFound {len(complete_sale_lines)} complete_sale functions")

if len(complete_sale_lines) > 1:
    print("⚠️ Multiple complete_sale functions found!")

    # Keep the last one, comment out or remove earlier ones
    for i in range(len(complete_sale_lines) - 1):
        line_num = complete_sale_lines[i]
        print(f"Commenting out duplicate at line {line_num + 1}")

        # Find the start of the function
        start = line_num
        while start > 0 and not lines[start - 1].strip().startswith('@app.route'):
            start -= 1

        # Comment out the route and function
        for j in range(start, line_num + 1):
            if lines[j].strip() and not lines[j].strip().startswith('#'):
                lines[j] = '# ' + lines[j]

        # Also need to find the end of the function
        end = line_num + 1
        indent = len(lines[line_num]) - len(lines[line_num].lstrip())
        while end < len(lines):
            current_indent = len(lines[end]) - len(lines[end].lstrip()) if lines[end].strip() else 0
            if current_indent <= indent and lines[end].strip():
                break
            if lines[end].strip() and not lines[end].strip().startswith('#'):
                lines[end] = '# ' + lines[end]
            end += 1

    with open(web_server_path, 'w', encoding='utf-8') as f:
        f.writelines(lines)

    print("✅ Fixed duplicate routes")
else:
    print("✅ Only one complete_sale function found")

print("\n✅ Done. Restart your server.")