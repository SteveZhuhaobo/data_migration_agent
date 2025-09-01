#!/bin/bash

# Build All MCP Servers Script
# This script builds all three MCP server containers with proper error handling and logging

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging function
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] SUCCESS:${NC} $1"
}

log_error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR:${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARNING:${NC} $1"
}

# Default values
TAG="latest"
REGISTRY=""
PUSH=false
PARALLEL=false

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -t|--tag)
            TAG="$2"
            shift 2
            ;;
        -r|--registry)
            REGISTRY="$2"
            shift 2
            ;;
        -p|--push)
            PUSH=true
            shift
            ;;
        --parallel)
            PARALLEL=true
            shift
            ;;
        -h|--help)
            echo "Usage: $0 [OPTIONS]"
            echo "Options:"
            echo "  -t, --tag TAG        Tag for the built images (default: latest)"
            echo "  -r, --registry REG   Registry prefix for images"
            echo "  -p, --push          Push images after building"
            echo "  --parallel          Build images in parallel"
            echo "  -h, --help          Show this help message"
            exit 0
            ;;
        *)
            log_error "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# MCP servers to build
SERVERS=("snowflake-mcp" "databricks-mcp" "sqlserver-mcp")

# Function to build a single server
build_server() {
    local server=$1
    local server_dir="$PROJECT_ROOT/$server"
    
    if [[ ! -d "$server_dir" ]]; then
        log_error "Server directory not found: $server_dir"
        return 1
    fi
    
    log "Building $server..."
    
    # Determine image name
    local image_name="$server"
    if [[ -n "$REGISTRY" ]]; then
        image_name="$REGISTRY/$server"
    fi
    
    # Build the image
    if docker build -t "$image_name:$TAG" "$server_dir"; then
        log_success "Built $server successfully"
        
        # Push if requested
        if [[ "$PUSH" == "true" ]]; then
            log "Pushing $image_name:$TAG..."
            if docker push "$image_name:$TAG"; then
                log_success "Pushed $image_name:$TAG successfully"
            else
                log_error "Failed to push $image_name:$TAG"
                return 1
            fi
        fi
    else
        log_error "Failed to build $server"
        return 1
    fi
}

# Function to build servers in parallel
build_parallel() {
    local pids=()
    
    for server in "${SERVERS[@]}"; do
        build_server "$server" &
        pids+=($!)
    done
    
    # Wait for all builds to complete
    local failed=0
    for pid in "${pids[@]}"; do
        if ! wait "$pid"; then
            failed=1
        fi
    done
    
    return $failed
}

# Function to build servers sequentially
build_sequential() {
    for server in "${SERVERS[@]}"; do
        if ! build_server "$server"; then
            return 1
        fi
    done
}

# Main execution
log "Starting build process..."
log "Tag: $TAG"
log "Registry: ${REGISTRY:-"(none)"}"
log "Push: $PUSH"
log "Parallel: $PARALLEL"

# Check if Docker is available
if ! command -v docker &> /dev/null; then
    log_error "Docker is not installed or not in PATH"
    exit 1
fi

# Check if Docker daemon is running
if ! docker info &> /dev/null; then
    log_error "Docker daemon is not running"
    exit 1
fi

# Build images
start_time=$(date +%s)

if [[ "$PARALLEL" == "true" ]]; then
    log "Building servers in parallel..."
    if build_parallel; then
        log_success "All servers built successfully in parallel"
    else
        log_error "One or more servers failed to build"
        exit 1
    fi
else
    log "Building servers sequentially..."
    if build_sequential; then
        log_success "All servers built successfully"
    else
        log_error "One or more servers failed to build"
        exit 1
    fi
fi

end_time=$(date +%s)
duration=$((end_time - start_time))

log_success "Build process completed in ${duration} seconds"

# Display built images
log "Built images:"
for server in "${SERVERS[@]}"; do
    local image_name="$server"
    if [[ -n "$REGISTRY" ]]; then
        image_name="$REGISTRY/$server"
    fi
    echo "  - $image_name:$TAG"
done