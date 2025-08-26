#!/usr/bin/env python3
"""
Web Search MCP Server - A Model Context Protocol server for web search operations
"""

import asyncio
import json
import yaml
import requests
import os
from typing import Dict, Any, List, Optional
from mcp.server import Server
from mcp.types import Resource, Tool, TextContent
import mcp.server.stdio
from bs4 import BeautifulSoup
import urllib.parse
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create the server instance
server = Server("websearch-mcp-server")

# Global config (loaded on startup)
config = None

def load_config():
    """Load configuration files with validation"""
    global config
    
    try:
        # Get the directory where this script is located
        script_dir = os.path.dirname(os.path.abspath(__file__))
        config_path = os.path.join(script_dir, "config", "config.yaml")
        
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
            
        # Set default web search configuration if not provided
        if 'web_search' not in config:
            config['web_search'] = {
                'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'timeout': 10,
                'max_results': 10
            }
            
    except FileNotFoundError:
        # Fallback config for testing
        config = {
            'web_search': {
                'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'timeout': 10,
                'max_results': 10
            }
        }
        logger.warning("Configuration file not found, using default web search config")
    except yaml.YAMLError as e:
        raise Exception(f"Error parsing YAML configuration file: {str(e)}")
    except Exception as e:
        raise Exception(f"Error loading configuration: {str(e)}")

def get_headers():
    """Get HTTP headers for web requests"""
    return {
        'User-Agent': config['web_search']['user_agent'],
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
    }

@server.list_tools()
async def list_tools() -> List[Tool]:
    """List available web search tools"""
    return [
        Tool(
            name="search_web",
            description="Search the web using DuckDuckGo and return results",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query"},
                    "max_results": {"type": "number", "description": "Maximum number of results to return (default: 5)"}
                },
                "required": ["query"]
            }
        ),
        Tool(
            name="get_webpage_content",
            description="Get the text content of a specific webpage",
            inputSchema={
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "URL of the webpage to fetch"},
                    "max_length": {"type": "number", "description": "Maximum length of content to return (default: 5000)"}
                },
                "required": ["url"]
            }
        ),
        Tool(
            name="search_news",
            description="Search for recent news articles",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "News search query"},
                    "max_results": {"type": "number", "description": "Maximum number of news results (default: 5)"}
                },
                "required": ["query"]
            }
        ),
        Tool(
            name="get_page_summary",
            description="Get a summary of a webpage's main content",
            inputSchema={
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "URL of the webpage to summarize"},
                    "max_sentences": {"type": "number", "description": "Maximum number of sentences in summary (default: 3)"}
                },
                "required": ["url"]
            }
        )
    ]

@server.call_tool()
async def call_tool(name: str, arguments: Optional[Dict[str, Any]] = None) -> List[TextContent]:
    """Handle tool calls"""
    if arguments is None:
        arguments = {}
    
    try:
        if name == "search_web":
            result = await search_web(arguments["query"], arguments.get("max_results", 5))
        elif name == "get_webpage_content":
            result = await get_webpage_content(arguments["url"], arguments.get("max_length", 5000))
        elif name == "search_news":
            result = await search_news(arguments["query"], arguments.get("max_results", 5))
        elif name == "get_page_summary":
            result = await get_page_summary(arguments["url"], arguments.get("max_sentences", 3))
        else:
            result = f"Unknown tool: {name}"
        
        return [TextContent(type="text", text=result)]
        
    except Exception as e:
        error_msg = f"Error executing {name}: {str(e)}"
        logger.error(error_msg)
        return [TextContent(type="text", text=json.dumps({
            "success": False,
            "error": error_msg
        }, indent=2))]

async def search_web(query: str, max_results: int = 5) -> str:
    """Search the web using DuckDuckGo"""
    try:
        # DuckDuckGo Instant Answer API
        search_url = "https://api.duckduckgo.com/"
        params = {
            'q': query,
            'format': 'json',
            'no_html': '1',
            'skip_disambig': '1'
        }
        
        response = requests.get(
            search_url, 
            params=params, 
            headers=get_headers(),
            timeout=config['web_search']['timeout']
        )
        response.raise_for_status()
        
        data = response.json()
        
        results = []
        
        # Get instant answer if available
        if data.get('Abstract'):
            results.append({
                "type": "instant_answer",
                "title": data.get('Heading', 'Instant Answer'),
                "content": data.get('Abstract'),
                "source": data.get('AbstractSource', 'DuckDuckGo'),
                "url": data.get('AbstractURL', '')
            })
        
        # Get related topics
        if data.get('RelatedTopics'):
            for i, topic in enumerate(data['RelatedTopics'][:max_results]):
                if isinstance(topic, dict) and 'Text' in topic:
                    results.append({
                        "type": "related_topic",
                        "title": topic.get('Text', '').split(' - ')[0] if ' - ' in topic.get('Text', '') else 'Related Topic',
                        "content": topic.get('Text', ''),
                        "url": topic.get('FirstURL', '')
                    })
        
        # If no results from DuckDuckGo API, try web scraping approach
        if not results:
            results = await scrape_search_results(query, max_results)
        
        return json.dumps({
            "success": True,
            "query": query,
            "results": results[:max_results],
            "total_results": len(results)
        }, indent=2)
        
    except Exception as e:
        logger.error(f"Error in web search: {e}")
        return json.dumps({
            "success": False,
            "error": f"Web search failed: {str(e)}"
        }, indent=2)

async def scrape_search_results(query: str, max_results: int) -> List[Dict]:
    """Fallback method to scrape search results"""
    try:
        # Use DuckDuckGo HTML search as fallback
        search_url = "https://duckduckgo.com/html/"
        params = {'q': query}
        
        response = requests.get(
            search_url,
            params=params,
            headers=get_headers(),
            timeout=config['web_search']['timeout']
        )
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        results = []
        
        # Find search result elements
        for result_div in soup.find_all('div', class_='result')[:max_results]:
            title_elem = result_div.find('a', class_='result__a')
            snippet_elem = result_div.find('a', class_='result__snippet')
            
            if title_elem:
                title = title_elem.get_text(strip=True)
                url = title_elem.get('href', '')
                snippet = snippet_elem.get_text(strip=True) if snippet_elem else ''
                
                results.append({
                    "type": "search_result",
                    "title": title,
                    "content": snippet,
                    "url": url
                })
        
        return results
        
    except Exception as e:
        logger.error(f"Error in scraping search results: {e}")
        return []

async def get_webpage_content(url: str, max_length: int = 5000) -> str:
    """Get the text content of a webpage"""
    try:
        response = requests.get(
            url,
            headers=get_headers(),
            timeout=config['web_search']['timeout']
        )
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.decompose()
        
        # Get text content
        text = soup.get_text()
        
        # Clean up text
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = ' '.join(chunk for chunk in chunks if chunk)
        
        # Truncate if too long
        if len(text) > max_length:
            text = text[:max_length] + "..."
        
        return json.dumps({
            "success": True,
            "url": url,
            "content": text,
            "length": len(text)
        }, indent=2)
        
    except Exception as e:
        logger.error(f"Error fetching webpage content: {e}")
        return json.dumps({
            "success": False,
            "error": f"Failed to fetch webpage: {str(e)}"
        }, indent=2)

async def search_news(query: str, max_results: int = 5) -> str:
    """Search for recent news articles"""
    try:
        # Use DuckDuckGo news search
        search_url = "https://duckduckgo.com/"
        params = {
            'q': f"{query} site:news.google.com OR site:bbc.com OR site:cnn.com OR site:reuters.com",
            'iar': 'news'
        }
        
        response = requests.get(
            search_url,
            params=params,
            headers=get_headers(),
            timeout=config['web_search']['timeout']
        )
        response.raise_for_status()
        
        # For now, return a simplified news search
        # In a production environment, you might want to use a proper news API
        results = await scrape_search_results(f"{query} news", max_results)
        
        return json.dumps({
            "success": True,
            "query": query,
            "news_results": results,
            "total_results": len(results)
        }, indent=2)
        
    except Exception as e:
        logger.error(f"Error in news search: {e}")
        return json.dumps({
            "success": False,
            "error": f"News search failed: {str(e)}"
        }, indent=2)

async def get_page_summary(url: str, max_sentences: int = 3) -> str:
    """Get a summary of a webpage's main content"""
    try:
        # First get the full content
        content_result = await get_webpage_content(url, 10000)
        content_data = json.loads(content_result)
        
        if not content_data.get("success"):
            return content_result
        
        text = content_data["content"]
        
        # Simple sentence extraction (first few sentences)
        sentences = text.split('. ')
        summary_sentences = sentences[:max_sentences]
        summary = '. '.join(summary_sentences)
        
        if not summary.endswith('.'):
            summary += '.'
        
        return json.dumps({
            "success": True,
            "url": url,
            "summary": summary,
            "sentences_count": len(summary_sentences)
        }, indent=2)
        
    except Exception as e:
        logger.error(f"Error creating page summary: {e}")
        return json.dumps({
            "success": False,
            "error": f"Failed to create summary: {str(e)}"
        }, indent=2)

async def main():
    """Main server entry point"""
    # Load configuration
    load_config()
    
    logger.info("Web Search MCP Server starting...")
    
    # Run the server
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options()
        )

if __name__ == "__main__":
    asyncio.run(main())