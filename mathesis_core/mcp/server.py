import asyncio
import logging
import inspect
import json
from typing import Dict, Any, Callable, List, Optional
from datetime import datetime

# Configure logging if not already configured
logger = logging.getLogger("mathesis.common.mcp")

class MCPServerError(Exception):
    """Base exception for MCP server errors"""
    pass

class ToolExecutionError(MCPServerError):
    """Raised when a tool execution fails"""
    pass

class BaseMCPServer:
    """
    Robust Base class for MCP servers in the Mathesis system.
    
    Features:
    - Automatic tool registration
    - standardized request logging
    - Error handling wrapper
    - Health check endpoint
    """

    def __init__(self, name: str, version: str):
        self.name = name
        self.version = version
        self.tools: Dict[str, Callable] = {}
        self.start_time = datetime.utcnow()
        self._register_internal_tools()
        
        # Register system tools
        self.tools["ping"] = self.ping
        self.tools["get_server_info"] = self.get_server_info

    def _register_internal_tools(self):
        """Automatically registers methods with certain signatures or decorators"""
        registered_count = 0
        for name, method in inspect.getmembers(self, predicate=inspect.ismethod):
            # Skip private methods, built-ins, and the run method
            if name.startswith("_") or name in ["handle_tool_call", "run", "ping", "get_server_info"]:
                continue
            
            self.tools[name] = method
            registered_count += 1
        
        logger.info(f"Registered {registered_count} tools for {self.name}")

    async def handle_tool_call(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """
        Dispatches a tool call to the registered method with logging and error handling.
        """
        if tool_name not in self.tools:
            logger.warning(f"Tool not found: {tool_name}")
            raise ValueError(f"Tool not found: {tool_name}")

        method = self.tools[tool_name]
        logger.info(f"Tool Call: {tool_name} | Args: {json.dumps(arguments, default=str)[:200]}")
        
        try:
            if inspect.iscoroutinefunction(method):
                result = await method(**arguments)
            else:
                result = method(**arguments)
            
            logger.info(f"Tool Success: {tool_name}")
            return result
            
        except TypeError as te:
            logger.error(f"Argument mismatch for {tool_name}: {te}")
            raise ToolExecutionError(f"Invalid arguments for {tool_name}: {str(te)}")
        except Exception as e:
            logger.error(f"Error executing tool {tool_name}: {e}", exc_info=True)
            raise ToolExecutionError(f"Execution failed: {str(e)}")

    async def ping(self) -> Dict[str, str]:
        """Simple health check"""
        return {"status": "ok", "timestamp": datetime.utcnow().isoformat()}

    async def get_server_info(self) -> Dict[str, Any]:
        """Returns server metadata"""
        return {
            "name": self.name,
            "version": self.version,
            "uptime_seconds": (datetime.utcnow() - self.start_time).total_seconds(),
            "tools": list(self.tools.keys())
        }

    async def run(self):
        """
        Main entry point. 
        Note: True MCP implementation requires integration with mcp-sdk using stdio/sse.
        This stub simulates the entry point for now.
        """
        logger.info(f"Starting MCP server {self.name} v{self.version}")
        # In a real scenario, this would potentially start a stdio loop or uvicorn
        print(f"MCP Server {self.name} running. Available tools: {list(self.tools.keys())}")
        # Keep alive for testing purposes if run directly
        while True:
            await asyncio.sleep(3600)
