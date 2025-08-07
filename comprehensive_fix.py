#!/usr/bin/env python3

# Comprehensive fix for sarima_delivery_optimization.py

import re

def fix_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Split into lines for processing
    lines = content.split('\n')
    fixed_lines = []
    
    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()
        
        # Skip empty lines
        if not stripped:
            fixed_lines.append(line)
            i += 1
            continue
            
        # Fix common patterns
        if stripped.endswith(' {'):
            # Convert { to :
            if 'try' in stripped:
                fixed_line = line.replace(' {', ':')
            elif 'if ' in stripped or 'elif ' in stripped:
                fixed_line = line.replace(' {', ':')
            elif 'else' in stripped:
                fixed_line = line.replace('} else {', 'else:').replace(' {', ':')
            elif 'for ' in stripped or 'while ' in stripped:
                fixed_line = line.replace(' {', ':')
            elif 'def ' in stripped or 'class ' in stripped:
                fixed_line = line.replace(' {', ':')
            else:
                fixed_line = line.replace(' {', ':')
        elif stripped.startswith('}') and 'catch' in stripped:
            # Convert } catch to except
            if 'Exception as e' in stripped:
                fixed_line = line.replace('} catch Exception as e {', 'except Exception as e:')
            elif 'Exception as e2' in stripped:
                fixed_line = line.replace('} catch Exception as e2 {', 'except Exception as e2:')
            else:
                fixed_line = line.replace('} catch', 'except').replace(' {', ':')
        elif stripped == '}':
            # Skip standalone closing braces
            i += 1
            continue
        else:
            fixed_line = line
            
        fixed_lines.append(fixed_line)
        i += 1
    
    # Join back and write
    content = '\n'.join(fixed_lines)
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"Comprehensive fix applied to {file_path}")

if __name__ == "__main__":
    fix_file('sarima_delivery_optimization.py')
