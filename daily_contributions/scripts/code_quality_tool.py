#!/usr/bin/env python3
"""
Code Quality Tool
Automatically improves code quality through formatting and linting
"""

import os
import subprocess
import re
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import logging
from datetime import datetime

class CodeQualityTool:
    """Automatically improves code quality and formatting"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.quality_tools = self._detect_quality_tools()
        self.supported_languages = self._detect_languages()
    
    def _detect_quality_tools(self) -> Dict[str, bool]:
        """Detect available code quality tools"""
        tools = {
            "black": self._check_tool_availability("black"),
            "isort": self._check_tool_availability("isort"),
            "flake8": self._check_tool_availability("flake8"),
            "pylint": self._check_tool_availability("pylint"),
            "mypy": self._check_tool_availability("mypy"),
            "prettier": self._check_tool_availability("prettier"),
            "eslint": self._check_tool_availability("eslint"),
            "gofmt": self._check_tool_availability("gofmt"),
            "rustfmt": self._check_tool_availability("rustfmt")
        }
        
        active_tools = {k: v for k, v in tools.items() if v}
        self.logger.info(f"Detected quality tools: {list(active_tools.keys())}")
        return active_tools
    
    def _detect_languages(self) -> Dict[str, bool]:
        """Detect programming languages in the project"""
        languages = {
            "python": self._has_python_files(),
            "javascript": self._has_js_files(),
            "typescript": self._has_ts_files(),
            "go": self._has_go_files(),
            "rust": self._has_rust_files(),
            "java": self._has_java_files()
        }
        
        active_languages = {k: v for k, v in languages.items() if v}
        self.logger.info(f"Detected languages: {list(active_languages.keys())}")
        return active_languages
    
    def _check_tool_availability(self, tool: str) -> bool:
        """Check if a quality tool is available"""
        try:
            result = subprocess.run(
                [tool, "--version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            return result.returncode == 0
        except (subprocess.TimeoutExpired, subprocess.SubprocessError, FileNotFoundError):
            return False
    
    def _has_python_files(self) -> bool:
        """Check if project has Python files"""
        return any(Path('.').glob('**/*.py'))
    
    def _has_js_files(self) -> bool:
        """Check if project has JavaScript files"""
        return any(Path('.').glob('**/*.js'))
    
    def _has_ts_files(self) -> bool:
        """Check if project has TypeScript files"""
        return any(Path('.').glob('**/*.ts'))
    
    def _has_go_files(self) -> bool:
        """Check if project has Go files"""
        return any(Path('.').glob('**/*.go'))
    
    def _has_rust_files(self) -> bool:
        """Check if project has Rust files"""
        return any(Path('.').glob('**/*.rs'))
    
    def _has_java_files(self) -> bool:
        """Check if project has Java files"""
        return any(Path('.').glob('**/*.java'))
    
    def get_improvement_tasks(self) -> List[Dict]:
        """Get list of code quality improvement tasks"""
        tasks = []
        
        # Code formatting tasks
        formatting_task = self._check_formatting_needs()
        if formatting_task:
            tasks.append(formatting_task)
        
        # Linting tasks
        linting_task = self._check_linting_needs()
        if linting_task:
            tasks.append(linting_task)
        
        # Type checking tasks
        type_checking_task = self._check_type_checking_needs()
        if type_checking_task:
            tasks.append(type_checking_task)
        
        # Code complexity analysis
        complexity_task = self._check_code_complexity()
        if complexity_task:
            tasks.append(complexity_task)
        
        # Configuration files
        config_task = self._check_quality_config_files()
        if config_task:
            tasks.append(config_task)
        
        return tasks
    
    def _check_formatting_needs(self) -> Optional[Dict]:
        """Check if code formatting is needed"""
        if not self.quality_tools and not self.supported_languages:
            return None
        
        formatting_needed = False
        details = []
        
        # Check Python formatting
        if self.supported_languages.get("python") and self.quality_tools.get("black"):
            if self._python_needs_formatting():
                formatting_needed = True
                details.append("Python files need formatting")
        
        # Check JavaScript/TypeScript formatting
        if (self.supported_languages.get("javascript") or self.supported_languages.get("typescript")) and self.quality_tools.get("prettier"):
            if self._js_needs_formatting():
                formatting_needed = True
                details.append("JavaScript/TypeScript files need formatting")
        
        # Check Go formatting
        if self.supported_languages.get("go") and self.quality_tools.get("gofmt"):
            if self._go_needs_formatting():
                formatting_needed = True
                details.append("Go files need formatting")
        
        # Check Rust formatting
        if self.supported_languages.get("rust") and self.quality_tools.get("rustfmt"):
            if self._rust_needs_formatting():
                formatting_needed = True
                details.append("Rust files need formatting")
        
        if formatting_needed:
            return {
                "type": "code_formatting",
                "description": "Improve code formatting and style consistency",
                "priority": 2,
                "action": self._format_code,
                "details": details
            }
        
        return None
    
    def _check_linting_needs(self) -> Optional[Dict]:
        """Check if linting issues exist"""
        linting_issues = 0
        details = []
        
        # Check Python linting
        if self.supported_languages.get("python"):
            if self.quality_tools.get("flake8"):
                flake8_issues = self._count_flake8_issues()
                linting_issues += flake8_issues
                if flake8_issues > 0:
                    details.append(f"flake8 found {flake8_issues} issues")
            
            if self.quality_tools.get("pylint"):
                pylint_issues = self._count_pylint_issues()
                linting_issues += pylint_issues
                if pylint_issues > 0:
                    details.append(f"pylint found {pylint_issues} issues")
        
        # Check JavaScript/TypeScript linting
        if self.supported_languages.get("javascript") or self.supported_languages.get("typescript"):
            if self.quality_tools.get("eslint"):
                eslint_issues = self._count_eslint_issues()
                linting_issues += eslint_issues
                if eslint_issues > 0:
                    details.append(f"eslint found {eslint_issues} issues")
        
        if linting_issues > 0:
            return {
                "type": "code_linting",
                "description": f"Resolve {linting_issues} linting issues",
                "priority": 3,
                "action": self._apply_linting,
                "issue_count": linting_issues,
                "details": details
            }
        
        return None
    
    def _check_type_checking_needs(self) -> Optional[Dict]:
        """Check if type checking can be improved"""
        if self.supported_languages.get("python") and self.quality_tools.get("mypy"):
            untyped_functions = self._count_untyped_functions()
            
            if untyped_functions > 10:
                return {
                    "type": "type_checking",
                    "description": f"Add type hints to {untyped_functions} untyped functions",
                    "priority": 4,
                    "action": self._improve_type_checking,
                    "untyped_count": untyped_functions
                }
        
        return None
    
    def _check_code_complexity(self) -> Optional[Dict]:
        """Check for high complexity code"""
        complex_functions = self._find_complex_functions()
        
        if complex_functions > 5:
            return {
                "type": "complexity_reduction",
                "description": f"Refactor {complex_functions} high-complexity functions",
                "priority": 5,
                "action": self._reduce_complexity,
                "complex_count": complex_functions
            }
        
        return None
    
    def _check_quality_config_files(self) -> Optional[Dict]:
        """Check if quality configuration files exist"""
        config_files = [
            (".flake8", "Python linting configuration"),
            ("pyproject.toml", "Python project configuration"),
            (".prettierrc", "JavaScript/TypeScript formatting config"),
            ("eslint.config.js", "JavaScript/TypeScript linting config"),
            (".golangci.yml", "Go linting configuration"),
            ("rustfmt.toml", "Rust formatting configuration")
        ]
        
        missing_configs = []
        for filename, description in config_files:
            if not Path(filename).exists():
                # Check if the file would be relevant
                if self._would_config_be_relevant(filename):
                    missing_configs.append((filename, description))
        
        if len(missing_configs) >= 2:
            return {
                "type": "quality_config",
                "description": f"Create {len(missing_configs)} missing quality configuration files",
                "priority": 6,
                "action": self._create_quality_configs,
                "configs": missing_configs
            }
        
        return None
    
    def _would_config_be_relevant(self, filename: str) -> bool:
        """Check if a config file would be relevant for this project"""
        if filename == ".flake8" and self.supported_languages.get("python"):
            return True
        elif filename == "pyproject.toml" and self.supported_languages.get("python"):
            return True
        elif filename == ".prettierrc" and (self.supported_languages.get("javascript") or self.supported_languages.get("typescript")):
            return True
        elif filename == "eslint.config.js" and (self.supported_languages.get("javascript") or self.supported_languages.get("typescript")):
            return True
        elif filename == ".golangci.yml" and self.supported_languages.get("go"):
            return True
        elif filename == "rustfmt.toml" and self.supported_languages.get("rust"):
            return True
        return False
    
    def _python_needs_formatting(self) -> bool:
        """Check if Python files need formatting"""
        try:
            result = subprocess.run(
                ["black", "--check", "--diff", "."],
                capture_output=True,
                text=True,
                timeout=30
            )
            return result.returncode != 0
        except (subprocess.TimeoutExpired, subprocess.SubprocessError):
            return False
    
    def _js_needs_formatting(self) -> bool:
        """Check if JS/TS files need formatting"""
        try:
            result = subprocess.run(
                ["prettier", "--check", "**/*.{js,ts,jsx,tsx}"],
                capture_output=True,
                text=True,
                timeout=30
            )
            return result.returncode != 0
        except (subprocess.TimeoutExpired, subprocess.SubprocessError):
            return False
    
    def _go_needs_formatting(self) -> bool:
        """Check if Go files need formatting"""
        try:
            result = subprocess.run(
                ["gofmt", "-d", "."],
                capture_output=True,
                text=True,
                timeout=30
            )
            return result.returncode != 0
        except (subprocess.TimeoutExpired, subprocess.SubprocessError):
            return False
    
    def _rust_needs_formatting(self) -> bool:
        """Check if Rust files need formatting"""
        try:
            result = subprocess.run(
                ["rustfmt", "--check", "."],
                capture_output=True,
                text=True,
                timeout=30
            )
            return result.returncode != 0
        except (subprocess.TimeoutExpired, subprocess.SubprocessError):
            return False
    
    def _count_flake8_issues(self) -> int:
        """Count flake8 issues"""
        try:
            result = subprocess.run(
                ["flake8", "--statistics"],
                capture_output=True,
                text=True,
                timeout=30
            )
            if result.returncode != 0:
                # Count lines in output (each issue is a line)
                return len(result.stdout.split('\n')) - 1
        except (subprocess.TimeoutExpired, subprocess.SubprocessError):
            pass
        return 0
    
    def _count_pylint_issues(self) -> int:
        """Count pylint issues"""
        try:
            result = subprocess.run(
                ["pylint", "--output-format=text", "."],
                capture_output=True,
                text=True,
                timeout=30
            )
            if result.returncode != 0:
                # Count lines that start with issue codes
                issues = [line for line in result.stdout.split('\n') if line and line[0].isdigit()]
                return len(issues)
        except (subprocess.TimeoutExpired, subprocess.SubprocessError):
            pass
        return 0
    
    def _count_eslint_issues(self) -> int:
        """Count eslint issues"""
        try:
            result = subprocess.run(
                ["eslint", ".", "--format=json"],
                capture_output=True,
                text=True,
                timeout=30
            )
            if result.returncode != 0:
                return len(result.stdout.split('\n')) - 1
        except (subprocess.TimeoutExpired, subprocess.SubprocessError):
            pass
        return 0
    
    def _count_untyped_functions(self) -> int:
        """Count functions without type hints"""
        untyped_count = 0
        
        for file_path in Path('.').rglob('*.py'):
            if file_path.name.startswith('.') or 'venv' in str(file_path):
                continue
            
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Find function definitions
                functions = re.findall(r'def\s+(\w+)\s*\([^)]*\):', content)
                
                # Simple heuristic: if few type hints, consider untyped
                type_hints = re.findall(r'def\s+(\w+)\s*\([^)]*\)\s*->\s*\w+', content)
                
                untyped_count += max(0, len(functions) - len(type_hints))
                
            except Exception:
                continue
        
        return untyped_count
    
    def _find_complex_functions(self) -> int:
        """Find functions that might be too complex"""
        complex_count = 0
        
        for file_path in Path('.').rglob('*.py'):
            if file_path.name.startswith('.') or 'venv' in str(file_path):
                continue
            
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Simple complexity heuristic: long functions
                functions = re.findall(r'def\s+(\w+)\s*\([^)]*\):\s*\n((?:.|\n)*?)(?=\n\S|\ndef|\nclass|\Z)', content)
                
                for func_name, func_body in functions:
                    lines = len(func_body.split('\n'))
                    if lines > 30:  # Functions longer than 30 lines
                        complex_count += 1
                        
            except Exception:
                continue
        
        return complex_count
    
    def _format_code(self, task: Dict) -> bool:
        """Apply code formatting"""
        formatted = 0
        
        # Format Python code
        if self.supported_languages.get("python") and self.quality_tools.get("black"):
            try:
                subprocess.run(["black", "."], timeout=60)
                formatted += 1
                self.logger.info("Formatted Python code with black")
            except Exception as e:
                self.logger.error(f"Failed to format Python code: {str(e)}")
        
        # Format JavaScript/TypeScript code
        if (self.supported_languages.get("javascript") or self.supported_languages.get("typescript")) and self.quality_tools.get("prettier"):
            try:
                subprocess.run(["prettier", "--write", "**/*.{js,ts,jsx,tsx}"], timeout=60)
                formatted += 1
                self.logger.info("Formatted JavaScript/TypeScript code with prettier")
            except Exception as e:
                self.logger.error(f"Failed to format JS/TS code: {str(e)}")
        
        # Format Go code
        if self.supported_languages.get("go") and self.quality_tools.get("gofmt"):
            try:
                subprocess.run(["gofmt", "-w", "."], timeout=60)
                formatted += 1
                self.logger.info("Formatted Go code with gofmt")
            except Exception as e:
                self.logger.error(f"Failed to format Go code: {str(e)}")
        
        # Format Rust code
        if self.supported_languages.get("rust") and self.quality_tools.get("rustfmt"):
            try:
                subprocess.run(["rustfmt", "."], timeout=60)
                formatted += 1
                self.logger.info("Formatted Rust code with rustfmt")
            except Exception as e:
                self.logger.error(f"Failed to format Rust code: {str(e)}")
        
        return formatted > 0
    
    def _apply_linting(self, task: Dict) -> bool:
        """Apply automatic linting fixes"""
        fixed = 0
        
        # Apply Python linting fixes
        if self.supported_languages.get("python"):
            if self.quality_tools.get("flake8"):
                try:
                    # Some flake8 issues can be auto-fixed
                    subprocess.run(["autopep8", "--in-place", "--recursive", "."], timeout=60)
                    fixed += 1
                    self.logger.info("Applied autopep8 fixes to Python code")
                except Exception as e:
                    self.logger.error(f"Failed to apply autopep8 fixes: {str(e)}")
        
        return fixed > 0
    
    def _improve_type_checking(self, task: Dict) -> bool:
        """Improve type checking coverage"""
        try:
            # Create a type checking improvement guide
            guide_content = self._generate_type_checking_guide(task.get('untyped_count', 0))
            with open("TYPE_CHECKING_GUIDE.md", 'w') as f:
                f.write(guide_content)
            
            self.logger.info("Created type checking guide")
            return True
        except Exception as e:
            self.logger.error(f"Failed to improve type checking: {str(e)}")
            return False
    
    def _reduce_complexity(self, task: Dict) -> bool:
        """Provide guidance for reducing code complexity"""
        try:
            guide_content = self._generate_complexity_reduction_guide(task.get('complex_count', 0))
            with open("COMPLEXITY_REDUCTION_GUIDE.md", 'w') as f:
                f.write(guide_content)
            
            self.logger.info("Created complexity reduction guide")
            return True
        except Exception as e:
            self.logger.error(f"Failed to reduce complexity: {str(e)}")
            return False
    
    def _create_quality_configs(self, task: Dict) -> bool:
        """Create missing quality configuration files"""
        configs = task.get('configs', [])
        created = 0
        
        for filename, description in configs:
            try:
                content = self._generate_config_content(filename)
                with open(filename, 'w') as f:
                    f.write(content)
                
                created += 1
                self.logger.info(f"Created {filename} configuration")
            except Exception as e:
                self.logger.error(f"Failed to create {filename}: {str(e)}")
        
        return created > 0
    
    def _generate_type_checking_guide(self, untyped_count: int) -> str:
        """Generate type checking improvement guide"""
        return f"""# Type Checking Improvement Guide

This guide helps improve type annotation coverage in your codebase.

## Current Status

Found approximately {untyped_count} functions without type hints.

## Why Type Hints Matter

- **Better IDE Support**: Autocomplete and error detection
- **Documentation**: Self-documenting code
- **Refactoring Safety**: Catch type errors early
- **Maintainability**: Easier to understand code intent

## Adding Type Hints

### Basic Function

```python
# Before
def process_data(items):
    return [item.upper() for item in items]

# After
from typing import List

def process_data(items: List[str]) -> List[str]:
    return [item.upper() for item in items]
```

### Function with Multiple Types

```python
# Before
def calculate(operation, a, b):
    if operation == 'add':
        return a + b
    elif operation == 'multiply':
        return a * b

# After
from typing import Union

def calculate(operation: str, a: Union[int, float], b: Union[int, float]) -> Union[int, float]:
    if operation == 'add':
        return a + b
    elif operation == 'multiply':
        return a * b
```

### Complex Type Hints

```python
from typing import Dict, List, Optional, Callable

def process_callback(
    data: Dict[str, List[int]], 
    callback: Optional[Callable[[str], None]] = None
) -> Optional[str]:
    \"\"\"Process data with optional callback.\"\"\"
    if callback:
        callback("processing")
    return "complete" if data else None
```

## Type Checking Tools

### mypy

Install and run:

```bash
pip install mypy
mypy your_package/
```

### Configuration

Create `mypy.ini`:

```ini
[mypy]
python_version = 3.7
warn_return_any = True
warn_unused_configs = True
disallow_untyped_defs = True
```

### Gradual Typing

Start with simple type hints and gradually add more:

1. Add type hints to public functions first
2. Include parameter and return types
3. Use `Any` for complex cases initially
4. Gradually replace `Any` with specific types

## Common Type Patterns

### Optional Values

```python
from typing import Optional

def get_user_name(user_id: int) -> Optional[str]:
    \"\"\"Return user name or None if not found.\"\"\"
    # implementation
```

### Collections

```python
from typing import List, Dict, Set, Tuple

def analyze_scores(scores: List[int]) -> Dict[str, int]:
    \"\"\"Analyze a list of scores.\"\"\"
    return {'max': max(scores), 'min': min(scores), 'avg': sum(scores) // len(scores)}
```

### Generators

```python
from typing import Generator

def number_generator(n: int) -> Generator[int, None, None]:
    \"\"\"Generate numbers from 0 to n-1.\"\"\"
    for i in range(n):
        yield i
```

## Best Practices

1. **Start Small**: Begin with simple functions
2. **Use IDE Support**: Let your IDE help add type hints
3. **Document Complex Types**: Add comments for complex generic types
4. **Be Consistent**: Use the same typing style throughout
5. **Test Type Checking**: Run mypy regularly to catch issues

## Resources

- [mypy documentation](https://mypy.readthedocs.io/)
- [PEP 484](https://www.python.org/dev/peps/pep-0484/)
- [typing module](https://docs.python.org/3/library/typing.html)

---
*Generated to help improve type annotation coverage.*
"""
    
    def _generate_complexity_reduction_guide(self, complex_count: int) -> str:
        """Generate complexity reduction guide"""
        return f"""# Code Complexity Reduction Guide

This guide helps reduce code complexity and improve maintainability.

## Current Status

Found approximately {complex_count} functions that might be too complex.

## Why Reduce Complexity?

- **Readability**: Easier to understand code intent
- **Maintainability**: Simple code is easier to modify
- **Testing**: Less complex code is easier to test
- **Debugging**: Lower complexity reduces bug potential

## Complexity Indicators

- Functions longer than 30 lines
- Nested conditionals more than 3 levels deep
- Multiple return points
- Too many parameters (more than 4)
- Complex boolean expressions

## Refactoring Techniques

### 1. Extract Function

```python
# Before - Complex function
def process_user_data(user_data):
    if user_data.get('age', 0) >= 18:
        if user_data.get('verified', False):
            if user_data.get('premium', False):
                # Process premium adult user
                return "premium_adult"
            else:
                # Process regular adult user
                return "regular_adult"
        else:
            # Process unverified user
            return "unverified"
    else:
        # Process minor user
        return "minor"

# After - Extracted functions
def is_adult(user_data):
    return user_data.get('age', 0) >= 18

def is_verified(user_data):
    return user_data.get('verified', False)

def is_premium(user_data):
    return user_data.get('premium', False)

def categorize_user_type(user_data):
    if not is_adult(user_data):
        return "minor"
    elif not is_verified(user_data):
        return "unverified"
    elif is_premium(user_data):
        return "premium_adult"
    else:
        return "regular_adult"
```

### 2. Replace Conditional with Polymorphism

```python
# Before - Complex if/else chain
def calculate_discount(customer_type, amount):
    if customer_type == "regular":
        if amount > 100:
            return 0.05
        else:
            return 0
    elif customer_type == "silver":
        if amount > 50:
            return 0.10
        else:
            return 0.05
    elif customer_type == "gold":
        return 0.15
    else:
        return 0

# After - Strategy pattern
from abc import ABC, abstractmethod

class DiscountStrategy(ABC):
    @abstractmethod
    def calculate_discount(self, amount: float) -> float:
        pass

class RegularDiscount(DiscountStrategy):
    def calculate_discount(self, amount: float) -> float:
        return 0.05 if amount > 100 else 0

class SilverDiscount(DiscountStrategy):
    def calculate_discount(self, amount: float) -> float:
        if amount > 50:
            return 0.10
        return 0.05

class GoldDiscount(DiscountStrategy):
    def calculate_discount(self, amount: float) -> float:
        return 0.15

class DiscountFactory:
    _strategies = {
        "regular": RegularDiscount(),
        "silver": SilverDiscount(),
        "gold": GoldDiscount()
    }
    
    @classmethod
    def get_discount_strategy(cls, customer_type: str) -> DiscountStrategy:
        return cls._strategies.get(customer_type, RegularDiscount())

def calculate_discount(customer_type: str, amount: float) -> float:
    strategy = DiscountFactory.get_discount_strategy(customer_type)
    return strategy.calculate_discount(amount)
```

### 3. Guard Clauses

```python
# Before - Nested if statements
def process_order(order):
    if order:
        if order.get('items'):
            if order.get('customer'):
                if order['customer'].get('valid'):
                    # Process valid order
                    return process_valid_order(order)
                else:
                    raise ValueError("Invalid customer")
            else:
                raise ValueError("Missing customer")
        else:
            raise ValueError("No items")
    else:
        raise ValueError("No order")

# After - Guard clauses
def process_order(order):
    if not order:
        raise ValueError("No order")
    
    if not order.get('items'):
        raise ValueError("No items")
    
    customer = order.get('customer')
    if not customer:
        raise ValueError("Missing customer")
    
    if not customer.get('valid'):
        raise ValueError("Invalid customer")
    
    # Process valid order
    return process_valid_order(order)
```

## Design Principles

### Single Responsibility Principle

Each function should do one thing well:

```python
# Before - Multiple responsibilities
def process_user(user_data):
    # Validation
    if not user_data.get('email'):
        raise ValueError("Email required")
    
    # Processing
    user_data['processed'] = True
    user_data['timestamp'] = datetime.now()
    
    # Saving
    with open('users.json', 'r') as f:
        users = json.load(f)
    users.append(user_data)
    with open('users.json', 'w') as f:
        json.dump(users, f)
    
    return user_data

# After - Separated concerns
def validate_user_data(user_data):
    if not user_data.get('email'):
        raise ValueError("Email required")
    return True

def enrich_user_data(user_data):
    user_data['processed'] = True
    user_data['timestamp'] = datetime.now()
    return user_data

def save_user(user_data):
    with open('users.json', 'r') as f:
        users = json.load(f)
    users.append(user_data)
    with open('users.json', 'w') as f:
        json.dump(users, f)

def process_user(user_data):
    validate_user_data(user_data)
    enriched_data = enrich_user_data(user_data)
    save_user(enriched_data)
    return enriched_data
```

### Keep Functions Small

- Aim for functions under 20 lines
- If a function is getting long, consider breaking it up
- Use meaningful function names that describe what they do

## Complexity Metrics

### Cyclomatic Complexity

Functions should have cyclomatic complexity under 10:

```python
# High complexity
def complex_function(a, b, c, d):
    if a > 0:
        if b > 0:
            if c > 0:
                if d > 0:
                    return "all positive"
                else:
                    return "d negative"
            else:
                return "c negative"
        else:
            return "b negative"
    else:
        return "a negative"
```

### Parameter Count

Functions should have 4 or fewer parameters:

```python
# Too many parameters
def create_user(name, email, age, address, phone, preferences):
    pass

# Better - use configuration object
def create_user(user_config):
    pass

# Or use named parameters with defaults
def create_user(name, email, age=None, address=None, phone=None):
    pass
```

## Testing Complex Code

Write tests for refactored functions:

```python
# Test extracted functions
def test_is_adult():
    assert is_adult({'age': 18}) == True
    assert is_adult({'age': 17}) == False
    assert is_adult({'age': 0}) == False

def test_is_verified():
    assert is_verified({'verified': True}) == True
    assert is_verified({'verified': False}) == False
    assert is_verified({}) == False
```

## When to Refactor

1. When adding new features
2. When debugging complex functions
3. When code review reveals complexity issues
4. When writing tests becomes difficult

## Tools for Complexity Analysis

- **radon**: Calculate cyclomatic complexity
- **pylint**: Detect complexity issues
- **mccabe**: Python complexity analyzer

```bash
pip install radon
radon cc your_package/
```

---
*Generated to help reduce code complexity and improve maintainability.*
"""
    
    def _generate_config_content(self, filename: str) -> str:
        """Generate configuration file content"""
        if filename == ".flake8":
            return """[flake8]
max-line-length = 88
select = E,W,F
ignore = 
    E203,  # whitespace before ':'
    E501,  # line too long
    W503,  # line break before binary operator
exclude = 
    .git,
    __pycache__,
    venv,
    .venv,
    build,
    dist,
    *.egg-info
max-complexity = 10
"""
        elif filename == "pyproject.toml":
            return """[tool.poetry]
name = "your-package"
version = "0.1.0"
description = "Your package description"
authors = ["Your Name <your.email@example.com>"]

[tool.poetry.dependencies]
python = "^3.7"

[tool.poetry.group.dev.dependencies]
pytest = "^7.0"
black = "^22.0"
flake8 = "^5.0"
mypy = "^1.0"
isort = "^5.0"

[build-system]
requires = ["poetry-core"]
build-backend = "poetry.core.masonry.api"

[tool.black]
line-length = 88
target-version = ['py37']
include = '\\.pyi?$'

[tool.isort]
profile = "black"
multi_line_output = 3
line_length = 88

[tool.mypy]
python_version = "3.7"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true
"""
        elif filename == ".prettierrc":
            return """{
  "semi": true,
  "trailingComma": "es5",
  "singleQuote": true,
  "printWidth": 80,
  "tabWidth": 2,
  "useTabs": false
}
"""
        elif filename == "eslint.config.js":
            return """module.exports = {
  env: {
    browser: true,
    es2021: true,
    node: true,
  },
  extends: [
    'eslint:recommended',
  ],
  parserOptions: {
    ecmaVersion: 2021,
    sourceType: 'module',
  },
  rules: {
    'indent': ['error', 2],
    'linebreak-style': ['error', 'unix'],
    'quotes': ['error', 'single'],
    'semi': ['error', 'always'],
    'no-unused-vars': 'warn',
    'no-console': 'warn',
  },
};
"""
        elif filename == ".golangci.yml":
            return """linters-settings:
  golint:
    min-confidence: 0.8
  gocyclo:
    min-complexity: 15
  maligned:
    suggest-new: true
  dupl:
    threshold: 100
  goconst:
    min-len: 2
    min-occurrences: 2

linters:
  enable:
    - golint
    - gocyclo
    - gofmt
    - goimports
    - golint
    - ineffassign
    - misspell
    - vet
    - deadcode
    - errcheck

run:
  deadline: 5m
  tests: true
  skip-dirs:
    - vendor
"""
        elif filename == "rustfmt.toml":
            return """edition = "2021"
use_small_heuristics = "Default"
indent_style = "Spaces"
hard_tabs = false
tab_width = 4
newline_style = "Unix"
use_tab_indentation = false
blank_line_upper = false
hide_orange_ripple_prefix_warning = false
force_explicit_abi = true
use_try_shorthand = false
use_field_init_shorthand = false
force_explicit_abi = true
condition_trailing_whitespace = true
single_line_if_else = false
single_line_let_else = true
space_before_fn = false
format_strings = true
format_macro_matches = true
empty_item_single_line = true
struct_lit_single_line = true
fn_single_line = false
where_single_line = false
imports_layout = "Mixed"
merge_derives = true
use_try_shorthand = false
use_field_init_shorthand = false
force_explicit_abi = true
condition_trailing_whitespace = true
"""
        return f"""# Configuration file for {filename}
# Add your configuration here
"""

    # Public interface methods
    def format_code(self, task: Dict) -> bool:
        """Format code according to task"""
        return self._format_code(task)
    
    def apply_linting(self, task: Dict) -> bool:
        """Apply linting fixes"""
        return self._apply_linting(task)