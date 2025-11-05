#!/usr/bin/env python3
"""
Repository Health Checker
Scans and improves repository health metrics
"""

import os
import re
from pathlib import Path
from typing import List, Dict, Optional
import logging

class RepoHealthChecker:
    """Analyzes and improves repository health"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def get_improvement_tasks(self) -> List[Dict]:
        """Get list of repository health improvement tasks"""
        tasks = []
        
        # Check README improvements
        readme_task = self._check_readme_improvements()
        if readme_task:
            tasks.append(readme_task)
        
        # Check TODO cleanup
        todo_task = self._check_todo_cleanup()
        if todo_task:
            tasks.append(todo_task)
        
        # Check code documentation
        doc_task = self._check_code_documentation()
        if doc_task:
            tasks.append(doc_task)
        
        # Check project structure
        structure_task = self._check_project_structure()
        if structure_task:
            tasks.append(structure_task)
        
        return tasks
    
    def _check_readme_improvements(self) -> Optional[Dict]:
        """Check if README needs improvements"""
        readme_files = ["README.md", "README.rst", "README.txt", "readme.md"]
        readme_path = None
        
        for filename in readme_files:
            if Path(filename).exists():
                readme_path = filename
                break
        
        if not readme_path:
            return {
                "type": "readme_creation",
                "description": "Create README.md file",
                "priority": 1,
                "action": self._create_readme
            }
        
        # Check if README is basic/short
        with open(readme_path, 'r') as f:
            content = f.read()
        
        if len(content) < 100 or self._is_basic_readme(content):
            return {
                "type": "readme_update",
                "description": "Enhance README with comprehensive project information",
                "priority": 2,
                "action": self._update_readme,
                "file": readme_path,
                "content": content
            }
        
        return None
    
    def _check_todo_cleanup(self) -> Optional[Dict]:
        """Check if TODO items need cleanup"""
        todo_pattern = r'(?i)(TODO|FIXME|XXX|HACK|NOTE):'
        files_checked = 0
        todos_found = 0
        
        for file_path in Path('.').rglob('*.py'):
            if files_checked > 50:  # Limit search for performance
                break
                
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    if re.search(todo_pattern, content):
                        todos_found += 1
                files_checked += 1
            except:
                continue
        
        if todos_found > 5:  # If many TODOs exist
            return {
                "type": "todo_cleanup",
                "description": f"Organize and prioritize {todos_found} TODO items found",
                "priority": 3,
                "action": self._cleanup_todos,
                "todo_count": todos_found
            }
        
        return None
    
    def _check_code_documentation(self) -> Optional[Dict]:
        """Check if code documentation can be improved"""
        undoc_functions = 0
        total_functions = 0
        
        for file_path in Path('.').rglob('*.py'):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    # Simple heuristic: count functions vs documented functions
                    functions = re.findall(r'def\s+\w+', content)
                    docstrings = re.findall(r'""".*?"""', content, re.DOTALL)
                    total_functions += len(functions)
                    if len(functions) > len(docstrings):
                        undoc_functions += len(functions) - len(docstrings)
            except:
                continue
        
        if undoc_functions > 3:
            return {
                "type": "code_documentation",
                "description": f"Add documentation to {undoc_functions} undocumented functions",
                "priority": 4,
                "action": self._improve_code_documentation,
                "undocumented_count": undoc_functions
            }
        
        return None
    
    def _check_project_structure(self) -> Optional[Dict]:
        """Check project structure and organization"""
        improvements = []
        
        # Check for common missing files
        common_files = [
            ("LICENSE", "Add license file"),
            (".gitignore", "Add .gitignore file"),
            ("requirements.txt", "Add requirements.txt for Python projects"),
            ("package.json", "Add package.json for Node.js projects"),
            ("pyproject.toml", "Add pyproject.toml for modern Python projects"),
            (".editorconfig", "Add .editorconfig for consistent editor settings")
        ]
        
        for filename, description in common_files:
            if not Path(filename).exists():
                improvements.append(description)
        
        if len(improvements) >= 2:
            return {
                "type": "project_structure",
                "description": "Improve project structure with missing configuration files",
                "priority": 5,
                "action": self._improve_project_structure,
                "improvements": improvements
            }
        
        return None
    
    def _is_basic_readme(self, content: str) -> bool:
        """Check if README is basic (has minimal content)"""
        basic_indicators = [
            "# ",
            "## ",
            "### ",
            "```",
            "- ",
            "* ",
            "1. "
        ]
        
        return sum(1 for indicator in basic_indicators if indicator in content) < 3
    
    def _create_readme(self, task: Dict) -> bool:
        """Create a new README file"""
        try:
            readme_content = self._generate_readme_content()
            with open("README.md", 'w') as f:
                f.write(readme_content)
            self.logger.info("Created README.md")
            return True
        except Exception as e:
            self.logger.error(f"Failed to create README: {str(e)}")
            return False
    
    def _update_readme(self, task: Dict) -> bool:
        """Update existing README with enhanced content"""
        try:
            current_content = task.get('content', '')
            enhanced_content = self._enhance_readme_content(current_content)
            
            with open(task['file'], 'w') as f:
                f.write(enhanced_content)
            
            self.logger.info(f"Updated {task['file']}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to update README: {str(e)}")
            return False
    
    def _cleanup_todos(self, task: Dict) -> bool:
        """Clean up TODO items and improve organization"""
        try:
            # This would typically parse and organize TODOs
            # For now, we'll create a TODO organization file
            todo_content = self._generate_todo_organization(task.get('todo_count', 0))
            
            with open("TODO.md", 'w') as f:
                f.write(todo_content)
            
            self.logger.info("Created TODO.md organization file")
            return True
        except Exception as e:
            self.logger.error(f"Failed to cleanup todos: {str(e)}")
            return False
    
    def _improve_code_documentation(self, task: Dict) -> bool:
        """Improve code documentation"""
        try:
            # This would typically add docstrings to functions
            # For now, create a documentation guide
            doc_content = self._generate_documentation_guide(task.get('undocumented_count', 0))
            
            with open("DOCUMENTATION_GUIDE.md", 'w') as f:
                f.write(doc_content)
            
            self.logger.info("Created documentation guide")
            return True
        except Exception as e:
            self.logger.error(f"Failed to improve documentation: {str(e)}")
            return False
    
    def _improve_project_structure(self, task: Dict) -> bool:
        """Improve project structure with configuration files"""
        try:
            improvements = task.get('improvements', [])
            for improvement in improvements:
                if "license" in improvement.lower():
                    self._create_license_file()
                elif "gitignore" in improvement.lower():
                    self._create_gitignore()
                elif "requirements" in improvement.lower():
                    self._create_requirements()
                elif "editorconfig" in improvement.lower():
                    self._create_editorconfig()
            
            self.logger.info("Improved project structure")
            return True
        except Exception as e:
            self.logger.error(f"Failed to improve project structure: {str(str)}")
            return False
    
    def _generate_readme_content(self) -> str:
        """Generate comprehensive README content"""
        return """# Project Name

A brief description of your project and its purpose.

## 🚀 Quick Start

### Installation
```bash
# Add installation instructions here
```

### Usage
```bash
# Add usage examples here
```

## 📋 Features

- Feature 1
- Feature 2
- Feature 3

## 🛠️ Development

### Prerequisites
- List prerequisites here

### Setup
```bash
# Add setup instructions
```

### Contributing
1. Fork the repository
2. Create your feature branch
3. Commit your changes
4. Push to the branch
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🤝 Support

If you have any questions or need help, please open an issue.
"""
    
    def _enhance_readme_content(self, current_content: str) -> str:
        """Enhance existing README content"""
        # Simple enhancement - add more structure to basic READMEs
        enhanced = current_content
        
        if "# " not in enhanced:
            enhanced = f"# Project Name\n\n{enhanced}"
        
        if "## Features" not in enhanced:
            enhanced += "\n\n## Features\n\n- Comprehensive feature list coming soon\n"
        
        if "## Installation" not in enhanced:
            enhanced += "\n\n## Installation\n\n```bash\n# Installation instructions\n```\n"
        
        if "## Contributing" not in enhanced:
            enhanced += "\n\n## Contributing\n\nContributions are welcome! Please follow the standard contribution guidelines.\n"
        
        return enhanced
    
    def _generate_todo_organization(self, todo_count: int) -> str:
        """Generate TODO organization content"""
        return f"""# TODO - Project Tasks

Total TODO items found: {todo_count}

## 🔥 High Priority
- [ ] Critical issue to address
- [ ] Important feature to implement

## 📋 Medium Priority
- [ ] Nice-to-have features
- [ ] Code improvements

## 💡 Future Ideas
- [ ] Long-term improvements
- [ ] Experimental features

## 📝 Notes
- All TODO items should be organized and prioritized
- Consider using project management tools for better tracking
- Regular cleanup of completed tasks is recommended

---
*This file is automatically generated. Update it as needed.*
"""
    
    def _generate_documentation_guide(self, undoc_count: int) -> str:
        """Generate documentation improvement guide"""
        return f"""# Documentation Improvement Guide

Found {undoc_count} undocumented functions that could benefit from documentation.

## 📚 Why Documentation Matters

Good documentation makes code:
- More maintainable
- Easier to understand
- More professional
- Better for collaboration

## 🎯 Areas to Focus On

### Functions and Methods
```python
def example_function(param1: str, param2: int) -> bool:
    '''
    Brief description of what the function does.
    
    Args:
        param1: Description of param1
        param2: Description of param2
    
    Returns:
        Description of return value
        
    Raises:
        ValueError: When param2 is negative
    '''
    pass
```

### Classes
```python
class ExampleClass:
    '''
    Brief description of the class purpose.
    '''
    def __init__(self, param: str):
        '''
        Initialize the class.
        
        Args:
            param: Description of param
        '''
        pass
```

## 🛠️ Tools for Documentation

- Use docstrings for functions and classes
- Add type hints for better IDE support
- Include usage examples in docstrings
- Document complex algorithms and business logic

## ✅ Checklist

- [ ] Add docstrings to undocumented functions
- [ ] Include parameter descriptions
- [ ] Document return values
- [ ] Add usage examples where helpful
- [ ] Review and update existing documentation

---
*This guide is automatically generated to help improve code documentation.*
"""
    
    def _create_license_file(self):
        """Create a basic license file"""
        license_content = """MIT License

Copyright (c) 2025

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""
        with open("LICENSE", 'w') as f:
            f.write(license_content)
    
    def _create_gitignore(self):
        """Create a comprehensive .gitignore file"""
        gitignore_content = """# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg
MANIFEST

# Virtual environments
venv/
env/
ENV/
env.bak/
venv.bak/

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# OS
.DS_Store
Thumbs.db

# Logs
*.log
logs/

# Node.js (if applicable)
node_modules/
npm-debug.log*
yarn-debug.log*
yarn-error.log*

# Temporary files
*.tmp
*.temp
.tmp/
temp/
"""
        with open(".gitignore", 'w') as f:
            f.write(gitignore_content)
    
    def _create_requirements(self):
        """Create requirements.txt file"""
        requirements_content = """# Core dependencies
# Add your project dependencies here
# Example:
# requests>=2.25.0
# numpy>=1.21.0
"""
        with open("requirements.txt", 'w') as f:
            f.write(requirements_content)
    
    def _create_editorconfig(self):
        """Create .editorconfig file"""
        editorconfig_content = """# EditorConfig is awesome: https://EditorConfig.org

# top-most EditorConfig file
root = true

# All files
[*]
charset = utf-8
end_of_line = lf
insert_final_newline = true
trim_trailing_whitespace = true

# Python files
[*.py]
indent_style = space
indent_size = 4

# YAML files
[*.{yml,yaml}]
indent_style = space
indent_size = 2

# JSON files
[*.json]
indent_style = space
indent_size = 2

# Markdown files
[*.md]
trim_trailing_whitespace = false

# Makefiles
[Makefile]
indent_style = tab

# Batch files
[*.{cmd,bat}]
end_of_line = crlf
"""
        with open(".editorconfig", 'w') as f:
            f.write(editorconfig_content)
    
    # Task execution methods
    def update_readme(self, task: Dict) -> bool:
        """Update README file"""
        return self._update_readme(task)
    
    def cleanup_todos(self, task: Dict) -> bool:
        """Clean up TODO items"""
        return self._cleanup_todos(task)
