# Databricks MCP Server

A Model Context Protocol (MCP) server for Databricks operations that can be installed and run via uvx.

## Overview

This package provides a streamlined way to run a Databricks MCP server without Docker dependencies. Users can install and run the server using just `uvx` and proper Databricks credentials.

The server provides MCP tools for:
- Executing SQL queries on Databricks
- Managing catalogs, schemas, and tables
- Retrieving table metadata and schema information
- Creating and managing database objects
- Checking warehouse status and connectivity

## Quick Start

1. **Install uv/uvx** (if not already installed):
   ```bash
   # On macOS/Linux
   curl -LsSf https://astral.sh/uv/install.sh | sh
   
   # On Windows
   powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
   ```

2. **Set up your Databricks credentials**:
   ```bash
   export DATABRICKS_SERVER_HOSTNAME="your-workspace.cloud.databricks.com"
   export DATABRICKS_HTTP_PATH="/sql/1.0/warehouses/your-warehouse-id"
   export DATABRICKS_ACCESS_TOKEN="your-access-token-here"
   ```

3. **Run the server**:
   ```bash
   uvx databricks-mcp-server
   ```

## Installation

### Prerequisites

- **Python 3.8 or higher**
- **uv/uvx**: [Installation Guide](https://docs.astral.sh/uv/getting-started/installation/)

### Install and Run via uvx

The simplest way to use the server is with uvx, which automatically handles installation and dependency management:

```bash
uvx databricks-mcp-server
```

This command will:
- Download and install the package in an isolated environment
- Install all required dependencies
- Start the MCP server with your configuration

### Install via pip (for development)

For development or if you prefer pip:

```bash
pip install databricks-mcp-server
databricks-mcp-server
```

## Configuration

The server supports multiple configuration methods with the following precedence (highest to lowest):

1. **Environment variables** (recommended for security)
2. **Config file specified via `--config` argument**
3. **Default config file locations**:
   - `./config.yaml`
   - `./config/config.yaml`
   - `~/.databricks-mcp/config.yaml`

### Environment Variables (Recommended)

Set these environment variables for secure credential management:

```bash
# Required
export DATABRICKS_SERVER_HOSTNAME="your-workspace.cloud.databricks.com"
export DATABRICKS_HTTP_PATH="/sql/1.0/warehouses/your-warehouse-id"
export DATABRICKS_ACCESS_TOKEN="your-access-token-here"

# Optional
export DATABRICKS_CATALOG="hive_metastore"     # Default catalog
export DATABRICKS_SCHEMA="default"             # Default schema
export DATABRICKS_TIMEOUT="120"                # Connection timeout (seconds)
export DATABRICKS_MCP_LOG_LEVEL="INFO"         # Log level
```

### Configuration File

Copy `config/config.yaml.example` to `config.yaml` and update with your credentials:

```yaml
databricks:
  server_hostname: "your-workspace.cloud.databricks.com"
  http_path: "/sql/1.0/warehouses/your-warehouse-id"
  access_token: "your-access-token-here"
  catalog: "hive_metastore"
  schema: "default"
  timeout: 120

server:
  log_level: "INFO"
```

### Getting Databricks Credentials

1. **Server Hostname**: Your Databricks workspace URL without `https://`
   - Example: `my-company.cloud.databricks.com`

2. **HTTP Path**: Found in your SQL Warehouse or Cluster connection details
   - SQL Warehouse: `/sql/1.0/warehouses/{warehouse-id}`
   - Cluster: `/sql/protocolv1/o/{org-id}/{cluster-id}`

3. **Access Token**: Generate in Databricks workspace
   - Go to: User Settings → Developer → Access Tokens
   - Click "Generate New Token"
   - Copy the token (you won't see it again!)

## Usage

### Basic Usage

Start the server with environment variables or default config:

```bash
databricks-mcp-server
```

### With Custom Config File

```bash
databricks-mcp-server --config /path/to/your/config.yaml
```

### Command Line Options

```bash
databricks-mcp-server --help
```

Options:
- `--config PATH`: Path to configuration file
- `--log-level LEVEL`: Override log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- `--version`: Show version information

### Using with Kiro

Add this to your Kiro MCP configuration (`.kiro/settings/mcp.json`):

```json
{
  "mcpServers": {
    "databricks": {
      "command": "uvx",
      "args": ["databricks-mcp-server"],
      "env": {
        "DATABRICKS_SERVER_HOSTNAME": "your-workspace.cloud.databricks.com",
        "DATABRICKS_HTTP_PATH": "/sql/1.0/warehouses/your-warehouse-id",
        "DATABRICKS_ACCESS_TOKEN": "your-access-token-here"
      },
      "disabled": false,
      "autoApprove": ["execute_query", "list_catalogs", "list_schemas", "list_tables"]
    }
  }
}
```

## Available MCP Tools

The server provides these MCP tools for Databricks operations:

- **execute_query**: Execute SQL queries and return results
- **list_catalogs**: List available catalogs
- **list_schemas**: List schemas in a catalog
- **list_tables**: List tables in a schema
- **get_table_schema**: Get detailed schema information for a table
- **describe_table**: Get comprehensive table metadata
- **create_table**: Create new tables
- **insert_data**: Insert data into tables
- **check_warehouse_status**: Check serverless warehouse status
- **ping**: Test server connectivity

## Development

### Setup Development Environment

```bash
git clone <repository-url>
cd databricks-mcp-server
pip install -e ".[dev]"
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src/databricks_mcp_server

# Run specific test file
pytest tests/test_config.py
```

### Code Quality

```bash
# Format code
black src/ tests/
isort src/ tests/

# Type checking
mypy src/

# Linting
flake8 src/ tests/
```

### Building the Package

```bash
# Build distribution packages
python -m build

# Install locally for testing
pip install -e .
```

## Features

- ✅ **Easy Installation**: Install with a single `uvx` command
- ✅ **Multiple Configuration Options**: Environment variables, config files, or command-line arguments
- ✅ **Isolated Environment**: uvx provides dependency isolation
- ✅ **Cross-Platform**: Works on Windows, macOS, and Linux
- ✅ **Full MCP Compatibility**: Maintains identical functionality to Docker version
- ✅ **Secure Credential Management**: Environment variable support
- ✅ **Comprehensive Error Handling**: Clear error messages and troubleshooting guidance
- ✅ **Flexible Configuration**: Multiple config file locations and precedence
- ✅ **Development-Friendly**: Easy local development and testing

## Migration from Docker Version

If you're currently using the Docker-based version, migration is straightforward:

### Step 1: Install uvx version
```bash
uvx databricks-mcp-server
```

### Step 2: Update your MCP client configuration

**Before (Docker):**
```json
{
  "mcpServers": {
    "databricks": {
      "command": "docker",
      "args": ["run", "-i", "--rm", "-v", "./config:/app/config", "databricks-mcp"],
      "disabled": false
    }
  }
}
```

**After (uvx):**
```json
{
  "mcpServers": {
    "databricks": {
      "command": "uvx",
      "args": ["databricks-mcp-server"],
      "env": {
        "DATABRICKS_SERVER_HOSTNAME": "your-workspace.cloud.databricks.com",
        "DATABRICKS_HTTP_PATH": "/sql/1.0/warehouses/your-warehouse-id",
        "DATABRICKS_ACCESS_TOKEN": "your-access-token-here"
      },
      "disabled": false
    }
  }
}
```

### Step 3: Test the migration
```bash
# Test the server starts correctly
databricks-mcp-server

# Test with your MCP client (e.g., Kiro)
```

The functionality remains identical - only the installation and execution method changes.

## Troubleshooting

### Installation Issues

**Problem**: `uvx: command not found`
```bash
# Solution: Install uv first
curl -LsSf https://astral.sh/uv/install.sh | sh
# Or on Windows:
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

**Problem**: `databricks-mcp-server: command not found` after uvx install
```bash
# Solution: Make sure uvx bin directory is in PATH
export PATH="$HOME/.local/bin:$PATH"
# Or restart your terminal
```

**Problem**: Python version compatibility issues
```bash
# Solution: Check Python version (requires 3.8+)
python --version
# Update Python if needed
```

### Configuration Issues

**Problem**: `Missing required field 'server_hostname'`
```bash
# Solution: Set required environment variables
export DATABRICKS_SERVER_HOSTNAME="your-workspace.cloud.databricks.com"
export DATABRICKS_HTTP_PATH="/sql/1.0/warehouses/your-warehouse-id"
export DATABRICKS_ACCESS_TOKEN="your-access-token-here"
```

**Problem**: `server_hostname should not include protocol`
```bash
# Wrong:
export DATABRICKS_SERVER_HOSTNAME="https://my-workspace.cloud.databricks.com"

# Correct:
export DATABRICKS_SERVER_HOSTNAME="my-workspace.cloud.databricks.com"
```

**Problem**: `http_path must start with '/'`
```bash
# Wrong:
export DATABRICKS_HTTP_PATH="sql/1.0/warehouses/abc123"

# Correct:
export DATABRICKS_HTTP_PATH="/sql/1.0/warehouses/abc123"
```

### Connection Issues

**Problem**: `Connection timeout` or `Unable to connect to Databricks`
```bash
# Solutions:
# 1. Check network connectivity
ping your-workspace.cloud.databricks.com

# 2. Verify credentials are correct
# 3. Check if warehouse/cluster is running
# 4. Increase timeout in config
export DATABRICKS_TIMEOUT="300"
```

**Problem**: `Authentication failed` or `Invalid access token`
```bash
# Solutions:
# 1. Generate a new access token in Databricks
# 2. Check token hasn't expired
# 3. Verify token has required permissions
# 4. Make sure token is set correctly (no extra spaces/quotes)
```

**Problem**: `Warehouse not found` or `Cluster not accessible`
```bash
# Solutions:
# 1. Verify the HTTP path is correct
# 2. Check if warehouse/cluster is running
# 3. Ensure you have access permissions
# 4. Try with a different warehouse/cluster
```

### Runtime Issues

**Problem**: Server starts but MCP tools don't work
```bash
# Solutions:
# 1. Check server logs for errors
databricks-mcp-server --log-level DEBUG

# 2. Test connection manually
# 3. Verify MCP client configuration
# 4. Check firewall/network restrictions
```

**Problem**: `Permission denied` errors
```bash
# Solutions:
# 1. Check Databricks workspace permissions
# 2. Verify access token permissions
# 3. Check catalog/schema access rights
# 4. Contact your Databricks administrator
```

### Getting Help

1. **Check the logs**: Run with `--log-level DEBUG` for detailed information
2. **Verify configuration**: Use the configuration examples in this README
3. **Test connectivity**: Try connecting to Databricks with other tools
4. **Check permissions**: Ensure your access token has the required permissions
5. **Update dependencies**: Make sure you're using the latest version

**Still having issues?**
- Check the [GitHub Issues](https://github.com/your-repo/databricks-mcp-server/issues)
- Create a new issue with:
  - Your configuration (without sensitive values)
  - Error messages and logs
  - Steps to reproduce the problem
  - Your environment details (OS, Python version, etc.)

## Security Best Practices

1. **Use Environment Variables**: Store sensitive credentials in environment variables, not config files
2. **File Permissions**: Set restrictive permissions on config files (`chmod 600 config.yaml`)
3. **Token Management**: 
   - Rotate access tokens regularly
   - Use workspace-specific tokens with minimal required permissions
   - Never commit tokens to version control
4. **Network Security**: Use HTTPS connections and verify certificates
5. **Audit Access**: Monitor Databricks audit logs for unusual activity

## License

MIT License

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes with tests
4. Run the test suite
5. Submit a pull request

See the development setup instructions above for getting started.