#!/bin/bash

# Automation Hub Dashboard Startup Script
# This script helps you set up and run the dashboard system

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_NAME="Automation Hub Dashboard"
CONFIG_FILE="config/dashboard.yaml"
LOG_FILE="logs/startup.log"

# Functions
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1" | tee -a "$LOG_FILE"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1" | tee -a "$LOG_FILE"
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1" | tee -a "$LOG_FILE"
}

info() {
    echo -e "${BLUE}[INFO]${NC} $1" | tee -a "$LOG_FILE"
}

check_requirements() {
    log "Checking system requirements..."
    
    # Check Python
    if ! command -v python3 &> /dev/null; then
        error "Python 3 is not installed. Please install Python 3.8 or higher."
        exit 1
    fi
    
    local python_version=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1-2)
    if [[ "$python_version" < "3.8" ]]; then
        error "Python version must be 3.8 or higher. Current version: $python_version"
        exit 1
    fi
    
    # Check Node.js
    if ! command -v node &> /dev/null; then
        warning "Node.js is not installed. Frontend development will not be available."
    fi
    
    # Check pip
    if ! command -v pip &> /dev/null; then
        error "pip is not installed. Please install pip."
        exit 1
    fi
    
    log "System requirements check passed"
}

setup_backend() {
    log "Setting up backend dependencies..."
    
    cd backend
    if [ -f "requirements.txt" ]; then
        pip install -r requirements.txt
        log "Backend dependencies installed"
    else
        error "Backend requirements.txt not found"
        exit 1
    fi
    cd ..
}

setup_frontend() {
    if ! command -v node &> /dev/null; then
        warning "Skipping frontend setup - Node.js not available"
        return
    fi
    
    log "Setting up frontend dependencies..."
    
    cd frontend
    if [ -f "package.json" ]; then
        npm install
        log "Frontend dependencies installed"
    else
        error "Frontend package.json not found"
        exit 1
    fi
    cd ..
}

setup_config() {
    log "Setting up configuration..."
    
    if [ ! -f "$CONFIG_FILE" ]; then
        warning "Configuration file not found. Creating from template..."
        mkdir -p config
        cp config/dashboard.yaml "$CONFIG_FILE"
        
        warning "Please edit $CONFIG_FILE with your settings"
        warning "Configure notification webhooks, database settings, etc."
    else
        log "Configuration file found"
    fi
}

create_directories() {
    log "Creating necessary directories..."
    
    mkdir -p logs
    mkdir -p data
    mkdir -p static
    mkdir -p uploads
    mkdir -p grafana/provisioning/datasources
    mkdir -p grafana/provisioning/dashboards
    
    log "Directories created"
}

start_services() {
    local mode="$1"
    
    case "$mode" in
        "development"|"dev")
            start_development
            ;;
        "production"|"prod")
            start_production
            ;;
        "docker")
            start_docker
            ;;
        "demo")
            start_demo
            ;;
        *)
            error "Unknown mode: $mode"
            show_help
            exit 1
            ;;
    esac
}

start_development() {
    log "Starting in development mode..."
    
    # Start backend in background
    log "Starting backend server..."
    cd backend
    python dashboard_api.py &
    BACKEND_PID=$!
    cd ..
    
    # Wait a moment for backend to start
    sleep 3
    
    # Start frontend
    if command -v node &> /dev/null; then
        log "Starting frontend development server..."
        cd frontend
        npm run dev &
        FRONTEND_PID=$!
        cd ..
    fi
    
    info "Development servers started!"
    info "Backend: http://localhost:8000"
    info "Frontend: http://localhost:3000"
    info "API Docs: http://localhost:8000/docs"
    
    # Wait for user input
    log "Press Ctrl+C to stop all servers..."
    
    trap cleanup SIGINT SIGTERM
    
    while true; do
        sleep 1
    done
}

start_production() {
    log "Starting in production mode..."
    
    if [ ! -f "$CONFIG_FILE" ]; then
        error "Configuration file not found. Please run setup first."
        exit 1
    fi
    
    log "Starting dashboard application..."
    python main.py --config "$CONFIG_FILE" --host 0.0.0.0
}

start_docker() {
    log "Starting with Docker Compose..."
    
    if ! command -v docker &> /dev/null; then
        error "Docker is not installed. Please install Docker first."
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        error "Docker Compose is not installed. Please install Docker Compose first."
        exit 1
    fi
    
    log "Starting services with Docker Compose..."
    docker-compose up -d
    
    info "Services started:"
    info "Dashboard: http://localhost:8000"
    info "Grafana: http://localhost:3001 (admin/admin123)"
    info "Prometheus: http://localhost:9090"
    info "Redis: localhost:6379"
    
    log "View logs with: docker-compose logs -f"
    log "Stop services with: docker-compose down"
}

start_demo() {
    log "Starting in demo mode with mock data..."
    
    # Use mock configuration
    DEMO_CONFIG="config/demo.yaml"
    
    if [ ! -f "$DEMO_CONFIG" ]; then
        log "Creating demo configuration..."
        cat > "$DEMO_CONFIG" << EOF
api:
  host: "0.0.0.0"
  port: 8000

development:
  mock_data:
    enabled: true
    interval: 5

notifications:
  slack:
    enabled: false
  discord:
    enabled: false

alerts:
  enabled: true
EOF
    fi
    
    start_production
}

cleanup() {
    log "Cleaning up..."
    
    if [ ! -z "$BACKEND_PID" ]; then
        kill $BACKEND_PID 2>/dev/null || true
    fi
    
    if [ ! -z "$FRONTEND_PID" ]; then
        kill $FRONTEND_PID 2>/dev/null || true
    fi
    
    log "Cleanup completed"
    exit 0
}

show_status() {
    log "Checking service status..."
    
    # Check if backend is running
    if curl -s http://localhost:8000/health > /dev/null 2>&1; then
        info "Backend: Running ✓"
    else
        info "Backend: Not running ✗"
    fi
    
    # Check if frontend is running
    if curl -s http://localhost:3000 > /dev/null 2>&1; then
        info "Frontend: Running ✓"
    else
        info "Frontend: Not running ✗"
    fi
    
    # Check Docker services
    if command -v docker-compose &> /dev/null; then
        info "Docker services status:"
        docker-compose ps 2>/dev/null | grep -E "(dashboard|prometheus|grafana|redis)" || true
    fi
}

show_logs() {
    log "Showing recent logs..."
    
    if [ -f "logs/startup.log" ]; then
        tail -50 logs/startup.log
    fi
    
    if command -v docker-compose &> /dev/null; then
        echo ""
        info "Docker service logs:"
        docker-compose logs --tail=20 dashboard
    fi
}

show_help() {
    echo "Usage: $0 [COMMAND] [OPTIONS]"
    echo ""
    echo "Commands:"
    echo "  setup          Set up the development environment"
    echo "  start [MODE]   Start the dashboard system"
    echo "  status         Check service status"
    echo "  logs           Show recent logs"
    echo "  help           Show this help message"
    echo ""
    echo "Modes for start command:"
    echo "  development    Start in development mode (default)"
    echo "  production     Start in production mode"
    echo "  docker         Start with Docker Compose"
    echo "  demo           Start in demo mode with mock data"
    echo ""
    echo "Examples:"
    echo "  $0 setup"
    echo "  $0 start development"
    echo "  $0 start docker"
    echo "  $0 status"
}

# Main script logic
main() {
    # Create logs directory
    mkdir -p logs
    
    # Create log file
    echo "=== Automation Hub Dashboard Startup ===" > "$LOG_FILE"
    log "Starting automation hub dashboard setup"
    
    case "$1" in
        "setup")
            check_requirements
            setup_backend
            setup_frontend
            setup_config
            create_directories
            log "Setup completed successfully!"
            ;;
        "start")
            create_directories
            start_services "${2:-development}"
            ;;
        "status")
            show_status
            ;;
        "logs")
            show_logs
            ;;
        "help"|"-h"|"--help")
            show_help
            ;;
        "")
            show_help
            ;;
        *)
            error "Unknown command: $1"
            show_help
            exit 1
            ;;
    esac
}

# Trap signals for cleanup
trap cleanup EXIT

# Run main function
main "$@"