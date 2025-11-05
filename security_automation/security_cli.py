#!/usr/bin/env python3
"""
Security Automation CLI Tool
Comprehensive security scanning and automation for projects.
"""

import argparse
import sys
import os
from pathlib import Path
from datetime import datetime
import json

# Add the current directory to Python path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from vulnerability_scanner import VulnerabilityScanner
from dependency_checker import DependencyChecker
from code_quality_scanner import CodeQualityScanner
from security_reporter import SecurityReporter
from github_security import GitHubSecurity
from monitoring_config import MonitoringConfig


def main():
    parser = argparse.ArgumentParser(
        description="Security Automation CLI Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python security_cli.py full-scan --project-path ./my-project
  python security_cli.py vuln-scan --project-path ./my-project --format json
  python security_cli.py dependency-check --project-path ./my-project
  python security_cli.py quality-scan --project-path ./my-project --fix
  python security_cli.py report --scan-results ./results.json
  python security_cli.py github-setup --repo-url https://github.com/user/repo
  python security_cli.py setup-monitoring --project-path ./my-project
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Full scan command
    full_scan_parser = subparsers.add_parser('full-scan', help='Run complete security scan')
    full_scan_parser.add_argument('--project-path', required=True, help='Path to project directory')
    full_scan_parser.add_argument('--output-dir', default='./security-reports', help='Output directory for reports')
    full_scan_parser.add_argument('--format', choices=['json', 'html', 'all'], default='all', help='Report format')
    
    # Vulnerability scan command
    vuln_scan_parser = subparsers.add_parser('vuln-scan', help='Run vulnerability scanning')
    vuln_scan_parser.add_argument('--project-path', required=True, help='Path to project directory')
    vuln_scan_parser.add_argument('--tools', nargs='+', default=['semgrep', 'bandit'], 
                                 choices=['semgrep', 'bandit', 'safety', 'all'], help='Security tools to use')
    vuln_scan_parser.add_argument('--format', choices=['json', 'html'], default='json', help='Output format')
    
    # Dependency check command
    dep_check_parser = subparsers.add_parser('dependency-check', help='Check dependencies for vulnerabilities')
    dep_check_parser.add_argument('--project-path', required=True, help='Path to project directory')
    dep_check_parser.add_argument('--auto-update', action='store_true', help='Auto-update vulnerable dependencies')
    
    # Code quality scan command
    quality_scan_parser = subparsers.add_parser('quality-scan', help='Run code quality scanning')
    quality_scan_parser.add_argument('--project-path', required=True, help='Path to project directory')
    quality_scan_parser.add_argument('--fix', action='store_true', help='Auto-fix linting issues')
    quality_scan_parser.add_argument('--linters', nargs='+', default=['flake8', 'black', 'isort'], 
                                    choices=['flake8', 'black', 'isort', 'pylint', 'mypy'], help='Linters to run')
    
    # Report command
    report_parser = subparsers.add_parser('report', help='Generate security report')
    report_parser.add_argument('--scan-results', required=True, help='Path to scan results JSON file')
    report_parser.add_argument('--format', choices=['json', 'html'], default='html', help='Report format')
    report_parser.add_argument('--output', required=True, help='Output file path')
    
    # GitHub integration command
    github_parser = subparsers.add_parser('github-setup', help='Setup GitHub security integration')
    github_parser.add_argument('--repo-url', required=True, help='GitHub repository URL')
    github_parser.add_argument('--token', help='GitHub token (optional, will prompt if not provided)')
    github_parser.add_argument('--setup-branch-protection', action='store_true', help='Setup branch protection rules')
    
    # Monitoring setup command
    monitoring_parser = subparsers.add_parser('setup-monitoring', help='Setup continuous security monitoring')
    monitoring_parser.add_argument('--project-path', required=True, help='Path to project directory')
    monitoring_parser.add_argument('--github-integration', action='store_true', help='Enable GitHub integration')
    monitoring_parser.add_argument('--schedule', default='daily', choices=['hourly', 'daily', 'weekly'], 
                                  help='Monitoring frequency')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    try:
        if args.command == 'full-scan':
            return run_full_scan(args)
        elif args.command == 'vuln-scan':
            return run_vulnerability_scan(args)
        elif args.command == 'dependency-check':
            return run_dependency_check(args)
        elif args.command == 'quality-scan':
            return run_quality_scan(args)
        elif args.command == 'report':
            return generate_report(args)
        elif args.command == 'github-setup':
            return setup_github_integration(args)
        elif args.command == 'setup-monitoring':
            return setup_monitoring(args)
    except Exception as e:
        print(f"Error: {e}")
        return 1
    
    return 0


def run_full_scan(args):
    """Run complete security scan"""
    print("Starting full security scan...")
    
    project_path = Path(args.project_path)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results = {}
    
    # 1. Vulnerability scanning
    print("Running vulnerability scanning...")
    vuln_scanner = VulnerabilityScanner(project_path)
    vuln_results = vuln_scanner.scan_all()
    results['vulnerabilities'] = vuln_results
    
    # 2. Dependency checking
    print("Checking dependencies...")
    dep_checker = DependencyChecker(project_path)
    dep_results = dep_checker.check_all()
    results['dependencies'] = dep_results
    
    # 3. Code quality scanning
    print("Running code quality scanning...")
    quality_scanner = CodeQualityScanner(project_path)
    quality_results = quality_scanner.scan_all()
    results['code_quality'] = quality_results
    
    # Generate report
    print("Generating security report...")
    reporter = SecurityReporter(output_dir)
    report_path = reporter.generate_report(results, timestamp)
    
    print(f"Full security scan completed. Report saved to: {report_path}")
    return 0


def run_vulnerability_scan(args):
    """Run vulnerability scanning"""
    print("Starting vulnerability scanning...")
    
    project_path = Path(args.project_path)
    vuln_scanner = VulnerabilityScanner(project_path)
    
    tools = ['all'] if args.tools == ['all'] else args.tools
    results = vuln_scanner.scan_with_tools(tools)
    
    # Save results
    output_file = f"vulnerability_scan_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"Vulnerability scan completed. Results saved to: {output_file}")
    return 0


def run_dependency_check(args):
    """Run dependency checking"""
    print("Starting dependency check...")
    
    project_path = Path(args.project_path)
    dep_checker = DependencyChecker(project_path)
    
    results = dep_checker.check_all()
    
    if args.auto_update:
        print("Auto-updating vulnerable dependencies...")
        dep_checker.auto_update_vulnerable_deps(results)
    
    # Save results
    output_file = f"dependency_check_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"Dependency check completed. Results saved to: {output_file}")
    return 0


def run_quality_scan(args):
    """Run code quality scanning"""
    print("Starting code quality scanning...")
    
    project_path = Path(args.project_path)
    quality_scanner = CodeQualityScanner(project_path)
    
    results = quality_scanner.scan_with_linters(args.linters, args.fix)
    
    # Save results
    output_file = f"code_quality_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"Code quality scan completed. Results saved to: {output_file}")
    return 0


def generate_report(args):
    """Generate security report"""
    print("Generating security report...")
    
    # Load scan results
    with open(args.scan_results, 'r') as f:
        results = json.load(f)
    
    # Generate report
    reporter = SecurityReporter()
    reporter.generate_report(results, datetime.now().strftime('%Y%m%d_%H%M%S'))
    
    print(f"Report generated: {args.output}")
    return 0


def setup_github_integration(args):
    """Setup GitHub security integration"""
    print("Setting up GitHub security integration...")
    
    github_security = GitHubSecurity(args.repo_url, args.token)
    github_security.setup_security_features()
    
    if args.setup_branch_protection:
        github_security.setup_branch_protection()
    
    print("GitHub security integration setup completed!")
    return 0


def setup_monitoring(args):
    """Setup continuous security monitoring"""
    print("Setting up continuous security monitoring...")
    
    project_path = Path(args.project_path)
    monitoring = MonitoringConfig(project_path)
    
    monitoring.setup_monitoring(args.github_integration, args.schedule)
    
    print("Continuous security monitoring setup completed!")
    return 0


if __name__ == "__main__":
    sys.exit(main())