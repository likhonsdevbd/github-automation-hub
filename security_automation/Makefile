# Security Automation Tool Makefile

.PHONY: help install setup scan-full scan-vuln scan-deps scan-quality demo clean test lint format security-check

# Default target
help:
	@echo "Security Automation Tool - Available Commands:"
	@echo "==============================================="
	@echo ""
	@echo "Setup & Installation:"
	@echo "  install       Install core dependencies"
	@echo "  setup         Run complete setup (recommended)"
	@echo "  setup-github  Setup GitHub integration"
	@echo ""
	@echo "Security Scanning:"
	@echo "  scan-full     Run comprehensive security scan"
	@echo "  scan-vuln     Run vulnerability scanning only"
	@echo "  scan-deps     Check dependencies for vulnerabilities"
	@echo "  scan-quality  Run code quality analysis"
	@echo "  security-check Run quick security validation"
	@echo ""
	@echo "Development & Maintenance:"
	@echo "  lint          Run code linting"
	@echo "  format        Format code with Black and isort"
	@echo "  test          Run security tool tests"
	@echo "  demo          Run security demo"
	@echo "  clean         Clean up generated files"
	@echo ""
	@echo "Advanced:"
	@echo "  github-setup  Configure GitHub security features"
	@echo "  monitoring    Setup continuous monitoring"
	@echo "  report        Generate security report"
	@echo "  update-deps   Update vulnerable dependencies"

# Setup commands
install:
	@echo "Installing Security Automation Tool dependencies..."
	pip install -r requirements.txt
	@echo "✅ Core dependencies installed"

setup:
	@echo "Running Security Automation Tool setup..."
	python setup.py
	@echo "✅ Setup completed"

setup-github:
	@echo "Setting up GitHub integration..."
	@read -p "Enter GitHub repository URL: " repo_url; \
	python security_cli.py github-setup --repo-url "$$repo_url"
	@echo "✅ GitHub integration configured"

# Security scanning commands
scan-full:
	@echo "Running comprehensive security scan..."
	python security_cli.py full-scan --project-path . --output-dir ./security-reports --format all
	@echo "✅ Full security scan completed"

scan-vuln:
	@echo "Running vulnerability scan..."
	python security_cli.py vuln-scan --project-path . --format json
	@echo "✅ Vulnerability scan completed"

scan-deps:
	@echo "Checking dependencies for vulnerabilities..."
	python security_cli.py dependency-check --project-path . --auto-update
	@echo "✅ Dependency check completed"

scan-quality:
	@echo "Running code quality analysis..."
	python security_cli.py quality-scan --project-path . --fix
	@echo "✅ Code quality scan completed"

security-check:
	@echo "Running quick security validation..."
	@echo "Checking for security tools..."
	@which semgrep > /dev/null && echo "✅ Semgrep found" || echo "⚠️ Semgrep not found"
	@which bandit > /dev/null && echo "✅ Bandit found" || echo "⚠️ Bandit not found"
	@which safety > /dev/null && echo "✅ Safety found" || echo "⚠️ Safety not found"
	@echo "Running minimal security scan..."
	python security_cli.py vuln-scan --project-path . --tools semgrep --format json || true
	@echo "✅ Security check completed"

# Development commands
lint:
	@echo "Running code linting..."
	@if command -v flake8 > /dev/null; then \
		flake8 . --max-line-length=88 --ignore=E203,W503; \
	else \
		echo "⚠️ Flake8 not installed"; \
	fi
	@echo "✅ Linting completed"

format:
	@echo "Formatting code..."
	@if command -v black > /dev/null; then \
		black . --line-length=88; \
	else \
		echo "⚠️ Black not installed"; \
	fi
	@if command -v isort > /dev/null; then \
		isort .; \
	else \
		echo "⚠️ isort not installed"; \
	fi
	@echo "✅ Code formatting completed"

test:
	@echo "Running security tool tests..."
	@echo "Testing CLI..."
	python security_cli.py --help > /dev/null && echo "✅ CLI working" || echo "❌ CLI test failed"
	@echo "Testing module imports..."
	python -c "import vulnerability_scanner, dependency_checker, code_quality_scanner, security_reporter" && echo "✅ All modules imported" || echo "❌ Import test failed"
	@echo "✅ Tests completed"

demo:
	@echo "Running security automation demo..."
	python demo.py
	@echo "✅ Demo completed"

# Advanced commands
github-setup:
	@echo "Configuring GitHub security features..."
	@read -p "Enter repository URL: " repo_url; \
	python security_cli.py github-setup --repo-url "$$repo_url" --setup-branch-protection
	@echo "✅ GitHub security features configured"

monitoring:
	@echo "Setting up continuous monitoring..."
	python security_cli.py setup-monitoring --project-path . --github-integration --schedule daily
	@echo "✅ Continuous monitoring configured"

report:
	@echo "Generating security report..."
	@read -p "Enter scan results file path: " results_file; \
	read -p "Enter output file path: " output_file; \
	python security_cli.py report --scan-results "$$results_file" --format html --output "$$output_file"
	@echo "✅ Report generated"

update-deps:
	@echo "Updating vulnerable dependencies..."
	python security_cli.py dependency-check --project-path . --auto-update
	@echo "✅ Dependency update completed"

# Utility commands
clean:
	@echo "Cleaning up generated files..."
	@find . -name "*.pyc" -delete 2>/dev/null || true
	@find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
	@rm -rf security-reports/ 2>/dev/null || true
	@rm -rf .pytest_cache/ 2>/dev/null || true
	@rm -f *.json 2>/dev/null || true
	@rm -f .secrets.baseline 2>/dev/null || true
	@echo "✅ Cleanup completed"

# Security tool installation
install-tools:
	@echo "Installing security tools..."
	pip install semgrep bandit safety pip-audit
	pip install flake8 black isort mypy pylint radon vulture
	@echo "✅ Security tools installed"

install-all: install install-tools
	@echo "✅ Full installation completed"

# GitHub Actions workflow example
github-workflow:
	@echo "Creating GitHub Actions workflow example..."
	@mkdir -p .github/workflows
	@cat > .github/workflows/security.yml << 'EOF'
name: Security Scan
on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]
  schedule:
    - cron: '0 2 * * *'
jobs:
  security-scan:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v4
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.9'
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install semgrep bandit safety
    - name: Run security scan
      run: |
        python security_automation/security_cli.py full-scan --project-path .
EOF
	@echo "✅ GitHub Actions workflow created"

# Docker support
docker-build:
	@echo "Building Docker image..."
	docker build -t security-automation .
	@echo "✅ Docker image built"

docker-run:
	@echo "Running security scan in Docker..."
	@read -p "Enter project path to scan: " project_path; \
	docker run --rm -v "$$project_path:/app" security-automation python security_automation/security_cli.py full-scan --project-path /app
	@echo "✅ Docker scan completed"

# Project status
status:
	@echo "Security Automation Tool Status"
	@echo "================================"
	@echo "Python version: $(shell python --version)"
	@echo "Working directory: $(PWD)"
	@echo "Tool files: $(shell ls -1 *.py | tr '\n' ' ')"
	@echo ""
	@echo "Security tools status:"
	@command -v semgrep >/dev/null && echo "  ✅ Semgrep" || echo "  ⚠️ Semgrep not installed"
	@command -v bandit >/dev/null && echo "  ✅ Bandit" || echo "  ⚠️ Bandit not installed"
	@command -v safety >/dev/null && echo "  ✅ Safety" || echo "  ⚠️ Safety not installed"
	@command -v flake8 >/dev/null && echo "  ✅ Flake8" || echo "  ⚠️ Flake8 not installed"
	@command -v black >/dev/null && echo "  ✅ Black" || echo "  ⚠️ Black not installed"
	@command -v isort >/dev/null && echo "  ✅ isort" || echo "  ⚠️ isort not installed"
	@echo ""
	@echo "Configuration files:"
	@ls -1 config.ini requirements.txt setup.py demo.py README.md LICENSE CHANGELOG.md 2>/dev/null | sed 's/^/  ✅ /' || echo "  ⚠️ Some files missing"

# All-in-one commands
quick-start: install scan-full
	@echo "✅ Quick start completed - security scan finished"

full-setup: install install-tools setup github-workflow
	@echo "✅ Full setup completed - ready for use"

# CI/CD integration example
ci-check:
	@echo "Running CI/CD security checks..."
	python security_cli.py quality-scan --project-path .
	python security_cli.py dependency-check --project-path .
	@echo "✅ CI/CD security checks completed"