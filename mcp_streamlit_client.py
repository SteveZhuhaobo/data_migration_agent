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
            
            self.process = subprocess.Popen(
                [self.command] + self.args,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd=os.path.dirname(self.args[0])
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
        if self.process and self.process.stdin:
            message = json.dumps(request) + "\n"
            self.process.stdin.write(message)
            self.process.stdin.flush()
    
    def _read_response(self) -> Optional[Dict[str, Any]]:
        """Read a response from the MCP server"""
        if self.process and self.process.stdout:
            try:
                line = self.process.stdout.readline()
                if line:
                    response = json.loads(line.strip())
                    return response
            except Exception as e:
                logger.error(f"Error reading response: {e}")
        return None
    
    def close(self):
        """Close the MCP server connection"""
        if self.process:
            self.process.terminate()
            self.process.wait()
            self.connected = False

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
        
        # MCP Server Selection
        mcp_server_options = {
            "SQL Server": os.path.join(current_dir, "SQL_MCP.py"),
            "Databricks": os.path.join(current_dir, "Databricks_MCP.py"),
            "Web Search": os.path.join(current_dir, "WebSearch_MCP.py")
        }
        
        selected_server = st.selectbox(
            "Select MCP Server",
            options=list(mcp_server_options.keys()),
            key="selected_mcp_server"
        )
        
        mcp_command = st.text_input(
            "Python Executable Path",
            value=default_python_path,
            key="mcp_command"
        )
        mcp_script = st.text_input(
            "MCP Script Path", 
            value=mcp_server_options[selected_server],
            key="mcp_script"
        )
        
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
                        "mcp_script": mcp_script
                    }
                })
    
    # Initialize session state
    if "mcp_client" not in st.session_state:
        st.session_state.mcp_client = None
    if "azure_client" not in st.session_state:
        st.session_state.azure_client = None
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "mcp_connected" not in st.session_state:
        st.session_state.mcp_connected = False
    
    # Connection status
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("Connect to MCP Server"):
            if mcp_command and mcp_script:
                with st.spinner("Connecting to MCP server..."):
                    try:
                        st.session_state.mcp_client = SimpleMCPClient(mcp_command, [mcp_script])
                        success, message = st.session_state.mcp_client.start()
                        if success:
                            st.session_state.mcp_connected = True
                            st.success(f"✅ {message}")
                            st.rerun()
                        else:
                            st.error(f"❌ {message}")
                            # Show additional debug info
                            with st.expander("Debug Information"):
                                st.write(f"**Command:** `{mcp_command}`")
                                st.write(f"**Script:** `{mcp_script}`")
                                st.write(f"**Working Directory:** `{os.path.dirname(mcp_script)}`")
                    except Exception as e:
                        st.error(f"❌ Error: {e}")
                        with st.expander("Debug Information"):
                            st.write(f"**Command:** `{mcp_command}`")
                            st.write(f"**Script:** `{mcp_script}`")
                            st.write(f"**Exception:** `{str(e)}`")
            else:
                st.error("Please provide MCP server configuration")
    
    with col2:
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
    
    # Connection status indicators
    col_status1, col_status2 = st.columns(2)
    with col_status1:
        if st.session_state.mcp_connected:
            st.success("🟢 MCP Server Connected")
        else:
            st.error("🔴 MCP Server Disconnected")
    
    with col_status2:
        if st.session_state.azure_client:
            st.success("🟢 Azure OpenAI Ready")
        else:
            st.error("🔴 Azure OpenAI Not Configured")
    
    # Show available tools if connected
    if st.session_state.mcp_connected and st.session_state.mcp_client:
        st.subheader("Available MCP Tools")
        if st.session_state.mcp_client.tools:
            for tool in st.session_state.mcp_client.tools:
                with st.expander(f"🔧 {tool['name']}"):
                    st.write(f"**Description:** {tool.get('description', 'No description')}")
                    if 'inputSchema' in tool:
                        st.write("**Parameters:**")
                        st.json(tool['inputSchema'])
        else:
            st.write("No tools available or not yet loaded.")
    
    # Chat interface
    st.subheader("💬 Chat with your SQL Server")
    
    # Display chat messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.write(message["content"])
    
    # Chat input
    if prompt := st.chat_input("Ask about your database..."):
        if not st.session_state.mcp_connected:
            st.error("Please connect to MCP server first!")
            st.stop()
        
        if not st.session_state.azure_client:
            st.error("Please initialize Azure OpenAI first!")
            st.stop()
        
        # Add user message
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.write(prompt)
        
        # Prepare tools for OpenAI
        openai_tools = convert_mcp_tools_to_openai_format(st.session_state.mcp_client.tools)
        
        # Get response from Azure OpenAI
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                try:
                    response = st.session_state.azure_client.chat_with_tools(
                        st.session_state.messages, 
                        openai_tools
                    )
                    
                    if response and response.choices:
                        message = response.choices[0].message
                        
                        # Check if the model wants to call a tool
                        if message.tool_calls:
                            for tool_call in message.tool_calls:
                                tool_name = tool_call.function.name
                                tool_args = json.loads(tool_call.function.arguments)
                                
                                st.write(f"🔧 Calling tool: {tool_name}")
                                st.write(f"Arguments: {tool_args}")
                                
                                # Call the MCP tool
                                tool_response = st.session_state.mcp_client.call_tool(tool_name, tool_args)
                                
                                if tool_response and "result" in tool_response:
                                    st.write("**Result:**")
                                    if isinstance(tool_response["result"], dict) and "content" in tool_response["result"]:
                                        for content in tool_response["result"]["content"]:
                                            if content.get("type") == "text":
                                                st.write(content["text"])
                                    else:
                                        st.json(tool_response["result"])
                                    
                                    # Add the tool response to conversation
                                    assistant_message = f"I called {tool_name} and got the following result:\n{json.dumps(tool_response['result'], indent=2)}"
                                    st.session_state.messages.append({"role": "assistant", "content": assistant_message})
                                else:
                                    st.error(f"Error calling tool: {tool_response}")
                        else:
                            # Regular response without tool calls
                            content = message.content
                            st.write(content)
                            st.session_state.messages.append({"role": "assistant", "content": content})
                            
                except Exception as e:
                    st.error(f"Error: {e}")
    
    # Cleanup button
    if st.session_state.mcp_connected:
        if st.button("Disconnect MCP Server"):
            if st.session_state.mcp_client:
                st.session_state.mcp_client.close()
                st.session_state.mcp_client = None
                st.session_state.mcp_connected = False
                st.success("Disconnected from MCP server")
                st.rerun()

if __name__ == "__main__":
    main()