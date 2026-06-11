import json

# ── Load Unihan_Variants.txt ──────────────────────────────────────────────────

def load_unihan(path="Unihan_Variants.txt"):
    simplified_of = {}   # char -> list of simplified variant chars
    traditional_of = {}  # char -> list of traditional variant chars

    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split("\t")
            if len(parts) < 3:
                continue
            codepoint, field, values = parts[0], parts[1], parts[2]
            if field not in ("kSimplifiedVariant", "kTraditionalVariant"):
                continue

            chars = []
            for token in values.split():
                token = token.split("<")[0].strip()
                if token.startswith("U+"):
                    try:
                        chars.append(chr(int(token[2:], 16)))
                    except ValueError:
                        pass

            if not chars:
                continue

            source_char = chr(int(codepoint[2:], 16))

            if field == "kSimplifiedVariant":
                simplified_of[source_char] = chars
            elif field == "kTraditionalVariant":
                traditional_of[source_char] = chars

    return simplified_of, traditional_of


# ── Load official_characters.json ─────────────────────────────────────────────

def load_official(path="official_characters.json"):
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    # keyed by officialChar for fast lookup
    return {entry["officialChar"]: entry for entry in data}


# ── Load final_radicals.txt ───────────────────────────────────────────────────

def load_final_radicals(path="final_radicals.txt"):
    # Format: U+XXXX\tRadical
    radicals = {}
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split("\t")
            if len(parts) < 2:
                continue
            codepoint, radical = parts[0], parts[1]
            if codepoint.startswith("U+"):
                try:
                    char = chr(int(codepoint[2:], 16))
                    radicals[char] = radical
                except ValueError:
                    pass
    return radicals
# Preserves your exact style:
#   - 4-space indented objects
#   - simple scalar properties on one line
#   - matches array on one line
#   - strokes array with each string on its own indented line

def format_entry(obj, indent=4):
    pad = " " * indent
    lines = ["{"]
    keys = list(obj.keys())
    for i, key in enumerate(keys):
        val = obj[key]
        comma = "," if i < len(keys) - 1 else ""

        if key == "strokes":
            stroke_pad = " " * (indent + 2)
            stroke_lines = ["["]
            for j, stroke in enumerate(val):
                s_comma = "," if j < len(val) - 1 else ""
                stroke_lines.append(f'{stroke_pad}{json.dumps(stroke, ensure_ascii=False)}{s_comma}')
            stroke_lines.append(f'{pad}]')
            lines.append(f'{pad}{json.dumps(key)}: ' + "\n".join(stroke_lines) + comma)

        elif key == "matches":
            # Inline array — use json.dumps per value to preserve null
            inline = "[" + ", ".join(json.dumps(v) for v in val) + "]"
            lines.append(f'{pad}{json.dumps(key)}: {inline}{comma}')

        elif isinstance(val, list):
            # Any other list (simplifiedVariant, traditionalVariant, etc.) — inline
            inline = "[" + ", ".join(json.dumps(v, ensure_ascii=False) for v in val) + "]"
            lines.append(f'{pad}{json.dumps(key)}: {inline}{comma}')

        else:
            lines.append(f'{pad}{json.dumps(key, ensure_ascii=False)}: {json.dumps(val, ensure_ascii=False)}{comma}')

    lines.append("  }")
    return "\n".join(lines)


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    simplified_of, traditional_of = load_unihan("Unihan_Variants.txt")
    official = load_official("official_characters.json")
    fallback_radicals = load_final_radicals("final_radicals.txt")

    with open("output.json", encoding="utf-8") as f:
        data = json.load(f)

    formatted_entries = []

    for entry in data:
        char = entry["character"]
        official_entry = official.get(char)

        # ── Unicode ───────────────────────────────────────────────────────────
        codepoint = f"U+{ord(char):04X}"

        # ── Stroke counts ─────────────────────────────────────────────────────
        actual_stroke_count = len(entry.get("strokes", []))
        if official_entry:
            official_stroke_number = official_entry["strokeNumber"]
            has_mismatch = official_stroke_number != actual_stroke_count
        else:
            official_stroke_number = actual_stroke_count
            has_mismatch = False

        # ── Unihan variants, filtering self-references ────────────────────────
        trad_variants = [c for c in traditional_of.get(char, []) if c != char]
        simp_variants = [c for c in simplified_of.get(char, []) if c != char]

        all_new_variant_chars = set(trad_variants + simp_variants)

        # ── Handle existing variants property ─────────────────────────────────
        existing_variants = entry.get("variants", None)
        keep_variants = None
        if existing_variants is not None:
            leftover = [v for v in existing_variants if v not in all_new_variant_chars]
            if leftover:
                keep_variants = leftover

        already_has_trad = "traditionalVariant" in entry
        already_has_simp = "simplifiedVariant" in entry
        already_has_stroke = "strokeNumber" in entry
        already_has_official = "officialChar" in entry
        already_has_mismatch = "mismatch" in entry

        # ── Build final entry ─────────────────────────────────────────────────
        final_entry = {}
        final_entry["character"] = char
        final_entry["unicode"] = codepoint

        # Insert officialChar and strokeNumber after unicode if not present
        if official_entry and not already_has_official:
            final_entry["officialChar"] = True
        elif already_has_official:
            final_entry["officialChar"] = entry["officialChar"]

        if not already_has_stroke:
            final_entry["strokeNumber"] = official_stroke_number
        else:
            final_entry["strokeNumber"] = entry["strokeNumber"]

        if has_mismatch and not already_has_mismatch:
            final_entry["mismatch"] = True

        # Copy remaining keys, skipping ones we've already handled or will handle
        skip = {"character", "unicode", "officialChar", "strokeNumber",
                "mismatch", "variants", "radical", "traditionalVariant",
                "simplifiedVariant", "matches", "taiwanFontMatches", "strokes"}

        for k, v in entry.items():
            if k in skip:
                continue
            final_entry[k] = v
            if k == "decomposition":
                # ── Radical — right after decomposition ──────────────────────
                if official_entry:
                    final_entry["radical"] = official_entry["radical"]
                elif char in fallback_radicals:
                    final_entry["radical"] = fallback_radicals[char]
                else:
                    final_entry["radical"] = entry.get("radical", "")

        # ── Mismatch — preserve if already existed ────────────────────────────
        if already_has_mismatch and not has_mismatch:
            final_entry["mismatch"] = entry["mismatch"]

        # ── Variant properties after radical ──────────────────────────────────
        if trad_variants and not already_has_trad:
            final_entry["traditionalVariant"] = trad_variants
        elif already_has_trad:
            final_entry["traditionalVariant"] = entry["traditionalVariant"]

        if simp_variants and not already_has_simp:
            final_entry["simplifiedVariant"] = simp_variants
        elif already_has_simp:
            final_entry["simplifiedVariant"] = entry["simplifiedVariant"]

        if keep_variants is not None:
            final_entry["variants"] = keep_variants

        # ── matches and strokes come last via the original entry order ─────────
        if "matches" in entry:
            final_entry["matches"] = entry["matches"]
        if "taiwanFontMatches" in entry:
            final_entry["taiwanFontMatches"] = entry["taiwanFontMatches"]
        if "strokes" in entry:
            final_entry["strokes"] = entry["strokes"]

        formatted_entries.append(format_entry(final_entry))

    output = "[\n  " + ",\n  ".join(formatted_entries) + "\n]\n"

    with open("output_with_variants.json", "w", encoding="utf-8") as f:
        f.write(output)

    print(f"Done. Processed {len(data)} characters.")
    print("Output written to output_with_variants.json")


if __name__ == "__main__":
    main()
