import pytest
from unittest.mock import MagicMock, AsyncMock
from mathesis_core.mcp.server import BaseMCPServer

class TestServer(BaseMCPServer):
    def __init__(self):
        super().__init__(name="test-server", version="0.1.0")
    
    async def get_concepts(self, **kwargs):
        return ["concept1", "concept2"]

@pytest.fixture
def server():
    return TestServer()

def test_server_init(server):
    assert server.name == "test-server"
    assert server.version == "0.1.0"
    assert "get_concepts" in server.tools

@pytest.mark.asyncio
async def test_server_call_tool(server):
    # This assumes we have a way to call tools internally for testing
    result = await server.handle_tool_call("get_concepts", {})
    assert result == ["concept1", "concept2"]

@pytest.mark.asyncio
async def test_server_invalid_tool(server):
    with pytest.raises(ValueError, match="Tool not found"):
        await server.handle_tool_call("invalid_tool", {})
