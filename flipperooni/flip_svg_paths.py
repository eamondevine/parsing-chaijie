import json
import re

CANVAS_HEIGHT = 1024

def flip_y_coord(y):
    """Flip a Y coordinate"""
    return CANVAS_HEIGHT - y

def flip_path(path_string):
    """
    Flip all Y coordinates in an SVG path string.
    Handles M, L, Q, C, etc. commands.
    """
    if not path_string:
        return path_string
    
    # Split path into tokens (commands and numbers)
    tokens = re.findall(r'[MLHVQTCSAZmlhvqtcsaz]|[-+]?[0-9]*\.?[0-9]+', path_string)
    
    result = []
    i = 0
    current_command = None
    
    while i < len(tokens):
        token = tokens[i]
        
        # Check if it's a command letter
        if re.match(r'[MLHVQTCSAZmlhvqtcsaz]', token):
            current_command = token
            result.append(token)
            i += 1
        else:
            # It's a number - need to determine if it's X or Y based on command
            num = float(token)
            
            if current_command in ['M', 'L', 'm', 'l']:
                # MoveTo, LineTo: x y pairs
                x = num
                y = float(tokens[i + 1])
                result.append(str(x))
                result.append(str(flip_y_coord(y)))
                i += 2
                
            elif current_command in ['H', 'h']:
                # Horizontal line: just x
                result.append(token)
                i += 1
                
            elif current_command in ['V', 'v']:
                # Vertical line: just y
                result.append(str(flip_y_coord(num)))
                i += 1
                
            elif current_command in ['Q', 'q']:
                # Quadratic curve: x1 y1 x y
                x1 = num
                y1 = float(tokens[i + 1])
                x = float(tokens[i + 2])
                y = float(tokens[i + 3])
                result.extend([str(x1), str(flip_y_coord(y1)), str(x), str(flip_y_coord(y))])
                i += 4
                
            elif current_command in ['C', 'c']:
                # Cubic curve: x1 y1 x2 y2 x y
                x1 = num
                y1 = float(tokens[i + 1])
                x2 = float(tokens[i + 2])
                y2 = float(tokens[i + 3])
                x = float(tokens[i + 4])
                y = float(tokens[i + 5])
                result.extend([
                    str(x1), str(flip_y_coord(y1)),
                    str(x2), str(flip_y_coord(y2)),
                    str(x), str(flip_y_coord(y))
                ])
                i += 6
                
            elif current_command in ['S', 's', 'T', 't']:
                # Smooth curve: x y
                x = num
                y = float(tokens[i + 1])
                result.append(str(x))
                result.append(str(flip_y_coord(y)))
                i += 2
                
            elif current_command in ['A', 'a']:
                # Arc: rx ry rotation large-arc sweep x y
                rx = num
                ry = float(tokens[i + 1])
                rotation = float(tokens[i + 2])
                large_arc = tokens[i + 3]
                sweep = tokens[i + 4]
                x = float(tokens[i + 5])
                y = float(tokens[i + 6])
                result.extend([
                    str(rx), str(ry), str(rotation),
                    large_arc, sweep,
                    str(x), str(flip_y_coord(y))
                ])
                i += 7
                
            elif current_command in ['Z', 'z']:
                # Close path - no coordinates
                i += 1
            else:
                # Unknown - just keep it
                result.append(token)
                i += 1
    
    # Join tokens back together with spaces
    return ' '.join(result)

def main():
    print("Loading output.json...")
    
    with open('output.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    print(f"Processing {len(data)} characters...")
    
    # Process each character's strokes
    for char_obj in data:
        if 'strokes' in char_obj and char_obj['strokes']:
            flipped_strokes = []
            for stroke in char_obj['strokes']:
                flipped_strokes.append(flip_path(stroke))
            char_obj['strokes'] = flipped_strokes
    
    # Write back to file
    print("Writing flipped output.json...")
    
    json_str = json.dumps(data, ensure_ascii=False, indent=2)
    
    # Make matches arrays inline
    def compress_matches(match):
        full_match = match.group(0)
        content = re.search(r'\[(.*?)\]', full_match, re.DOTALL)
        if content:
            values = re.findall(r'(null|\d+)', content.group(1))
            inline = ', '.join(values)
            return f'"matches": [{inline}]'
        return full_match
    
    json_str = re.sub(
        r'"matches":\s*\[(.*?)\]',
        compress_matches,
        json_str,
        flags=re.DOTALL
    )
    
    with open('output.json', 'w', encoding='utf-8') as f:
        f.write(json_str)
    
    print("✓ Done! Y-axis flipped for all strokes.")

if __name__ == '__main__':
    main()
