# SQL Server MCP Server Usage Guide

## Understanding MCP Server Behavior

The SQL Server MCP Server is designed to work with MCP (Model Context Protocol) clients, not as a standalone application. When you see "Starting SQL Server MCP Server..." and it appears to "hang", this is actually **normal behavior** - the server is waiting for MCP protocol messages from a client.

## Testing the Server

### 1. Connection Test
Test if the server can connect to your SQL Server:
```cmd
sqlserver-mcp-local\test-connection.bat
```

### 2. Component Test  
Test if all server components are working:
```cmd
sqlserver-mcp-local\test-startup.bat
```

### 3. Full Server Test
Run the actual MCP server (will wait for client input):
```cmd
sqlserver-mcp-local\docker-run.bat
```

## Using with MCP Clients

### Option 1: Use with Kiro IDE
1. Add the server to your MCP configuration in `.kiro/settings/mcp.json`:
```json
{
  "mcpServers": {
    "sqlserver-mcp": {
      "command": "docker",
      "args": [
        "run", "--rm", "-i",
        "--name", "sqlserver-mcp-server",
        "-e", "SQLSERVER_SERVER=host.docker.internal",
        "-e", "SQLSERVER_DATABASE=Test_Steve", 
        "-e", "SQLSERVER_USERNAME=steve_test",
        "-e", "SQLSERVER_PASSWORD=SteveTest!23",
        "-e", "SQLSERVER_DRIVER=ODBC Driver 18 for SQL Server",
        "-e", "SQLSERVER_ENCRYPT=no",
        "-e", "SQLSERVER_TRUST_CERTIFICATE=yes",
        "sqlserver-mcp:latest"
      ],
      "disabled": false,
      "autoApprove": ["test_connection", "list_tables", "get_table_schema"]
    }
  }
}
```

### Option 2: Use with Claude Desktop
Add to your Claude Desktop MCP configuration.

### Option 3: Test with Manual MCP Messages
You can send MCP protocol messages manually to test:

1. Run the server:
```cmd
docker run -i --rm -e SQLSERVER_SERVER=host.docker.internal -e SQLSERVER_DATABASE=Test_Steve -e SQLSERVER_USERNAME=steve_test -e SQLSERVER_PASSWORD=SteveTest!23 -e SQLSERVER_DRIVER="ODBC Driver 18 for SQL Server" -e SQLSERVER_ENCRYPT=no -e SQLSERVER_TRUST_CERTIFICATE=yes sqlserver-mcp:latest
```

2. Send initialization message:
```json
{"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"protocolVersion": "2024-11-05", "capabilities": {}, "clientInfo": {"name": "test-client", "version": "1.0.0"}}}
```

3. Send tool list request:
```json
{"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}}
```

## Available Tools

The server provides these tools:
- `execute_query` - Execute SQL queries
- `get_table_schema` - Get table schema information  
- `list_tables` - List all tables in the database
- `create_table` - Create new tables
- `insert_data` - Insert data into tables
- `test_connection` - Test database connectivity
- `health_check` - Comprehensive health check

## Configuration

Update the environment variables in the run scripts:
- `SQLSERVER_SERVER` - SQL Server hostname (use `host.docker.internal` for local SQL Server)
- `SQLSERVER_DATABASE` - Database name
- `SQLSERVER_USERNAME` - SQL Server username
- `SQLSERVER_PASSWORD` - SQL Server password
- `SQLSERVER_DRIVER` - ODBC driver name (use "ODBC Driver 18 for SQL Server")
- `SQLSERVER_ENCRYPT` - Enable encryption (yes/no)
- `SQLSERVER_TRUST_CERTIFICATE` - Trust server certificate (yes/no)

## Troubleshooting

If the connection tests fail:
1. Ensure SQL Server is running and accessible
2. Check SQL Server allows remote connections
3. Verify SQL Server Authentication is enabled (mixed mode)
4. Check Windows Firewall allows connections on port 1433
5. Test connection from host machine first using SSMS

The server "hanging" on startup is normal - it's waiting for MCP client input!