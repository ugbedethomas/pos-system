import os
import re


def update_file_for_naira(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # Replace $ with ₦
    content = content.replace('$', '₦')

    # Replace USD with NGN
    content = content.replace('USD', 'NGN')

    # Replace "dollar" with "naira" (case insensitive)
    content = re.sub(r'\bdollar(s)?\b', r'naira\1', content, flags=re.IGNORECASE)

    # Update currency in templates
    content = content.replace('"%.2f"|format(', 'format_naira(')

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

    return content.count('₦')


print("🔄 Updating templates for Nigerian Naira...")

templates_dir = "templates"
updated_files = 0
total_replacements = 0

for filename in os.listdir(templates_dir):
    if filename.endswith('.html'):
        filepath = os.path.join(templates_dir, filename)
        replacements = update_file_for_naira(filepath)
        updated_files += 1
        total_replacements += replacements
        print(f"✅ {filename}: {replacements} replacements")

print(f"\n🎉 Updated {updated_files} files with {total_replacements} Naira conversions")
print("💡 Note: You may need to manually adjust some formatting")