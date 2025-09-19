#!/bin/bash
set -e

# ARTIFACTOR v3.0 Production Deployment Script
# INFRASTRUCTURE Agent: Automated deployment orchestration

# Color output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
ENVIRONMENT=${1:-staging}
NAMESPACE="artifactor"
if [ "$ENVIRONMENT" = "staging" ]; then
    NAMESPACE="artifactor-staging"
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
K8S_DIR="$PROJECT_ROOT/k8s"

# Functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_prerequisites() {
    log_info "Checking prerequisites..."

    # Check required tools
    for tool in kubectl helm kustomize docker aws; do
        if ! command -v $tool &> /dev/null; then
            log_error "$tool is not installed or not in PATH"
            exit 1
        fi
    done

    # Check Kubernetes connectivity
    if ! kubectl cluster-info &> /dev/null; then
        log_error "Cannot connect to Kubernetes cluster"
        exit 1
    fi

    # Check namespace exists
    if ! kubectl get namespace $NAMESPACE &> /dev/null; then
        log_info "Creating namespace: $NAMESPACE"
        kubectl create namespace $NAMESPACE
    fi

    log_success "Prerequisites check passed"
}

deploy_storage() {
    log_info "Deploying storage configuration..."
    kubectl apply -f "$K8S_DIR/base/storage.yml"

    # Wait for storage classes to be ready
    kubectl wait --for=condition=ready storageclass/fast-ssd --timeout=60s || true
    kubectl wait --for=condition=ready storageclass/standard-ssd --timeout=60s || true

    log_success "Storage configuration deployed"
}

deploy_database() {
    log_info "Deploying PostgreSQL cluster..."
    kubectl apply -f "$K8S_DIR/base/postgres-cluster.yml"

    # Wait for primary database to be ready
    log_info "Waiting for PostgreSQL primary to be ready..."
    kubectl wait --for=condition=ready pod -l app=postgres-primary -n $NAMESPACE --timeout=600s

    # Wait for replicas to be ready
    log_info "Waiting for PostgreSQL replicas to be ready..."
    kubectl wait --for=condition=ready pod -l app=postgres-replica -n $NAMESPACE --timeout=600s || true

    # Verify replication status
    log_info "Verifying PostgreSQL replication..."
    kubectl exec -it postgres-primary-0 -n $NAMESPACE -- \
        psql -U artifactor -c "SELECT * FROM pg_stat_replication;" || true

    log_success "PostgreSQL cluster deployed successfully"
}

deploy_redis() {
    log_info "Deploying Redis cluster..."
    kubectl apply -f "$K8S_DIR/base/redis.yml"

    # Wait for Redis to be ready
    kubectl wait --for=condition=ready pod -l app=redis -n $NAMESPACE --timeout=300s

    log_success "Redis cluster deployed successfully"
}

deploy_application() {
    log_info "Deploying application services..."

    # Deploy backend
    kubectl apply -f "$K8S_DIR/base/backend.yml"

    # Deploy frontend
    kubectl apply -f "$K8S_DIR/base/frontend.yml"

    # Wait for application pods to be ready
    log_info "Waiting for backend services to be ready..."
    kubectl wait --for=condition=ready pod -l app=artifactor-backend -n $NAMESPACE --timeout=300s

    log_info "Waiting for frontend services to be ready..."
    kubectl wait --for=condition=ready pod -l app=artifactor-frontend -n $NAMESPACE --timeout=300s

    log_success "Application services deployed successfully"
}

deploy_loadbalancer() {
    log_info "Deploying Nginx load balancer..."
    kubectl apply -f "$K8S_DIR/base/nginx.yml"

    # Wait for Nginx to be ready
    kubectl wait --for=condition=ready pod -l app=nginx -n $NAMESPACE --timeout=300s

    log_success "Load balancer deployed successfully"
}

deploy_monitoring() {
    log_info "Deploying monitoring stack..."

    # Deploy Prometheus
    kubectl apply -f "$K8S_DIR/base/monitoring.yml"

    # Deploy Alertmanager
    kubectl apply -f "$K8S_DIR/base/alertmanager.yml"

    # Wait for monitoring services to be ready
    log_info "Waiting for Prometheus to be ready..."
    kubectl wait --for=condition=ready pod -l app=prometheus -n $NAMESPACE --timeout=300s

    log_info "Waiting for Grafana to be ready..."
    kubectl wait --for=condition=ready pod -l app=grafana -n $NAMESPACE --timeout=300s

    log_success "Monitoring stack deployed successfully"
}

deploy_security() {
    log_info "Deploying security configurations..."
    kubectl apply -f "$K8S_DIR/base/security.yml"

    # Verify network policies
    kubectl get networkpolicies -n $NAMESPACE

    log_success "Security configurations deployed successfully"
}

deploy_backup() {
    log_info "Deploying backup system..."
    kubectl apply -f "$K8S_DIR/base/backup.yml"

    # Test backup configuration
    log_info "Testing backup configuration..."
    kubectl create job --from=cronjob/postgres-backup postgres-backup-test-$(date +%Y%m%d%H%M%S) -n $NAMESPACE || true

    log_success "Backup system deployed successfully"
}

deploy_environment_specific() {
    if [ "$ENVIRONMENT" = "production" ]; then
        log_info "Applying production-specific configurations..."
        kubectl apply -k "$K8S_DIR/production/"

        # Verify production scaling
        kubectl get hpa -n $NAMESPACE

    elif [ "$ENVIRONMENT" = "staging" ]; then
        log_info "Applying staging-specific configurations..."
        kubectl apply -k "$K8S_DIR/staging/"

    else
        log_warning "Unknown environment: $ENVIRONMENT. Using base configuration only."
    fi

    log_success "Environment-specific configurations applied"
}

run_health_checks() {
    log_info "Running deployment health checks..."

    # Check all pods are running
    if kubectl get pods -n $NAMESPACE | grep -v Running | grep -v Completed | grep -v STATUS; then
        log_warning "Some pods are not in Running state"
    else
        log_success "All pods are running"
    fi

    # Check services are accessible
    log_info "Checking service health..."

    # Backend health check
    kubectl run health-check-backend --image=curlimages/curl --rm -it --restart=Never -n $NAMESPACE -- \
        curl -f http://artifactor-backend-service:8000/health || log_warning "Backend health check failed"

    # Frontend health check
    kubectl run health-check-frontend --image=curlimages/curl --rm -it --restart=Never -n $NAMESPACE -- \
        curl -f http://artifactor-frontend-service:3000/ || log_warning "Frontend health check failed"

    # Database connectivity check
    kubectl exec -it postgres-primary-0 -n $NAMESPACE -- \
        pg_isready -U artifactor || log_warning "Database connectivity check failed"

    # Redis connectivity check
    kubectl exec -it $(kubectl get pods -l app=redis -n $NAMESPACE -o jsonpath='{.items[0].metadata.name}') -n $NAMESPACE -- \
        redis-cli ping || log_warning "Redis connectivity check failed"

    log_success "Health checks completed"
}

show_deployment_status() {
    log_info "Deployment Status Summary"
    echo "=========================="

    echo "Environment: $ENVIRONMENT"
    echo "Namespace: $NAMESPACE"
    echo ""

    echo "Pods:"
    kubectl get pods -n $NAMESPACE -o wide
    echo ""

    echo "Services:"
    kubectl get services -n $NAMESPACE
    echo ""

    echo "Horizontal Pod Autoscalers:"
    kubectl get hpa -n $NAMESPACE
    echo ""

    echo "Persistent Volume Claims:"
    kubectl get pvc -n $NAMESPACE
    echo ""

    # Get external IPs/URLs
    echo "External Access:"
    kubectl get services -n $NAMESPACE -o jsonpath='{range .items[*]}{.metadata.name}{": "}{.status.loadBalancer.ingress[0].hostname}{"\n"}{end}' | grep -v '^:'
    echo ""

    # Show monitoring access
    echo "Monitoring Access:"
    echo "Grafana: kubectl port-forward service/grafana 3000:3000 -n $NAMESPACE"
    echo "Prometheus: kubectl port-forward service/prometheus 9090:9090 -n $NAMESPACE"
    echo ""

    log_success "Deployment completed successfully!"
}

rollback_deployment() {
    log_error "Deployment failed. Starting rollback..."

    # Rollback application deployments
    kubectl rollout undo deployment/artifactor-backend -n $NAMESPACE || true
    kubectl rollout undo deployment/artifactor-frontend -n $NAMESPACE || true
    kubectl rollout undo deployment/nginx -n $NAMESPACE || true

    # Wait for rollback to complete
    kubectl rollout status deployment/artifactor-backend -n $NAMESPACE --timeout=300s || true
    kubectl rollout status deployment/artifactor-frontend -n $NAMESPACE --timeout=300s || true
    kubectl rollout status deployment/nginx -n $NAMESPACE --timeout=300s || true

    log_info "Rollback completed. Please check the logs and fix the issues before redeploying."
}

# Main deployment flow
main() {
    log_info "Starting ARTIFACTOR v3.0 deployment to $ENVIRONMENT environment"

    # Trap errors for rollback
    trap rollback_deployment ERR

    # Execute deployment steps
    check_prerequisites
    deploy_storage
    deploy_database
    deploy_redis
    deploy_application
    deploy_loadbalancer
    deploy_monitoring
    deploy_security
    deploy_backup
    deploy_environment_specific

    # Run health checks
    run_health_checks

    # Show deployment status
    show_deployment_status

    # Remove error trap on success
    trap - ERR
}

# Script usage
usage() {
    echo "Usage: $0 [environment]"
    echo ""
    echo "Environments:"
    echo "  staging     Deploy to staging environment (default)"
    echo "  production  Deploy to production environment"
    echo ""
    echo "Examples:"
    echo "  $0                    # Deploy to staging"
    echo "  $0 staging           # Deploy to staging"
    echo "  $0 production        # Deploy to production"
    echo ""
    echo "Prerequisites:"
    echo "  - kubectl configured and connected to cluster"
    echo "  - helm v3.12+ installed"
    echo "  - kustomize v5.0+ installed"
    echo "  - docker 24.0+ installed"
    echo "  - aws-cli v2.0+ installed (for backups)"
}

# Handle command line arguments
case "${1:-}" in
    -h|--help)
        usage
        exit 0
        ;;
    staging|production|"")
        main
        ;;
    *)
        log_error "Invalid environment: $1"
        usage
        exit 1
        ;;
esac