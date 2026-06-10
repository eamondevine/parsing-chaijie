import json
import re

# IDC symbols to remove from decomposition
IDC_SYMBOLS = set("⿰⿱⿲⿳⿴⿵⿶⿷⿸⿹⿺⿻")


def flatten_matches(matches, original_decomp):
    """
    Flatten nested matches array by assigning indices based on order of first appearance.
    Each unique path gets a unique index, assigned in order of first appearance.
    If a path reappears later, it reuses its previously assigned index.
    
    Example: [[0], [0], [1,0], [1,1], [1,0]] -> [0, 0, 1, 2, 1]
    """
    if not matches or not isinstance(matches, list):
        return None
    
    path_to_index = {}
    result = []
    
    for item in matches:
        if item is None:
            result.append(None)
        elif isinstance(item, list):
            key = tuple(item)
            if key not in path_to_index:
                path_to_index[key] = len(path_to_index)
            result.append(path_to_index[key])
        else:
            # Scalar value - treat as a single-element tuple key
            key = (item,)
            if key not in path_to_index:
                path_to_index[key] = len(path_to_index)
            result.append(path_to_index[key])
    
    return result


def remove_idc_symbols(decomposition):
    """Remove all IDC symbols from decomposition string"""
    if not decomposition or not isinstance(decomposition, str):
        return decomposition
    
    result = ""
    for char in decomposition:
        if char not in IDC_SYMBOLS:
            result += char
    
    return result if result else None


def main():
    print("Loading output.json...")
    
    with open('output.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    print(f"Processing {len(data)} characters...")
    
    # Process each character
    for char_obj in data:
        original_decomp = char_obj.get('decomposition')
        
        # Flatten matches arrays using original decomposition
        if 'matches' in char_obj and char_obj['matches'] is not None:
            char_obj['matches'] = flatten_matches(
                char_obj['matches'],
                original_decomp
            )
        
        # Remove IDC symbols from decomposition (after using it for matches)
        if original_decomp:
            char_obj['decomposition'] = remove_idc_symbols(original_decomp)
    
    # Write back to file with custom formatting
    print("Writing updated output.json...")
    
    # Convert to JSON string
    json_str = json.dumps(data, ensure_ascii=False, indent=2)
    
    # Post-process: make matches arrays inline
    def compress_matches(match):
        """Convert multi-line matches array to single line"""
        full_match = match.group(0)
        # Extract the array content between brackets
        content = re.search(r'\[(.*?)\]', full_match, re.DOTALL)
        if content:
            # Get all values, strip whitespace, and join inline
            values = re.findall(r'(null|\d+)', content.group(1))
            inline = ', '.join(values)
            return f'"matches": [{inline}]'
        return full_match
    
    # Match "matches": [ ... ] patterns across multiple lines
    json_str = re.sub(
        r'"matches":\s*\[(.*?)\]',
        compress_matches,
        json_str,
        flags=re.DOTALL
    )
    
    with open('output.json', 'w', encoding='utf-8') as f:
        f.write(json_str)
    
    print("✓ Done! Matches flattened and IDC symbols removed.")


if __name__ == '__main__':
    main()