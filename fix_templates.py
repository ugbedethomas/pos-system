import os
import re


def fix_template(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # Replace format_naira function calls
    # Pattern: {{ format_naira(some_variable) }}
    content = re.sub(r'\{\{\s*format_naira\((.*?)\)\s*\}\}', r'{{ format_naira(\1) }}', content)

    # Replace old dollar formatting
    content = re.sub(r'\{\{\s*\"%\\.2f\"\s*\|\s*format\((.*?)\)\s*\}\}', r'{{ format_naira(\1) }}', content)

    # Replace ${{ with {{ format_naira(
    content = re.sub(r'\$\{\{\s*(.*?)\s*\}\}', r'{{ format_naira(\1) }}', content)

    # Simple $ replacement
    content = content.replace('${{', '{{ format_naira(')
    content = content.replace('}}$', ') }}')

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

    return content.count('format_naira')


print("🔄 Fixing templates for Naira formatting...")

templates_dir = "templates"
updated_files = 0
total_replacements = 0

for filename in os.listdir(templates_dir):
    if filename.endswith('.html'):
        filepath = os.path.join(templates_dir, filename)
        replacements = fix_template(filepath)
        updated_files += 1
        total_replacements += replacements
        print(f"✅ {filename}: {replacements} replacements")

print(f"\n🎉 Updated {updated_files} files")
print("💡 Remember to add format_naira to render_template calls!")