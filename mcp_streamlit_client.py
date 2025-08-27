import streamlit as st
import asyncio
import json
import subprocess
import sys
import os
import yaml
from typing import Dict, List, Any, Optional
import openai
from openai import AzureOpenAI
import logging
import threading
import queue
import time
import pandas as pd
import select

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def load_config():
    """Load configuration from config.yaml file"""
    try:
        # Get the directory where this script is located
        script_dir = os.path.dirname(os.path.abspath(__file__))
        config_path = os.path.join(script_dir, "config", "config.yaml")
        
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
            return config
    except FileNotFoundError:
        logger.error(f"Configuration file not found at: {config_path}")
        return None
    except yaml.YAMLError as e:
        logger.error(f"Error parsing YAML configuration file: {str(e)}")
        return None
    except Exception as e:
        logger.error(f"Error loading configuration: {str(e)}")
        return None

class SimpleMCPClient:
    def __init__(self, command: str, args: List[str]):
        self.command = command
        self.args = args
        self.process = None
        self.tools = []
        self.connected = False
        
    def start(self):
        """Start the MCP server process (synchronous version)"""
        try:
            # Check if files exist
            if not os.path.exists(self.command):
                logger.error(f"Python executable not found: {self.command}")
                return False, f"Python executable not found: {self.command}"
            
            if not os.path.exists(self.args[0]):
                logger.error(f"MCP script not found: {self.args[0]}")
                return False, f"MCP script not found: {self.args[0]}"
            
            logger.info(f"Starting MCP server: {self.command} {' '.join(self.args)}")
            
            # Windows-specific subprocess settings
            startupinfo = None
            creationflags = 0
            if sys.platform == "win32":
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                startupinfo.wShowWindow = subprocess.SW_HIDE
                creationflags = subprocess.CREATE_NO_WINDOW
            
            self.process = subprocess.Popen(
                [self.command] + self.args,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,  # Line buffered
                cwd=os.path.dirname(self.args[0]),
                startupinfo=startupinfo,
                creationflags=creationflags
            )
            
            logger.info(f"MCP server started with PID: {self.process.pid}")
            
            # Give it a moment to start
            time.sleep(1)
            
            # Check if process is still running
            if self.process.poll() is not None:
                stderr_output = self.process.stderr.read()
                error_msg = stderr_output if stderr_output else "Unknown error"
                logger.error(f"MCP server exited immediately: {error_msg}")
                return False, f"MCP server exited: {error_msg}"
            
            # Initialize the connection
            success, error = self._initialize()
            if not success:
                return False, error
            
            self.connected = True
            return True, "Connected successfully"
            
        except Exception as e:
            logger.error(f"Failed to start MCP server: {e}")
            return False, f"Failed to start MCP server: {str(e)}"
    
    def _initialize(self):
        """Initialize MCP connection and get available tools"""
        try:
            # Send initialize request
            init_request = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {
                        "roots": {"listChanged": True},
                        "sampling": {}
                    },
                    "clientInfo": {
                        "name": "streamlit-mcp-client",
                        "version": "1.0.0"
                    }
                }
            }
            
            self._send_request(init_request)
            response = self._read_response()
            
            if not response:
                return False, "No response from MCP server during initialization"
            
            if "error" in response:
                return False, f"MCP server error: {response['error']}"
            
            # Send initialized notification
            initialized_notification = {
                "jsonrpc": "2.0",
                "method": "notifications/initialized"
            }
            self._send_request(initialized_notification)
            
            # Get available tools
            success, error = self._get_tools()
            return success, error
            
        except Exception as e:
            logger.error(f"Error during initialization: {e}")
            return False, f"Initialization error: {str(e)}"
    
    def _get_tools(self):
        """Get list of available tools from the MCP server"""
        try:
            tools_request = {
                "jsonrpc": "2.0",
                "id": 2,
                "method": "tools/list"
            }
            
            self._send_request(tools_request)
            response = self._read_response()
            
            if response and "result" in response:
                self.tools = response["result"].get("tools", [])
                logger.info(f"Available tools: {[tool['name'] for tool in self.tools]}")
                return True, None
            else:
                logger.warning("No tools found or invalid response")
                return True, "No tools available"
                
        except Exception as e:
            logger.error(f"Error getting tools: {e}")
            return False, f"Error getting tools: {str(e)}"
    
    def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Call a specific tool with given arguments"""
        if not self.connected or not self.process:
            return {"error": "MCP client not connected"}
        
        request = {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {
                "name": tool_name,
                "arguments": arguments
            }
        }
        
        self._send_request(request)
        response = self._read_response()
        return response
    
    def _send_request(self, request: Dict[str, Any]):
        """Send a JSON-RPC request to the MCP server"""
        if not self.process or not self.process.stdin:
            raise Exception("No process or stdin available")
        
        try:
            # Check if process is still alive
            if self.process.poll() is not None:
                raise Exception("MCP server process has terminated")
            
            message = json.dumps(request) + "\n"
            self.process.stdin.write(message)
            self.process.stdin.flush()
            logger.debug(f"Sent request: {request}")
            
        except Exception as e:
            logger.error(f"Error sending request: {e}")
            raise
    
    def _read_response(self, timeout: int = 30) -> Optional[Dict[str, Any]]:
        """Read a response from the MCP server with simple timeout"""
        if not self.process or not self.process.stdout:
            return {"error": "No process or stdout available"}
        
        try:
            # Check if process is still alive
            if self.process.poll() is not None:
                return {"error": "Process has terminated"}
            
            # Simple blocking read with timeout using select (Unix) or polling (Windows)
            import sys
            if sys.platform == "win32":
                # Windows: use simple readline with basic timeout
                import time
                start_time = time.time()
                while time.time() - start_time < timeout:
                    if self.process.poll() is not None:
                        return {"error": "Process terminated"}
                    
                    # Try to read with a short timeout
                    try:
                        line = self.process.stdout.readline()
                        if line:
                            line = line.strip()
                            if line:
                                try:
                                    response = json.loads(line)
                                    return response
                                except json.JSONDecodeError as e:
                                    logger.error(f"Invalid JSON response: {line}")
                                    return {"error": f"Invalid JSON: {str(e)}"}
                        time.sleep(0.1)  # Small delay to prevent busy waiting
                    except Exception as e:
                        logger.error(f"Error reading line: {e}")
                        return {"error": f"Read error: {str(e)}"}
                
                return {"error": f"Timeout after {timeout} seconds"}
            else:
                # Unix: use select for proper timeout
                import select
                ready, _, _ = select.select([self.process.stdout], [], [], timeout)
                if ready:
                    line = self.process.stdout.readline()
                    if line:
                        line = line.strip()
                        if line:
                            try:
                                response = json.loads(line)
                                return response
                            except json.JSONDecodeError as e:
                                logger.error(f"Invalid JSON response: {line}")
                                return {"error": f"Invalid JSON: {str(e)}"}
                    return {"error": "Empty response"}
                else:
                    return {"error": f"Timeout after {timeout} seconds"}
                    
        except Exception as e:
            logger.error(f"Error reading response: {e}")
            return {"error": f"Error reading response: {str(e)}"}
    
    def close(self):
        """Close the MCP server connection"""
        if self.process:
            try:
                # Close stdin first to signal shutdown
                if self.process.stdin:
                    self.process.stdin.close()
                
                # First try graceful termination
                self.process.terminate()
                
                # Wait up to 5 seconds for graceful shutdown
                try:
                    self.process.wait(timeout=5)
                    logger.info("MCP server terminated gracefully")
                except subprocess.TimeoutExpired:
                    # Force kill if it doesn't terminate gracefully
                    logger.warning("MCP server didn't terminate gracefully, force killing...")
                    self.process.kill()
                    try:
                        self.process.wait(timeout=2)
                        logger.info("MCP server force killed")
                    except subprocess.TimeoutExpired:
                        logger.error("Failed to kill MCP server process")
            except Exception as e:
                logger.error(f"Error closing MCP server: {e}")
            finally:
                self.connected = False
                self.process = None

class AzureOpenAIClient:
    def __init__(self, api_key: str, api_version: str, azure_endpoint: str, deployment_name: str):
        self.client = AzureOpenAI(
            api_key=api_key,
            api_version=api_version,
            azure_endpoint=azure_endpoint
        )
        self.deployment_name = deployment_name
    
    def chat_with_tools(self, messages: List[Dict], tools: List[Dict]) -> Dict:
        """Send chat completion request with available tools"""
        try:
            response = self.client.chat.completions.create(
                model=self.deployment_name,
                messages=messages,
                tools=tools,
                tool_choice="auto"
            )
            return response
        except Exception as e:
            logger.error(f"Error calling Azure OpenAI: {e}")
            return None

def convert_mcp_tools_to_openai_format(mcp_tools: List[Dict]) -> List[Dict]:
    """Convert MCP tools format to OpenAI tools format"""
    openai_tools = []
    for tool in mcp_tools:
        openai_tool = {
            "type": "function",
            "function": {
                "name": tool["name"],
                "description": tool.get("description", ""),
                "parameters": tool.get("inputSchema", {})
            }
        }
        openai_tools.append(openai_tool)
    return openai_tools

def main():
    st.set_page_config(page_title="MCP Client", page_icon="🔗", layout="wide")
    
    st.title("🔗 MCP Client with Azure OpenAI")
    st.write("Simple MCP client to interact with your SQL Server MCP using Azure OpenAI")
    
    # Initialize session state first
    if "mcp_clients" not in st.session_state:
        st.session_state.mcp_clients = {}  # Dictionary to store multiple clients
    if "azure_client" not in st.session_state:
        st.session_state.azure_client = None
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    # Load configuration from config.yaml
    config = load_config()
    
    # Sidebar for configuration
    with st.sidebar:
        st.header("Configuration")
        
        if config:
            st.success("✅ Configuration loaded from config.yaml")
        else:
            st.warning("⚠️ Could not load config.yaml, using manual configuration")
        
        # Azure OpenAI Configuration
        st.subheader("Azure OpenAI")
        
        # Pre-populate from config if available
        default_api_key = config.get('azure_openai', {}).get('api_key', '') if config else ''
        default_endpoint = config.get('azure_openai', {}).get('endpoint', '') if config else ''
        default_api_version = config.get('azure_openai', {}).get('api_version', '2024-02-15-preview') if config else '2024-02-15-preview'
        default_deployment = config.get('azure_openai', {}).get('deployment_name', '') if config else ''
        
        azure_api_key = st.text_input("API Key", value=default_api_key, type="password", key="azure_key")
        azure_endpoint = st.text_input("Azure Endpoint", value=default_endpoint, key="azure_endpoint")
        azure_api_version = st.text_input("API Version", value=default_api_version, key="azure_version")
        deployment_name = st.text_input("Deployment Name", value=default_deployment, key="deployment_name")
        
        # MCP Server Configuration
        st.subheader("MCP Server")
        
        # Get current directory for default paths
        current_dir = os.path.dirname(os.path.abspath(__file__))
        default_python_path = os.path.join(current_dir, "dm_steve", "Scripts", "python.exe")
        
        # MCP Server Configuration
        mcp_server_options = {
            "SQL Server": os.path.join(current_dir, "SQL_MCP.py"),
            "Databricks": os.path.join(current_dir, "Databricks_MCP.py"),
            "Web Search": os.path.join(current_dir, "WebSearch_MCP.py")
        }
        
        mcp_command = st.text_input(
            "Python Executable Path",
            value=default_python_path,
            key="mcp_command"
        )
        
        st.write("**Connect to Multiple MCP Servers:**")
        
        # Show connection status for each server
        for server_name, script_path in mcp_server_options.items():
            col1, col2 = st.columns([3, 1])
            with col1:
                is_connected = server_name in st.session_state.mcp_clients and st.session_state.mcp_clients[server_name].connected
                status = "🟢 Connected" if is_connected else "🔴 Disconnected"
                st.write(f"{server_name}: {status}")
            
            with col2:
                if is_connected:
                    if st.button(f"Disconnect", key=f"disconnect_{server_name}"):
                        st.session_state.mcp_clients[server_name].close()
                        del st.session_state.mcp_clients[server_name]
                        st.rerun()
                else:
                    if st.button(f"Connect", key=f"connect_{server_name}"):
                        with st.spinner(f"Connecting to {server_name}..."):
                            try:
                                client = SimpleMCPClient(mcp_command, [script_path])
                                success, message = client.start()
                                if success:
                                    st.session_state.mcp_clients[server_name] = client
                                    st.success(f"✅ Connected to {server_name}")
                                    st.rerun()
                                else:
                                    st.error(f"❌ Failed to connect to {server_name}: {message}")
                            except Exception as e:
                                st.error(f"❌ Error connecting to {server_name}: {e}")
        
        # Show loaded configuration for debugging
        if config:
            with st.expander("📋 Loaded Configuration"):
                st.json({
                    "Azure OpenAI": {
                        "endpoint": config.get('azure_openai', {}).get('endpoint', 'Not set'),
                        "api_version": config.get('azure_openai', {}).get('api_version', 'Not set'),
                        "deployment_name": config.get('azure_openai', {}).get('deployment_name', 'Not set'),
                        "api_key": "***" if config.get('azure_openai', {}).get('api_key') else 'Not set'
                    },
                    "Paths": {
                        "python_executable": mcp_command,
                        "available_servers": list(mcp_server_options.keys())
                    }
                })
        
        # Clear History Button
        st.subheader("Chat History")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🗑️ Clear History"):
                st.session_state.messages = []
                st.success("Chat history cleared!")
                st.rerun()
        
        with col2:
            message_count = len(st.session_state.messages)
            st.write(f"📝 {message_count} messages")

    
    # Azure OpenAI Connection
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("Initialize Azure OpenAI"):
            if all([azure_api_key, azure_endpoint, deployment_name]):
                try:
                    st.session_state.azure_client = AzureOpenAIClient(
                        azure_api_key, azure_api_version, azure_endpoint, deployment_name
                    )
                    st.success("✅ Azure OpenAI initialized!")
                except Exception as e:
                    st.error(f"❌ Error initializing Azure OpenAI: {e}")
            else:
                st.error("Please provide Azure OpenAI configuration")
    
    with col2:
        if st.session_state.azure_client:
            st.success("🟢 Azure OpenAI Ready")
        else:
            st.error("🔴 Azure OpenAI Not Configured")
    
    # Overall connection status
    connected_servers = len(st.session_state.mcp_clients)
    if connected_servers > 0:
        st.success(f"🟢 {connected_servers} MCP Server(s) Connected - Full functionality available")
    else:
        st.info("💬 No MCP Servers Connected - General chat available, connect servers for database/web tools")
    
    # Show available tools from all connected servers
    if st.session_state.mcp_clients:
        st.subheader("Available MCP Tools")
        for server_name, client in st.session_state.mcp_clients.items():
            if client.connected and client.tools:
                st.write(f"**{server_name} Tools:**")
                for tool in client.tools:
                    with st.expander(f"🔧 {tool['name']} ({server_name})"):
                        st.write(f"**Description:** {tool.get('description', 'No description')}")
                        if 'inputSchema' in tool:
                            st.write("**Parameters:**")
                            st.json(tool['inputSchema'])
    else:
        st.write("No MCP servers connected.")
    
    # Chat interface
    st.subheader("💬 Chat with your SQL Server")
    
    # Display chat messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.write(message["content"])
    
    # Chat input
    if prompt := st.chat_input("Ask questions, or connect MCP servers for database/web search capabilities..."):
        if not st.session_state.azure_client:
            st.error("Please initialize Azure OpenAI first!")
            st.stop()
        
        # Add user message
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.write(prompt)
        
        # Collect all tools from all connected servers (if any)
        all_tools = []
        if st.session_state.mcp_clients:
            for server_name, client in st.session_state.mcp_clients.items():
                if client.connected and client.tools:
                    # Sanitize server name for tool naming (remove spaces and special chars)
                    sanitized_server_name = server_name.replace(" ", "_").replace("-", "_")
                    # Add server name to tool names to avoid conflicts
                    for tool in client.tools:
                        tool_copy = tool.copy()
                        tool_copy['server_name'] = server_name
                        tool_copy['original_name'] = tool['name']
                        tool_copy['name'] = f"{sanitized_server_name}_{tool['name']}"
                        all_tools.append(tool_copy)
        
        # Prepare tools for OpenAI (empty list if no MCP servers connected)
        openai_tools = convert_mcp_tools_to_openai_format(all_tools)
        
        # Get response from Azure OpenAI
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                try:
                    # Show different messages based on MCP availability
                    if st.session_state.mcp_clients:
                        st.write("🤖 Calling Azure OpenAI with MCP tools...")
                    else:
                        st.write("🤖 Calling Azure OpenAI (no MCP servers connected - general chat only)...")
                    
                    response = st.session_state.azure_client.chat_with_tools(
                        st.session_state.messages, 
                        openai_tools
                    )
                    st.write("✅ Got response from Azure OpenAI")
                    
                    if response and response.choices:
                        message = response.choices[0].message
                        
                        # Check if the model wants to call a tool
                        if message.tool_calls:
                            # Check if we have any MCP servers to handle tool calls
                            if not st.session_state.mcp_clients:
                                st.warning("🔧 The AI wanted to use tools, but no MCP servers are connected.")
                                st.info("💡 Connect to MCP servers (SQL Server, Databricks, Web Search) to enable tool functionality.")
                                
                                # Add the assistant's tool call message to conversation (required by OpenAI API)
                                st.session_state.messages.append({
                                    "role": "assistant", 
                                    "content": message.content or "",
                                    "tool_calls": [
                                        {
                                            "id": tc.id,
                                            "type": "function",
                                            "function": {
                                                "name": tc.function.name,
                                                "arguments": tc.function.arguments
                                            }
                                        } for tc in message.tool_calls
                                    ]
                                })
                                
                                # Add tool response messages for each tool call (required by OpenAI API)
                                for tool_call in message.tool_calls:
                                    error_response = {
                                        "error": "No MCP servers connected. Please connect to MCP servers to use tools.",
                                        "available_servers": ["SQL Server", "Databricks", "Web Search"]
                                    }
                                    st.session_state.messages.append({
                                        "role": "tool",
                                        "tool_call_id": tool_call.id,
                                        "content": json.dumps(error_response, indent=2)
                                    })
                                
                                # Now get a follow-up response from the AI to explain the situation
                                try:
                                    follow_up_response = st.session_state.azure_client.chat_with_tools(
                                        st.session_state.messages, 
                                        []  # No tools for follow-up
                                    )
                                    if follow_up_response and follow_up_response.choices:
                                        follow_up_content = follow_up_response.choices[0].message.content
                                        st.write(follow_up_content)
                                        st.session_state.messages.append({"role": "assistant", "content": follow_up_content})
                                    else:
                                        # Fallback response
                                        helpful_response = "I'd like to help you with that, but I need access to MCP servers to perform database queries, web searches, or other tool-based operations. Please connect to the appropriate MCP servers in the sidebar to enable these capabilities."
                                        st.write(helpful_response)
                                        st.session_state.messages.append({"role": "assistant", "content": helpful_response})
                                except Exception as e:
                                    # Fallback response if follow-up fails
                                    helpful_response = "I'd like to help you with that, but I need access to MCP servers to perform database queries, web searches, or other tool-based operations. Please connect to the appropriate MCP servers in the sidebar to enable these capabilities."
                                    st.write(helpful_response)
                                    st.session_state.messages.append({"role": "assistant", "content": helpful_response})
                            else:
                                # Add the assistant's tool call message to conversation
                                st.session_state.messages.append({
                                    "role": "assistant", 
                                    "content": message.content or "",
                                    "tool_calls": [
                                        {
                                            "id": tc.id,
                                            "type": "function",
                                            "function": {
                                                "name": tc.function.name,
                                                "arguments": tc.function.arguments
                                            }
                                        } for tc in message.tool_calls
                                    ]
                                })
                                
                                # Process each tool call and ensure we have matching responses
                                for tool_call in message.tool_calls:
                                    tool_name = tool_call.function.name
                                    tool_args = json.loads(tool_call.function.arguments)
                                    
                                    # Extract server name and original tool name
                                    server_name = None
                                    original_tool_name = tool_name
                                    
                                    # Find which server this tool belongs to by checking the tool name prefix
                                    for orig_server_name in st.session_state.mcp_clients.keys():
                                        sanitized_name = orig_server_name.replace(" ", "_").replace("-", "_")
                                        if tool_name.startswith(f"{sanitized_name}_"):
                                            server_name = orig_server_name
                                            original_tool_name = tool_name[len(f"{sanitized_name}_"):]
                                            break
                                    
                                    # Fallback if no server found
                                    if not server_name and st.session_state.mcp_clients:
                                        server_name = list(st.session_state.mcp_clients.keys())[0]
                                        original_tool_name = tool_name
                                    elif not server_name:
                                        # No MCP servers available at all
                                        st.error(f"❌ Tool '{tool_name}' requires MCP server but none are connected")
                                        tool_response = {"error": "No MCP servers connected"}
                                        continue
                                
                                    st.write(f"🔧 Calling tool: {original_tool_name} on {server_name}")
                                    st.write(f"Arguments: {tool_args}")
                                    
                                    # Call the MCP tool on the appropriate server
                                    if server_name in st.session_state.mcp_clients:
                                        st.write("📡 Sending request to MCP server...")
                                        tool_response = st.session_state.mcp_clients[server_name].call_tool(original_tool_name, tool_args)
                                        st.write("✅ Got response from MCP server")
                                    else:
                                        tool_response = {"error": f"Server {server_name} not connected"}
                                
                                # Process MCP tool response properly
                                if tool_response and "result" in tool_response:
                                    result = tool_response["result"]
                                    
                                    # Handle MCP result format: {"content": [{"type": "text", "text": "..."}], "isError": false}
                                    if isinstance(result, dict) and "content" in result:
                                        content_items = result.get("content", [])
                                        if content_items and len(content_items) > 0:
                                            # Extract the actual text content
                                            text_content = content_items[0].get("text", "")
                                            try:
                                                # Try to parse the text as JSON for better formatting
                                                parsed_content = json.loads(text_content)
                                                content = json.dumps(parsed_content, indent=2)
                                            except json.JSONDecodeError:
                                                # If not JSON, use as-is
                                                content = text_content
                                        else:
                                            content = json.dumps(result, indent=2)
                                    else:
                                        # Fallback to original result
                                        content = json.dumps(result, indent=2)
                                    
                                    st.write("✅ Got results from tool")
                                else:
                                    # Handle error case
                                    error_msg = tool_response.get("error", "Unknown error") if tool_response else "No response"
                                    content = json.dumps({"error": error_msg}, indent=2)
                                    st.error(f"Error calling tool: {error_msg}")
                                
                                # Add tool result to messages for LLM to format
                                tool_result_message = {
                                    "role": "tool",
                                    "tool_call_id": tool_call.id,
                                    "content": content
                                }
                                
                                st.write("🔄 Processing results...")
                                st.session_state.messages.append(tool_result_message)
                            
                                # Show raw results as JSON - simple and fast
                                st.write("**Results:**")
                                for msg in st.session_state.messages[-len(message.tool_calls):]:
                                    if msg.get("role") == "tool":
                                        st.json(msg["content"])
                                
                                # Add a simple summary to conversation
                                summary = f"Tool execution completed. Results displayed above."
                                st.session_state.messages.append({"role": "assistant", "content": summary})
                                
                        else:
                            # Regular response without tool calls
                            content = message.content
                            st.write(content)
                            st.session_state.messages.append({"role": "assistant", "content": content})
                            
                except Exception as e:
                    st.error(f"Error: {e}")
    
    # Cleanup button
    if st.session_state.mcp_clients:
        if st.button("Disconnect All MCP Servers"):
            for client in st.session_state.mcp_clients.values():
                client.close()
            st.session_state.mcp_clients = {}
            st.success("Disconnected from all MCP servers")
            st.rerun()

if __name__ == "__main__":
    main()