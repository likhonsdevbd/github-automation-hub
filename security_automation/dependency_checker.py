"""
Dependency Security Checker and Updater
Checks for vulnerable dependencies and can automatically update them.
"""

import subprocess
import json
import re
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import requests
import toml
import yaml
from packaging.version import Version, parse


class DependencyChecker:
    """Dependency security checker and updater"""
    
    def __init__(self, project_path: Path):
        self.project_path = Path(project_path)
        self.vulnerability_db = self._load_vulnerability_database()
        
    def check_all(self) -> Dict[str, Any]:
        """Check all dependencies for vulnerabilities"""
        results = {}
        
        # Find and check different dependency file formats
        results['requirements_txt'] = self._check_requirements_files()
        results['pyproject_toml'] = self._check_pyproject_toml()
        results['pipenv'] = self._check_pipenv()
        results['poetry'] = self._check_poetry()
        
        # Check for package.json if Node.js project
        results['npm_packages'] = self._check_npm_packages()
        
        # Check for Ruby Gemfile if Ruby project
        results['ruby_gems'] = self._check_ruby_gems()
        
        # Generate summary
        results['summary'] = self._generate_dependency_summary(results)
        
        return results
    
    def _check_requirements_files(self) -> Dict[str, Any]:
        """Check requirements.txt files for vulnerabilities"""
        print("  Checking requirements.txt files...")
        
        req_files = list(self.project_path.rglob("requirements*.txt"))
        
        if not req_files:
            return {
                'status': 'no_files',
                'files_checked': 0
            }
        
        results = []
        
        for req_file in req_files:
            try:
                dependencies = self._parse_requirements_file(req_file)
                vulnerabilities = self._check_package_vulnerabilities(dependencies)
                
                results.append({
                    'file': str(req_file.relative_to(self.project_path)),
                    'dependencies': dependencies,
                    'vulnerabilities': vulnerabilities
                })
                
            except Exception as e:
                results.append({
                    'file': str(req_file.relative_to(self.project_path)),
                    'error': str(e)
                })
        
        return {
            'status': 'success',
            'files_checked': len(req_files),
            'results': results
        }
    
    def _check_pyproject_toml(self) -> Dict[str, Any]:
        """Check pyproject.toml dependencies"""
        print("  Checking pyproject.toml...")
        
        pyproject_files = list(self.project_path.rglob("pyproject.toml"))
        
        if not pyproject_files:
            return {
                'status': 'no_files',
                'files_checked': 0
            }
        
        results = []
        
        for pyproject_file in pyproject_files:
            try:
                with open(pyproject_file, 'r') as f:
                    data = toml.load(f)
                
                # Extract dependencies from different sections
                dependencies = {}
                
                # Check dependencies section
                if 'tool' in data and 'poetry' in data['tool']:
                    poetry_config = data['tool']['poetry']
                    if 'dependencies' in poetry_config:
                        dependencies.update(poetry_config['dependencies'])
                    if 'dev-dependencies' in poetry_config:
                        dependencies.update({
                            f"{pkg} (dev)": version 
                            for pkg, version in poetry_config['dev-dependencies'].items()
                        })
                
                # Check dependencies directly in project
                if 'project' in data and 'dependencies' in data['project']:
                    dependencies.update(data['project']['dependencies'])
                
                if 'project' in data and 'optional-dependencies' in data['project']:
                    for group, deps in data['project']['optional-dependencies'].items():
                        dependencies.update({
                            f"{pkg} ({group})": version 
                            for pkg, version in deps.items()
                        })
                
                vulnerabilities = self._check_package_vulnerabilities(dependencies)
                
                results.append({
                    'file': str(pyproject_file.relative_to(self.project_path)),
                    'dependencies': dependencies,
                    'vulnerabilities': vulnerabilities
                })
                
            except Exception as e:
                results.append({
                    'file': str(pyproject_file.relative_to(self.project_path)),
                    'error': str(e)
                })
        
        return {
            'status': 'success',
            'files_checked': len(pyproject_files),
            'results': results
        }
    
    def _check_pipenv(self) -> Dict[str, Any]:
        """Check Pipfile and Pipfile.lock"""
        print("  Checking Pipfile...")
        
        pipfile = self.project_path / "Pipfile"
        pipfile_lock = self.project_path / "Pipfile.lock"
        
        if not pipfile.exists():
            return {
                'status': 'no_files',
                'files_checked': 0
            }
        
        try:
            dependencies = {}
            
            # Parse Pipfile
            with open(pipfile, 'r') as f:
                pipfile_data = toml.load(f)
            
            if 'packages' in pipfile_data:
                dependencies.update(pipfile_data['packages'])
            
            if 'dev-packages' in pipfile_data:
                dependencies.update({
                    f"{pkg} (dev)": version 
                    for pkg, version in pipfile_data['dev-packages'].items()
                })
            
            # Parse Pipfile.lock for more detailed version info
            if pipfile_lock.exists():
                with open(pipfile_lock, 'r') as f:
                    lock_data = json.load(f)
                
                # Extract versions from lock file
                lock_versions = lock_data.get('default', {})
                for pkg, info in lock_versions.items():
                    if pkg in dependencies:
                        dependencies[pkg] = info.get('version', dependencies[pkg])
            
            vulnerabilities = self._check_package_vulnerabilities(dependencies)
            
            return {
                'status': 'success',
                'files_checked': 2 if pipfile_lock.exists() else 1,
                'dependencies': dependencies,
                'vulnerabilities': vulnerabilities
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e)
            }
    
    def _check_poetry(self) -> Dict[str, Any]:
        """Check Poetry-specific files"""
        # Poetry dependencies are already handled in pyproject.toml
        return {
            'status': 'integrated_with_pyproject',
            'note': 'Poetry dependencies are checked via pyproject.toml'
        }
    
    def _check_npm_packages(self) -> Dict[str, Any]:
        """Check Node.js package.json dependencies"""
        print("  Checking package.json files...")
        
        package_json_files = list(self.project_path.rglob("package.json"))
        
        if not package_json_files:
            return {
                'status': 'no_files',
                'files_checked': 0
            }
        
        results = []
        
        for package_json in package_json_files:
            try:
                with open(package_json, 'r') as f:
                    package_data = json.load(f)
                
                dependencies = {}
                
                if 'dependencies' in package_data:
                    dependencies.update(package_data['dependencies'])
                
                if 'devDependencies' in package_data:
                    dependencies.update({
                        f"{pkg} (dev)": version 
                        for pkg, version in package_data['devDependencies'].items()
                    })
                
                vulnerabilities = self._check_npm_vulnerabilities(dependencies)
                
                results.append({
                    'file': str(package_json.relative_to(self.project_path)),
                    'dependencies': dependencies,
                    'vulnerabilities': vulnerabilities
                })
                
            except Exception as e:
                results.append({
                    'file': str(package_json.relative_to(self.project_path)),
                    'error': str(e)
                })
        
        return {
            'status': 'success',
            'files_checked': len(package_json_files),
            'results': results
        }
    
    def _check_ruby_gems(self) -> Dict[str, Any]:
        """Check Ruby Gemfile dependencies"""
        print("  Checking Gemfile...")
        
        gemfile = self.project_path / "Gemfile"
        
        if not gemfile.exists():
            return {
                'status': 'no_files',
                'files_checked': 0
            }
        
        try:
            dependencies = {}
            
            # Parse Gemfile
            with open(gemfile, 'r') as f:
                gemfile_content = f.read()
            
            # Extract gem dependencies using regex
            gem_pattern = r"gem\s+['\"]([^'\"]+)['\"]\s*(?:,\s*['\"]([^'\"]+)['\"])?"
            matches = re.findall(gem_pattern, gemfile_content)
            
            for gem_name, version in matches:
                if version:
                    dependencies[gem_name] = version
                else:
                    dependencies[gem_name] = "latest"
            
            vulnerabilities = self._check_ruby_vulnerabilities(dependencies)
            
            return {
                'status': 'success',
                'files_checked': 1,
                'dependencies': dependencies,
                'vulnerabilities': vulnerabilities
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e)
            }
    
    def _parse_requirements_file(self, file_path: Path) -> Dict[str, str]:
        """Parse requirements.txt file"""
        dependencies = {}
        
        with open(file_path, 'r') as f:
            for line in f:
                line = line.strip()
                
                # Skip comments and empty lines
                if not line or line.startswith('#'):
                    continue
                
                # Handle different requirement formats
                if '==' in line:
                    name, version = line.split('==', 1)
                    dependencies[name] = version
                elif '>=' in line:
                    name, version = line.split('>=', 1)
                    dependencies[name] = f">={version}"
                elif '>' in line:
                    name, version = line.split('>', 1)
                    dependencies[name] = f">{version}"
                elif '~=' in line:
                    name, version = line.split('~=', 1)
                    dependencies[name] = f">={version}"
                else:
                    # Just package name
                    dependencies[line] = "latest"
        
        return dependencies
    
    def _check_package_vulnerabilities(self, dependencies: Dict[str, str]) -> List[Dict[str, Any]]:
        """Check Python package vulnerabilities"""
        vulnerabilities = []
        
        for package, version_spec in dependencies.items():
            try:
                # Check local vulnerability database
                pkg_vulns = self.vulnerability_db.get(package.lower(), [])
                
                for vuln in pkg_vulns:
                    if self._version_matches(version_spec, vuln['affected_versions']):
                        vulnerabilities.append({
                            'package': package,
                            'version': version_spec,
                            'vulnerability_id': vuln['id'],
                            'description': vuln['description'],
                            'severity': vuln['severity'],
                            'affected_versions': vuln['affected_versions'],
                            'fixed_versions': vuln.get('fixed_versions', [])
                        })
            except Exception as e:
                # Log error but continue checking other packages
                continue
        
        return vulnerabilities
    
    def _check_npm_vulnerabilities(self, dependencies: Dict[str, str]) -> List[Dict[str, Any]]:
        """Check Node.js package vulnerabilities"""
        # For demonstration, we'll use a simplified check
        # In a real implementation, you'd integrate with npm audit or OSV database
        vulnerabilities = []
        
        # Common vulnerable packages (example list)
        common_vulns = {
            'lodash': ['<4.17.21'],
            'express': ['<4.17.1'],
            'request': ['<2.88.0'],
            'moment': ['<2.29.2']
        }
        
        for package, version_spec in dependencies.items():
            if package.lower() in common_vulns:
                for vuln_range in common_vulns[package.lower()]:
                    # Simplified version check (in real implementation, use semver)
                    if self._version_matches(version_spec, [vuln_range]):
                        vulnerabilities.append({
                            'package': package,
                            'version': version_spec,
                            'vulnerability_id': 'CVE-EXAMPLE',
                            'description': f'Version {version_spec} has known vulnerabilities',
                            'severity': 'medium',
                            'affected_versions': [vuln_range],
                            'fix_available': True
                        })
        
        return vulnerabilities
    
    def _check_ruby_vulnerabilities(self, dependencies: Dict[str, str]) -> List[Dict[str, Any]]:
        """Check Ruby gem vulnerabilities"""
        # Simplified Ruby gem vulnerability check
        vulnerabilities = []
        
        # Common vulnerable gems (example)
        common_vulns = {
            'rails': ['<6.0.0'],
            'jquery-rails': ['<4.3.0'],
            'nokogiri': ['<1.10.0']
        }
        
        for gem, version_spec in dependencies.items():
            if gem.lower() in common_vulns:
                for vuln_range in common_vulns[gem.lower()]:
                    if self._version_matches(version_spec, [vuln_range]):
                        vulnerabilities.append({
                            'package': gem,
                            'version': version_spec,
                            'vulnerability_id': 'CVE-RUBY-EXAMPLE',
                            'description': f'Version {version_spec} has known vulnerabilities',
                            'severity': 'high',
                            'affected_versions': [vuln_range],
                            'fix_available': True
                        })
        
        return vulnerabilities
    
    def _version_matches(self, version_spec: str, affected_versions: List[str]) -> bool:
        """Check if version specification matches affected versions"""
        # Simplified version matching - in real implementation, use packaging library
        try:
            if version_spec == "latest":
                return True  # Assume latest could be affected
            
            for vuln_range in affected_versions:
                if vuln_range.startswith('<'):
                    # Less than version
                    vuln_version = parse(vuln_range[1:])
                    spec_version = parse(version_spec.replace('>=', '').replace('>', '').replace('==', ''))
                    return spec_version < vuln_version
                elif vuln_range.startswith('<='):
                    # Less than or equal to version
                    vuln_version = parse(vuln_range[2:])
                    spec_version = parse(version_spec.replace('>=', '').replace('>', '').replace('==', ''))
                    return spec_version <= vuln_version
                elif vuln_range.startswith('>='):
                    # Greater than or equal to version
                    vuln_version = parse(vuln_range[2:])
                    spec_version = parse(version_spec.replace('>=', '').replace('>', '').replace('==', ''))
                    return spec_version >= vuln_version
                elif vuln_range.startswith('=='):
                    # Equal to version
                    vuln_version = parse(vuln_range[2:])
                    spec_version = parse(version_spec.replace('>=', '').replace('>', '').replace('==', ''))
                    return spec_version == vuln_version
            
            return False
        except Exception:
            return False  # If we can't parse versions, assume no match
    
    def _load_vulnerability_database(self) -> Dict[str, List[Dict[str, Any]]]:
        """Load vulnerability database (simplified version)"""
        # In a real implementation, this would load from OSV, Snyk, or other sources
        # For demonstration, using a small sample database
        return {
            'django': [
                {
                    'id': 'CVE-2023-31047',
                    'description': 'Potential directory traversal via archive extraction',
                    'severity': 'high',
                    'affected_versions': ['<4.2.1'],
                    'fixed_versions': ['4.2.1']
                }
            ],
            'requests': [
                {
                    'id': 'CVE-2023-32681',
                    'description': 'Proxy TLS certificate verification bypass',
                    'severity': 'medium',
                    'affected_versions': ['<2.31.0'],
                    'fixed_versions': ['2.31.0']
                }
            ],
            'pillow': [
                {
                    'id': 'CVE-2023-32681',
                    'description': 'Buffer overflow in image processing',
                    'severity': 'high',
                    'affected_versions': ['<10.0.0'],
                    'fixed_versions': ['10.0.0']
                }
            ]
        }
    
    def _generate_dependency_summary(self, results: Dict) -> Dict[str, Any]:
        """Generate summary of dependency check results"""
        summary = {
            'total_dependencies': 0,
            'vulnerable_dependencies': 0,
            'high_severity_issues': 0,
            'medium_severity_issues': 0,
            'low_severity_issues': 0,
            'files_checked': 0
        }
        
        for section, data in results.items():
            if section == 'summary':
                continue
            
            if data.get('status') == 'success':
                if 'files_checked' in data:
                    summary['files_checked'] += data['files_checked']
                
                if 'results' in data:
                    for result in data['results']:
                        if 'dependencies' in result:
                            summary['total_dependencies'] += len(result['dependencies'])
                        
                        if 'vulnerabilities' in result:
                            summary['vulnerable_dependencies'] += len(result['vulnerabilities'])
                            
                            for vuln in result['vulnerabilities']:
                                severity = vuln.get('severity', '').lower()
                                if severity == 'high':
                                    summary['high_severity_issues'] += 1
                                elif severity == 'medium':
                                    summary['medium_severity_issues'] += 1
                                elif severity == 'low':
                                    summary['low_severity_issues'] += 1
                elif 'dependencies' in data:
                    summary['total_dependencies'] += len(data['dependencies'])
                    if 'vulnerabilities' in data:
                        summary['vulnerable_dependencies'] += len(data['vulnerabilities'])
                        
                        for vuln in data['vulnerabilities']:
                            severity = vuln.get('severity', '').lower()
                            if severity == 'high':
                                summary['high_severity_issues'] += 1
                            elif severity == 'medium':
                                summary['medium_severity_issues'] += 1
                            elif severity == 'low':
                                summary['low_severity_issues'] += 1
        
        return summary
    
    def auto_update_vulnerable_deps(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Automatically update vulnerable dependencies"""
        print("Auto-updating vulnerable dependencies...")
        
        updates = []
        
        # Process different dependency file types
        if results.get('requirements_txt', {}).get('status') == 'success':
            for result in results['requirements_txt']['results']:
                if 'vulnerabilities' in result and result['vulnerabilities']:
                    file_updates = self._update_requirements_file(
                        self.project_path / result['file'], 
                        result['vulnerabilities']
                    )
                    updates.extend(file_updates)
        
        if results.get('pyproject_toml', {}).get('status') == 'success':
            for result in results['pyproject_toml']['results']:
                if 'vulnerabilities' in result and result['vulnerabilities']:
                    file_updates = self._update_pyproject_toml(
                        self.project_path / result['file'], 
                        result['vulnerabilities']
                    )
                    updates.extend(file_updates)
        
        return {
            'status': 'completed',
            'updates_applied': len(updates),
            'details': updates
        }
    
    def _update_requirements_file(self, file_path: Path, vulnerabilities: List[Dict]) -> List[Dict[str, Any]]:
        """Update requirements.txt file with fixed versions"""
        updates = []
        
        try:
            with open(file_path, 'r') as f:
                lines = f.readlines()
            
            # Create mapping of package to vulnerabilities
            package_vulns = {}
            for vuln in vulnerabilities:
                pkg = vuln['package']
                if pkg not in package_vulns:
                    package_vulns[pkg] = []
                package_vulns[pkg].append(vuln)
            
            updated_lines = []
            for line in lines:
                line = line.strip()
                updated_line = line
                
                # Check if line contains a vulnerable package
                for pkg, vulns in package_vulns.items():
                    if line.startswith(pkg):
                        # Find best fix version
                        best_fix = None
                        for vuln in vulns:
                            if 'fixed_versions' in vuln and vuln['fixed_versions']:
                                fix_version = vuln['fixed_versions'][0]  # Use first available fix
                                if not best_fix or Version(fix_version) > Version(best_fix):
                                    best_fix = fix_version
                        
                        if best_fix:
                            updated_line = f"{pkg}=={best_fix}"
                            updates.append({
                                'package': pkg,
                                'file': str(file_path.relative_to(self.project_path)),
                                'old_version': line,
                                'new_version': updated_line,
                                'reason': f"Fixed vulnerability: {vulns[0].get('vulnerability_id', 'Unknown')}"
                            })
                        break
                
                updated_lines.append(updated_line)
            
            # Write updated file
            with open(file_path, 'w') as f:
                for line in updated_lines:
                    f.write(line + '\n')
        
        except Exception as e:
            updates.append({
                'package': 'unknown',
                'file': str(file_path.relative_to(self.project_path)),
                'error': str(e)
            })
        
        return updates
    
    def _update_pyproject_toml(self, file_path: Path, vulnerabilities: List[Dict]) -> List[Dict[str, Any]]:
        """Update pyproject.toml file with fixed versions"""
        # Similar implementation for pyproject.toml
        updates = []
        
        try:
            with open(file_path, 'r') as f:
                data = toml.load(f)
            
            # Find dependencies and update them
            # This is a simplified implementation
            package_vulns = {}
            for vuln in vulnerabilities:
                pkg = vuln['package']
                if pkg not in package_vulns:
                    package_vulns[pkg] = []
                package_vulns[pkg].append(vuln)
            
            # Check and update dependencies
            updated = False
            for section in ['project', 'tool.poetry']:
                if section in data:
                    if section == 'project' and 'dependencies' in data['project']:
                        for pkg, version_spec in data['project']['dependencies'].items():
                            if pkg in package_vulns:
                                for vuln in package_vulns[pkg]:
                                    if 'fixed_versions' in vuln and vuln['fixed_versions']:
                                        fix_version = vuln['fixed_versions'][0]
                                        data['project']['dependencies'][pkg] = fix_version
                                        updates.append({
                                            'package': pkg,
                                            'file': str(file_path.relative_to(self.project_path)),
                                            'old_version': version_spec,
                                            'new_version': fix_version,
                                            'reason': f"Fixed vulnerability: {vuln.get('vulnerability_id', 'Unknown')}"
                                        })
                                        updated = True
                                        break
            
            if updated:
                with open(file_path, 'w') as f:
                    toml.dump(data, f)
        
        except Exception as e:
            updates.append({
                'package': 'unknown',
                'file': str(file_path.relative_to(self.project_path)),
                'error': str(e)
            })
        
        return updates