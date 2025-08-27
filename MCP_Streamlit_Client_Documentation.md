# MCP Streamlit Client - Code Documentation

## Overview for Principal Data Engineers

This document explains the `mcp_streamlit_client.py` application, which creates a web-based chat interface that connects to multiple Model Context Protocol (MCP) servers. Think of it as a unified dashboard where you can chat with AI while having access to your databases, Databricks, and web search capabilities.

## Architecture Overview

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Streamlit     │    │   Azure OpenAI   │    │  MCP Servers    │
│   Web UI        │◄──►│   GPT Model      │◄──►│  (SQL, Databricks,│
│                 │    │                  │    │   Web Search)   │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

## Key Components Breakdown

### 1. Configuration Management

```python
def load_config():
    """Load configuration from config.yaml file"""
```

**What it does:** Reads your `config/config.yaml` file containing database credentials, API keys, and connection settings.

**Why it matters:** Centralizes all your connection details in one secure location instead of hardcoding them in the application.

**Data Engineer Perspective:** Similar to how you'd manage connection strings in ETL pipelines - keeps sensitive data separate from code.

### 2. MCP Client Class (`SimpleMCPClient`)

This is the core class that manages connections to your data sources through MCP servers.

#### Key Methods:

**`start()`** - Establishes Connection
```python
def start(self):
    """Start the MCP server process (synchronous version)"""
```
- Launches a subprocess running your MCP server (SQL Server, Databricks, etc.)
- Similar to opening a database connection in your ETL jobs
- Handles Windows-specific process management

**`call_tool()`** - Execute Operations
```python
def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
```
- Sends requests to MCP servers (like "list tables", "execute query")
- Think of it as your SQL client sending queries to different databases
- Returns structured JSON responses

**`_read_response()`** - Handle Timeouts
```python
def _read_response(self, timeout: int = 30) -> Optional[Dict[str, Any]]:
```
- Waits for responses with timeout handling
- Critical for Databricks serverless warehouses that may take time to "warm up"
- Uses platform-specific timeout mechanisms (Windows vs Unix)

### 3. Azure OpenAI Integration

```python
class AzureOpenAIClient:
    def chat_with_tools(self, messages: List[Dict], tools: List[Dict]) -> Dict:
```

**What it does:** 
- Connects to your Azure OpenAI service
- Sends chat messages along with available "tools" (your database operations)
- The AI decides when to use tools vs. provide direct answers

**Data Engineer Perspective:** 
- Like having a smart query assistant that knows when to run SQL vs. explain concepts
- The AI can chain multiple operations (e.g., "list tables, then describe the largest one")

### 4. Streamlit UI Components

#### Sidebar Configuration
```python
with st.sidebar:
    st.header("Configuration")
```

**Purpose:** 
- Connection management interface
- Shows status of each MCP server (SQL Server, Databricks, Web Search)
- Allows connecting/disconnecting individual services

**Key Features:**
- **Multi-server support:** Connect to multiple data sources simultaneously
- **Status indicators:** Green/red status for each connection
- **Configuration display:** Shows loaded settings for debugging

#### Main Chat Interface
```python
if prompt := st.chat_input("Ask questions..."):
```

**Flow:**
1. User types a question
2. System collects available tools from connected MCP servers
3. Sends question + tools to Azure OpenAI
4. AI decides whether to use tools or answer directly
5. If tools are used, results are formatted and displayed

### 5. Tool Call Processing

This is the most complex part - here's how it works:

#### Step 1: Tool Collection
```python
# Collect all tools from all connected servers
all_tools = []
for server_name, client in st.session_state.mcp_clients.items():
    # Add server name prefix to avoid conflicts
    tool_copy['name'] = f"{sanitized_server_name}_{tool['name']}"
```

**Why:** Each MCP server might have tools with the same name (e.g., "list_tables"), so we prefix them with the server name.

#### Step 2: AI Decision Making
```python
response = st.session_state.azure_client.chat_with_tools(
    st.session_state.messages, 
    openai_tools
)
```

**What happens:** Azure OpenAI analyzes your question and decides:
- Can I answer this directly? (e.g., "What is a SQL join?")
- Do I need to query a database? (e.g., "Show me all tables")
- Do I need multiple operations? (e.g., "Find the largest table and show its schema")

#### Step 3: Tool Execution
```python
if message.tool_calls:
    for tool_call in message.tool_calls:
        # Extract server name from tool name
        # Call the appropriate MCP server
        tool_response = client.call_tool(original_tool_name, tool_args)
```

**Process:**
1. Parse which server the tool belongs to
2. Send the request to that specific MCP server
3. Get structured JSON response
4. Display results to user

### 6. Error Handling & Resilience

#### Timeout Management
```python
def _read_response(self, timeout: int = 30):
    # Platform-specific timeout handling
    if sys.platform == "win32":
        # Windows polling approach
    else:
        # Unix select approach
```

**Why this matters:** 
- Databricks serverless warehouses can take 30-60 seconds to start
- SQL Server should respond in seconds
- Different timeout strategies prevent the app from hanging

#### Graceful Degradation
```python
if not st.session_state.mcp_clients:
    st.info("💬 No MCP Servers Connected - General chat available")
```

**Benefit:** App still works for general questions even if no databases are connected.

## Session State Management

Streamlit uses session state to maintain data across user interactions:

```python
if "mcp_clients" not in st.session_state:
    st.session_state.mcp_clients = {}  # Store multiple MCP connections
if "messages" not in st.session_state:
    st.session_state.messages = []     # Chat history
```

**Data Engineer Perspective:** Similar to maintaining connection pools in your ETL applications.

## Configuration Structure

Your `config/config.yaml` should look like:

```yaml
azure_openai:
  endpoint: "https://your-endpoint.openai.azure.com"
  api_key: "your-api-key"
  deployment_name: "gpt-4"

sql_server:
  server: "localhost"
  database: "your_database"
  username: "your_user"
  password: "your_password"

databricks:
  server_hostname: "your-workspace.cloud.databricks.com"
  http_path: "/sql/1.0/warehouses/your-warehouse-id"
  access_token: "your-token"
```

## Common Use Cases

### 1. Database Exploration
- "What tables do I have in SQL Server?"
- "Show me the schema of the customers table"
- "How many rows are in each table?"

### 2. Cross-Platform Queries
- "Compare table structures between SQL Server and Databricks"
- "List all my data sources and their status"

### 3. Data Analysis
- "What's the largest table in my database?"
- "Show me recent data in the orders table"

## Troubleshooting Guide

### Connection Issues
- **SQL Server:** Check credentials, network connectivity
- **Databricks:** Verify warehouse is running, token is valid
- **Azure OpenAI:** Confirm endpoint and API key

### Timeout Issues
- **Databricks cold start:** First query may take 1-2 minutes
- **Network latency:** Adjust timeout values if needed

### Tool Call Errors
- Usually indicates MCP server disconnection
- Check server status in sidebar
- Reconnect affected servers

## Security Considerations

1. **Credentials:** Stored in config.yaml (keep this file secure)
2. **Network:** All connections use encrypted protocols
3. **Tokens:** Azure OpenAI and Databricks tokens have expiration dates
4. **Logging:** Sensitive data is not logged to console

## Performance Tips

1. **Connection Reuse:** Keep MCP servers connected during your session
2. **Query Optimization:** Large result sets are displayed as paginated tables
3. **Timeout Tuning:** Adjust based on your warehouse performance
4. **Resource Management:** Close unused connections to free resources

This architecture provides a flexible, scalable way to interact with your data infrastructure through natural language, while maintaining the reliability and security standards expected in enterprise data environments.