# SQL Server MCP Server - Docker Distribution

A containerized Model Context Protocol (MCP) server for SQL Server operations. This server provides SQL Server connectivity for MCP clients like Kiro IDE, Claude Desktop, and other MCP-compatible applications.

## 🚀 Quick Start

### Prerequisites
- Docker Desktop installed and running
- Access to a SQL Server instance
- MCP client (Kiro IDE, Claude Desktop, etc.)

### 1. Pull the Docker Image
```bash
# Replace with actual registry location when published
docker pull yourusername/sqlserver-mcp:latest
```

### 2. Configure Your MCP Client

Add this configuration to your MCP settings:

#### For Kiro IDE (`.kiro/settings/mcp.json`):
```json
{
  "mcpServers": {
    "sqlserver-mcp": {
      "command": "docker",
      "args": [
        "run", "--rm", "-i",
        "-e", "SQLSERVER_SERVER=your-sql-server-host",
        "-e", "SQLSERVER_DATABASE=your-database-name",
        "-e", "SQLSERVER_USERNAME=your-username",
        "-e", "SQLSERVER_PASSWORD=your-password",
        "-e", "SQLSERVER_DRIVER=ODBC Driver 18 for SQL Server",
        "-e", "SQLSERVER_ENCRYPT=yes",
        "-e", "SQLSERVER_TRUST_CERTIFICATE=yes",
        "yourusername/sqlserver-mcp:latest"
      ],
      "disabled": false,
      "autoApprove": ["test_connection", "list_tables", "get_table_schema"]
    }
  }
}
```

#### For Claude Desktop:
```json
{
  "mcpServers": {
    "sqlserver": {
      "command": "docker",
      "args": [
        "run", "--rm", "-i",
        "-e", "SQLSERVER_SERVER=your-sql-server-host",
        "-e", "SQLSERVER_DATABASE=your-database-name",
        "-e", "SQLSERVER_USERNAME=your-username",
        "-e", "SQLSERVER_PASSWORD=your-password",
        "-e", "SQLSERVER_DRIVER=ODBC Driver 18 for SQL Server",
        "-e", "SQLSERVER_ENCRYPT=yes",
        "-e", "SQLSERVER_TRUST_CERTIFICATE=yes",
        "yourusername/sqlserver-mcp:latest"
      ]
    }
  }
}
```

## ⚙️ Configuration Options

### Required Environment Variables
- `SQLSERVER_SERVER` - SQL Server hostname or IP address
- `SQLSERVER_DATABASE` - Database name to connect to
- `SQLSERVER_USERNAME` - SQL Server username (not needed for Windows auth)
- `SQLSERVER_PASSWORD` - SQL Server password (not needed for Windows auth)

### Optional Environment Variables
- `SQLSERVER_DRIVER` - ODBC driver name (default: "ODBC Driver 18 for SQL Server")
- `SQLSERVER_ENCRYPT` - Enable encryption (default: "yes")
- `SQLSERVER_TRUST_CERTIFICATE` - Trust server certificate (default: "yes")
- `SQLSERVER_USE_WINDOWS_AUTH` - Use Windows authentication (default: "false")

### Connection Examples

#### Local SQL Server (Windows/Mac/Linux)
```bash
-e SQLSERVER_SERVER=host.docker.internal
```

#### Remote SQL Server
```bash
-e SQLSERVER_SERVER=sql-server.company.com
-e SQLSERVER_SERVER=192.168.1.100
-e SQLSERVER_SERVER=sql-server.company.com,1433
```

#### Windows Authentication (Windows only)
```bash
-e SQLSERVER_USE_WINDOWS_AUTH=true
# Remove SQLSERVER_USERNAME and SQLSERVER_PASSWORD
```

#### Azure SQL Database
```bash
-e SQLSERVER_SERVER=yourserver.database.windows.net
-e SQLSERVER_DATABASE=yourdatabase
-e SQLSERVER_USERNAME=yourusername@yourserver
-e SQLSERVER_ENCRYPT=yes
```

## 🛠️ Available Tools

The MCP server provides these tools:

| Tool | Description |
|------|-------------|
| `execute_query` | Execute SQL queries and return results |
| `get_table_schema` | Get detailed schema information for a table |
| `list_tables` | List all tables in the database |
| `create_table` | Create new tables |
| `insert_data` | Insert data into tables |
| `test_connection` | Test database connectivity |
| `health_check` | Comprehensive health check |

## 🧪 Testing Your Setup

### 1. Test Connection
```bash
docker run --rm \
  -e SQLSERVER_SERVER=your-server \
  -e SQLSERVER_DATABASE=your-database \
  -e SQLSERVER_USERNAME=your-username \
  -e SQLSERVER_PASSWORD=your-password \
  -e SQLSERVER_DRIVER="ODBC Driver 18 for SQL Server" \
  -e SQLSERVER_ENCRYPT=yes \
  -e SQLSERVER_TRUST_CERTIFICATE=yes \
  yourusername/sqlserver-mcp:latest python test_connection.py
```

### 2. Test All Components
```bash
docker run --rm \
  -e SQLSERVER_SERVER=your-server \
  -e SQLSERVER_DATABASE=your-database \
  -e SQLSERVER_USERNAME=your-username \
  -e SQLSERVER_PASSWORD=your-password \
  yourusername/sqlserver-mcp:latest python test_startup.py
```

## 🔧 Troubleshooting

### Common Issues

#### Connection Refused
- Ensure SQL Server is running and accessible
- Check firewall settings (port 1433)
- Verify SQL Server allows remote connections

#### Authentication Failed
- Verify username and password
- Check if SQL Server Authentication is enabled (mixed mode)
- For Windows auth, ensure container has proper permissions

#### SSL/Certificate Errors
- Try setting `SQLSERVER_ENCRYPT=no` for testing
- Or set `SQLSERVER_TRUST_CERTIFICATE=yes`

#### Docker Issues
- Ensure Docker Desktop is running
- Check if you have permission to run Docker commands
- For local SQL Server, use `host.docker.internal` as server name

### Getting Help

1. **Test connection first**: Use the test commands above
2. **Check SQL Server logs**: Look for connection attempts
3. **Verify network connectivity**: Can you ping the SQL Server?
4. **Test with SSMS**: Can you connect with SQL Server Management Studio?

## 📝 Example Usage in MCP Clients

Once configured, you can use these functions in your MCP client:

```python
# Test connection
mcp_sql_server_test_connection()

# List all tables
mcp_sql_server_list_tables()

# Get table schema
mcp_sql_server_get_table_schema({"table_name": "Users"})

# Execute queries
mcp_sql_server_execute_query({"query": "SELECT TOP 10 * FROM Users"})
```

## 🔒 Security Notes

- **Never hardcode passwords** in configuration files
- **Use environment variables** or secure secret management
- **Enable encryption** for production environments
- **Use least privilege** database accounts
- **Consider network security** (VPNs, private networks)

## 📦 Building from Source

If you want to build the image yourself:

```bash
git clone <repository-url>
cd containerized-mcp-servers/sqlserver-mcp
docker build -t sqlserver-mcp:latest .
```

## 📄 License

[Add your license information here]

## 🤝 Contributing

[Add contribution guidelines here]