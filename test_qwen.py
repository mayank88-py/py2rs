#!/usr/bin/env python3
"""
Test script for the Qwen2.5-Coder-3B based transpiler
"""

import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from py2rs_transpiler import PythonToRustTranspiler

def test_qwen_transpiler():
    """Test the Qwen2.5-Coder-3B transpiler with various Python code examples."""
    
    print("🤖 Testing Qwen2.5-Coder-3B Python to Rust Transpiler")
    print("=" * 60)
    
    transpiler = PythonToRustTranspiler()
    
    examples = [
        # Basic print
        ('print("Hello, World!")', "Basic print statement"),
        
        # Function definition
        ('''def greet(name):
    print(f"Hello, {name}!")
    return f"Greeting for {name}"

result = greet("Alice")
print(result)''', "Function with f-string"),
        
        # Simple loop
        ('''for i in range(5):
    print(f"Number: {i}")''', "Simple for loop"),
        
        # If-else statement
        ('''x = 10
if x > 5:
    print("x is greater than 5")
else:
    print("x is 5 or less")''', "If-else statement"),
        
        # List operations
        ('''numbers = [1, 2, 3, 4, 5]
for num in numbers:
    print(f"Number: {num}")''', "List iteration"),
    ]
    
    for i, (python_code, description) in enumerate(examples, 1):
        print(f"\n📝 Test {i}: {description}")
        print("-" * 40)
        print("Python:")
        print(python_code)
        print("\nRust:")
        try:
            rust_code = transpiler.transpile(python_code)
            print(rust_code)
        except Exception as e:
            print(f"Error: {e}")
        print("-" * 40)

if __name__ == "__main__":
    test_qwen_transpiler() 