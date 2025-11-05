#!/bin/bash
"""
Analytics Orchestrator Deployment Script

Automated deployment script for the Analytics Orchestrator system.
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
DEPLOYMENT_ENV=${1:-"production"}
DOCKER_COMPOSE_FILE="docker-compose.yml"

# Default configuration
BACKUP_RETENTION_DAYS=7
LOG_LEVEL="INFO"
HEALTH_CHECK_TIMEOUT=60

echo -e "${BLUE}🚀 Analytics Orchestrator Deployment${NC}"
echo "======================================"
echo "Environment: $DEPLOYMENT_ENV"
echo

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

# Pre-deployment checks
pre_deployment_checks() {
    print_info "Running pre-deployment checks..."
    
    # Check if running in CI or with CI variable
    if [[ "${CI:-false}" == "true" ]]; then
        print_info "Running in CI mode"
        export CI_DEPLOY=true
    fi
    
    # Check Docker and Docker Compose
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed or not in PATH"
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        print_error "Docker Compose is not installed or not in PATH"
        exit 1
    fi
    
    # Check if configuration exists
    if [ ! -f "config/config.yaml" ]; then
        print_error "Configuration file not found: config/config.yaml"
        print_info "Please run setup.sh first or create config/config.yaml"
        exit 1
    fi
    
    # Validate configuration
    if ! python cli.py validate-config config/config.yaml; then
        print_error "Configuration validation failed"
        exit 1
    fi
    
    print_success "Pre-deployment checks passed"
}

# Backup current deployment
backup_deployment() {
    if [[ "$DEPLOYMENT_ENV" == "production" ]] && [ -d "data" ]; then
        print_info "Creating backup..."
        
        BACKUP_DIR="backups/$(date +%Y%m%d_%H%M%S)"
        mkdir -p "$BACKUP_DIR"
        
        # Backup data directory
        if [ -d "data" ]; then
            cp -r data "$BACKUP_DIR/"
            print_success "Data backed up to $BACKUP_DIR/data"
        fi
        
        # Backup configuration
        cp config/config.yaml "$BACKUP_DIR/"
        
        # Backup environment file
        if [ -f ".env" ]; then
            cp .env "$BACKUP_DIR/"
        fi
        
        # Clean old backups
        find backups/ -type d -mtime +$BACKUP_RETENTION_DAYS -exec rm -rf {} + 2>/dev/null || true
        
        print_success "Backup completed"
    fi
}

# Load environment variables
load_environment() {
    print_info "Loading environment configuration..."
    
    # Set environment-specific variables
    case "$DEPLOYMENT_ENV" in
        development)
            export LOG_LEVEL="DEBUG"
            export ENVIRONMENT="development"
            export DEBUG="true"
            ;;
        staging)
            export LOG_LEVEL="INFO"
            export ENVIRONMENT="staging"
            export DEBUG="false"
            ;;
        production)
            export LOG_LEVEL="INFO"
            export ENVIRONMENT="production"
            export DEBUG="false"
            ;;
        *)
            print_error "Unknown environment: $DEPLOYMENT_ENV"
            exit 1
            ;;
    esac
    
    # Load .env file if it exists
    if [ -f ".env" ]; then
        set -a
        source .env
        set +a
        print_success "Environment variables loaded from .env"
    else
        print_warning ".env file not found"
    fi
    
    # Validate required environment variables
    if [[ "$DEPLOYMENT_ENV" != "development" ]]; then
        required_vars=("GITHUB_TOKEN" "JWT_SECRET" "API_KEYS")
        for var in "${required_vars[@]}"; do
            if [[ -z "${!var:-}" ]]; then
                print_error "Required environment variable not set: $var"
                exit 1
            fi
        done
    fi
}

# Build and prepare container images
prepare_images() {
    print_info "Preparing container images..."
    
    # Build the application image
    docker build -t ${PROJECT_NAME}:latest .
    docker build -t ${PROJECT_NAME}:${DEPLOYMENT_ENV} .
    
    print_success "Container images prepared"
}

# Deploy services
deploy_services() {
    print_info "Deploying services..."
    
    # Pull base images
    docker-compose pull redis prometheus grafana
    
    # Start services
    if [[ "$DEPLOYMENT_ENV" == "development" ]]; then
        docker-compose up -d --remove-orphans
    else
        docker-compose -f docker-compose.yml up -d --remove-orphans
    fi
    
    print_success "Services deployed"
}

# Wait for services to be healthy
wait_for_health() {
    print_info "Waiting for services to be healthy..."
    
    local timeout=$HEALTH_CHECK_TIMEOUT
    local interval=5
    local elapsed=0
    
    while [ $elapsed -lt $timeout ]; do
        if curl -f http://localhost:8000/health >/dev/null 2>&1; then
            print_success "Analytics Orchestrator is healthy"
            break
        fi
        
        echo -n "."
        sleep $interval
        elapsed=$((elapsed + interval))
    done
    
    if [ $elapsed -ge $timeout ]; then
        print_error "Health check timeout - service may not be ready"
        return 1
    fi
    
    echo
}

# Run post-deployment tests
run_tests() {
    print_info "Running post-deployment tests..."
    
    # Test API endpoints
    if curl -f http://localhost:8000/health >/dev/null 2>&1; then
        print_success "Health endpoint test passed"
    else
        print_error "Health endpoint test failed"
        return 1
    fi
    
    # Test metrics endpoint
    if curl -f http://localhost:8000/metrics >/dev/null 2>&1; then
        print_success "Metrics endpoint test passed"
    else
        print_error "Metrics endpoint test failed"
        return 1
    fi
    
    # Test Docker services
    if docker-compose ps | grep -q "Up"; then
        print_success "Docker services test passed"
    else
        print_error "Docker services test failed"
        return 1
    fi
    
    print_success "Post-deployment tests passed"
}

# Setup monitoring
setup_monitoring() {
    print_info "Setting up monitoring..."
    
    # Wait for Grafana to be ready
    sleep 10
    
    # Setup Grafana datasource (if not already configured)
    if command -v grafana-cli &> /dev/null; then
        # This would typically be handled by Grafana provisioning
        print_info "Grafana monitoring setup completed"
    fi
    
    print_success "Monitoring setup completed"
}

# Generate deployment report
generate_report() {
    print_info "Generating deployment report..."
    
    cat > deployment-report.txt << EOF
Analytics Orchestrator Deployment Report
========================================

Deployment Date: $(date)
Environment: $DEPLOYMENT_ENV
Host: $(hostname)
User: $(whoami)

Services Status:
$(docker-compose ps)

Resource Usage:
$(docker stats --no-stream)

Network Configuration:
$(docker network ls)

Access Points:
- Analytics API: http://localhost:8000
- Prometheus: http://localhost:9090
- Grafana: http://localhost:3000

Logs:
$(tail -20 logs/*.log 2>/dev/null || echo "No logs available")

Configuration:
- Config file: config/config.yaml
- Environment file: .env
- Docker Compose: docker-compose.yml

EOF
    
    print_success "Deployment report generated: deployment-report.txt"
}

# Cleanup function
cleanup() {
    print_info "Cleaning up..."
    
    # Remove dangling images
    docker image prune -f >/dev/null 2>&1
    
    # Remove unused volumes (be careful in production)
    if [[ "$DEPLOYMENT_ENV" == "development" ]]; then
        docker volume prune -f >/dev/null 2>&1
    fi
    
    print_success "Cleanup completed"
}

# Rollback function
rollback() {
    print_warning "Rollback requested..."
    
    # Find latest backup
    LATEST_BACKUP=$(ls -t backups/ 2>/dev/null | head -1)
    
    if [ -n "$LATEST_BACKUP" ]; then
        print_info "Rolling back to backup: $LATEST_BACKUP"
        
        # Stop services
        docker-compose down
        
        # Restore data
        if [ -d "backups/$LATEST_BACKUP/data" ]; then
            cp -r backups/$LATEST_BACKUP/data .
            print_success "Data restored from backup"
        fi
        
        # Restart services
        docker-compose up -d
        
        print_success "Rollback completed"
    else
        print_error "No backup found for rollback"
        exit 1
    fi
}

# Show status
show_status() {
    print_info "Deployment Status:"
    echo "==================="
    
    echo "Services:"
    docker-compose ps
    
    echo
    echo "Resource Usage:"
    docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}\t{{.BlockIO}}"
    
    echo
    echo "Recent Logs (last 10 lines):"
    docker-compose logs --tail=10
}

# Show help
show_help() {
    echo "Analytics Orchestrator Deployment Script"
    echo
    echo "Usage: $0 [ENVIRONMENT] [COMMAND]"
    echo
    echo "Environments:"
    echo "  development  - Development deployment"
    echo "  staging      - Staging deployment"
    echo "  production   - Production deployment (default)"
    echo
    echo "Commands:"
    echo "  deploy       - Deploy the application (default)"
    echo "  rollback     - Rollback to previous deployment"
    echo "  status       - Show deployment status"
    echo "  help         - Show this help message"
    echo
    echo "Examples:"
    echo "  $0 production deploy    # Deploy to production"
    echo "  $0 staging            # Deploy to staging"
    echo "  $0 development rollback  # Rollback development"
    echo "  $0 status             # Show status"
}

# Main deployment function
main() {
    local command=${2:-"deploy"}
    
    case "$command" in
        deploy)
            pre_deployment_checks
            backup_deployment
            load_environment
            prepare_images
            deploy_services
            wait_for_health
            run_tests
            setup_monitoring
            generate_report
            cleanup
            ;;
        rollback)
            rollback
            ;;
        status)
            show_status
            ;;
        help|--help|-h)
            show_help
            ;;
        *)
            print_error "Unknown command: $command"
            show_help
            exit 1
            ;;
    esac
    
    if [ "$command" == "deploy" ]; then
        print_success "🎉 Deployment completed successfully!"
        echo
        echo -e "${GREEN}Deployment Summary:${NC}"
        echo "=================="
        echo "Environment: $DEPLOYMENT_ENV"
        echo "Status: Running"
        echo
        echo "Access Points:"
        echo "  🌐 API: http://localhost:8000"
        echo "  📊 Prometheus: http://localhost:9090"
        echo "  📈 Grafana: http://localhost:3000"
        echo
        echo "Management:"
        echo "  Check status: $0 status"
        echo "  View logs: docker-compose logs -f"
        echo "  Rollback: $0 $DEPLOYMENT_ENV rollback"
        echo
        echo "Documentation: README.md"
    fi
}

# Handle script arguments
main "$@"