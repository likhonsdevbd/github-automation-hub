"""
Security Reporter
Generates comprehensive security reports in multiple formats.
"""

import json
import html
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
import base64
import os


class SecurityReporter:
    """Security report generator with multiple output formats"""
    
    def __init__(self, output_dir: Optional[Path] = None):
        self.output_dir = output_dir or Path("./security-reports")
        self.output_dir.mkdir(exist_ok=True)
    
    def generate_report(self, scan_results: Dict[str, Any], timestamp: str, format: str = 'all') -> Dict[str, str]:
        """Generate security report in specified format(s)"""
        
        if format == 'json' or format == 'all':
            json_path = self._generate_json_report(scan_results, timestamp)
        
        if format == 'html' or format == 'all':
            html_path = self._generate_html_report(scan_results, timestamp)
        
        if format == 'all':
            return {
                'json': str(json_path),
                'html': str(html_path),
                'summary': str(self._generate_summary_report(scan_results, timestamp))
            }
        elif format == 'json':
            return {'json': str(json_path)}
        elif format == 'html':
            return {'html': str(html_path)}
    
    def _generate_json_report(self, scan_results: Dict[str, Any], timestamp: str) -> Path:
        """Generate JSON report"""
        report_data = {
            'metadata': {
                'generated_at': datetime.now().isoformat(),
                'timestamp': timestamp,
                'report_version': '1.0',
                'scan_types': list(scan_results.keys())
            },
            'results': scan_results
        }
        
        output_file = self.output_dir / f"security_report_{timestamp}.json"
        
        with open(output_file, 'w') as f:
            json.dump(report_data, f, indent=2)
        
        return output_file
    
    def _generate_summary_report(self, scan_results: Dict[str, Any], timestamp: str) -> Path:
        """Generate summary report (text format)"""
        output_file = self.output_dir / f"security_summary_{timestamp}.txt"
        
        with open(output_file, 'w') as f:
            f.write(self._generate_summary_text(scan_results))
        
        return output_file
    
    def _generate_html_report(self, scan_results: Dict[str, Any], timestamp: str) -> Path:
        """Generate HTML report"""
        html_content = self._generate_html_content(scan_results, timestamp)
        
        output_file = self.output_dir / f"security_report_{timestamp}.html"
        
        with open(output_file, 'w') as f:
            f.write(html_content)
        
        return output_file
    
    def _generate_html_content(self, scan_results: Dict[str, Any], timestamp: str) -> str:
        """Generate HTML content for the report"""
        
        # Calculate overall statistics
        stats = self._calculate_overall_stats(scan_results)
        
        html_template = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Security Scan Report - {timestamp}</title>
    <style>
        {self._get_css_styles()}
    </style>
</head>
<body>
    <div class="container">
        <header class="header">
            <h1>🔒 Security Scan Report</h1>
            <div class="metadata">
                <p><strong>Generated:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                <p><strong>Timestamp:</strong> {timestamp}</p>
                <p><strong>Report Version:</strong> 1.0</p>
            </div>
        </header>

        <section class="executive-summary">
            <h2>📊 Executive Summary</h2>
            <div class="summary-cards">
                <div class="card critical">
                    <div class="card-value">{stats['critical']}</div>
                    <div class="card-label">Critical Issues</div>
                </div>
                <div class="card high">
                    <div class="card-value">{stats['high']}</div>
                    <div class="card-label">High Priority</div>
                </div>
                <div class="card medium">
                    <div class="card-value">{stats['medium']}</div>
                    <div class="card-label">Medium Priority</div>
                </div>
                <div class="card low">
                    <div class="card-value">{stats['low']}</div>
                    <div class="card-label">Low Priority</div>
                </div>
                <div class="card total">
                    <div class="card-value">{stats['total']}</div>
                    <div class="card-label">Total Issues</div>
                </div>
            </div>
        </section>

        <section class="scan-results">
            <h2>🔍 Detailed Scan Results</h2>
            {self._generate_html_sections(scan_results)}
        </section>

        <section class="recommendations">
            <h2>💡 Recommendations</h2>
            {self._generate_recommendations_html(stats, scan_results)}
        </section>

        <footer class="footer">
            <p>Generated by Security Automation Tool | Version 1.0</p>
            <p>For questions or support, please contact the security team.</p>
        </footer>
    </div>
</body>
</html>
        """
        
        return html_template
    
    def _get_css_styles(self) -> str:
        """Get CSS styles for the HTML report"""
        return """
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            line-height: 1.6;
            color: #333;
            background-color: #f5f5f5;
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background-color: white;
            box-shadow: 0 0 20px rgba(0,0,0,0.1);
            margin-top: 20px;
            margin-bottom: 20px;
            border-radius: 8px;
        }
        
        .header {
            text-align: center;
            padding: 30px 0;
            border-bottom: 3px solid #e0e0e0;
            margin-bottom: 30px;
        }
        
        .header h1 {
            color: #d32f2f;
            font-size: 2.5em;
            margin-bottom: 10px;
        }
        
        .metadata {
            background-color: #f8f9fa;
            padding: 15px;
            border-radius: 5px;
            margin-top: 15px;
        }
        
        .metadata p {
            margin-bottom: 5px;
        }
        
        .executive-summary {
            margin-bottom: 40px;
        }
        
        .summary-cards {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-top: 20px;
        }
        
        .card {
            text-align: center;
            padding: 20px;
            border-radius: 8px;
            color: white;
        }
        
        .card.critical { background-color: #d32f2f; }
        .card.high { background-color: #f57c00; }
        .card.medium { background-color: #fbc02d; color: #333; }
        .card.low { background-color: #388e3c; }
        .card.total { background-color: #1976d2; }
        
        .card-value {
            font-size: 3em;
            font-weight: bold;
            margin-bottom: 5px;
        }
        
        .card-label {
            font-size: 1.1em;
            opacity: 0.9;
        }
        
        h2 {
            color: #1976d2;
            margin-bottom: 20px;
            padding-bottom: 10px;
            border-bottom: 2px solid #e0e0e0;
        }
        
        .section {
            margin-bottom: 30px;
            padding: 20px;
            background-color: #f8f9fa;
            border-radius: 8px;
            border-left: 4px solid #1976d2;
        }
        
        .section-title {
            color: #1976d2;
            font-size: 1.3em;
            margin-bottom: 15px;
        }
        
        .status-badge {
            display: inline-block;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 0.9em;
            font-weight: bold;
            color: white;
        }
        
        .status-success { background-color: #4caf50; }
        .status-error { background-color: #f44336; }
        .status-warning { background-color: #ff9800; }
        .status-info { background-color: #2196f3; }
        
        .issue-list {
            margin-top: 15px;
        }
        
        .issue-item {
            background-color: white;
            padding: 15px;
            margin-bottom: 10px;
            border-radius: 5px;
            border-left: 4px solid #ddd;
        }
        
        .issue-item.high { border-left-color: #f57c00; }
        .issue-item.medium { border-left-color: #fbc02d; }
        .issue-item.low { border-left-color: #388e3c; }
        .issue-item.critical { border-left-color: #d32f2f; }
        
        .issue-severity {
            font-weight: bold;
            margin-bottom: 5px;
        }
        
        .issue-severity.critical { color: #d32f2f; }
        .issue-severity.high { color: #f57c00; }
        .issue-severity.medium { color: #fbc02d; }
        .issue-severity.low { color: #388e3c; }
        
        .recommendations ul {
            list-style-type: none;
            padding-left: 0;
        }
        
        .recommendations li {
            background-color: #e3f2fd;
            padding: 10px 15px;
            margin-bottom: 8px;
            border-radius: 5px;
            border-left: 4px solid #1976d2;
        }
        
        .recommendations li:before {
            content: "💡 ";
            margin-right: 10px;
        }
        
        .footer {
            text-align: center;
            margin-top: 40px;
            padding-top: 20px;
            border-top: 2px solid #e0e0e0;
            color: #666;
        }
        
        .footer p {
            margin-bottom: 5px;
        }
        
        .stats-table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 15px;
        }
        
        .stats-table th,
        .stats-table td {
            padding: 10px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }
        
        .stats-table th {
            background-color: #f5f5f5;
            font-weight: bold;
        }
        """
    
    def _calculate_overall_stats(self, scan_results: Dict[str, Any]) -> Dict[str, int]:
        """Calculate overall statistics from scan results"""
        stats = {
            'critical': 0,
            'high': 0,
            'medium': 0,
            'low': 0,
            'total': 0
        }
        
        # Check vulnerability results
        if 'vulnerabilities' in scan_results:
            vuln_results = scan_results['vulnerabilities']
            
            # Process Semgrep results
            if 'semgrep' in vuln_results:
                semgrep_data = vuln_results['semgrep']
                if semgrep_data.get('status') == 'success':
                    severity_breakdown = semgrep_data.get('severity_breakdown', {})
                    stats['critical'] += severity_breakdown.get('error', 0)
                    stats['high'] += severity_breakdown.get('error', 0)  # Map error to high
                    stats['medium'] += severity_breakdown.get('warning', 0)
                    stats['low'] += severity_breakdown.get('info', 0)
            
            # Process Bandit results
            if 'bandit' in vuln_results:
                bandit_data = vuln_results['bandit']
                if bandit_data.get('status') == 'success':
                    severity_breakdown = bandit_data.get('severity_breakdown', {})
                    stats['critical'] += severity_breakdown.get('high', 0)
                    stats['high'] += severity_breakdown.get('high', 0)
                    stats['medium'] += severity_breakdown.get('medium', 0)
                    stats['low'] += severity_breakdown.get('low', 0)
        
        # Check dependency results
        if 'dependencies' in scan_results:
            dep_results = scan_results['dependencies']
            if dep_results.get('summary'):
                summary = dep_results['summary']
                stats['high'] += summary.get('high_severity_issues', 0)
                stats['medium'] += summary.get('medium_severity_issues', 0)
                stats['low'] += summary.get('low_severity_issues', 0)
        
        # Check custom security checks
        if 'vulnerabilities' in scan_results and 'custom_checks' in scan_results['vulnerabilities']:
            custom_checks = scan_results['vulnerabilities']['custom_checks']
            if custom_checks.get('status') == 'success':
                for check_result in custom_checks.get('results', []):
                    for issue in check_result.get('issues', []):
                        severity = issue.get('severity', 'medium')
                        if severity == 'high':
                            stats['high'] += 1
                        elif severity == 'medium':
                            stats['medium'] += 1
                        elif severity == 'low':
                            stats['low'] += 1
        
        stats['total'] = stats['critical'] + stats['high'] + stats['medium'] + stats['low']
        
        return stats
    
    def _generate_html_sections(self, scan_results: Dict[str, Any]) -> str:
        """Generate HTML sections for each scan type"""
        sections = []
        
        # Vulnerability scanning section
        if 'vulnerabilities' in scan_results:
            vuln_section = self._generate_vulnerability_section_html(scan_results['vulnerabilities'])
            sections.append(f'<div class="section">{vuln_section}</div>')
        
        # Dependency checking section
        if 'dependencies' in scan_results:
            dep_section = self._generate_dependency_section_html(scan_results['dependencies'])
            sections.append(f'<div class="section">{dep_section}</div>')
        
        # Code quality section
        if 'code_quality' in scan_results:
            quality_section = self._generate_quality_section_html(scan_results['code_quality'])
            sections.append(f'<div class="section">{quality_section}</div>')
        
        return '\n'.join(sections)
    
    def _generate_vulnerability_section_html(self, vuln_data: Dict[str, Any]) -> str:
        """Generate HTML for vulnerability scan results"""
        html = '<h3 class="section-title">🛡️ Vulnerability Scanning</h3>'
        
        # Semgrep results
        if 'semgrep' in vuln_data:
            semgrep_data = vuln_data['semgrep']
            html += f"""
            <h4>Semgrep Security Scan</h4>
            <p>Status: <span class="status-badge status-{'success' if semgrep_data.get('status') == 'success' else 'error'}">
                {semgrep_data.get('status', 'unknown').upper()}
            </span></p>
            """
            
            if semgrep_data.get('status') == 'success':
                total_findings = semgrep_data.get('total_findings', 0)
                html += f"<p><strong>Total Findings:</strong> {total_findings}</p>"
                
                severity_breakdown = semgrep_data.get('severity_breakdown', {})
                if severity_breakdown:
                    html += "<div class='stats-table'>"
                    html += "<table><tr><th>Severity</th><th>Count</th></tr>"
                    for severity, count in severity_breakdown.items():
                        html += f"<tr><td>{severity.title()}</td><td>{count}</td></tr>"
                    html += "</table></div>"
        
        # Bandit results
        if 'bandit' in vuln_data:
            bandit_data = vuln_data['bandit']
            html += f"""
            <h4>Bandit Security Scan</h4>
            <p>Status: <span class="status-badge status-{'success' if bandit_data.get('status') == 'success' else 'error'}">
                {bandit_data.get('status', 'unknown').upper()}
            </span></p>
            """
        
        # Custom checks
        if 'custom_checks' in vuln_data:
            custom_data = vuln_data['custom_checks']
            html += f"""
            <h4>Custom Security Checks</h4>
            <p>Status: <span class="status-badge status-{'success' if custom_data.get('status') == 'success' else 'error'}">
                {custom_data.get('status', 'unknown').upper()}
            </span></p>
            """
            
            if custom_data.get('status') == 'success':
                html += f"<p><strong>Checks Performed:</strong> {custom_data.get('checks_performed', 0)}</p>"
        
        return html
    
    def _generate_dependency_section_html(self, dep_data: Dict[str, Any]) -> str:
        """Generate HTML for dependency check results"""
        html = '<h3 class="section-title">📦 Dependency Security</h3>'
        
        if 'summary' in dep_data:
            summary = dep_data['summary']
            html += f"""
            <h4>Summary</h4>
            <div class='stats-table'>
            <table>
                <tr><th>Metric</th><th>Count</th></tr>
                <tr><td>Total Dependencies</td><td>{summary.get('total_dependencies', 0)}</td></tr>
                <tr><td>Vulnerable Dependencies</td><td>{summary.get('vulnerable_dependencies', 0)}</td></tr>
                <tr><td>High Severity Issues</td><td>{summary.get('high_severity_issues', 0)}</td></tr>
                <tr><td>Medium Severity Issues</td><td>{summary.get('medium_severity_issues', 0)}</td></tr>
                <tr><td>Low Severity Issues</td><td>{summary.get('low_severity_issues', 0)}</td></tr>
            </table>
            </div>
            """
        
        return html
    
    def _generate_quality_section_html(self, quality_data: Dict[str, Any]) -> str:
        """Generate HTML for code quality scan results"""
        html = '<h3 class="section-title">🔧 Code Quality</h3>'
        
        if 'summary' in quality_data:
            summary = quality_data['summary']
            html += f"""
            <h4>Summary</h4>
            <div class='stats-table'>
            <table>
                <tr><th>Metric</th><th>Count</th></tr>
                <tr><td>Total Linters Run</td><td>{summary.get('total_linters_run', 0)}</td></tr>
                <tr><td>Total Issues Found</td><td>{summary.get('total_issues_found', 0)}</td></tr>
                <tr><td>Code Formatting Issues</td><td>{summary.get('code_formatting_issues', 0)}</td></tr>
                <tr><td>Type Checking Issues</td><td>{summary.get('type_checking_issues', 0)}</td></tr>
                <tr><td>Security Issues</td><td>{summary.get('security_issues', 0)}</td></tr>
                <tr><td>Documentation Coverage</td><td>{summary.get('documentation_coverage', 0)}%</td></tr>
            </table>
            </div>
            """
        
        return html
    
    def _generate_recommendations_html(self, stats: Dict[str, int], scan_results: Dict[str, Any]) -> str:
        """Generate recommendations HTML based on scan results"""
        recommendations = []
        
        # Critical issues recommendations
        if stats['critical'] > 0:
            recommendations.append(
                f"<strong>Critical Issues Detected ({stats['critical']}):</strong> "
                "Address critical security vulnerabilities immediately as they pose "
                "significant security risks to your application."
            )
        
        # High severity recommendations
        if stats['high'] > 0:
            recommendations.append(
                f"<strong>High Priority Issues ({stats['high']}):</strong> "
                "Review and resolve high-severity issues promptly. These could lead "
                "to security breaches if exploited."
            )
        
        # Dependency recommendations
        if 'dependencies' in scan_results:
            dep_summary = scan_results['dependencies'].get('summary', {})
            if dep_summary.get('vulnerable_dependencies', 0) > 0:
                recommendations.append(
                    f"<strong>Vulnerable Dependencies ({dep_summary.get('vulnerable_dependencies', 0)}):</strong> "
                    "Update or replace vulnerable dependencies to known secure versions. "
                    "Enable automated dependency updates where possible."
                )
        
        # Code quality recommendations
        if 'code_quality' in scan_results:
            quality_summary = scan_results['code_quality'].get('summary', {})
            if quality_summary.get('code_formatting_issues', 0) > 0:
                recommendations.append(
                    "<strong>Code Formatting:</strong> "
                    "Implement automated code formatting to improve code consistency "
                    "and maintainability. Consider using tools like Black or Prettier."
                )
            
            if quality_summary.get('documentation_coverage', 0) < 80:
                recommendations.append(
                    f"<strong>Documentation Coverage ({quality_summary.get('documentation_coverage', 0)}%):</strong> "
                    "Improve documentation coverage to enhance code maintainability "
                    "and reduce onboarding time for new developers."
                )
        
        # General security recommendations
        recommendations.extend([
            "<strong>Regular Scanning:</strong> "
            "Implement automated security scanning in your CI/CD pipeline to catch "
            "issues early in the development process.",
            
            "<strong>Security Training:</strong> "
            "Provide security training for development teams to improve secure "
            "coding practices and awareness of common vulnerabilities.",
            
            "<strong>Update Strategy:</strong> "
            "Establish a regular schedule for dependency updates and security patches "
            "to maintain a secure codebase."
        ])
        
        # Generate HTML list
        html = "<ul>"
        for rec in recommendations:
            html += f"<li>{rec}</li>"
        html += "</ul>"
        
        return html
    
    def _generate_summary_text(self, scan_results: Dict[str, Any]) -> str:
        """Generate summary text for the report"""
        stats = self._calculate_overall_stats(scan_results)
        
        summary = f"""
SECURITY SCAN REPORT SUMMARY
===========================
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

EXECUTIVE SUMMARY
-----------------
Critical Issues:   {stats['critical']}
High Priority:     {stats['high']}
Medium Priority:   {stats['medium']}
Low Priority:      {stats['low']}
Total Issues:      {stats['total']}

VULNERABILITY SCANNING
---------------------
"""
        
        if 'vulnerabilities' in scan_results:
            vuln_data = scan_results['vulnerabilities']
            
            if 'semgrep' in vuln_data:
                semgrep_data = vuln_data['semgrep']
                if semgrep_data.get('status') == 'success':
                    summary += f"Semgrep: {semgrep_data.get('total_findings', 0)} findings\n"
            
            if 'bandit' in vuln_data:
                bandit_data = vuln_data['bandit']
                if bandit_data.get('status') == 'success':
                    summary += f"Bandit: {bandit_data.get('total_findings', 0)} findings\n"
            
            if 'custom_checks' in vuln_data:
                custom_data = vuln_data['custom_checks']
                if custom_data.get('status') == 'success':
                    summary += f"Custom Checks: {custom_data.get('checks_performed', 0)} checks performed\n"
        
        summary += "\nDEPENDENCY SECURITY\n-------------------\n"
        
        if 'dependencies' in scan_results:
            dep_summary = scan_results['dependencies'].get('summary', {})
            summary += f"Total Dependencies: {dep_summary.get('total_dependencies', 0)}\n"
            summary += f"Vulnerable Dependencies: {dep_summary.get('vulnerable_dependencies', 0)}\n"
            summary += f"High Severity Issues: {dep_summary.get('high_severity_issues', 0)}\n"
            summary += f"Medium Severity Issues: {dep_summary.get('medium_severity_issues', 0)}\n"
        
        summary += "\nCODE QUALITY\n-------------\n"
        
        if 'code_quality' in scan_results:
            quality_summary = scan_results['code_quality'].get('summary', {})
            summary += f"Total Issues: {quality_summary.get('total_issues_found', 0)}\n"
            summary += f"Documentation Coverage: {quality_summary.get('documentation_coverage', 0)}%\n"
        
        summary += "\nRECOMMENDATIONS\n---------------\n"
        summary += "1. Address critical and high-priority issues immediately\n"
        summary += "2. Update vulnerable dependencies to secure versions\n"
        summary += "3. Implement automated security scanning in CI/CD\n"
        summary += "4. Provide security training for development teams\n"
        summary += "5. Establish regular security update schedules\n"
        
        summary += "\n" + "="*50 + "\n"
        summary += "End of Report\n"
        
        return summary
    
    def export_markdown_report(self, scan_results: Dict[str, Any], timestamp: str) -> Path:
        """Generate Markdown report"""
        output_file = self.output_dir / f"security_report_{timestamp}.md"
        
        stats = self._calculate_overall_stats(scan_results)
        
        markdown_content = f"""# 🔒 Security Scan Report

**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  
**Timestamp:** {timestamp}

## 📊 Executive Summary

| Severity | Count |
|----------|-------|
| 🔴 Critical | {stats['critical']} |
| 🟠 High | {stats['high']} |
| 🟡 Medium | {stats['medium']} |
| 🟢 Low | {stats['low']} |
| **Total** | **{stats['total']}** |

## 🛡️ Vulnerability Scanning

{self._generate_markdown_vulnerabilities(scan_results.get('vulnerabilities', {}))}

## 📦 Dependency Security

{self._generate_markdown_dependencies(scan_results.get('dependencies', {}))}

## 🔧 Code Quality

{self._generate_markdown_quality(scan_results.get('code_quality', {}))}

## 💡 Recommendations

{self._generate_markdown_recommendations(stats, scan_results)}

---
*Generated by Security Automation Tool | Version 1.0*
"""
        
        with open(output_file, 'w') as f:
            f.write(markdown_content)
        
        return output_file
    
    def _generate_markdown_vulnerabilities(self, vuln_data: Dict[str, Any]) -> str:
        """Generate markdown for vulnerability results"""
        markdown = ""
        
        for tool, data in vuln_data.items():
            if tool == 'summary':
                continue
            
            status = data.get('status', 'unknown')
            markdown += f"### {tool.title()}\n\n"
            markdown += f"**Status:** {status}\n\n"
            
            if tool == 'semgrep' and status == 'success':
                markdown += f"**Total Findings:** {data.get('total_findings', 0)}\n\n"
                severity_breakdown = data.get('severity_breakdown', {})
                if severity_breakdown:
                    markdown += "**Severity Breakdown:**\n"
                    for severity, count in severity_breakdown.items():
                        markdown += f"- {severity.title()}: {count}\n"
                    markdown += "\n"
        
        return markdown
    
    def _generate_markdown_dependencies(self, dep_data: Dict[str, Any]) -> str:
        """Generate markdown for dependency results"""
        if 'summary' not in dep_data:
            return "No dependency data available.\n"
        
        summary = dep_data['summary']
        markdown = f"""**Total Dependencies:** {summary.get('total_dependencies', 0)}
**Vulnerable Dependencies:** {summary.get('vulnerable_dependencies', 0)}
**High Severity Issues:** {summary.get('high_severity_issues', 0)}
**Medium Severity Issues:** {summary.get('medium_severity_issues', 0)}
"""
        
        return markdown
    
    def _generate_markdown_quality(self, quality_data: Dict[str, Any]) -> str:
        """Generate markdown for code quality results"""
        if 'summary' not in quality_data:
            return "No quality data available.\n"
        
        summary = quality_data['summary']
        markdown = f"""**Total Linters Run:** {summary.get('total_linters_run', 0)}
**Total Issues Found:** {summary.get('total_issues_found', 0)}
**Documentation Coverage:** {summary.get('documentation_coverage', 0)}%
"""
        
        return markdown
    
    def _generate_markdown_recommendations(self, stats: Dict[str, int], scan_results: Dict[str, Any]) -> str:
        """Generate markdown recommendations"""
        recommendations = [
            "Address critical and high-priority issues immediately",
            "Update vulnerable dependencies to secure versions",
            "Implement automated security scanning in CI/CD pipeline",
            "Provide security training for development teams",
            "Establish regular security update schedules"
        ]
        
        if stats['critical'] > 0:
            recommendations.insert(0, f"🚨 Critical issues detected - requires immediate attention")
        
        markdown = ""
        for i, rec in enumerate(recommendations, 1):
            markdown += f"{i}. {rec}\n"
        
        return markdown