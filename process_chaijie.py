import json
import re
import sys

INPUT_FILE = "output.json"  # Change this to your actual filename
OUTPUT_FILE = "data_processed.json"

with open(INPUT_FILE, "r", encoding="utf-8") as f:
    data = json.load(f)

# 1. Add unicodeDecimal and unicodeHexadecimal to each object
for item in data:
    char = item["character"]
    code_point = ord(char)
    item["unicodeDecimal"] = code_point
    item["unicodeHexadecimal"] = f"U+{code_point:04X}"

# 2. Check ordering and sort by unicode code point
original_order = [item["character"] for item in data]
sorted_data = sorted(data, key=lambda x: ord(x["character"]))
sorted_order = [item["character"] for item in sorted_data]

# Find which characters changed position
changed = []
for i, (orig, new) in enumerate(zip(original_order, sorted_order)):
    if orig != new:
        original_index = original_order.index(new)
        changed.append({
            "character": new,
            "unicodeHexadecimal": f"U+{ord(new):04X}",
            "original_position": original_index + 1,
            "new_position": i + 1
        })

print(f"Total characters: {len(data)}")
print(f"Characters that changed position: {len(changed)}")

if changed:
    print("\nCharacters that moved:")
    for c in changed:
        print(f"  {c['character']} ({c['unicodeHexadecimal']}): position {c['original_position']} → {c['new_position']}")
else:
    print("All characters were already in the correct order!")

# 3. Write sorted data with new fields to output file, matches inline
def compress_matches(match):
    full_match = match.group(0)
    content = re.search(r'\[(.*?)\]', full_match, re.DOTALL)
    if content:
        values = re.findall(r'(null|\d+)', content.group(1))
        inline = ', '.join(values)
        return f'"matches": [{inline}]'
    return full_match

json_str = json.dumps(sorted_data, ensure_ascii=False, indent=2)
json_str = re.sub(r'"matches":\s*\[(.*?)\]', compress_matches, json_str, flags=re.DOTALL)

with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    f.write(json_str)

print(f"\nProcessed file saved to: {OUTPUT_FILE}")

# 4. Write log file
LOG_FILE = "changes_log.txt"
with open(LOG_FILE, "w", encoding="utf-8") as f:
    f.write(f"Total characters: {len(data)}\n")
    f.write(f"Characters that changed position: {len(changed)}\n\n")
    if changed:
        f.write("Characters that moved:\n")
        for c in changed:
            f.write(f"  {c['character']} ({c['unicodeHexadecimal']}): position {c['original_position']} → {c['new_position']}\n")
    else:
        f.write("All characters were already in the correct order!\n")

print(f"Log file saved to: {LOG_FILE}")
