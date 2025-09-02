# Design Document

## Overview

This design transforms the existing Databricks MCP server from a Docker-based distribution to a uvx-compatible Python package. The solution leverages Python's standard packaging ecosystem with pyproject.toml configuration, enabling users to install and run the MCP server using `uvx databricks-mcp-server` without Docker dependencies.

The design maintains full compatibility with the existing functionality while providing a more streamlined installation and sharing experience. Users will only need uv/uvx installed and proper Databricks credentials configured.

## Architecture

### Package Structure
```
databricks-mcp-server/
├── pyproject.toml              # Package configuration and metadata
├── README.md                   # Installation and usage documentation
├── src/
│   └── databricks_mcp_server/
│       ├── __init__.py         # Package initialization
│       ├── main.py             # Entry point for uvx execution
│       ├── server.py           # Core MCP server logic (refactored from Databricks_MCP.py)
│       └── config.py           # Configuration management
├── config/
│   └── config.yaml.example     # Example configuration file
└── tests/
    ├── __init__.py
    ├── test_server.py          # Server functionality tests
    └── test_config.py          # Configuration tests
```

### Entry Point Design
The package will use Python's console_scripts entry point mechanism to create the `databricks-mcp-server` executable. When installed via uvx, this creates an isolated environment with all dependencies and makes the command globally available.

### Configuration Strategy
The server will support multiple configuration methods with the following precedence:
1. Environment variables (highest priority)
2. Config file specified via `--config` argument
3. Default config file locations (`./config.yaml`, `~/.databricks-mcp/config.yaml`)
4. Interactive prompts for missing required values (lowest priority)

## Components and Interfaces

### Main Entry Point (`main.py`)
```python
def main():
    """Main entry point for uvx execution"""
    # Parse command line arguments
    # Load configuration from multiple sources
    # Initialize and start MCP server
    # Handle graceful shutdown
```

**Responsibilities:**
- Command-line argument parsing
- Configuration loading and validation
- Server lifecycle management
- Error handling and logging setup

### Configuration Manager (`config.py`)
```python
class ConfigManager:
    def load_config(self, config_path: Optional[str] = None) -> Dict[str, Any]
    def validate_config(self, config: Dict[str, Any]) -> bool
    def get_databricks_config(self) -> Dict[str, Any]
```

**Responsibilities:**
- Multi-source configuration loading (files, environment variables)
- Configuration validation and error reporting
- Default value management
- Credential security handling

### MCP Server (`server.py`)
Refactored version of the existing `Databricks_MCP.py` with:
- Modular design for better testability
- Improved error handling and logging
- Configuration injection rather than global config
- Same MCP tool interface and functionality

### Package Configuration (`pyproject.toml`)
```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "databricks-mcp-server"
version = "1.0.0"
description = "Model Context Protocol server for Databricks operations"
requires-python = ">=3.8"
dependencies = [
    "databricks-sql-connector>=3.0.0",
    "requests>=2.31.0",
    "pyyaml>=6.0",
    "mcp>=1.0.0"
]

[project.scripts]
databricks-mcp-server = "databricks_mcp_server.main:main"
```

## Data Models

### Configuration Schema
```python
@dataclass
class DatabricksConfig:
    server_hostname: str
    http_path: str
    access_token: str
    catalog: str = "hive_metastore"
    schema: str = "default"
    timeout: int = 120
    
@dataclass
class ServerConfig:
    databricks: DatabricksConfig
    log_level: str = "INFO"
    config_file: Optional[str] = None
```

### Environment Variable Mapping
- `DATABRICKS_SERVER_HOSTNAME` → server_hostname
- `DATABRICKS_HTTP_PATH` → http_path  
- `DATABRICKS_ACCESS_TOKEN` → access_token
- `DATABRICKS_CATALOG` → catalog
- `DATABRICKS_SCHEMA` → schema
- `DATABRICKS_MCP_LOG_LEVEL` → log_level

## Error Handling

### Configuration Errors
- Missing required credentials: Clear error messages with setup instructions
- Invalid configuration format: Specific validation error details
- File access issues: Permission and path error guidance

### Runtime Errors
- Connection failures: Databricks connectivity troubleshooting
- Authentication errors: Token validation and refresh guidance
- Dependency issues: Package installation and version conflict resolution

### uvx-Specific Errors
- Python version compatibility: Clear version requirement messages
- Package installation failures: Dependency resolution guidance
- Environment isolation issues: uvx troubleshooting steps

## Testing Strategy

### Unit Tests
- Configuration loading and validation logic
- MCP tool functionality (isolated from Databricks connections)
- Error handling and edge cases
- Environment variable processing

### Integration Tests
- End-to-end MCP server functionality
- Databricks connection and query execution
- Configuration file processing
- Command-line interface behavior

### Package Tests
- Installation via pip and uvx
- Entry point execution
- Dependency resolution
- Cross-platform compatibility (Windows, macOS, Linux)

### Performance Tests
- Server startup time
- Query execution performance
- Memory usage in isolated environment
- Concurrent connection handling

## Migration Strategy

### Phase 1: Package Structure Setup
- Create proper Python package structure
- Configure pyproject.toml with dependencies and entry points
- Refactor existing code into modular components
- Implement configuration management system

### Phase 2: uvx Compatibility
- Test package installation via uvx
- Validate entry point execution
- Ensure environment isolation works correctly
- Test cross-platform compatibility

### Phase 3: Documentation and Distribution
- Create comprehensive README with installation instructions
- Document configuration options and examples
- Prepare package for PyPI distribution
- Create migration guide from Docker version

### Backward Compatibility
- Maintain identical MCP tool interface
- Support existing config.yaml format
- Preserve all current functionality
- Provide Docker-to-uvx migration documentation

## Security Considerations

### Credential Management
- Environment variables preferred over config files
- Config file permission validation (readable only by owner)
- No credential logging or exposure in error messages
- Support for credential rotation without restart

### Package Security
- Pin dependency versions to prevent supply chain attacks
- Use official PyPI distribution channels
- Include security scanning in CI/CD pipeline
- Regular dependency updates and vulnerability monitoring

### Isolation Benefits
- uvx provides isolated Python environment
- No system-wide package conflicts
- Clean uninstallation without residual files
- Reduced attack surface compared to Docker

## Performance Considerations

### Startup Performance
- Lazy loading of heavy dependencies
- Configuration caching to avoid repeated file reads
- Connection pooling for Databricks API calls
- Optimized import structure

### Memory Usage
- Efficient JSON processing for large query results
- Connection cleanup and resource management
- Configurable timeout and retry settings
- Memory profiling and optimization

### Distribution Size
- Minimal dependency footprint
- Exclude development and testing dependencies from distribution
- Optimize package size for faster uvx installation
- Consider optional dependencies for advanced features