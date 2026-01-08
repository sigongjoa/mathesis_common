import pytest
import asyncio
from node1_logic_engine.backend.app.mcp.server import Node1MCPServer
from unittest.mock import MagicMock, patch

@pytest.mark.asyncio
async def test_node1_mcp_tool_execution():
    # We need to make sure node1 is importable or add it to PYTHONPATH
    # For this test, let's assume PYTHONPATH is root
    server = Node1MCPServer()
    
    # Verify tool registration
    assert "extract_concepts" in server.tools
    assert "get_node1_status" in server.tools
    
    # Mock the extractor to avoid actual LLM calls during integration test
    with patch.object(server.extractor, 'extract') as mock_extract:
        mock_knowledge = MagicMock()
        return_val = {"concepts": ["test_concept"]}
        mock_knowledge.dict.return_value = return_val
        mock_knowledge.model_dump.return_value = return_val
        mock_extract.return_value = mock_knowledge
        
        # Call tool via server handler
        result = await server.handle_tool_call(
            "extract_concepts", 
            {
                "section_heading": "Intro",
                "paper_title": "Paper 1",
                "section_content": "Content..."
            }
        )
        
        assert result == {"concepts": ["test_concept"]}
        mock_extract.assert_called_once()

@pytest.mark.asyncio
async def test_node1_mcp_status():
    server = Node1MCPServer()
    result = await server.handle_tool_call("get_node1_status", {})
    assert result["status"] == "operational"
