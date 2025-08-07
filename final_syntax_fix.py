#!/usr/bin/env python3

import re

def fix_sarima_syntax():
    with open('sarima_delivery_optimization.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Fix all remaining } except patterns
    content = re.sub(r'\s*\}\s*except\s+', '\nexcept ', content)
    
    # Fix all remaining } else patterns
    content = re.sub(r'\s*\}\s*else\s*:', '\nelse:', content)
    
    # Fix all remaining } elif patterns
    content = re.sub(r'\s*\}\s*elif\s+', '\nelif ', content)
    
    # Remove standalone } lines
    lines = content.split('\n')
    fixed_lines = []
    for line in lines:
        if line.strip() != '}':
            fixed_lines.append(line)
    
    content = '\n'.join(fixed_lines)
    
    with open('sarima_delivery_optimization.py', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("Fixed all remaining syntax errors")

if __name__ == "__main__":
    fix_sarima_syntax()
