#!/usr/bin/env python3

import ast
import re

def fix_all_issues(filename):
    """Fix all syntax and indentation issues in the SARIMA file"""
    
    with open(filename, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Remove any remaining } characters not in strings
    lines = content.split('\n')
    fixed_lines = []
    
    for i, line in enumerate(lines):
        # Skip lines that are comments or strings
        stripped = line.strip()
        
        # Remove standalone }
        if stripped == '}':
            continue
            
        # Fix } at end of lines
        if stripped.endswith('}') and not stripped.startswith('#') and not stripped.startswith('"""'):
            line = line.rstrip('}').rstrip()
            
        # Fix indentation for function/class definitions
        if stripped.startswith('def ') or stripped.startswith('class '):
            # Ensure proper indentation (should start at column 0 for top-level)
            if not line.startswith('def ') and not line.startswith('class '):
                line = re.sub(r'^\s*', '', line)
                
        # Fix if/else/try/except indentation
        if any(keyword in stripped for keyword in ['if ', 'else:', 'elif ', 'try:', 'except ', 'for ', 'while ']):
            # Check if it should be indented more based on previous lines
            pass  # Keep existing indentation for now
            
        fixed_lines.append(line)
    
    # Join and write back
    content = '\n'.join(fixed_lines)
    
    # Additional regex fixes
    content = re.sub(r'except\s+Exception as e:', 'except Exception as e:', content)
    content = re.sub(r'try\s*:', 'try:', content)
    
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"Applied comprehensive fixes to {filename}")

if __name__ == "__main__":
    fix_all_issues('sarima_delivery_optimization.py')
