#!/bin/bash

# Publish All MCP Servers Script
# This script publishes all three MCP server containers to multiple registries

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
VERSION=""
REGISTRIES=()
BUILD=false
LATEST=true
DRY_RUN=false
PARALLEL=false

# Supported registries
SUPPORTED_REGISTRIES=("docker.io" "ghcr.io" "quay.io")

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -v|--version)
            VERSION="$2"
            shift 2
            ;;
        -r|--registry)
            REGISTRIES+=("$2")
            shift 2
            ;;
        -b|--build)
            BUILD=true
            shift
            ;;
        --no-latest)
            LATEST=false
            shift
            ;;
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        --parallel)
            PARALLEL=true
            shift
            ;;
        -h|--help)
            echo "Usage: $0 [OPTIONS]"
            echo "Options:"
            echo "  -v, --version VER    Version to tag and publish (required)"
            echo "  -r, --registry REG   Registry to publish to (can be used multiple times)"
            echo "                       Supported: ${SUPPORTED_REGISTRIES[*]}"
            echo "  -b, --build         Build images before publishing"
            echo "  --no-latest         Don't tag as 'latest'"
            echo "  --dry-run           Show what would be done without actually doing it"
            echo "  --parallel          Publish to registries in parallel"
            echo "  -h, --help          Show this help message"
            echo ""
            echo "Examples:"
            echo "  $0 -v 1.0.0 -r ghcr.io/username"
            echo "  $0 -v 1.0.0 -r docker.io/username -r ghcr.io/username --build"
            echo "  $0 -v 1.0.0 -r ghcr.io/username --dry-run"
            exit 0
            ;;
        *)
            log_error "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Validate required arguments
if [[ -z "$VERSION" ]]; then
    log_error "Version is required. Use -v or --version to specify."
    exit 1
fi

if [[ ${#REGISTRIES[@]} -eq 0 ]]; then
    log_error "At least one registry is required. Use -r or --registry to specify."
    exit 1
fi

# Validate version format (semantic versioning)
if [[ ! "$VERSION" =~ ^[0-9]+\.[0-9]+\.[0-9]+(-[a-zA-Z0-9.-]+)?(\+[a-zA-Z0-9.-]+)?$ ]]; then
    log_warning "Version '$VERSION' doesn't follow semantic versioning format (x.y.z)"
fi

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# MCP servers to publish
SERVERS=("snowflake-mcp" "databricks-mcp" "sqlserver-mcp")

# Function to validate registry format
validate_registry() {
    local registry=$1
    
    # Check if it's a supported registry or custom format
    for supported in "${SUPPORTED_REGISTRIES[@]}"; do
        if [[ "$registry" == "$supported"* ]]; then
            return 0
        fi
    done
    
    # Check if it looks like a valid registry URL
    if [[ "$registry" =~ ^[a-zA-Z0-9.-]+(/[a-zA-Z0-9._-]+)*$ ]]; then
        return 0
    fi
    
    log_error "Invalid registry format: $registry"
    return 1
}

# Function to build images if requested
build_images() {
    if [[ "$BUILD" == "true" ]]; then
        log "Building images before publishing..."
        
        local build_script="$SCRIPT_DIR/build-all.sh"
        if [[ ! -f "$build_script" ]]; then
            log_error "Build script not found: $build_script"
            return 1
        fi
        
        if [[ "$DRY_RUN" == "true" ]]; then
            log "DRY RUN: Would execute: $build_script -t $VERSION"
        else
            if ! "$build_script" -t "$VERSION"; then
                log_error "Failed to build images"
                return 1
            fi
        fi
    fi
}

# Function to tag image for registry
tag_image() {
    local server=$1
    local registry=$2
    local version=$3
    local tag_latest=$4
    
    local source_image="$server:$version"
    local target_image="$registry/$server:$version"
    local latest_image="$registry/$server:latest"
    
    log "Tagging $source_image as $target_image"
    
    if [[ "$DRY_RUN" == "true" ]]; then
        log "DRY RUN: Would execute: docker tag $source_image $target_image"
        if [[ "$tag_latest" == "true" ]]; then
            log "DRY RUN: Would execute: docker tag $source_image $latest_image"
        fi
    else
        if ! docker tag "$source_image" "$target_image"; then
            log_error "Failed to tag $source_image as $target_image"
            return 1
        fi
        
        if [[ "$tag_latest" == "true" ]]; then
            if ! docker tag "$source_image" "$latest_image"; then
                log_error "Failed to tag $source_image as $latest_image"
                return 1
            fi
        fi
    fi
}

# Function to push image to registry
push_image() {
    local server=$1
    local registry=$2
    local version=$3
    local tag_latest=$4
    
    local target_image="$registry/$server:$version"
    local latest_image="$registry/$server:latest"
    
    log "Pushing $target_image"
    
    if [[ "$DRY_RUN" == "true" ]]; then
        log "DRY RUN: Would execute: docker push $target_image"
        if [[ "$tag_latest" == "true" ]]; then
            log "DRY RUN: Would execute: docker push $latest_image"
        fi
    else
        if ! docker push "$target_image"; then
            log_error "Failed to push $target_image"
            return 1
        fi
        
        if [[ "$tag_latest" == "true" ]]; then
            if ! docker push "$latest_image"; then
                log_error "Failed to push $latest_image"
                return 1
            fi
        fi
    fi
    
    log_success "Successfully pushed $server to $registry"
}

# Function to publish a single server to a single registry
publish_server_to_registry() {
    local server=$1
    local registry=$2
    
    log "Publishing $server to $registry..."
    
    # Check if source image exists
    if [[ "$DRY_RUN" != "true" ]] && ! docker image inspect "$server:$VERSION" &> /dev/null; then
        log_error "Source image not found: $server:$VERSION"
        log "Hint: Use --build to build images before publishing"
        return 1
    fi
    
    # Tag the image
    if ! tag_image "$server" "$registry" "$VERSION" "$LATEST"; then
        return 1
    fi
    
    # Push the image
    if ! push_image "$server" "$registry" "$VERSION" "$LATEST"; then
        return 1
    fi
}

# Function to publish all servers to all registries in parallel
publish_parallel() {
    local pids=()
    local failed=0
    
    for registry in "${REGISTRIES[@]}"; do
        for server in "${SERVERS[@]}"; do
            publish_server_to_registry "$server" "$registry" &
            pids+=($!)
        done
    done
    
    # Wait for all publishes to complete
    for pid in "${pids[@]}"; do
        if ! wait "$pid"; then
            failed=1
        fi
    done
    
    return $failed
}

# Function to publish all servers to all registries sequentially
publish_sequential() {
    for registry in "${REGISTRIES[@]}"; do
        log "Publishing to registry: $registry"
        
        for server in "${SERVERS[@]}"; do
            if ! publish_server_to_registry "$server" "$registry"; then
                return 1
            fi
        done
        
        log_success "Completed publishing to $registry"
        echo
    done
}

# Function to check registry authentication
check_registry_auth() {
    local registry=$1
    
    log "Checking authentication for $registry..."
    
    if [[ "$DRY_RUN" == "true" ]]; then
        log "DRY RUN: Would check authentication for $registry"
        return 0
    fi
    
    # Try to get auth info (this will fail if not authenticated)
    if docker system info 2>/dev/null | grep -q "Registry:"; then
        log_success "Docker is authenticated"
    else
        log_warning "Cannot verify Docker authentication status"
    fi
    
    # For GHCR, check if we have a token
    if [[ "$registry" == "ghcr.io"* ]]; then
        if [[ -z "$GITHUB_TOKEN" ]] && [[ -z "$CR_PAT" ]]; then
            log_warning "For GHCR publishing, set GITHUB_TOKEN or CR_PAT environment variable"
            log_warning "Or run: echo \$GITHUB_TOKEN | docker login ghcr.io -u USERNAME --password-stdin"
        fi
    fi
}

# Main execution
log "Starting publish process..."
log "Version: $VERSION"
log "Registries: ${REGISTRIES[*]}"
log "Build: $BUILD"
log "Latest: $LATEST"
log "Dry Run: $DRY_RUN"
log "Parallel: $PARALLEL"

# Validate registries
for registry in "${REGISTRIES[@]}"; do
    if ! validate_registry "$registry"; then
        exit 1
    fi
done

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

# Check registry authentication
for registry in "${REGISTRIES[@]}"; do
    check_registry_auth "$registry"
done

# Build images if requested
if ! build_images; then
    exit 1
fi

# Publish images
start_time=$(date +%s)

if [[ "$PARALLEL" == "true" ]]; then
    log "Publishing in parallel..."
    if ! publish_parallel; then
        log_error "One or more publishes failed"
        exit 1
    fi
else
    log "Publishing sequentially..."
    if ! publish_sequential; then
        log_error "Publishing failed"
        exit 1
    fi
fi

end_time=$(date +%s)
duration=$((end_time - start_time))

# Summary
echo "========================================="
log "Publish Summary"
echo "========================================="

log_success "All images published successfully!"
log "Published version: $VERSION"
if [[ "$LATEST" == "true" ]]; then
    log "Also tagged as: latest"
fi

log "Published images:"
for registry in "${REGISTRIES[@]}"; do
    for server in "${SERVERS[@]}"; do
        echo "  - $registry/$server:$VERSION"
        if [[ "$LATEST" == "true" ]]; then
            echo "  - $registry/$server:latest"
        fi
    done
done

log_success "Publish process completed in ${duration} seconds"

if [[ "$DRY_RUN" == "true" ]]; then
    log_warning "This was a dry run. No actual publishing was performed."
fi