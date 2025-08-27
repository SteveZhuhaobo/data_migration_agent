# Microsoft Fabric MCP Server

A Model Context Protocol (MCP) server that provides integration with Microsoft Fabric, enabling programmatic access to Fabric workspaces, lakehouses, warehouses, and data through standardized MCP tools.

## Features

- **Authentication**: Secure Azure AD authentication using service principals
- **Resource Discovery**: List and explore workspaces, lakehouses, and warehouses
- **SQL Execution**: Execute queries against Fabric resources with proper result formatting
- **Data Management**: Create tables and insert data into Fabric resources
- **Schema Operations**: Get detailed table schema and metadata information
- **Error Handling**: Comprehensive error handling with retry logic and detailed error messages

## Prerequisites

- Python 3.8 or higher
- Microsoft Fabric workspace with appropriate permissions
- Azure AD service principal with Fabric access
- Required Python packages (see fabric_requirements.txt)

## Installation

1. **Install dependencies**:
   ```bash
   pip install -r fabric_requirements.txt
   ```

2. **Set up configuration**:
   - Copy `config/fabric_config.yaml` to `config/config.yaml`
   - Update the configuration with your Azure AD and Fabric settings

3. **Configure Azure AD Service Principal**:
   - Create a service principal in Azure AD
   - Grant appropriate permissions to your Fabric workspace
   - Note down the tenant_id, client_id, and client_secret

## Configuration

Create a `config/config.yaml` file with the following structure:

```yaml
fabric:
  # Required: Azure AD Configuration
  tenant_id: "your-tenant-id-here"
  client_id: "your-client-id-here"
  client_secret: "your-client-secret-here"  # or use FABRIC_CLIENT_SECRET env var
  
  # Optional: Default workspace and resources
  workspace_id: "your-default-workspace-id"
  default_lakehouse: "your-default-lakehouse-id"
  default_warehouse: "your-default-warehouse-id"
  
  # Optional: Connection settings
  timeout: 120
  max_retries: 3
  retry_delay: 5
```

### Environment Variables

For security, you can use environment variables for sensitive information:

```bash
export FABRIC_CLIENT_SECRET="your-client-secret"
```

## Usage

### Running the MCP Server

```bash
python Fabric_MCP.py
```

### Testing the Server

Run the test script to verify basic functionality:

```bash
python test_fabric_mcp.py
```

### Available Tools

The server provides the following MCP tools:

#### Resource Discovery
- `list_workspaces`: List all accessible workspaces
- `list_lakehouses`: List lakehouses in a workspace
- `list_warehouses`: List warehouses in a workspace
- `list_tables`: List tables in a lakehouse or warehouse
- `get_workspace_info`: Get detailed workspace information

#### Query Execution
- `execute_query`: Execute SQL queries against Fabric resources
- `get_table_schema`: Get detailed table schema information
- `describe_table`: Get comprehensive table metadata

#### Data Management
- `create_table`: Create new tables in lakehouses or warehouses
- `insert_data`: Insert data into existing tables

#### Utility Tools
- `ping`: Test server responsiveness
- `test_connection`: Test Fabric connectivity and authentication

### Example Tool Usage

#### List Workspaces
```json
{
  "name": "list_workspaces",
  "arguments": {}
}
```

#### Execute Query
```json
{
  "name": "execute_query",
  "arguments": {
    "query": "SELECT * FROM my_table LIMIT 10",
    "resource_type": "lakehouse",
    "resource_id": "your-lakehouse-id"
  }
}
```

#### Create Table
```json
{
  "name": "create_table",
  "arguments": {
    "table_name": "test_table",
    "columns": ["id INT", "name STRING", "created_date DATE"],
    "resource_type": "lakehouse",
    "resource_id": "your-lakehouse-id"
  }
}
```

## Architecture

The server consists of several key components:

- **Authentication Layer**: Handles Azure AD authentication and token management
- **Fabric API Client**: Manages REST API calls to Microsoft Fabric
- **SQL Execution Engine**: Handles SQL query execution and result formatting
- **MCP Tools**: Implements the various MCP tools for different operations

## Error Handling

The server implements comprehensive error handling:

- **Authentication Errors**: Clear messages for credential issues
- **Resource Errors**: Detailed information about missing or inaccessible resources
- **Query Errors**: SQL syntax and execution error reporting
- **Network Errors**: Retry logic with exponential backoff for transient failures

## Security Considerations

- Store sensitive credentials in environment variables
- Use least-privilege principle for service principal permissions
- All communication uses HTTPS
- No sensitive data is logged

## Troubleshooting

### Common Issues

1. **Authentication Failed**
   - Verify tenant_id, client_id, and client_secret are correct
   - Ensure service principal has proper Fabric permissions
   - Check if client_secret has expired

2. **Resource Not Found**
   - Verify workspace_id, lakehouse_id, or warehouse_id are correct
   - Ensure you have access to the specified resources
   - Check if resources exist in the specified workspace

3. **Connection Timeout**
   - Check network connectivity
   - Increase timeout value in configuration
   - Verify Fabric service availability

### Debug Mode

For debugging, you can modify the logging level in the code or add print statements to trace execution flow.

## Contributing

When contributing to this project:

1. Follow the existing code style and patterns
2. Add appropriate error handling for new features
3. Update documentation for any new tools or configuration options
4. Test thoroughly with real Fabric resources

## License

This project follows the same license as your other MCP servers.

## Related Projects

- [Databricks MCP Server](./Databricks_MCP.py) - Similar functionality for Databricks
- [SQL Server MCP Server](./SQL_MCP.py) - SQL Server integration