#!/bin/bash

# Test All MCP Servers Script
# This script tests all three MCP server containers with comprehensive validation

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
TIMEOUT=30
VERBOSE=false

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
        --timeout)
            TIMEOUT="$2"
            shift 2
            ;;
        -v|--verbose)
            VERBOSE=true
            shift
            ;;
        -h|--help)
            echo "Usage: $0 [OPTIONS]"
            echo "Options:"
            echo "  -t, --tag TAG        Tag for the images to test (default: latest)"
            echo "  -r, --registry REG   Registry prefix for images"
            echo "  --timeout SECONDS    Timeout for container tests (default: 30)"
            echo "  -v, --verbose        Enable verbose output"
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

# MCP servers to test
SERVERS=("snowflake-mcp" "databricks-mcp" "sqlserver-mcp")

# Function to test image exists
test_image_exists() {
    local server=$1
    local image_name="$server"
    if [[ -n "$REGISTRY" ]]; then
        image_name="$REGISTRY/$server"
    fi
    
    log "Checking if image exists: $image_name:$TAG"
    
    if docker image inspect "$image_name:$TAG" &> /dev/null; then
        log_success "Image $image_name:$TAG exists"
        return 0
    else
        log_error "Image $image_name:$TAG not found"
        return 1
    fi
}

# Function to test container startup
test_container_startup() {
    local server=$1
    local image_name="$server"
    if [[ -n "$REGISTRY" ]]; then
        image_name="$REGISTRY/$server"
    fi
    
    local container_name="test-$server-$(date +%s)"
    
    log "Testing container startup for $server..."
    
    # Start container in detached mode
    local container_id
    if container_id=$(docker run -d --name "$container_name" "$image_name:$TAG" 2>/dev/null); then
        log "Container started: $container_id"
        
        # Wait for container to be ready or timeout
        local count=0
        local max_attempts=$((TIMEOUT / 2))
        
        while [[ $count -lt $max_attempts ]]; do
            if docker ps --filter "id=$container_id" --filter "status=running" --quiet | grep -q "$container_id"; then
                log_success "Container $server is running"
                
                # Test health check if available
                if docker inspect "$container_id" --format='{{.State.Health.Status}}' 2>/dev/null | grep -q "healthy\|starting"; then
                    log_success "Container $server health check passed"
                fi
                
                # Clean up
                docker stop "$container_id" &> /dev/null || true
                docker rm "$container_id" &> /dev/null || true
                return 0
            fi
            
            sleep 2
            ((count++))
        done
        
        # If we get here, container didn't start properly
        log_error "Container $server failed to start within $TIMEOUT seconds"
        
        # Show logs for debugging
        if [[ "$VERBOSE" == "true" ]]; then
            log "Container logs:"
            docker logs "$container_id" 2>&1 | head -20
        fi
        
        # Clean up
        docker stop "$container_id" &> /dev/null || true
        docker rm "$container_id" &> /dev/null || true
        return 1
    else
        log_error "Failed to start container for $server"
        return 1
    fi
}

# Function to test image security
test_image_security() {
    local server=$1
    local image_name="$server"
    if [[ -n "$REGISTRY" ]]; then
        image_name="$REGISTRY/$server"
    fi
    
    log "Testing image security for $server..."
    
    # Check if image runs as non-root user
    local user_info
    if user_info=$(docker run --rm "$image_name:$TAG" id 2>/dev/null); then
        if echo "$user_info" | grep -q "uid=1000"; then
            log_success "Image $server runs as non-root user"
        else
            log_warning "Image $server may be running as root: $user_info"
        fi
    else
        log_warning "Could not check user for $server"
    fi
}

# Function to test image size
test_image_size() {
    local server=$1
    local image_name="$server"
    if [[ -n "$REGISTRY" ]]; then
        image_name="$REGISTRY/$server"
    fi
    
    log "Checking image size for $server..."
    
    local size
    if size=$(docker image inspect "$image_name:$TAG" --format='{{.Size}}' 2>/dev/null); then
        local size_mb=$((size / 1024 / 1024))
        log "Image $server size: ${size_mb}MB"
        
        # Warn if image is very large (>1GB)
        if [[ $size_mb -gt 1024 ]]; then
            log_warning "Image $server is quite large (${size_mb}MB)"
        else
            log_success "Image $server size is reasonable (${size_mb}MB)"
        fi
    else
        log_error "Could not get size for $server"
        return 1
    fi
}

# Function to test a single server
test_server() {
    local server=$1
    local failed=0
    
    log "Testing $server..."
    
    # Test image exists
    if ! test_image_exists "$server"; then
        ((failed++))
    fi
    
    # Test container startup
    if ! test_container_startup "$server"; then
        ((failed++))
    fi
    
    # Test image security
    if ! test_image_security "$server"; then
        ((failed++))
    fi
    
    # Test image size
    if ! test_image_size "$server"; then
        ((failed++))
    fi
    
    if [[ $failed -eq 0 ]]; then
        log_success "All tests passed for $server"
        return 0
    else
        log_error "$failed test(s) failed for $server"
        return 1
    fi
}

# Function to run docker-compose tests
test_docker_compose() {
    local server=$1
    local server_dir="$PROJECT_ROOT/$server"
    
    if [[ ! -f "$server_dir/docker-compose.yml" ]]; then
        log_warning "No docker-compose.yml found for $server"
        return 0
    fi
    
    log "Testing docker-compose for $server..."
    
    # Check if docker-compose is available
    if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
        log_warning "docker-compose not available, skipping compose tests"
        return 0
    fi
    
    # Use docker compose or docker-compose based on availability
    local compose_cmd="docker compose"
    if ! docker compose version &> /dev/null; then
        compose_cmd="docker-compose"
    fi
    
    # Test compose file validation
    if (cd "$server_dir" && $compose_cmd config &> /dev/null); then
        log_success "docker-compose.yml is valid for $server"
        return 0
    else
        log_error "docker-compose.yml is invalid for $server"
        return 1
    fi
}

# Main execution
log "Starting test process..."
log "Tag: $TAG"
log "Registry: ${REGISTRY:-"(none)"}"
log "Timeout: $TIMEOUT seconds"
log "Verbose: $VERBOSE"

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

# Test all servers
start_time=$(date +%s)
failed_servers=()

for server in "${SERVERS[@]}"; do
    if ! test_server "$server"; then
        failed_servers+=("$server")
    fi
    
    # Test docker-compose
    if ! test_docker_compose "$server"; then
        log_warning "docker-compose test failed for $server"
    fi
    
    echo # Add spacing between server tests
done

end_time=$(date +%s)
duration=$((end_time - start_time))

# Summary
echo "========================================="
log "Test Summary"
echo "========================================="

if [[ ${#failed_servers[@]} -eq 0 ]]; then
    log_success "All servers passed tests!"
    log_success "Test process completed in ${duration} seconds"
    exit 0
else
    log_error "The following servers failed tests:"
    for server in "${failed_servers[@]}"; do
        echo "  - $server"
    done
    log_error "Test process completed in ${duration} seconds"
    exit 1
fi