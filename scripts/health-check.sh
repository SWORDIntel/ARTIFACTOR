#!/bin/bash
set -e

# ARTIFACTOR v3.0 Health Check Script
# MONITOR Agent: Comprehensive system health validation

# Color output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
NAMESPACE=${1:-artifactor}
TIMEOUT=${2:-300}
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Health check results
HEALTH_SCORE=0
TOTAL_CHECKS=0
FAILED_CHECKS=()

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

check_result() {
    local test_name="$1"
    local result="$2"

    TOTAL_CHECKS=$((TOTAL_CHECKS + 1))

    if [ "$result" -eq 0 ]; then
        log_success "$test_name: PASSED"
        HEALTH_SCORE=$((HEALTH_SCORE + 1))
    else
        log_error "$test_name: FAILED"
        FAILED_CHECKS+=("$test_name")
    fi
}

check_kubernetes_connectivity() {
    log_info "Checking Kubernetes connectivity..."

    kubectl cluster-info &> /dev/null
    check_result "Kubernetes connectivity" $?

    kubectl get nodes &> /dev/null
    check_result "Kubernetes nodes access" $?
}

check_namespace() {
    log_info "Checking namespace: $NAMESPACE"

    kubectl get namespace $NAMESPACE &> /dev/null
    check_result "Namespace exists" $?
}

check_pods_status() {
    log_info "Checking pods status..."

    # Check if all pods are running
    local not_running=$(kubectl get pods -n $NAMESPACE --field-selector=status.phase!=Running --no-headers 2>/dev/null | wc -l)
    [ "$not_running" -eq 0 ]
    check_result "All pods running" $?

    # Check specific application pods
    kubectl get pods -l app=artifactor-backend -n $NAMESPACE &> /dev/null
    check_result "Backend pods exist" $?

    kubectl get pods -l app=artifactor-frontend -n $NAMESPACE &> /dev/null
    check_result "Frontend pods exist" $?

    kubectl get pods -l app=postgres-primary -n $NAMESPACE &> /dev/null
    check_result "Database primary pods exist" $?

    kubectl get pods -l app=redis -n $NAMESPACE &> /dev/null
    check_result "Redis pods exist" $?
}

check_services() {
    log_info "Checking services..."

    kubectl get service artifactor-backend-service -n $NAMESPACE &> /dev/null
    check_result "Backend service exists" $?

    kubectl get service artifactor-frontend-service -n $NAMESPACE &> /dev/null
    check_result "Frontend service exists" $?

    kubectl get service postgres-service -n $NAMESPACE &> /dev/null
    check_result "Database service exists" $?

    kubectl get service redis-service -n $NAMESPACE &> /dev/null
    check_result "Redis service exists" $?
}

check_endpoints() {
    log_info "Checking service endpoints..."

    local backend_endpoints=$(kubectl get endpoints artifactor-backend-service -n $NAMESPACE -o jsonpath='{.subsets[*].addresses[*].ip}' 2>/dev/null | wc -w)
    [ "$backend_endpoints" -gt 0 ]
    check_result "Backend service has endpoints" $?

    local frontend_endpoints=$(kubectl get endpoints artifactor-frontend-service -n $NAMESPACE -o jsonpath='{.subsets[*].addresses[*].ip}' 2>/dev/null | wc -w)
    [ "$frontend_endpoints" -gt 0 ]
    check_result "Frontend service has endpoints" $?
}

check_application_health() {
    log_info "Checking application health endpoints..."

    # Backend health check
    kubectl run health-check-backend-$$ --image=curlimages/curl --rm -i --restart=Never -n $NAMESPACE \
        --timeout=$TIMEOUT --command -- curl -f -s http://artifactor-backend-service:8000/health &> /dev/null
    check_result "Backend health endpoint" $?

    # Frontend accessibility check
    kubectl run health-check-frontend-$$ --image=curlimages/curl --rm -i --restart=Never -n $NAMESPACE \
        --timeout=$TIMEOUT --command -- curl -f -s http://artifactor-frontend-service:3000/ &> /dev/null
    check_result "Frontend accessibility" $?
}

check_database_connectivity() {
    log_info "Checking database connectivity..."

    # PostgreSQL primary connectivity
    kubectl exec -it postgres-primary-0 -n $NAMESPACE -- pg_isready -U artifactor &> /dev/null
    check_result "PostgreSQL primary connectivity" $?

    # Database query test
    kubectl exec -it postgres-primary-0 -n $NAMESPACE -- \
        psql -U artifactor -d artifactor -c "SELECT 1;" &> /dev/null
    check_result "PostgreSQL query execution" $?

    # Check replication status if replicas exist
    local replica_count=$(kubectl get pods -l app=postgres-replica -n $NAMESPACE --no-headers 2>/dev/null | wc -l)
    if [ "$replica_count" -gt 0 ]; then
        kubectl exec -it postgres-primary-0 -n $NAMESPACE -- \
            psql -U artifactor -c "SELECT client_addr FROM pg_stat_replication;" &> /dev/null
        check_result "PostgreSQL replication status" $?
    fi
}

check_redis_connectivity() {
    log_info "Checking Redis connectivity..."

    # Get first Redis pod
    local redis_pod=$(kubectl get pods -l app=redis -n $NAMESPACE -o jsonpath='{.items[0].metadata.name}' 2>/dev/null)

    if [ -n "$redis_pod" ]; then
        kubectl exec -it $redis_pod -n $NAMESPACE -- redis-cli ping &> /dev/null
        check_result "Redis connectivity" $?

        # Redis memory usage check
        local memory_usage=$(kubectl exec -it $redis_pod -n $NAMESPACE -- redis-cli info memory | grep used_memory_human | cut -d: -f2 | tr -d '\r')
        [ -n "$memory_usage" ]
        check_result "Redis memory status" $?
    else
        check_result "Redis pod availability" 1
    fi
}

check_persistent_volumes() {
    log_info "Checking persistent volumes..."

    # Check PVC status
    local bound_pvcs=$(kubectl get pvc -n $NAMESPACE --no-headers 2>/dev/null | grep Bound | wc -l)
    local total_pvcs=$(kubectl get pvc -n $NAMESPACE --no-headers 2>/dev/null | wc -l)

    if [ "$total_pvcs" -gt 0 ]; then
        [ "$bound_pvcs" -eq "$total_pvcs" ]
        check_result "All PVCs bound" $?
    fi
}

check_autoscaling() {
    log_info "Checking autoscaling configuration..."

    kubectl get hpa -n $NAMESPACE &> /dev/null
    check_result "HPA configuration exists" $?

    # Check if HPA is functioning
    local hpa_count=$(kubectl get hpa -n $NAMESPACE --no-headers 2>/dev/null | wc -l)
    [ "$hpa_count" -gt 0 ]
    check_result "HPA instances configured" $?
}

check_monitoring() {
    log_info "Checking monitoring stack..."

    kubectl get pods -l app=prometheus -n $NAMESPACE &> /dev/null
    check_result "Prometheus pod exists" $?

    kubectl get pods -l app=grafana -n $NAMESPACE &> /dev/null
    check_result "Grafana pod exists" $?

    # Check Prometheus metrics endpoint
    kubectl run prometheus-check-$$ --image=curlimages/curl --rm -i --restart=Never -n $NAMESPACE \
        --timeout=60 --command -- curl -f -s http://prometheus:9090/metrics &> /dev/null
    check_result "Prometheus metrics endpoint" $?
}

check_security() {
    log_info "Checking security configurations..."

    kubectl get networkpolicies -n $NAMESPACE &> /dev/null
    check_result "Network policies exist" $?

    kubectl get serviceaccount artifactor-security -n $NAMESPACE &> /dev/null
    check_result "Security service account exists" $?

    # Check for security scanner
    kubectl get cronjob security-scanner -n $NAMESPACE &> /dev/null
    check_result "Security scanner configured" $?
}

check_backup_system() {
    log_info "Checking backup system..."

    kubectl get cronjob postgres-backup -n $NAMESPACE &> /dev/null
    check_result "PostgreSQL backup cron job exists" $?

    kubectl get cronjob redis-backup -n $NAMESPACE &> /dev/null
    check_result "Redis backup cron job exists" $?

    kubectl get pods -l app=backup-management -n $NAMESPACE &> /dev/null
    check_result "Backup management pod exists" $?
}

check_resource_usage() {
    log_info "Checking resource usage..."

    # Check if we can get resource usage (requires metrics-server)
    kubectl top pods -n $NAMESPACE &> /dev/null
    check_result "Pod metrics available" $?

    kubectl top nodes &> /dev/null
    check_result "Node metrics available" $?
}

check_logs() {
    log_info "Checking for critical errors in logs..."

    # Check backend logs for errors
    local backend_pod=$(kubectl get pods -l app=artifactor-backend -n $NAMESPACE -o jsonpath='{.items[0].metadata.name}' 2>/dev/null)
    if [ -n "$backend_pod" ]; then
        local error_count=$(kubectl logs $backend_pod -n $NAMESPACE --tail=100 2>/dev/null | grep -i error | wc -l)
        [ "$error_count" -lt 5 ]  # Allow up to 5 errors in last 100 lines
        check_result "Backend log errors (< 5)" $?
    fi

    # Check database logs for critical errors
    local db_error_count=$(kubectl logs postgres-primary-0 -n $NAMESPACE --tail=100 2>/dev/null | grep -i "FATAL\|ERROR" | wc -l)
    [ "$db_error_count" -lt 3 ]  # Allow up to 3 errors in last 100 lines
    check_result "Database log errors (< 3)" $?
}

generate_health_report() {
    local health_percentage=$((HEALTH_SCORE * 100 / TOTAL_CHECKS))

    echo ""
    echo "========================================"
    echo "        HEALTH CHECK SUMMARY"
    echo "========================================"
    echo "Namespace: $NAMESPACE"
    echo "Timestamp: $(date)"
    echo "Total Checks: $TOTAL_CHECKS"
    echo "Passed Checks: $HEALTH_SCORE"
    echo "Failed Checks: $((TOTAL_CHECKS - HEALTH_SCORE))"
    echo "Health Score: $health_percentage%"
    echo ""

    if [ "$health_percentage" -ge 95 ]; then
        echo -e "${GREEN}Overall Health: EXCELLENT${NC}"
    elif [ "$health_percentage" -ge 85 ]; then
        echo -e "${YELLOW}Overall Health: GOOD${NC}"
    elif [ "$health_percentage" -ge 70 ]; then
        echo -e "${YELLOW}Overall Health: FAIR${NC}"
    else
        echo -e "${RED}Overall Health: POOR${NC}"
    fi

    if [ ${#FAILED_CHECKS[@]} -gt 0 ]; then
        echo ""
        echo "Failed Checks:"
        for check in "${FAILED_CHECKS[@]}"; do
            echo "  - $check"
        done
    fi

    echo ""
    echo "Detailed Status:"
    kubectl get pods -n $NAMESPACE -o wide
    echo ""
    kubectl get services -n $NAMESPACE
    echo ""

    # Return appropriate exit code
    if [ "$health_percentage" -ge 80 ]; then
        return 0
    else
        return 1
    fi
}

# Main health check flow
main() {
    log_info "Starting ARTIFACTOR v3.0 health check for namespace: $NAMESPACE"

    check_kubernetes_connectivity
    check_namespace
    check_pods_status
    check_services
    check_endpoints
    check_application_health
    check_database_connectivity
    check_redis_connectivity
    check_persistent_volumes
    check_autoscaling
    check_monitoring
    check_security
    check_backup_system
    check_resource_usage
    check_logs

    generate_health_report
}

# Script usage
usage() {
    echo "Usage: $0 [namespace] [timeout]"
    echo ""
    echo "Arguments:"
    echo "  namespace   Kubernetes namespace to check (default: artifactor)"
    echo "  timeout     Timeout in seconds for individual checks (default: 300)"
    echo ""
    echo "Examples:"
    echo "  $0                           # Check artifactor namespace with 300s timeout"
    echo "  $0 artifactor-staging        # Check staging namespace"
    echo "  $0 artifactor 600            # Check with 10-minute timeout"
    echo ""
}

# Handle command line arguments
case "${1:-}" in
    -h|--help)
        usage
        exit 0
        ;;
    *)
        main
        ;;
esac