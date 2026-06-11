import json

with open("output.json", encoding="utf-8") as f:
    data = json.load(f)

lines = []

for entry in data:
    char = entry["character"]
    codepoint = f"U+{ord(char):04X}"

    trad = entry.get("traditionalVariant", [])
    simp = entry.get("simplifiedVariant", [])

    if len(trad) > 1:
        lines.append(f"{char} ({codepoint}) traditionalVariant: {trad}")
    if len(simp) > 1:
        lines.append(f"{char} ({codepoint}) simplifiedVariant: {simp}")

with open("multi_variants.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(lines) + "\n")

print(f"Found {len(lines)} characters with multiple variants.")
print("Output written to multi_variants.txt")
