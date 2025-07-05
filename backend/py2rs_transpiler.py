import logging
import re
import torch
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM, pipeline
from typing import Optional, Dict, Any
import warnings

# Suppress warnings for cleaner output
warnings.filterwarnings("ignore")
logging.getLogger("transformers").setLevel(logging.WARNING)


class PythonToRustTranspiler:
    """LLM-based transpiler that converts Python code to Rust using open source models."""
    
    def __init__(self):
        self.model_name = "Qwen/Qwen2.5-Coder-3B"  # Use Qwen2.5-Coder for code generation
        self.tokenizer = None
        self.model = None
        self.pipeline = None
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model_loaded = False
        self.fallback_rules = self._create_fallback_rules()
        
    def _create_fallback_rules(self) -> Dict[str, str]:
        """Create fallback conversion rules for basic Python constructs."""
        return {
            'print(': 'println!(',
            'def ': 'fn ',
            'elif ': 'else if ',
            'True': 'true',
            'False': 'false',
            'None': 'None',
            'len(': '.len(',
            'range(': '0..',
            'for i in range(': 'for i in 0..',
            'import ': 'use ',
            'from ': 'use ',
            'class ': 'struct ',
            'self.': 'self.',
            '__init__': 'new',
            'return ': 'return ',
            'if ': 'if ',
            'else:': 'else {',
            'while ': 'while ',
            'for ': 'for ',
            'try:': '// try equivalent',
            'except': '// except equivalent',
            'raise': 'panic!',
            'lambda': '|',
            'and': '&&',
            'or': '||',
            'not': '!',
            'in ': '.contains(',
            'is ': '==',
            'is not': '!=',
        }
    
    def _load_model(self):
        """Load the code generation model."""
        if self.model_loaded:
            return
            
        try:
            print("Loading Qwen2.5-Coder-3B model for Python to Rust conversion...")
            
            # Create pipeline for text generation with Qwen2.5-Coder
            self.pipeline = pipeline(
                "text-generation",
                model=self.model_name,
                device=0 if self.device == "cuda" else -1,
                max_length=1024,  # Increased for better code generation
                num_return_sequences=1,
                temperature=0.1,  # Lower temperature for more deterministic code
                do_sample=True,
                top_p=0.95,  # Nuclear sampling for better code quality
                repetition_penalty=1.1
            )
            
            self.model_loaded = True
            print(f"Qwen2.5-Coder-3B model loaded successfully on {self.device}")
            
        except Exception as e:
            print(f"Error loading model: {e}")
            print("Falling back to rule-based conversion...")
            self.model_loaded = False
        
    def transpile(self, python_code: str) -> str:
        """Main entry point to transpile Python code to Rust using LLM."""
        try:
            # Try LLM-based conversion first
            if not self.model_loaded:
                self._load_model()
            
            if self.model_loaded and self.pipeline:
                return self._llm_transpile(python_code)
            else:
                # Fall back to rule-based conversion
                return self._fallback_transpile(python_code)
                
        except Exception as e:
            return f"// Error during transpilation: {str(e)}\n// Falling back to rule-based conversion\n\n{self._fallback_transpile(python_code)}"
    
    def _llm_transpile(self, python_code: str) -> str:
        """Convert Python code to Rust using the LLM."""
        try:
            # Create a optimized prompt for Qwen2.5-Coder
            prompt = f"""Convert the following Python code to equivalent Rust code:

```python
{python_code}
```

```rust"""
            
            # Generate Rust code using the model
            result = self.pipeline(prompt, max_new_tokens=512, do_sample=True, temperature=0.1)
            
            if result and len(result) > 0:
                generated_text = result[0]['generated_text']
                
                # Extract Rust code from the generated text
                rust_code = self._extract_rust_code(generated_text)
                
                # Post-process the generated code
                rust_code = self._post_process_rust_code(rust_code)
                
                return rust_code
            else:
                return self._fallback_transpile(python_code)
                
        except Exception as e:
            print(f"LLM transpilation error: {e}")
            return self._fallback_transpile(python_code)
    
    def _extract_rust_code(self, generated_text: str) -> str:
        """Extract Rust code from the generated text."""
        # Look for code blocks specifically for Qwen2.5-Coder output
        rust_patterns = [
            r'```rust\n(.*?)```',
            r'```rust(.*?)```',
            r'```\n(.*?)```',
            r'```rust\n(.*?)$',
            r'```rust(.*?)$',
            r'```\n(.*?)$'
        ]
        
        for pattern in rust_patterns:
            match = re.search(pattern, generated_text, re.DOTALL | re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        # If the prompt format worked, extract everything after the rust code block start
        if '```rust' in generated_text:
            start_index = generated_text.find('```rust') + len('```rust')
            # Find the end of the code block or end of text
            end_index = generated_text.find('```', start_index)
            if end_index == -1:
                end_index = len(generated_text)
            return generated_text[start_index:end_index].strip()
        
        # If no pattern matches, return the generated text as-is
        return generated_text.strip()
    
    def _post_process_rust_code(self, rust_code: str) -> str:
        """Post-process the generated Rust code to fix common issues."""
        # Fix common formatting issues
        rust_code = re.sub(r'\n\s*\n\s*\n', '\n\n', rust_code)  # Remove excessive newlines
        rust_code = re.sub(r'^\s*', '', rust_code, flags=re.MULTILINE)  # Remove leading spaces
        
        # Fix println! macro formatting issues
        rust_code = re.sub(r'println!\("{}","([^"]+)"\);', r'println!("\1");', rust_code)
        rust_code = re.sub(r'println!\("{}","([^"]+)", ([^)]+)\);', r'println!("\1", \2);', rust_code)
        
        # Fix format string issues
        rust_code = re.sub(r'format!\("([^"]+)", ([^)]+)\)', r'format!("\1", \2)', rust_code)
        
        # Ensure proper main function if needed
        if 'fn main()' not in rust_code and not rust_code.startswith('fn '):
            lines = rust_code.split('\n')
            indented_lines = ['    ' + line if line.strip() else line for line in lines]
            rust_code = 'fn main() {\n' + '\n'.join(indented_lines) + '\n}'
        
        # Add proper indentation
        lines = rust_code.split('\n')
        formatted_lines = []
        indent_level = 0
        
        for line in lines:
            stripped = line.strip()
            if stripped:
                # Decrease indent for closing braces
                if stripped.startswith('}'):
                    indent_level = max(0, indent_level - 1)
                
                formatted_lines.append('    ' * indent_level + stripped)
                
                # Increase indent for opening braces
                if stripped.endswith('{'):
                    indent_level += 1
            else:
                formatted_lines.append('')
        
        return '\n'.join(formatted_lines)
    
    def _fallback_transpile(self, python_code: str) -> str:
        """Fallback rule-based transpilation when LLM is not available."""
        rust_code = python_code
        
        # Apply basic conversion rules
        for py_pattern, rust_replacement in self.fallback_rules.items():
            rust_code = rust_code.replace(py_pattern, rust_replacement)
        
        # Handle string formatting
        rust_code = re.sub(r'print\("([^"]*)"\.format\([^)]*\)\)', r'println!("{}", \1)', rust_code)
        rust_code = re.sub(r'print\(f"([^"]*)"([^)]*)\)', r'println!("{}", \1)', rust_code)
        
        # Handle function definitions
        rust_code = re.sub(r'def (\w+)\(([^)]*)\):', r'fn \1(\2) {', rust_code)
        
        # Handle variable assignments
        rust_code = re.sub(r'^(\s*)(\w+)\s*=\s*(.+)$', r'\1let \2 = \3;', rust_code, flags=re.MULTILINE)
        
        # Handle if statements
        rust_code = re.sub(r'if (.+):', r'if \1 {', rust_code)
        rust_code = re.sub(r'else:', r'} else {', rust_code)
        
        # Handle for loops
        rust_code = re.sub(r'for (\w+) in range\((\d+)\):', r'for \1 in 0..\2 {', rust_code)
        rust_code = re.sub(r'for (\w+) in range\((\d+),\s*(\d+)\):', r'for \1 in \2..\3 {', rust_code)
        
        # Handle while loops
        rust_code = re.sub(r'while (.+):', r'while \1 {', rust_code)
        
        # Add closing braces and proper formatting
        lines = rust_code.split('\n')
        formatted_lines = []
        indent_level = 0
        
        for line in lines:
            stripped = line.strip()
            if stripped:
                if stripped.endswith('{'):
                    formatted_lines.append('    ' * indent_level + stripped)
                    indent_level += 1
                elif stripped == '}':
                    indent_level = max(0, indent_level - 1)
                    formatted_lines.append('    ' * indent_level + stripped)
                else:
                    formatted_lines.append('    ' * indent_level + stripped)
            else:
                formatted_lines.append('')
        
        # Wrap in main function if needed
        if 'fn main()' not in rust_code:
            formatted_lines = ['fn main() {'] + ['    ' + line for line in formatted_lines] + ['}']
        
        return '\n'.join(formatted_lines) 