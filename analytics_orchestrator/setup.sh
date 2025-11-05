#!/bin/bash
"""
Analytics Orchestrator Setup Script

Automated setup and configuration for the Analytics Orchestrator system.
"""

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_NAME="analytics-orchestrator"

echo -e "${BLUE}🚀 Analytics Orchestrator Setup${NC}"
echo "================================="

# Function to print colored output
print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️ $1${NC}"
}

# Check if running as root
check_root() {
    if [[ $EUID -eq 0 ]]; then
        print_warning "Running as root. Consider using a non-root user for security."
    fi
}

# Check system requirements
check_requirements() {
    print_info "Checking system requirements..."
    
    # Check Python version
    if command -v python3 &> /dev/null; then
        PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
        print_success "Python 3 found: $PYTHON_VERSION"
        
        # Check if Python 3.8+
        if python3 -c "import sys; sys.exit(0 if sys.version_info >= (3, 8) else 1)"; then
            print_success "Python version is compatible"
        else
            print_error "Python 3.8+ required. Found: $PYTHON_VERSION"
            exit 1
        fi
    else
        print_error "Python 3 not found. Please install Python 3.8+"
        exit 1
    fi
    
    # Check pip
    if command -v pip3 &> /dev/null; then
        print_success "pip3 found"
    else
        print_error "pip3 not found. Please install pip3"
        exit 1
    fi
    
    # Check Docker
    if command -v docker &> /dev/null; then
        DOCKER_VERSION=$(docker --version | cut -d' ' -f3 | cut -d',' -f1)
        print_success "Docker found: $DOCKER_VERSION"
    else
        print_warning "Docker not found. Docker deployment will not be available."
    fi
    
    # Check Docker Compose
    if command -v docker-compose &> /dev/null; then
        COMPOSE_VERSION=$(docker-compose --version | cut -d' ' -f3 | cut -d',' -f1)
        print_success "Docker Compose found: $COMPOSE_VERSION"
    else
        print_warning "Docker Compose not found."
    fi
    
    # Check Redis
    if command -v redis-cli &> /dev/null; then
        print_success "Redis CLI found"
    else
        print_warning "Redis CLI not found. Redis may need to be installed separately."
    fi
}

# Create directory structure
setup_directories() {
    print_info "Setting up directory structure..."
    
    mkdir -p data/{cache,logs,database}
    mkdir -p config
    mkdir -p monitoring/{grafana,prometheus}
    mkdir -p scripts
    mkdir -p tests
    
    print_success "Directory structure created"
}

# Install Python dependencies
install_dependencies() {
    print_info "Installing Python dependencies..."
    
    # Create virtual environment if it doesn't exist
    if [ ! -d "venv" ]; then
        print_info "Creating virtual environment..."
        python3 -m venv venv
        print_success "Virtual environment created"
    fi
    
    # Activate virtual environment
    source venv/bin/activate
    
    # Upgrade pip
    pip install --upgrade pip
    
    # Install requirements
    pip install -r requirements.txt
    print_success "Python dependencies installed"
}

# Setup configuration
setup_config() {
    print_info "Setting up configuration..."
    
    if [ ! -f "config/config.yaml" ]; then
        if [ -f "config/config.yaml.example" ]; then
            cp config/config.yaml.example config/config.yaml
            print_success "Configuration template created"
            print_warning "Please edit config/config.yaml with your settings"
        else
            print_error "Configuration template not found"
            exit 1
        fi
    else
        print_info "Configuration file already exists"
    fi
    
    # Create environment file template
    if [ ! -f ".env.example" ]; then
        cat > .env.example << 'EOF'
# Analytics Orchestrator Environment Variables

# GitHub Integration
GITHUB_TOKEN=your_github_token_here
GITHUB_WEBHOOK_SECRET=your_webhook_secret_here

# Database
DATABASE_URL=sqlite:///data/analytics.db

# Cache
CACHE_URL=redis://localhost:6379/0
REDIS_URL=redis://localhost:6379/1

# Security
JWT_SECRET=your_jwt_secret_here
API_KEYS=your_api_keys_here

# Monitoring
PROMETHEUS_PORT=9090
GRAFANA_PORT=3000

# Application
LOG_LEVEL=INFO
DEBUG=false
ENVIRONMENT=development
EOF
        print_success "Environment template created"
    fi
}

# Setup monitoring configuration
setup_monitoring() {
    print_info "Setting up monitoring configuration..."
    
    # Prometheus configuration
    cat > monitoring/prometheus.yml << 'EOF'
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'analytics-orchestrator'
    static_configs:
      - targets: ['analytics-orchestrator:8000']
    metrics_path: '/metrics'
    scrape_interval: 30s

  - job_name: 'redis'
    static_configs:
      - targets: ['redis:6379']
    metrics_path: '/metrics'
    scrape_interval: 30s
EOF
    
    # Grafana provisioning
    mkdir -p monitoring/grafana/provisioning/{datasources,dashboards}
    
    cat > monitoring/grafana/provisioning/datasources/prometheus.yml << 'EOF'
apiVersion: 1
datasources:
  - name: Prometheus
    type: prometheus
    access: proxy
    url: http://prometheus:9090
    isDefault: true
EOF
    
    cat > monitoring/grafana/provisioning/dashboards/default.yml << 'EOF'
apiVersion: 1
providers:
  - name: 'default'
    orgId: 1
    folder: ''
    type: file
    disableDeletion: false
    editable: true
    updateIntervalSeconds: 10
    allowUiUpdates: true
    options:
      path: /var/lib/grafana/dashboards
EOF
    
    print_success "Monitoring configuration created"
}

# Setup systemd service (Linux only)
setup_systemd() {
    if [[ "$OSTYPE" != "linux-gnu"* ]]; then
        print_info "Systemd service setup skipped (not Linux)"
        return
    fi
    
    read -p "Setup systemd service? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        print_info "Setting up systemd service..."
        
        SERVICE_FILE="/etc/systemd/system/${PROJECT_NAME}.service"
        
        # Get current user
        CURRENT_USER=$(whoami)
        CURRENT_DIR=$(pwd)
        
        sudo tee $SERVICE_FILE > /dev/null << EOF
[Unit]
Description=Analytics Orchestrator Service
After=network.target

[Service]
Type=simple
User=$CURRENT_USER
WorkingDirectory=$CURRENT_DIR
ExecStart=$CURRENT_DIR/venv/bin/python cli.py start
Restart=always
RestartSec=10
Environment=PATH=$CURRENT_DIR/venv/bin
EnvironmentFile=$CURRENT_DIR/.env

[Install]
WantedBy=multi-user.target
EOF
        
        sudo systemctl daemon-reload
        sudo systemctl enable $PROJECT_NAME
        print_success "Systemd service created and enabled"
        print_info "Use 'sudo systemctl start $PROJECT_NAME' to start the service"
    fi
}

# Create startup scripts
create_scripts() {
    print_info "Creating startup scripts..."
    
    # Start script
    cat > scripts/start.sh << 'EOF'
#!/bin/bash
# Analytics Orchestrator Start Script

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_DIR"

# Activate virtual environment
source venv/bin/activate

# Check if .env file exists
if [ ! -f .env ]; then
    echo "⚠️ .env file not found. Copying from .env.example..."
    cp .env.example .env
    echo "⚠️ Please edit .env with your settings before running"
    exit 1
fi

# Start the orchestrator
echo "🚀 Starting Analytics Orchestrator..."
python cli.py start
EOF
    
    # Stop script
    cat > scripts/stop.sh << 'EOF'
#!/bin/bash
# Analytics Orchestrator Stop Script

# This is a placeholder - implement actual stop logic
echo "Stop script not implemented"
echo "Use Ctrl+C to stop the service or manage with systemd"
EOF
    
    # Docker start script
    cat > scripts/docker-start.sh << 'EOF'
#!/bin/bash
# Analytics Orchestrator Docker Start Script

set -e

echo "🚀 Starting Analytics Orchestrator with Docker Compose..."

# Check if .env file exists
if [ ! -f .env ]; then
    echo "⚠️ .env file not found. Copying from .env.example..."
    cp .env.example .env
    echo "⚠️ Please edit .env with your settings before running"
fi

# Start services
docker-compose up -d

echo "✅ Analytics Orchestrator started with Docker"
echo "📊 Access points:"
echo "  - API: http://localhost:8000"
echo "  - Prometheus: http://localhost:9090"
echo "  - Grafana: http://localhost:3000 (admin/admin123)"
EOF
    
    # Make scripts executable
    chmod +x scripts/*.sh
    
    print_success "Startup scripts created"
}

# Run tests
run_tests() {
    print_info "Running basic configuration tests..."
    
    source venv/bin/activate
    
    if python -c "from core.config_manager import ConfigManager; ConfigManager('config/config.yaml').load_config()" 2>/dev/null; then
        print_success "Configuration test passed"
    else
        print_error "Configuration test failed"
        return 1
    fi
    
    if python -c "import core.orchestrator" 2>/dev/null; then
        print_success "Import test passed"
    else
        print_error "Import test failed"
        return 1
    fi
    
    print_success "All tests passed"
}

# Main setup function
main() {
    check_root
    check_requirements
    setup_directories
    install_dependencies
    setup_config
    setup_monitoring
    create_scripts
    
    # Ask about systemd setup
    setup_systemd
    
    # Run tests
    if run_tests; then
        print_success "Setup completed successfully!"
        
        echo
        echo -e "${GREEN}🎉 Setup Complete!${NC}"
        echo "=================="
        echo "Next steps:"
        echo "1. Edit config/config.yaml with your settings"
        echo "2. Copy .env.example to .env and add your credentials"
        echo "3. Start the service:"
        echo "   - Development: ./scripts/start.sh"
        echo "   - Docker: ./scripts/docker-start.sh"
        echo "   - Systemd: sudo systemctl start analytics-orchestrator"
        echo
        echo "Documentation: README.md"
        echo "CLI Help: python cli.py --help"
        
    else
        print_error "Setup completed with errors. Please check the output above."
        exit 1
    fi
}

# Handle script arguments
case "${1:-}" in
    --help|-h)
        echo "Analytics Orchestrator Setup Script"
        echo "Usage: $0 [--help]"
        echo
        echo "This script will:"
        echo "- Check system requirements"
        echo "- Install Python dependencies"
        echo "- Setup directory structure"
        echo "- Create configuration files"
        echo "- Setup monitoring (Prometheus, Grafana)"
        echo "- Create startup scripts"
        echo "- Optionally setup systemd service"
        echo "- Run basic tests"
        exit 0
        ;;
    *)
        main "$@"
        ;;
esac