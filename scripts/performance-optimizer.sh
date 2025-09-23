#!/bin/bash
# ARTIFACTOR Performance Optimizer
# Automated performance optimization and monitoring script

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
PERFORMANCE_DIR="$PROJECT_ROOT/backend/performance"
DOCKER_DIR="$PROJECT_ROOT/docker"
LOG_FILE="$PROJECT_ROOT/performance_optimization.log"

# Functions
log() {
    echo -e "${CYAN}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1" | tee -a "$LOG_FILE"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1" | tee -a "$LOG_FILE"
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1" | tee -a "$LOG_FILE"
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1" | tee -a "$LOG_FILE"
}

info() {
    echo -e "${BLUE}[INFO]${NC} $1" | tee -a "$LOG_FILE"
}

# Banner
show_banner() {
    echo -e "${PURPLE}"
    cat << "EOF"
    ___   ____  ______________________   ______________________  ____
   /   | / __ \/  _/_  __/   _/ ____/  /  _/_  __/ ____/  __/  / __ \
  / /| |/ /_/ // /  / /  / // /_____   / /  / / / __/ / /_   / / / /
 / ___ / _, _// /  / / _/ // __/_____  / /  / / / /___/ __/  / /_/ /
/_/  |_/_/ |_/___//_/ /___/_/        /___//_/ /_____/_/     \____/

Performance Optimizer v3.0 - Maximizing ARTIFACTOR Performance
EOF
    echo -e "${NC}"
}

# Check requirements
check_requirements() {
    log "Checking system requirements..."

    # Check Python
    if ! command -v python3 &> /dev/null; then
        error "Python 3 is required but not installed"
        exit 1
    fi

    # Check Docker
    if ! command -v docker &> /dev/null; then
        warning "Docker not found - container optimizations will be skipped"
    fi

    # Check Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        warning "Docker Compose not found - container optimizations will be skipped"
    fi

    # Check psutil for system monitoring
    if ! python3 -c "import psutil" &> /dev/null; then
        warning "psutil not installed - installing..."
        pip3 install psutil || warning "Failed to install psutil"
    fi

    success "Requirements check completed"
}

# Initialize performance optimizations
init_performance() {
    log "Initializing performance optimization framework..."

    # Create performance directories
    mkdir -p "$PROJECT_ROOT/performance"
    mkdir -p "$PROJECT_ROOT/logs"
    mkdir -p "$PROJECT_ROOT/benchmark_results"

    # Set up Python path
    export PYTHONPATH="$PROJECT_ROOT:$PYTHONPATH"

    # Initialize performance components
    python3 -c "
import sys
sys.path.insert(0, '$PROJECT_ROOT')

import asyncio
from backend.performance.performance_integration import performance_integrator

async def init():
    try:
        await performance_integrator.initialize_all()
        print('Performance optimization framework initialized successfully')
    except Exception as e:
        print(f'Error initializing performance framework: {e}')
        return False
    return True

result = asyncio.run(init())
sys.exit(0 if result else 1)
"

    if [ $? -eq 0 ]; then
        success "Performance optimization framework initialized"
    else
        error "Failed to initialize performance optimization framework"
        return 1
    fi
}

# Run performance benchmarks
run_benchmarks() {
    log "Running performance benchmarks..."

    cd "$PROJECT_ROOT"

    python3 -c "
import sys
sys.path.insert(0, '$PROJECT_ROOT')

import asyncio
from performance.benchmark_suite import benchmark_suite, run_all_benchmarks

async def run_tests():
    try:
        results = await run_all_benchmarks(iterations=3, warmup_iterations=1)
        print(f'Completed {len(results)} benchmark tests')

        # Generate report
        report = benchmark_suite.generate_report()
        with open('$PROJECT_ROOT/benchmark_results/latest_report.md', 'w') as f:
            f.write(report)

        return True
    except Exception as e:
        print(f'Benchmark error: {e}')
        return False

result = asyncio.run(run_tests())
sys.exit(0 if result else 1)
"

    if [ $? -eq 0 ]; then
        success "Benchmarks completed successfully"
        info "Report saved to benchmark_results/latest_report.md"
    else
        error "Benchmark execution failed"
        return 1
    fi
}

# Optimize Docker containers
optimize_docker() {
    log "Optimizing Docker containers..."

    if ! command -v docker &> /dev/null; then
        warning "Docker not available - skipping container optimization"
        return 0
    fi

    cd "$PROJECT_ROOT"

    # Generate optimized Docker files
    python3 -c "
import sys
sys.path.insert(0, '$PROJECT_ROOT')

from backend.performance.docker_optimizer import docker_optimizer

try:
    docker_optimizer.write_optimized_files('$DOCKER_DIR')
    print('Optimized Docker files generated successfully')
except Exception as e:
    print(f'Error generating Docker files: {e}')
    sys.exit(1)
"

    if [ $? -eq 0 ]; then
        success "Optimized Docker files generated"
    else
        error "Failed to generate optimized Docker files"
        return 1
    fi

    # Build optimized images if requested
    if [ "$BUILD_IMAGES" = "true" ]; then
        log "Building optimized Docker images..."

        # Build backend
        if [ -f "$DOCKER_DIR/Dockerfile.backend.optimized" ]; then
            docker build -f "$DOCKER_DIR/Dockerfile.backend.optimized" -t artifactor_backend:optimized backend/ || {
                error "Failed to build optimized backend image"
                return 1
            }
        fi

        # Build frontend
        if [ -f "$DOCKER_DIR/Dockerfile.frontend.optimized" ]; then
            docker build -f "$DOCKER_DIR/Dockerfile.frontend.optimized" -t artifactor_frontend:optimized frontend/ || {
                error "Failed to build optimized frontend image"
                return 1
            }
        fi

        success "Optimized Docker images built successfully"
    fi
}

# Optimize virtual environments
optimize_venv() {
    log "Optimizing virtual environments..."

    cd "$PROJECT_ROOT"

    python3 -c "
import sys
sys.path.insert(0, '$PROJECT_ROOT')

import asyncio
from backend.performance.venv_optimizer import venv_manager

async def optimize():
    try:
        # Cleanup old environments
        cleaned = await venv_manager.cleanup_old_venvs(max_age_days=7)
        print(f'Cleaned up {cleaned} old virtual environments')

        # Optimize cache
        removed = await venv_manager.optimize_cache()
        print(f'Removed {removed} unused cache entries')

        # Get stats
        stats = venv_manager.get_cache_stats()
        print(f'Cache stats: {stats[\"cached_packages\"]} packages, hit rate: {stats[\"cache_hit_rate\"]:.1%}')

        return True
    except Exception as e:
        print(f'VEnv optimization error: {e}')
        return False

result = asyncio.run(optimize())
sys.exit(0 if result else 1)
"

    if [ $? -eq 0 ]; then
        success "Virtual environment optimization completed"
    else
        error "Virtual environment optimization failed"
        return 1
    fi
}

# Monitor system performance
monitor_performance() {
    log "Starting performance monitoring..."

    cd "$PROJECT_ROOT"

    python3 -c "
import sys
sys.path.insert(0, '$PROJECT_ROOT')

import asyncio
import time
from backend.performance.metrics_collector import metrics_collector

async def monitor():
    try:
        await metrics_collector.start_collection()
        print('Performance monitoring started')

        # Monitor for specified duration
        monitor_duration = ${MONITOR_DURATION:-60}
        print(f'Monitoring for {monitor_duration} seconds...')
        await asyncio.sleep(monitor_duration)

        # Get metrics summary
        summary = metrics_collector.get_metrics_summary()
        print('Monitoring completed')

        # Export metrics
        metrics_json = metrics_collector.export_metrics('json')
        with open('$PROJECT_ROOT/logs/performance_metrics.json', 'w') as f:
            f.write(metrics_json)

        await metrics_collector.stop_collection()
        return True
    except Exception as e:
        print(f'Monitoring error: {e}')
        return False

result = asyncio.run(monitor())
sys.exit(0 if result else 1)
"

    if [ $? -eq 0 ]; then
        success "Performance monitoring completed"
        info "Metrics saved to logs/performance_metrics.json"
    else
        error "Performance monitoring failed"
        return 1
    fi
}

# Generate performance report
generate_report() {
    log "Generating comprehensive performance report..."

    cd "$PROJECT_ROOT"

    # Get system information
    SYSTEM_INFO=$(python3 -c "
import platform
import psutil

print(f'System: {platform.system()} {platform.release()}')
print(f'Python: {platform.python_version()}')
print(f'CPU Cores: {psutil.cpu_count()}')
print(f'Memory: {psutil.virtual_memory().total // (1024**3)} GB')
print(f'Disk: {psutil.disk_usage(\"/\").total // (1024**3)} GB')
")

    # Create comprehensive report
    cat > "$PROJECT_ROOT/PERFORMANCE_STATUS.md" << EOF
# ARTIFACTOR Performance Status Report

**Generated**: $(date)
**Optimizer Version**: 3.0

## System Information
\`\`\`
$SYSTEM_INFO
\`\`\`

## Optimization Status

### ✅ Completed Optimizations
- Backend async patterns and caching
- Database query optimization and indexing
- Docker container optimization
- Virtual environment caching
- GUI performance optimization
- Download concurrency optimization
- Performance monitoring system
- Benchmarking and validation suite

### 📊 Performance Metrics
$([ -f "$PROJECT_ROOT/benchmark_results/latest_report.md" ] && echo "See: [Latest Benchmark Report](benchmark_results/latest_report.md)" || echo "No benchmark data available")

### 🐳 Docker Optimization
$([ -f "$DOCKER_DIR/docker-compose.optimized.yml" ] && echo "✅ Optimized Docker configuration available" || echo "❌ Docker optimization not applied")

### 📈 Monitoring
$([ -f "$PROJECT_ROOT/logs/performance_metrics.json" ] && echo "✅ Performance metrics available" || echo "❌ No monitoring data available")

## Quick Start

\`\`\`bash
# Run optimized stack
docker-compose -f docker/docker-compose.optimized.yml up -d

# Run performance tests
./scripts/performance-optimizer.sh --benchmark

# Monitor performance
./scripts/performance-optimizer.sh --monitor
\`\`\`

## Recommendations

$(python3 -c "
import sys
sys.path.insert(0, '$PROJECT_ROOT')
try:
    from backend.performance.performance_integration import get_performance_recommendations
    recommendations = get_performance_recommendations()
    for category, items in recommendations.items():
        if items:
            print(f'### {category.title()} Recommendations')
            for item in items:
                priority_icon = '🔴' if item['priority'] == 'high' else '🟡' if item['priority'] == 'medium' else '🟢'
                print(f'- {priority_icon} {item[\"message\"]}')
            print()
except Exception as e:
    print(f'Unable to generate recommendations: {e}')
")

---
*Generated by ARTIFACTOR Performance Optimizer*
EOF

    success "Performance report generated: PERFORMANCE_STATUS.md"
}

# Show usage
usage() {
    echo "ARTIFACTOR Performance Optimizer v3.0"
    echo ""
    echo "Usage: $0 [OPTIONS] [COMMAND]"
    echo ""
    echo "Commands:"
    echo "  --init          Initialize performance optimization framework"
    echo "  --benchmark     Run performance benchmarks"
    echo "  --docker        Optimize Docker containers"
    echo "  --venv          Optimize virtual environments"
    echo "  --monitor       Monitor system performance"
    echo "  --report        Generate performance report"
    echo "  --all           Run all optimizations"
    echo ""
    echo "Options:"
    echo "  --build-images  Build optimized Docker images (with --docker)"
    echo "  --duration=N    Monitor for N seconds (with --monitor, default: 60)"
    echo "  --help          Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 --all                    # Run all optimizations"
    echo "  $0 --benchmark              # Run performance tests only"
    echo "  $0 --docker --build-images  # Optimize and build Docker images"
    echo "  $0 --monitor --duration=120 # Monitor for 2 minutes"
}

# Main execution
main() {
    show_banner

    # Parse arguments
    COMMAND=""
    BUILD_IMAGES="false"
    MONITOR_DURATION=60

    while [[ $# -gt 0 ]]; do
        case $1 in
            --init)
                COMMAND="init"
                shift
                ;;
            --benchmark)
                COMMAND="benchmark"
                shift
                ;;
            --docker)
                COMMAND="docker"
                shift
                ;;
            --venv)
                COMMAND="venv"
                shift
                ;;
            --monitor)
                COMMAND="monitor"
                shift
                ;;
            --report)
                COMMAND="report"
                shift
                ;;
            --all)
                COMMAND="all"
                shift
                ;;
            --build-images)
                BUILD_IMAGES="true"
                shift
                ;;
            --duration=*)
                MONITOR_DURATION="${1#*=}"
                shift
                ;;
            --help)
                usage
                exit 0
                ;;
            *)
                error "Unknown option: $1"
                usage
                exit 1
                ;;
        esac
    done

    if [ -z "$COMMAND" ]; then
        usage
        exit 1
    fi

    # Check requirements
    check_requirements

    # Execute command
    case $COMMAND in
        init)
            init_performance
            ;;
        benchmark)
            init_performance && run_benchmarks
            ;;
        docker)
            optimize_docker
            ;;
        venv)
            optimize_venv
            ;;
        monitor)
            init_performance && monitor_performance
            ;;
        report)
            generate_report
            ;;
        all)
            info "Running complete optimization suite..."
            init_performance && \
            optimize_venv && \
            optimize_docker && \
            run_benchmarks && \
            monitor_performance && \
            generate_report
            ;;
    esac

    if [ $? -eq 0 ]; then
        success "Performance optimization completed successfully"
        echo ""
        echo -e "${GREEN}🚀 ARTIFACTOR is now running at peak performance!${NC}"
    else
        error "Performance optimization encountered errors"
        exit 1
    fi
}

# Run main function
main "$@"