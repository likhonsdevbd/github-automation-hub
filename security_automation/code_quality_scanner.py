"""
Code Quality Scanner
Automated code quality analysis with linting, formatting, and static analysis.
"""

import subprocess
import json
import re
import os
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import tempfile
import shutil


class CodeQualityScanner:
    """Code quality scanner with support for multiple linters and formatters"""
    
    def __init__(self, project_path: Path):
        self.project_path = Path(project_path)
        self.results = {}
        
        # Define supported tools and their configurations
        self.linters = {
            'flake8': {
                'command': ['flake8', '.', '--format=json'],
                'install_cmd': 'pip install flake8',
                'config_file': '.flake8'
            },
            'pylint': {
                'command': ['pylint', '--output-format=json', '.'],
                'install_cmd': 'pip install pylint',
                'config_file': '.pylintrc'
            },
            'black': {
                'command': ['black', '--check', '--diff', '.'],
                'install_cmd': 'pip install black',
                'config_file': 'pyproject.toml'
            },
            'isort': {
                'command': ['isort', '--check-only', '--diff', '.'],
                'install_cmd': 'pip install isort',
                'config_file': 'pyproject.toml'
            },
            'mypy': {
                'command': ['mypy', '--ignore-missing-imports', '--output-format=json', '.'],
                'install_cmd': 'pip install mypy',
                'config_file': 'mypy.ini'
            },
            'bandit': {
                'command': ['bandit', '-r', '.', '-f', 'json'],
                'install_cmd': 'pip install bandit',
                'config_file': '.bandit'
            },
            'radon': {
                'command': ['radon', 'cc', '-j', '.'],
                'install_cmd': 'pip install radon',
                'config_file': 'pyproject.toml'
            },
            'vulture': {
                'command': ['vulture', '--min-confidence', '80', '--format', 'json', '.'],
                'install_cmd': 'pip install vulture',
                'config_file': '.vulture'
            }
        }
        
    def scan_all(self) -> Dict[str, Any]:
        """Run all code quality scans"""
        results = {}
        
        for tool_name in self.linters.keys():
            results[tool_name] = self._run_linter(tool_name)
        
        # Run additional checks
        results['complexity'] = self._check_complexity()
        results['duplication'] = self._check_code_duplication()
        results['documentation'] = self._check_documentation_coverage()
        
        # Generate summary
        results['summary'] = self._generate_quality_summary(results)
        
        return results
    
    def scan_with_linters(self, linters: List[str], auto_fix: bool = False) -> Dict[str, Any]:
        """Run scans with specific linters"""
        results = {}
        
        for tool_name in linters:
            if tool_name in self.linters:
                results[tool_name] = self._run_linter(tool_name, auto_fix)
            else:
                results[tool_name] = {
                    'status': 'unknown_tool',
                    'error': f'Unknown tool: {tool_name}'
                }
        
        results['summary'] = self._generate_quality_summary(results)
        
        return results
    
    def _run_linter(self, tool_name: str, auto_fix: bool = False) -> Dict[str, Any]:
        """Run a specific linter"""
        print(f"  Running {tool_name}...")
        
        tool_config = self.linters.get(tool_name)
        if not tool_config:
            return {
                'status': 'unknown_tool',
                'error': f'Tool {tool_name} not configured'
            }
        
        try:
            cmd = tool_config['command'][:]  # Copy list
            
            if auto_fix and tool_name in ['black', 'isort']:
                # For formatters, run without --check in auto-fix mode
                if tool_name == 'black':
                    cmd = ['black', '.']
                elif tool_name == 'isort':
                    cmd = ['isort', '.']
            elif auto_fix:
                # Some linters support auto-fix
                if tool_name == 'flake8':
                    cmd.append('--fix')
                elif tool_name == 'autopep8':
                    cmd.append('--in-place')
            
            result = subprocess.run(
                cmd, 
                capture_output=True, 
                text=True, 
                cwd=self.project_path,
                timeout=300  # 5 minute timeout
            )
            
            return self._parse_linter_output(tool_name, result, cmd)
            
        except subprocess.TimeoutExpired:
            return {
                'status': 'timeout',
                'error': f'{tool_name} scan timed out after 5 minutes'
            }
        except FileNotFoundError:
            return {
                'status': 'not_installed',
                'error': f'{tool_name} not found',
                'install_command': tool_config['install_cmd']
            }
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e)
            }
    
    def _parse_linter_output(self, tool_name: str, result: subprocess.CompletedProcess, cmd: List[str]) -> Dict[str, Any]:
        """Parse linter output based on tool type"""
        
        if tool_name == 'flake8':
            return self._parse_flake8_output(result)
        elif tool_name == 'pylint':
            return self._parse_pylint_output(result)
        elif tool_name == 'black':
            return self._parse_black_output(result, cmd)
        elif tool_name == 'isort':
            return self._parse_isort_output(result, cmd)
        elif tool_name == 'mypy':
            return self._parse_mypy_output(result)
        elif tool_name == 'bandit':
            return self._parse_bandit_output(result)
        elif tool_name == 'radon':
            return self._parse_radon_output(result)
        elif tool_name == 'vulture':
            return self._parse_vulture_output(result)
        else:
            # Generic parsing for unknown tools
            return {
                'status': 'success' if result.returncode == 0 else 'issues_found',
                'return_code': result.returncode,
                'stdout': result.stdout,
                'stderr': result.stderr
            }
    
    def _parse_flake8_output(self, result: subprocess.CompletedProcess) -> Dict[str, Any]:
        """Parse Flake8 output"""
        if not result.stdout.strip():
            return {
                'status': 'success',
                'issues_found': 0,
                'issues': []
            }
        
        try:
            issues = json.loads(result.stdout)
            return {
                'status': 'issues_found',
                'issues_found': len(issues),
                'issues': issues
            }
        except json.JSONDecodeError:
            # Flake8 might output in text format
            issues = []
            for line in result.stdout.splitlines():
                if line.strip():
                    # Parse Flake8 text format: file:line:col: error_code message
                    match = re.match(r'([^:]+):(\d+):(\d+):\s+(\w+)\s+(.+)', line)
                    if match:
                        issues.append({
                            'filename': match.group(1),
                            'line': int(match.group(2)),
                            'column': int(match.group(3)),
                            'code': match.group(4),
                            'message': match.group(5)
                        })
            
            return {
                'status': 'issues_found',
                'issues_found': len(issues),
                'issues': issues
            }
    
    def _parse_pylint_output(self, result: subprocess.CompletedProcess) -> Dict[str, Any]:
        """Parse Pylint output"""
        try:
            issues = json.loads(result.stdout) if result.stdout.strip() else []
            
            return {
                'status': 'issues_found',
                'issues_found': len(issues),
                'issues': issues
            }
        except json.JSONDecodeError:
            return {
                'status': 'error',
                'error': 'Failed to parse Pylint JSON output',
                'raw_output': result.stdout
            }
    
    def _parse_black_output(self, result: subprocess.CompletedProcess, cmd: List[str]) -> Dict[str, Any]:
        """Parse Black output"""
        # If cmd contains --check, then we're checking, not fixing
        is_checking = '--check' in cmd or '--diff' in cmd
        
        if result.returncode == 0:
            return {
                'status': 'success',
                'message': 'All files are properly formatted' if is_checking else 'Files formatted successfully'
            }
        else:
            return {
                'status': 'needs_formatting' if is_checking else 'formatted',
                'diff_output': result.stdout,
                'stderr': result.stderr
            }
    
    def _parse_isort_output(self, result: subprocess.CompletedProcess, cmd: List[str]) -> Dict[str, Any]:
        """Parse isort output"""
        # If cmd contains --check-only, then we're checking, not fixing
        is_checking = '--check-only' in cmd or '--diff' in cmd
        
        if result.returncode == 0:
            return {
                'status': 'success',
                'message': 'All imports are properly sorted' if is_checking else 'Imports sorted successfully'
            }
        else:
            return {
                'status': 'needs_sorting' if is_checking else 'sorted',
                'diff_output': result.stdout,
                'stderr': result.stderr
            }
    
    def _parse_mypy_output(self, result: subprocess.CompletedProcess) -> Dict[str, Any]:
        """Parse MyPy output"""
        try:
            issues = json.loads(result.stdout) if result.stdout.strip() else []
            
            return {
                'status': 'issues_found' if issues else 'success',
                'issues_found': len(issues),
                'issues': issues
            }
        except json.JSONDecodeError:
            return {
                'status': 'error',
                'error': 'Failed to parse MyPy JSON output',
                'raw_output': result.stdout
            }
    
    def _parse_bandit_output(self, result: subprocess.CompletedProcess) -> Dict[str, Any]:
        """Parse Bandit output (security issues)"""
        try:
            data = json.loads(result.stdout) if result.stdout.strip() else {}
            
            return {
                'status': 'issues_found' if result.returncode == 1 else 'success',
                'issues_found': len(data.get('results', [])),
                'results': data
            }
        except json.JSONDecodeError:
            return {
                'status': 'error',
                'error': 'Failed to parse Bandit JSON output',
                'raw_output': result.stdout
            }
    
    def _parse_radon_output(self, result: subprocess.CompletedProcess) -> Dict[str, Any]:
        """Parse Radon complexity output"""
        try:
            complexity_data = json.loads(result.stdout) if result.stdout.strip() else {}
            
            total_functions = sum(len(complexity_data.get(file, {}).get('functions', [])) 
                                for file in complexity_data)
            
            return {
                'status': 'success',
                'total_files_analyzed': len(complexity_data),
                'total_functions_analyzed': total_functions,
                'complexity_data': complexity_data
            }
        except json.JSONDecodeError:
            return {
                'status': 'error',
                'error': 'Failed to parse Radon JSON output',
                'raw_output': result.stdout
            }
    
    def _parse_vulture_output(self, result: subprocess.CompletedProcess) -> Dict[str, Any]:
        """Parse Vulture dead code output"""
        try:
            unused_code = json.loads(result.stdout) if result.stdout.strip() else []
            
            return {
                'status': 'issues_found' if unused_code else 'success',
                'unused_items_found': len(unused_code),
                'unused_items': unused_code
            }
        except json.JSONDecodeError:
            return {
                'status': 'error',
                'error': 'Failed to parse Vulture JSON output',
                'raw_output': result.stdout
            }
    
    def _check_complexity(self) -> Dict[str, Any]:
        """Check code complexity using multiple metrics"""
        print("  Checking code complexity...")
        
        try:
            # Use multiple complexity tools
            results = {}
            
            # Cyclomatic complexity with Radon
            radon_result = self._run_linter('radon')
            if radon_result.get('status') == 'success':
                results['cyclomatic'] = radon_result
            
            # Function complexity
            function_complexity = self._check_function_complexity()
            results['function_complexity'] = function_complexity
            
            # Nesting depth
            nesting_depth = self._check_nesting_depth()
            results['nesting_depth'] = nesting_depth
            
            return {
                'status': 'success',
                'results': results
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e)
            }
    
    def _check_function_complexity(self) -> Dict[str, Any]:
        """Check for overly complex functions"""
        complex_functions = []
        
        for py_file in self.project_path.rglob("*.py"):
            try:
                with open(py_file, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                
                # Simple complexity check: count decision points
                complexity_patterns = [
                    r'\bif\b', r'\belif\b', r'\belse\b', r'\bfor\b', r'\bwhile\b',
                    r'\btry\b', r'\bexcept\b', r'\bwith\b', r'\band\b', r'\bor\b'
                ]
                
                functions = self._extract_functions(content)
                
                for func_name, func_code in functions:
                    complexity_score = 0
                    for pattern in complexity_patterns:
                        complexity_score += len(re.findall(pattern, func_code))
                    
                    if complexity_score > 10:  # Threshold for high complexity
                        complex_functions.append({
                            'file': str(py_file.relative_to(self.project_path)),
                            'function': func_name,
                            'complexity_score': complexity_score,
                            'threshold': 10
                        })
                        
            except Exception:
                continue
        
        return {
            'complex_functions_found': len(complex_functions),
            'complex_functions': complex_functions
        }
    
    def _check_nesting_depth(self) -> Dict[str, Any]:
        """Check for excessive nesting depth"""
        deeply_nested_functions = []
        
        for py_file in self.project_path.rglob("*.py"):
            try:
                with open(py_file, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                
                functions = self._extract_functions(content)
                
                for func_name, func_code in functions:
                    lines = func_code.split('\n')
                    max_indent = 0
                    current_indent = 0
                    
                    for line in lines:
                        if line.strip():
                            # Count leading spaces to determine indentation
                            leading_spaces = len(line) - len(line.lstrip())
                            if leading_spaces > current_indent:
                                current_indent = leading_spaces
                                max_indent = max(max_indent, current_indent)
                    
                    # Convert spaces to approximate indentation level (assuming 4 spaces per level)
                    nesting_level = max_indent // 4
                    
                    if nesting_level > 4:  # Threshold for deep nesting
                        deeply_nested_functions.append({
                            'file': str(py_file.relative_to(self.project_path)),
                            'function': func_name,
                            'nesting_level': nesting_level,
                            'threshold': 4
                        })
                        
            except Exception:
                continue
        
        return {
            'deeply_nested_functions': len(deeply_nested_functions),
            'functions': deeply_nested_functions
        }
    
    def _check_code_duplication(self) -> Dict[str, Any]:
        """Check for code duplication"""
        print("  Checking for code duplication...")
        
        code_blocks = {}
        duplicated_blocks = []
        
        for py_file in self.project_path.rglob("*.py"):
            try:
                with open(py_file, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                
                # Extract code blocks (functions and methods)
                functions = self._extract_functions(content)
                
                for func_name, func_code in func_code_blocks():
                    # Normalize the code for comparison
                    normalized_code = self._normalize_code(func_code)
                    
                    if normalized_code not in code_blocks:
                        code_blocks[normalized_code] = []
                    
                    code_blocks[normalized_code].append({
                        'file': str(py_file.relative_to(self.project_path)),
                        'function': func_name,
                        'lines': len(func_code.splitlines())
                    })
                    
            except Exception:
                continue
        
        # Find duplicates
        for normalized_code, occurrences in code_blocks.items():
            if len(occurrences) > 1:
                duplicated_blocks.append({
                    'occurrences': len(occurrences),
                    'details': occurrences
                })
        
        return {
            'duplicated_blocks_found': len(duplicated_blocks),
            'duplicates': duplicated_blocks
        }
    
    def _check_documentation_coverage(self) -> Dict[str, Any]:
        """Check documentation coverage"""
        print("  Checking documentation coverage...")
        
        total_functions = 0
        documented_functions = 0
        undocumented_functions = []
        
        for py_file in self.project_path.rglob("*.py"):
            try:
                with open(py_file, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                
                functions = self._extract_functions(content)
                
                for func_name, func_code in functions:
                    total_functions += 1
                    
                    # Check if function has docstring
                    has_docstring = (
                        func_code.strip().startswith('"""') or 
                        func_code.strip().startswith("'''") or
                        func_code.startswith('def') and '"""' in func_code.split('"""')[0]
                    )
                    
                    if has_docstring:
                        documented_functions += 1
                    else:
                        undocumented_functions.append({
                            'file': str(py_file.relative_to(self.project_path)),
                            'function': func_name
                        })
                        
            except Exception:
                continue
        
        coverage_percentage = (documented_functions / total_functions * 100) if total_functions > 0 else 0
        
        return {
            'total_functions': total_functions,
            'documented_functions': documented_functions,
            'undocumented_functions': undocumented_functions,
            'coverage_percentage': round(coverage_percentage, 2)
        }
    
    def _extract_functions(self, code: str) -> List[Tuple[str, str]]:
        """Extract functions from Python code"""
        functions = []
        
        # Pattern to match function definitions
        func_pattern = r'def\s+(\w+)\s*\([^)]*\):\s*(.*?)(?=\ndef|\nclass|\Z)'
        
        matches = re.finditer(func_pattern, code, re.DOTALL)
        
        for match in matches:
            func_name = match.group(1)
            func_body = match.group(2)
            functions.append((func_name, match.group(0)))
        
        return functions
    
    def _normalize_code(self, code: str) -> str:
        """Normalize code for comparison by removing variable names and values"""
        # Remove comments
        code = re.sub(r'#.*$', '', code, flags=re.MULTILINE)
        
        # Replace variable names with placeholders
        code = re.sub(r'\b\w+\s*=', 'var =', code)
        
        # Replace string literals with placeholder
        code = re.sub(r'["\'].*?["\']', '"string"', code)
        
        # Replace numbers with placeholder
        code = re.sub(r'\b\d+\b', 'number', code)
        
        # Normalize whitespace
        code = re.sub(r'\s+', ' ', code)
        
        return code.strip().lower()
    
    def _generate_quality_summary(self, results: Dict) -> Dict[str, Any]:
        """Generate summary of code quality results"""
        summary = {
            'total_linters_run': 0,
            'total_issues_found': 0,
            'linters_with_issues': [],
            'code_formatting_issues': 0,
            'type_checking_issues': 0,
            'security_issues': 0,
            'complexity_issues': 0,
            'documentation_coverage': 0
        }
        
        for tool_name, result in results.items():
            if tool_name == 'summary':
                continue
            
            summary['total_linters_run'] += 1
            
            if result.get('status') == 'success':
                continue
            
            summary['linters_with_issues'].append(tool_name)
            
            # Count issues based on tool type
            if 'issues_found' in result:
                summary['total_issues_found'] += result['issues_found']
            
            if tool_name in ['black', 'isort']:
                summary['code_formatting_issues'] += result.get('issues_found', 0)
            elif tool_name == 'mypy':
                summary['type_checking_issues'] += result.get('issues_found', 0)
            elif tool_name == 'bandit':
                summary['security_issues'] += result.get('issues_found', 0)
            elif tool_name in ['radon', 'complexity']:
                summary['complexity_issues'] += result.get('complex_functions_found', 0)
        
        # Calculate documentation coverage if available
        if 'documentation' in results:
            doc_data = results['documentation']
            if 'coverage_percentage' in doc_data:
                summary['documentation_coverage'] = doc_data['coverage_percentage']
        
        return summary
    
    def generate_config_files(self) -> Dict[str, str]:
        """Generate configuration files for supported linters"""
        configs = {}
        
        # Flake8 config
        flake8_config = """[flake8]
max-line-length = 88
exclude = .git,__pycache__,build,dist,*.egg-info
ignore = E203,W503
"""
        configs['.flake8'] = flake8_config
        
        # MyPy config
        mypy_config = """[mypy]
python_version = 3.8
warn_return_any = True
warn_unused_configs = True
disallow_untyped_defs = True
"""
        configs['mypy.ini'] = mypy_config
        
        # Pylint config (basic)
        pylint_config = """[MASTER]
disable = C0111,C0103

[MESSAGES CONTROL]
disable = missing-module-docstring,missing-class-docstring,missing-function-docstring
"""
        configs['.pylintrc'] = pylint_config
        
        # Bandit config
        bandit_config = """[bandit]
exclude_dirs = tests,docs
skips = B101,B601
"""
        configs['.bandit'] = bandit_config
        
        return configs