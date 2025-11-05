#!/usr/bin/env python3
"""
Documentation Automator
Automatically improves and maintains project documentation
"""

import os
import re
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import logging
from datetime import datetime

class DocumentationAutomator:
    """Automatically improves project documentation"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.doc_files = self._find_documentation_files()
    
    def _find_documentation_files(self) -> List[str]:
        """Find existing documentation files"""
        doc_patterns = [
            "*.md", "*.rst", "*.txt",
            "docs/**/*.md", "docs/**/*.rst",
            "**/README*", "**/CHANGELOG*", "**/CONTRIBUTING*",
            "**/LICENSE*", "**/INSTALL*", "**/SETUP*"
        ]
        
        doc_files = []
        for pattern in doc_patterns:
            doc_files.extend([str(p) for p in Path('.').glob(pattern)])
        
        # Remove duplicates
        return list(set(doc_files))
    
    def get_documentation_tasks(self) -> List[Dict]:
        """Get list of documentation improvement tasks"""
        tasks = []
        
        # Check for missing documentation files
        missing_files_task = self._check_missing_documentation()
        if missing_files_task:
            tasks.append(missing_files_task)
        
        # Check documentation formatting and structure
        formatting_task = self._check_documentation_formatting()
        if formatting_task:
            tasks.append(formatting_task)
        
        # Check code documentation
        code_doc_task = self._check_code_documentation()
        if code_doc_task:
            tasks.append(code_doc_task)
        
        # Check API documentation
        api_doc_task = self._check_api_documentation()
        if api_doc_task:
            tasks.append(api_doc_task)
        
        return tasks
    
    def _check_missing_documentation(self) -> Optional[Dict]:
        """Check for missing documentation files"""
        expected_docs = [
            ("README.md", "Project overview and setup instructions"),
            ("CONTRIBUTING.md", "Contribution guidelines"),
            ("CHANGELOG.md", "Version history and changes"),
            ("LICENSE", "License information"),
            ("docs/api.md", "API documentation"),
            ("docs/installation.md", "Installation guide"),
            ("docs/usage.md", "Usage examples"),
            ("docs/development.md", "Development setup")
        ]
        
        missing_files = []
        for filename, description in expected_docs:
            if not Path(filename).exists():
                missing_files.append((filename, description))
        
        if missing_files:
            return {
                "type": "create_documentation",
                "description": f"Create {len(missing_files)} missing documentation files",
                "priority": 2,
                "action": self._create_missing_documentation,
                "files": missing_files
            }
        
        return None
    
    def _check_documentation_formatting(self) -> Optional[Dict]:
        """Check documentation formatting and consistency"""
        formatting_issues = []
        
        for doc_file in self.doc_files[:10]:  # Limit check to first 10 files
            if not Path(doc_file).exists():
                continue
            
            try:
                with open(doc_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Check for common formatting issues
                issues = self._analyze_file_formatting(doc_file, content)
                if issues:
                    formatting_issues.extend(issues)
            except Exception as e:
                self.logger.warning(f"Could not analyze {doc_file}: {str(e)}")
        
        if formatting_issues:
            return {
                "type": "format_documentation",
                "description": f"Fix {len(formatting_issues)} formatting issues in documentation",
                "priority": 3,
                "action": self._fix_documentation_formatting,
                "issues": formatting_issues
            }
        
        return None
    
    def _check_code_documentation(self) -> Optional[Dict]:
        """Check code documentation quality"""
        try:
            # Scan Python files for undocumented functions/classes
            undoc_items = self._scan_undocumented_code()
            
            if undoc_items > 5:  # If many undocumented items
                return {
                    "type": "improve_code_docs",
                    "description": f"Improve documentation for {undoc_items} code items",
                    "priority": 4,
                    "action": self._improve_code_documentation,
                    "undocumented_count": undoc_items
                }
        except Exception as e:
            self.logger.warning(f"Could not scan code documentation: {str(e)}")
        
        return None
    
    def _check_api_documentation(self) -> Optional[Dict]:
        """Check API documentation completeness"""
        try:
            # Check if API docs exist and are comprehensive
            api_doc_paths = ["docs/api.md", "API.md", "api.md"]
            
            existing_api_docs = [p for p in api_doc_paths if Path(p).exists()]
            
            if not existing_api_docs:
                return {
                    "type": "create_api_docs",
                    "description": "Create comprehensive API documentation",
                    "priority": 5,
                    "action": self._create_api_documentation
                }
            elif self._needs_api_doc_improvement(existing_api_docs[0]):
                return {
                    "type": "improve_api_docs",
                    "description": "Enhance existing API documentation",
                    "priority": 5,
                    "action": self._improve_api_documentation,
                    "file": existing_api_docs[0]
                }
        except Exception as e:
            self.logger.warning(f"Could not check API documentation: {str(e)}")
        
        return None
    
    def _analyze_file_formatting(self, filename: str, content: str) -> List[Dict]:
        """Analyze formatting issues in a documentation file"""
        issues = []
        
        # Check for missing newlines
        if content and not content.endswith('\n'):
            issues.append({
                "file": filename,
                "type": "missing_final_newline",
                "description": "File should end with a newline"
            })
        
        # Check for trailing whitespace
        lines = content.split('\n')
        for i, line in enumerate(lines, 1):
            if line.rstrip() != line:
                issues.append({
                    "file": filename,
                    "line": i,
                    "type": "trailing_whitespace",
                    "description": "Line has trailing whitespace"
                })
        
        # Check for consistent heading structure
        if self._has_inconsistent_headings(content):
            issues.append({
                "file": filename,
                "type": "inconsistent_headings",
                "description": "Inconsistent heading structure (use # ## ### consistently)"
            })
        
        # Check for missing table of contents in large files
        if len(content) > 2000 and "Table of Contents" not in content and "TOC" not in content:
            issues.append({
                "file": filename,
                "type": "missing_toc",
                "description": "Large file should have a table of contents"
            })
        
        return issues
    
    def _has_inconsistent_headings(self, content: str) -> bool:
        """Check if headings are used inconsistently"""
        lines = content.split('\n')
        heading_pattern = re.compile(r'^#{1,6}\s+')
        
        heading_levels = []
        for line in lines:
            match = heading_pattern.match(line)
            if match:
                level = len(match.group())
                heading_levels.append(level)
        
        # Check for jumps in heading levels (e.g., # to ###)
        for i in range(len(heading_levels) - 1):
            if heading_levels[i + 1] > heading_levels[i] + 1:
                return True
        
        return False
    
    def _scan_undocumented_code(self) -> int:
        """Scan for undocumented functions and classes"""
        undoc_count = 0
        
        for file_path in Path('.').rglob('*.py'):
            if file_path.name.startswith('.') or 'venv' in str(file_path):
                continue
            
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Find functions and classes
                functions = re.findall(r'def\s+(\w+)\s*\([^)]*\):', content)
                classes = re.findall(r'class\s+(\w+)', content)
                
                # Count docstrings
                docstrings = re.findall(r'""".*?"""', content, re.DOTALL)
                
                # Simple heuristic: if more functions than docstrings, some are undocumented
                total_items = len(functions) + len(classes)
                if total_items > len(docstrings):
                    undoc_count += total_items - len(docstrings)
                
            except Exception:
                continue
        
        return min(undoc_count, 50)  # Cap to avoid overcounting
    
    def _needs_api_doc_improvement(self, api_file: str) -> bool:
        """Check if API documentation needs improvement"""
        try:
            with open(api_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Check for minimal content
            if len(content) < 500:
                return True
            
            # Check for missing common sections
            required_sections = ["Installation", "Usage", "Examples", "API Reference"]
            missing_sections = [section for section in required_sections 
                              if section not in content]
            
            if len(missing_sections) > 2:
                return True
        
        except Exception:
            return True
        
        return False
    
    def _create_missing_documentation(self, task: Dict) -> bool:
        """Create missing documentation files"""
        files = task.get('files', [])
        created = 0
        
        for filename, description in files:
            try:
                if not Path(filename).parent.exists():
                    Path(filename).parent.mkdir(parents=True, exist_ok=True)
                
                content = self._generate_file_content(filename, description)
                
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                created += 1
                self.logger.info(f"Created {filename}")
            except Exception as e:
                self.logger.error(f"Failed to create {filename}: {str(e)}")
        
        return created > 0
    
    def _generate_file_content(self, filename: str, description: str) -> str:
        """Generate content for documentation files"""
        filename_lower = filename.lower()
        
        if "readme" in filename_lower:
            return self._generate_readme_content()
        elif "contributing" in filename_lower:
            return self._generate_contributing_content()
        elif "changelog" in filename_lower:
            return self._generate_changelog_content()
        elif "installation" in filename_lower or "install" in filename_lower:
            return self._generate_installation_content()
        elif "usage" in filename_lower:
            return self._generate_usage_content()
        elif "api" in filename_lower:
            return self._generate_api_content()
        elif "development" in filename_lower:
            return self._generate_development_content()
        else:
            return self._generate_generic_doc_content(filename, description)
    
    def _fix_documentation_formatting(self, task: Dict) -> bool:
        """Fix documentation formatting issues"""
        issues = task.get('issues', [])
        fixed_files = set()
        
        for issue in issues:
            try:
                file_path = issue['file']
                if file_path in fixed_files:
                    continue
                
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Apply fixes
                content = self._apply_formatting_fixes(content)
                
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                fixed_files.add(file_path)
                self.logger.info(f"Fixed formatting in {file_path}")
            except Exception as e:
                self.logger.error(f"Failed to fix formatting in {issue['file']}: {str(e)}")
        
        return len(fixed_files) > 0
    
    def _apply_formatting_fixes(self, content: str) -> str:
        """Apply common formatting fixes"""
        lines = content.split('\n')
        
        # Remove trailing whitespace
        lines = [line.rstrip() for line in lines]
        
        # Ensure file ends with newline
        if lines and lines[-1]:
            lines.append('')
        
        return '\n'.join(lines)
    
    def _improve_code_documentation(self, task: Dict) -> bool:
        """Improve code documentation"""
        try:
            # Create a code documentation guide
            guide_content = self._generate_code_doc_guide(task.get('undocumented_count', 0))
            with open("CODE_DOCUMENTATION_GUIDE.md", 'w') as f:
                f.write(guide_content)
            
            self.logger.info("Created code documentation guide")
            return True
        except Exception as e:
            self.logger.error(f"Failed to improve code documentation: {str(e)}")
            return False
    
    def _create_api_documentation(self, task: Dict) -> bool:
        """Create comprehensive API documentation"""
        try:
            api_content = self._generate_api_content()
            with open("docs/api.md", 'w') as f:
                f.write(api_content)
            
            self.logger.info("Created API documentation")
            return True
        except Exception as e:
            self.logger.error(f"Failed to create API documentation: {str(e)}")
            return False
    
    def _improve_api_documentation(self, task: Dict) -> bool:
        """Improve existing API documentation"""
        try:
            api_file = task.get('file', 'docs/api.md')
            with open(api_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            improved_content = self._enhance_api_content(content)
            
            with open(api_file, 'w', encoding='utf-8') as f:
                f.write(improved_content)
            
            self.logger.info(f"Improved API documentation in {api_file}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to improve API documentation: {str(e)}")
            return False
    
    def improve_documentation(self, task: Dict) -> bool:
        """Improve documentation based on task type"""
        task_type = task.get('type')
        
        if task_type == "create_documentation":
            return self._create_missing_documentation(task)
        elif task_type == "format_documentation":
            return self._fix_documentation_formatting(task)
        elif task_type == "improve_code_docs":
            return self._improve_code_documentation(task)
        elif task_type == "create_api_docs":
            return self._create_api_documentation(task)
        elif task_type == "improve_api_docs":
            return self._improve_api_documentation(task)
        
        return False
    
    # Content generation methods
    def _generate_readme_content(self) -> str:
        return """# Project Name

A brief description of your project and its main purpose.

## 🚀 Quick Start

### Installation
```bash
pip install your-package-name
```

### Basic Usage
```python
import your_package

# Your code example here
result = your_package.main_function()
print(result)
```

## 📋 Features

- Feature 1: Description
- Feature 2: Description  
- Feature 3: Description

## 🛠️ Development

### Prerequisites
- Python 3.7+
- pip or conda

### Setup
```bash
git clone https://github.com/username/project-name.git
cd project-name
pip install -r requirements.txt
```

### Running Tests
```bash
python -m pytest tests/
```

## 📖 Documentation

- [API Reference](docs/api.md)
- [Installation Guide](docs/installation.md)
- [Usage Examples](docs/usage.md)

## 🤝 Contributing

Please read [CONTRIBUTING.md](CONTRIBUTING.md) for details on our code of conduct and development process.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
"""
    
    def _generate_contributing_content(self) -> str:
        return """# Contributing to [Project Name]

Thank you for your interest in contributing! This document provides guidelines for contributing to the project.

## Code of Conduct

- Be respectful and inclusive
- Focus on constructive feedback
- Help create a welcoming environment for all contributors

## Getting Started

1. Fork the repository
2. Clone your fork: `git clone https://github.com/YOUR-USERNAME/project-name.git`
3. Create a virtual environment
4. Install dependencies: `pip install -r requirements.txt`
5. Make your changes

## Development Process

### Branch Naming
- Feature: `feature/your-feature-name`
- Bug fix: `fix/issue-description`
- Documentation: `docs/your-doc-update`

### Commit Messages
Use clear, descriptive commit messages:
- `feat: add user authentication`
- `fix: resolve login redirect issue`
- `docs: update installation instructions`

### Pull Requests

1. **Before submitting:**
   - Run tests: `python -m pytest`
   - Check code style: `flake8`
   - Update documentation if needed

2. **PR Description should include:**
   - Brief description of changes
   - Related issue number
   - Screenshots (if applicable)
   - Testing notes

## Code Style

- Follow PEP 8 for Python code
- Use type hints where appropriate
- Write descriptive docstrings
- Keep functions focused and small

## Testing

- Write tests for new features
- Ensure all tests pass before submitting
- Aim for good test coverage

## Documentation

- Update relevant documentation with your changes
- Add docstrings to new functions/classes
- Include usage examples where helpful

## Questions?

Feel free to open an issue for questions or clarification!
"""
    
    def _generate_changelog_content(self) -> str:
        return """# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- TODO: Add new features here

### Changed
- TODO: List changes here

### Deprecated
- TODO: List deprecated features here

### Removed
- TODO: List removed features here

### Fixed
- TODO: List bug fixes here

### Security
- TODO: List security improvements here

## [1.0.0] - 2025-01-01

### Added
- Initial release
- Basic functionality
- Documentation
- Test suite
"""
    
    def _generate_installation_content(self) -> str:
        return """# Installation Guide

This guide will help you install and set up the project.

## Prerequisites

- Python 3.7 or higher
- pip or conda package manager

## Installation Methods

### Using pip

```bash
pip install your-package-name
```

### From Source

```bash
git clone https://github.com/username/project-name.git
cd project-name
pip install -e .
```

### Using Poetry

```bash
poetry add your-package-name
```

## Development Installation

For development setup:

```bash
git clone https://github.com/username/project-name.git
cd project-name

# Using pip
pip install -r requirements-dev.txt
pip install -e .

# Or using Poetry
poetry install
```

## Verification

Verify your installation:

```python
import your_package
print(your_package.__version__)
```

## Troubleshooting

### Common Issues

**Issue: Module not found**
- Solution: Make sure you've activated your virtual environment

**Issue: Permission denied**
- Solution: Try using `pip install --user your-package-name`

**Issue: Version conflicts**
- Solution: Use a virtual environment to isolate dependencies

## Next Steps

- Read the [Usage Guide](usage.md)
- Check the [API Documentation](api.md)
- Visit the [GitHub Repository](https://github.com/username/project-name)
"""
    
    def _generate_usage_content(self) -> str:
        return """# Usage Guide

This guide demonstrates how to use the project effectively.

## Basic Usage

### Import and Initialize

```python
from your_package import MainClass

# Initialize
instance = MainClass()
```

### Common Operations

```python
# Process data
result = instance.process_data(input_data)

# Configuration
instance.configure(option='value')

# Get results
output = instance.get_results()
```

## Advanced Usage

### Configuration Options

```python
# Set configuration
instance.set_config({
    'option1': 'value1',
    'option2': 'value2'
})
```

### Error Handling

```python
try:
    result = instance.risky_operation()
except SpecificError as e:
    print(f"Operation failed: {e}")
```

## Examples

### Example 1: Basic Setup

```python
from your_package import YourClass

# Create instance
obj = YourClass()

# Use it
result = obj.method()
```

### Example 2: Advanced Configuration

```python
from your_package import AdvancedClass

# With custom settings
advanced = AdvancedClass(
    setting1='value1',
    setting2='value2'
)

# Use advanced features
result = advanced.advanced_method()
```

## Best Practices

1. **Always check documentation** for the latest features
2. **Use appropriate error handling** for robust applications
3. **Configure logging** for debugging when needed
4. **Keep dependencies updated** for security and features

## Performance Tips

- Use batch operations when available
- Configure appropriate timeouts
- Monitor memory usage for large datasets

## Integration Examples

### With Other Libraries

```python
import pandas as pd
from your_package import YourClass

# Load data
data = pd.read_csv('data.csv')

# Process with your library
processor = YourClass()
results = processor.process(data)
```

## Troubleshooting

### Common Issues

**Problem: Unexpected results**
- Check input data format
- Verify configuration settings
- Review documentation for correct usage

**Problem: Performance issues**
- Consider using batch operations
- Check for memory leaks
- Optimize configuration parameters

## Getting Help

- Check the [API Documentation](api.md)
- Search [existing issues](https://github.com/username/project-name/issues)
- Create a [new issue](https://github.com/username/project-name/issues/new)
"""
    
    def _generate_api_content(self) -> str:
        return """# API Documentation

This document provides detailed information about the project's API.

## Overview

The API provides access to the core functionality of the project. All classes and methods are designed to be intuitive and well-documented.

## Main Classes

### YourClass

Main class for core functionality.

```python
from your_package import YourClass

class YourClass:
    def __init__(self, config=None):
        """Initialize the class.
        
        Args:
            config (dict, optional): Configuration dictionary
        """
        pass
```

#### Methods

##### `method_name(param1, param2)`

Brief description of the method.

**Parameters:**
- `param1` (str): Description of param1
- `param2` (int): Description of param2

**Returns:**
- `dict`: Description of return value

**Example:**
```python
instance = YourClass()
result = instance.method_name('test', 42)
```

##### `another_method()`

Description of another method.

**Returns:**
- `bool`: True if successful, False otherwise

## Utility Functions

### `utility_function(data)`

Utility function for common operations.

**Parameters:**
- `data` (list): Input data

**Returns:**
- `list`: Processed data

## Configuration

### Available Options

- `option1` (str): Description of option1
- `option2` (bool): Description of option2
- `option3` (int): Description of option3

### Configuration Example

```python
config = {
    'option1': 'value1',
    'option2': True,
    'option3': 100
}

instance = YourClass(config=config)
```

## Error Handling

### Common Exceptions

- `ValidationError`: Raised when input validation fails
- `ConfigurationError`: Raised when configuration is invalid
- `ProcessingError`: Raised when processing fails

### Error Handling Example

```python
try:
    result = instance.method_name('invalid', 'input')
except ValidationError as e:
    print(f"Validation failed: {e}")
```

## Rate Limiting

The API implements rate limiting to ensure fair usage:
- Default limit: 100 requests per minute
- Burst limit: 10 requests per second

## Changelog

See [CHANGELOG.md](../CHANGELOG.md) for API changes.

## Support

For API support and questions:
- Email: support@example.com
- Issues: [GitHub Issues](https://github.com/username/project-name/issues)
- Documentation: [Project Wiki](https://github.com/username/project-name/wiki)
"""
    
    def _generate_development_content(self) -> str:
        return """# Development Guide

This guide covers development setup and processes for the project.

## Development Environment Setup

### Prerequisites

- Python 3.7+
- Git
- Virtual environment tool (venv, conda, etc.)

### Initial Setup

```bash
# Clone repository
git clone https://github.com/username/project-name.git
cd project-name

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\\Scripts\\activate

# Install development dependencies
pip install -r requirements-dev.txt
pip install -e .

# Or with Poetry
poetry install
```

### Pre-commit Hooks

Install pre-commit hooks for code quality:

```bash
pre-commit install
```

## Development Workflow

### Making Changes

1. Create a feature branch: `git checkout -b feature/your-feature`
2. Make your changes
3. Run tests and linting
4. Commit with descriptive messages
5. Push and create a pull request

### Code Quality Tools

#### Running Tests

```bash
# Run all tests
python -m pytest

# Run with coverage
python -m pytest --cov=your_package tests/

# Run specific test file
python -m pytest tests/test_specific.py
```

#### Code Formatting

```bash
# Format code
black your_package/ tests/

# Sort imports
isort your_package/ tests/

# Check formatting
black --check your_package/ tests/
isort --check-only your_package/ tests/
```

#### Linting

```bash
# Run linter
flake8 your_package/ tests/

# Type checking
mypy your_package/
```

## Project Structure

```
project-name/
├── your_package/          # Main package
│   ├── __init__.py
│   ├── core.py
│   └── utils.py
├── tests/                 # Test suite
│   ├── __init__.py
│   ├── test_core.py
│   └── test_utils.py
├── docs/                  # Documentation
├── scripts/              # Utility scripts
├── requirements.txt      # Dependencies
├── requirements-dev.txt  # Development dependencies
├── pyproject.toml       # Project configuration
└── README.md           # Project documentation
```

## Testing Strategy

### Test Types

1. **Unit Tests**: Test individual functions/methods
2. **Integration Tests**: Test component interactions
3. **Edge Case Tests**: Test boundary conditions

### Test Data

- Use factories for test data generation
- Mock external dependencies
- Create realistic test scenarios

### Test Coverage

- Aim for >80% code coverage
- Test all public APIs
- Include edge cases and error conditions

## Documentation

### Docstrings

Use Google-style docstrings:

```python
def example_function(param1, param2):
    """Brief description of the function.
    
    Longer description if needed.
    
    Args:
        param1 (str): Description of param1
        param2 (int): Description of param2
        
    Returns:
        bool: Description of return value
        
    Raises:
        ValueError: When param2 is invalid
        
    Example:
        >>> result = example_function('test', 42)
        >>> print(result)
        True
    """
    return True
```

### Building Documentation

```bash
# Generate API documentation
sphinx-build -b html docs/ docs/_build/html

# Or using MkDocs (if configured)
mkdocs serve
```

## Debugging

### Using Debugger

```python
import pdb; pdb.set_trace()  # Basic debugging

# Or with ipdb (better)
import ipdb; ipdb.set_trace()
```

### Logging

```python
import logging

logger = logging.getLogger(__name__)
logger.info("Informational message")
logger.debug("Debug message")
```

## Release Process

1. Update version in relevant files
2. Update CHANGELOG.md
3. Create release PR
4. After merge, create GitHub release
5. Build and publish package

## Performance Considerations

- Profile code with cProfile or line_profiler
- Use appropriate data structures
- Consider caching for expensive operations
- Monitor memory usage

## Security

- Never commit secrets or API keys
- Use environment variables for configuration
- Validate all input data
- Keep dependencies updated
- Use secure coding practices

## Getting Help

- Ask questions in issues
- Check existing documentation
- Review code examples
- Contact maintainers
"""
    
    def _generate_generic_doc_content(self, filename: str, description: str) -> str:
        return f"""# {filename}

{description}

## Overview

This document provides information about {description.lower()}.

## Content

Add content here...

## Examples

```python
# Add examples here
```

## Related Documentation

- [Main README](../README.md)
- [API Documentation](api.md)
- [Contributing Guidelines](../CONTRIBUTING.md)

---
*This file was automatically generated. Please update with relevant content.*
"""
    
    def _generate_code_doc_guide(self, undoc_count: int) -> str:
        return f"""# Code Documentation Guide

This guide helps improve code documentation quality.

## Current Status

Found approximately {undoc_count} undocumented code items that could benefit from documentation.

## Documentation Standards

### Functions and Methods

```python
def example_function(param1, param2=None):
    """Brief description of what the function does.
    
    Longer description if the function is complex. Explain the purpose,
    behavior, and any important considerations.
    
    Args:
        param1 (str): Description of param1 and its expected format
        param2 (str, optional): Description of optional param2
        
    Returns:
        dict: Description of return value structure and meaning
        
    Raises:
        ValueError: When param1 is empty or invalid
        TypeError: When param1 is not a string
        
    Example:
        >>> result = example_function('test', param2='optional')
        >>> print(result['status'])
        'success'
    """
    pass
```

### Classes

```python
class ExampleClass:
    """Brief description of the class and its main purpose.
    
    More detailed description if needed. Explain the class's role
    in the system and how it should be used.
    """
    
    def __init__(self, required_param, optional_param="default"):
        """Initialize the class.
        
        Args:
            required_param (str): Description of required parameter
            optional_param (str, optional): Default parameter description
        """
        self.required_param = required_param
        self.optional_param = optional_param
        
    def example_method(self, data):
        """Description of this method.
        
        Args:
            data: Description of data parameter
            
        Returns:
            Description of return value
        """
        pass
```

### Modules

```python
"""Module docstring - brief description.

More detailed description of the module's purpose and contents.
Describes what functionality is provided and when to use it.

Attributes:
    module_constant (str): Description of module-level constants
    ModuleClass: Main class exported by this module
"""

from typing import Dict, List

module_constant = "constant_value"
```

## Type Hints

Use type hints for better IDE support and documentation:

```python
from typing import List, Dict, Optional, Union

def process_data(items: List[str]) -> Dict[str, int]:
    \"\"\"Process a list of strings into a frequency dictionary.
    
    Args:
        items: List of strings to count
        
    Returns:
        Dictionary mapping strings to their frequency
    \"\"\"
    return {item: items.count(item) for item in items}

def optional_example(value: Optional[str] = None) -> str:
    \"\"\"Example with optional parameter.
    
    Args:
        value: Optional string value
        
    Returns:
        The input value or 'default' if None
    \"\"\"
    return value or 'default'
```

## Best Practices

1. **Write docstrings for all public functions and classes**
2. **Include parameter descriptions with types**
3. **Document return values and their meaning**
4. **Add usage examples for complex functions**
5. **Explain edge cases and exceptions**
6. **Keep docstrings up-to-date with code changes**

## Tools for Documentation

- **IDE Support**: Modern IDEs use docstrings for autocomplete
- **Sphinx**: Generate API documentation from docstrings
- **pydoc**: Built-in Python documentation generator
- **Type checkers**: mypy validates type hints

## Checklist

- [ ] All public functions have docstrings
- [ ] All classes have docstrings
- [ ] Parameters are documented with types
- [ ] Return values are documented
- [ ] Examples are included for complex functions
- [ ] Exceptions are documented
- [ ] Type hints are used consistently

---
*This guide was generated to help improve code documentation quality.*
"""
    
    def _enhance_api_content(self, content: str) -> str:
        """Enhance existing API content"""
        enhanced = content
        
        # Add missing sections if content is minimal
        if len(content) < 1000:
            sections_to_add = [
                "## Installation\n\nSee the main README for installation instructions.\n",
                "## Basic Usage\n\n```python\nfrom your_package import YourClass\n\ninstance = YourClass()\nresult = instance.method()\n```\n",
                "## Configuration\n\nCustomize behavior through configuration parameters.\n",
                "## Error Handling\n\nHandle exceptions appropriately in your code.\n"
            ]
            
            enhanced += "\n".join(sections_to_add)
        
        # Improve formatting if needed
        enhanced = enhanced.replace("```python", "```python\n")
        enhanced = enhanced.replace("```\n\n```", "```\n\n")
        
        return enhanced