# Troubleshooting Guide

This guide provides detailed solutions for common issues when using the Databricks MCP Server.

## Table of Contents

1. [Installation Issues](#installation-issues)
2. [Configuration Issues](#configuration-issues)
3. [Connection Issues](#connection-issues)
4. [Authentication Issues](#authentication-issues)
5. [Runtime Issues](#runtime-issues)
6. [Performance Issues](#performance-issues)
7. [Platform-Specific Issues](#platform-specific-issues)
8. [Development Issues](#development-issues)
9. [Debugging Tips](#debugging-tips)
10. [Getting Help](#getting-help)

## Installation Issues

### uvx command not found

**Problem**: `bash: uvx: command not found` or `'uvx' is not recognized`

**Cause**: uv/uvx is not installed or not in PATH

**Solutions**:

1. **Install uv/uvx**:
   ```bash
   # macOS/Linux
   curl -LsSf https://astral.sh/uv/install.sh | sh
   
   # Windows (PowerShell)
   powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
   
   # Alternative: pip install
   pip install uv
   ```

2. **Add to PATH**:
   ```bash
   # Linux/macOS
   export PATH="$HOME/.local/bin:$PATH"
   echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
   
   # Windows
   # Add %USERPROFILE%\.local\bin to your PATH environment variable
   ```

3. **Restart terminal** after installation

### databricks-mcp-server command not found after uvx install

**Problem**: `databricks-mcp-server: command not found` after running `uvx databricks-mcp-server`

**Cause**: uvx binary directory not in PATH or installation failed

**Solutions**:

1. **Check uvx installation**:
   ```bash
   uvx --version
   uvx list
   ```

2. **Try full path**:
   ```bash
   ~/.local/bin/uvx databricks-mcp-server
   ```

3. **Reinstall with verbose output**:
   ```bash
   uvx --verbose databricks-mcp-server
   ```

4. **Use pip as alternative**:
   ```bash
   pip install databricks-mcp-server
   databricks-mcp-server
   ```

### Python version compatibility issues

**Problem**: `Python 3.x is not supported` or version-related errors

**Cause**: Python version is older than 3.8

**Solutions**:

1. **Check Python version**:
   ```bash
   python --version
   python3 --version
   ```

2. **Update Python**:
   ```bash
   # macOS (Homebrew)
   brew install python@3.11
   
   # Ubuntu/Debian
   sudo apt update
   sudo apt install python3.11
   
   # Windows: Download from python.org
   ```

3. **Use specific Python version with uvx**:
   ```bash
   uvx --python python3.11 databricks-mcp-server
   ```

### Package installation fails

**Problem**: `Failed to install databricks-mcp-server` or dependency conflicts

**Cause**: Network issues, dependency conflicts, or package repository problems

**Solutions**:

1. **Check network connectivity**:
   ```bash
   ping pypi.org
   curl -I https://pypi.org/simple/databricks-mcp-server/
   ```

2. **Clear uvx cache**:
   ```bash
   uvx cache clean
   ```

3. **Try with pip**:
   ```bash
   pip install --upgrade pip
   pip install databricks-mcp-server
   ```

4. **Use different index**:
   ```bash
   uvx --index-url https://pypi.org/simple/ databricks-mcp-server
   ```

## Configuration Issues

### Missing required configuration

**Problem**: `Missing required field 'server_hostname'` or similar errors

**Cause**: Required environment variables or config file values not set

**Solutions**:

1. **Set required environment variables**:
   ```bash
   export DATABRICKS_SERVER_HOSTNAME="your-workspace.cloud.databricks.com"
   export DATABRICKS_HTTP_PATH="/sql/1.0/warehouses/your-warehouse-id"
   export DATABRICKS_ACCESS_TOKEN="your-access-token-here"
   ```

2. **Create config file**:
   ```bash
   cp config/config.yaml.example config.yaml
   # Edit config.yaml with your values
   ```

3. **Verify configuration**:
   ```bash
   databricks-mcp-server --log-level DEBUG
   ```

### Invalid hostname format

**Problem**: `server_hostname should not include protocol`

**Cause**: Including `https://` in the hostname

**Solutions**:

```bash
# Wrong
export DATABRICKS_SERVER_HOSTNAME="https://my-workspace.cloud.databricks.com"

# Correct
export DATABRICKS_SERVER_HOSTNAME="my-workspace.cloud.databricks.com"
```

### Invalid HTTP path format

**Problem**: `http_path must start with '/'`

**Cause**: HTTP path doesn't start with forward slash

**Solutions**:

```bash
# Wrong
export DATABRICKS_HTTP_PATH="sql/1.0/warehouses/abc123"

# Correct
export DATABRICKS_HTTP_PATH="/sql/1.0/warehouses/abc123"
```

### Configuration file not found

**Problem**: `Config file not found: /path/to/config.yaml`

**Cause**: Specified config file doesn't exist or wrong path

**Solutions**:

1. **Check file exists**:
   ```bash
   ls -la /path/to/config.yaml
   ```

2. **Use absolute path**:
   ```bash
   databricks-mcp-server --config /absolute/path/to/config.yaml
   ```

3. **Check file permissions**:
   ```bash
   chmod 644 config.yaml
   ```

4. **Use default locations**:
   ```bash
   # Place config in one of these locations:
   ./config.yaml
   ./config/config.yaml
   ~/.databricks-mcp/config.yaml
   ```

### YAML parsing errors

**Problem**: `YAML parsing error` or `Invalid YAML format`

**Cause**: Malformed YAML in config file

**Solutions**:

1. **Validate YAML syntax**:
   ```bash
   python -c "import yaml; yaml.safe_load(open('config.yaml'))"
   ```

2. **Check indentation** (use spaces, not tabs):
   ```yaml
   databricks:
     server_hostname: "example.com"  # 2 spaces
     http_path: "/sql/1.0/warehouses/abc"  # 2 spaces
   ```

3. **Quote special characters**:
   ```yaml
   databricks:
     access_token: "dapi-abc123!@#$%"  # Quote tokens with special chars
   ```

## Connection Issues

### Connection timeout

**Problem**: `Connection timeout` or `Unable to connect to Databricks`

**Cause**: Network issues, firewall, or slow connection

**Solutions**:

1. **Test network connectivity**:
   ```bash
   ping your-workspace.cloud.databricks.com
   curl -I https://your-workspace.cloud.databricks.com
   ```

2. **Increase timeout**:
   ```bash
   export DATABRICKS_TIMEOUT="300"  # 5 minutes
   ```

3. **Check firewall settings**:
   - Ensure outbound HTTPS (port 443) is allowed
   - Check corporate firewall/proxy settings

4. **Try different network**:
   - Test from different network (mobile hotspot)
   - Check VPN requirements

### SSL/TLS certificate errors

**Problem**: `SSL certificate verification failed` or `Certificate error`

**Cause**: Certificate validation issues or corporate proxy

**Solutions**:

1. **Update certificates**:
   ```bash
   # macOS
   /Applications/Python\ 3.x/Install\ Certificates.command
   
   # Linux
   sudo apt-get update && sudo apt-get install ca-certificates
   ```

2. **Check system time**:
   ```bash
   date
   # Ensure system time is correct
   ```

3. **Corporate proxy setup**:
   ```bash
   export HTTPS_PROXY="http://proxy.company.com:8080"
   export REQUESTS_CA_BUNDLE="/path/to/corporate-ca-bundle.crt"
   ```

### DNS resolution issues

**Problem**: `Name resolution failed` or `Host not found`

**Cause**: DNS configuration issues

**Solutions**:

1. **Test DNS resolution**:
   ```bash
   nslookup your-workspace.cloud.databricks.com
   dig your-workspace.cloud.databricks.com
   ```

2. **Try different DNS servers**:
   ```bash
   # Temporarily use Google DNS
   export DNS_SERVER="8.8.8.8"
   ```

3. **Check /etc/hosts** (Linux/macOS):
   ```bash
   cat /etc/hosts
   # Ensure no conflicting entries
   ```

## Authentication Issues

### Invalid access token

**Problem**: `Authentication failed` or `Invalid access token`

**Cause**: Token is expired, invalid, or has insufficient permissions

**Solutions**:

1. **Generate new token**:
   - Go to Databricks workspace
   - User Settings → Developer → Access Tokens
   - Generate New Token
   - Copy and use the new token

2. **Check token format**:
   ```bash
   # Token should start with 'dapi'
   echo $DATABRICKS_ACCESS_TOKEN | head -c 10
   ```

3. **Verify token permissions**:
   - Ensure token has SQL warehouse access
   - Check workspace permissions
   - Verify catalog/schema access rights

4. **Test token manually**:
   ```bash
   curl -H "Authorization: Bearer $DATABRICKS_ACCESS_TOKEN" \
        "https://$DATABRICKS_SERVER_HOSTNAME/api/2.0/clusters/list"
   ```

### Token expired

**Problem**: `Token has expired` or `Authentication token is no longer valid`

**Cause**: Access token has reached its expiration date

**Solutions**:

1. **Generate new token** (see above)

2. **Set up token rotation**:
   ```bash
   # Use shorter-lived tokens and rotate regularly
   # Consider using service principals for production
   ```

3. **Check token expiration**:
   - Tokens can be set to never expire or have specific expiration dates
   - Monitor token usage in Databricks audit logs

### Insufficient permissions

**Problem**: `Permission denied` or `Access forbidden`

**Cause**: Token or user doesn't have required permissions

**Solutions**:

1. **Check workspace permissions**:
   - Verify user has workspace access
   - Check if user is in required groups

2. **Verify SQL warehouse permissions**:
   - Ensure user can access the specified warehouse
   - Check warehouse permissions in Databricks UI

3. **Test with different warehouse**:
   ```bash
   export DATABRICKS_HTTP_PATH="/sql/1.0/warehouses/different-warehouse-id"
   ```

4. **Contact administrator**:
   - Request necessary permissions
   - Verify account status

## Runtime Issues

### Server starts but MCP tools don't work

**Problem**: Server starts successfully but MCP operations fail

**Cause**: MCP client configuration issues or tool-specific problems

**Solutions**:

1. **Test server directly**:
   ```bash
   databricks-mcp-server --log-level DEBUG
   ```

2. **Check MCP client configuration**:
   ```json
   {
     "mcpServers": {
       "databricks": {
         "command": "uvx",
         "args": ["databricks-mcp-server"],
         "env": { /* your env vars */ }
       }
     }
   }
   ```

3. **Verify tool availability**:
   - Check if specific MCP tools are working
   - Test with simple operations first

4. **Check client logs**:
   - Review MCP client logs for errors
   - Look for connection or protocol issues

### Memory issues

**Problem**: `Out of memory` or high memory usage

**Cause**: Large query results or memory leaks

**Solutions**:

1. **Limit query result size**:
   ```sql
   SELECT * FROM large_table LIMIT 1000;
   ```

2. **Increase available memory**:
   ```bash
   # For uvx, this is handled automatically
   # For pip installations, consider virtual environments
   ```

3. **Monitor memory usage**:
   ```bash
   # Linux/macOS
   top -p $(pgrep -f databricks-mcp-server)
   
   # Windows
   tasklist | findstr databricks-mcp-server
   ```

### Query execution failures

**Problem**: SQL queries fail or return errors

**Cause**: SQL syntax errors, permission issues, or data problems

**Solutions**:

1. **Test query in Databricks UI**:
   - Run the same query in Databricks SQL editor
   - Verify syntax and permissions

2. **Check query logs**:
   ```bash
   databricks-mcp-server --log-level DEBUG
   ```

3. **Simplify query**:
   ```sql
   -- Start with simple queries
   SELECT 1;
   SHOW CATALOGS;
   ```

4. **Check data types**:
   - Verify column types match expectations
   - Handle NULL values appropriately

## Performance Issues

### Slow query execution

**Problem**: Queries take too long to execute

**Cause**: Large datasets, inefficient queries, or warehouse sizing

**Solutions**:

1. **Optimize queries**:
   ```sql
   -- Add WHERE clauses to limit data
   SELECT * FROM table WHERE date >= '2024-01-01' LIMIT 1000;
   
   -- Use appropriate indexes
   -- Avoid SELECT *
   ```

2. **Check warehouse size**:
   - Use larger warehouse for better performance
   - Consider serverless SQL warehouses

3. **Monitor query performance**:
   - Check Databricks query history
   - Review execution plans

4. **Increase timeout**:
   ```bash
   export DATABRICKS_TIMEOUT="600"  # 10 minutes
   ```

### Slow server startup

**Problem**: Server takes long time to start

**Cause**: Dependency loading or configuration validation

**Solutions**:

1. **Use uvx for faster startup**:
   ```bash
   uvx databricks-mcp-server  # Cached after first run
   ```

2. **Optimize configuration**:
   - Use environment variables instead of config files
   - Minimize configuration validation

3. **Check system resources**:
   - Ensure adequate CPU and memory
   - Close unnecessary applications

## Platform-Specific Issues

### Windows Issues

**PowerShell execution policy**:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

**Path separator issues**:
```powershell
# Use forward slashes in HTTP paths
$env:DATABRICKS_HTTP_PATH = "/sql/1.0/warehouses/abc123"
```

**Environment variable persistence**:
```powershell
[Environment]::SetEnvironmentVariable("DATABRICKS_SERVER_HOSTNAME", "value", "User")
```

### macOS Issues

**Certificate issues**:
```bash
/Applications/Python\ 3.x/Install\ Certificates.command
```

**Homebrew Python conflicts**:
```bash
brew unlink python@3.x
brew link python@3.11
```

### Linux Issues

**Permission denied**:
```bash
chmod +x ~/.local/bin/uvx
```

**Missing dependencies**:
```bash
sudo apt-get install python3-dev python3-pip
```

## Development Issues

### Import errors during development

**Problem**: `ModuleNotFoundError` or import issues

**Cause**: Development environment not set up correctly

**Solutions**:

1. **Install in development mode**:
   ```bash
   pip install -e ".[dev]"
   ```

2. **Check Python path**:
   ```bash
   python -c "import sys; print(sys.path)"
   ```

3. **Verify package structure**:
   ```bash
   ls -la src/databricks_mcp_server/
   ```

### Test failures

**Problem**: Tests fail during development

**Cause**: Missing test dependencies or configuration

**Solutions**:

1. **Install test dependencies**:
   ```bash
   pip install -e ".[test]"
   ```

2. **Set test environment variables**:
   ```bash
   export DATABRICKS_SERVER_HOSTNAME="test-workspace.cloud.databricks.com"
   # Set other test variables
   ```

3. **Run specific tests**:
   ```bash
   pytest tests/test_config.py -v
   ```

### Build issues

**Problem**: Package build fails

**Cause**: Missing build dependencies or configuration issues

**Solutions**:

1. **Install build tools**:
   ```bash
   pip install build wheel
   ```

2. **Clean build artifacts**:
   ```bash
   rm -rf dist/ build/ *.egg-info/
   ```

3. **Build with verbose output**:
   ```bash
   python -m build --verbose
   ```

## Debugging Tips

### Enable debug logging

```bash
databricks-mcp-server --log-level DEBUG
```

### Check configuration loading

```bash
# Test configuration without starting server
python -c "
from databricks_mcp_server.config import ConfigManager
config = ConfigManager().load_config()
print(config)
"
```

### Test Databricks connection

```bash
# Test connection manually
python -c "
from databricks import sql
import os
connection = sql.connect(
    server_hostname=os.getenv('DATABRICKS_SERVER_HOSTNAME'),
    http_path=os.getenv('DATABRICKS_HTTP_PATH'),
    access_token=os.getenv('DATABRICKS_ACCESS_TOKEN')
)
cursor = connection.cursor()
cursor.execute('SELECT 1')
print(cursor.fetchall())
cursor.close()
connection.close()
"
```

### Monitor system resources

```bash
# Linux/macOS
htop
iostat 1
netstat -an | grep :443

# Windows
taskmgr
netstat -an | findstr :443
```

### Network debugging

```bash
# Test HTTPS connectivity
curl -v https://your-workspace.cloud.databricks.com

# Check DNS resolution
nslookup your-workspace.cloud.databricks.com

# Test with different DNS
nslookup your-workspace.cloud.databricks.com 8.8.8.8
```

## Getting Help

### Before asking for help

1. **Check this troubleshooting guide**
2. **Enable debug logging**: `--log-level DEBUG`
3. **Test with minimal configuration**
4. **Verify credentials work in Databricks UI**
5. **Check system requirements**

### Information to include when reporting issues

1. **Environment details**:
   - Operating system and version
   - Python version
   - uvx/uv version
   - Package version

2. **Configuration** (without sensitive values):
   ```bash
   # Example
   OS: Ubuntu 22.04
   Python: 3.11.2
   uvx: 0.4.15
   Package: databricks-mcp-server 1.0.0
   ```

3. **Error messages and logs**:
   - Full error messages
   - Debug logs (with sensitive info removed)
   - Stack traces

4. **Steps to reproduce**:
   - Exact commands run
   - Configuration used
   - Expected vs actual behavior

### Where to get help

1. **GitHub Issues**: [Repository Issues](https://github.com/your-repo/databricks-mcp-server/issues)
2. **Documentation**: Check README.md and other docs
3. **Community**: Databricks community forums
4. **Support**: Contact your Databricks administrator

### Creating a minimal reproduction case

```bash
# Create minimal test case
export DATABRICKS_SERVER_HOSTNAME="your-workspace.cloud.databricks.com"
export DATABRICKS_HTTP_PATH="/sql/1.0/warehouses/your-warehouse-id"
export DATABRICKS_ACCESS_TOKEN="your-token"
export DATABRICKS_MCP_LOG_LEVEL="DEBUG"

# Run with debug logging
databricks-mcp-server --log-level DEBUG > debug.log 2>&1

# Share debug.log (remove sensitive information first)
```

Remember to remove sensitive information (tokens, hostnames, etc.) before sharing logs or configuration files!