import pytest
from unittest.mock import MagicMock, AsyncMock
from mathesis_core.llm.clients import OllamaClient

@pytest.fixture
def mock_ollama_lib(mocker):
    return mocker.patch("ollama.Client")

@pytest.fixture
def mock_httpx_client(mocker):
    return mocker.patch("httpx.AsyncClient")

def test_ollama_client_sync_chat(mock_ollama_lib):
    # Setup mock
    mock_instance = mock_ollama_lib.return_value
    mock_instance.chat.return_value = {
        'message': {'content': 'Hello from AI'}
    }
    
    client = OllamaClient(async_mode=False)
    messages = [{"role": "user", "content": "Hi"}]
    
    response = client.chat(messages)
    
    assert response == "Hello from AI"
    mock_instance.chat.assert_called_once()

@pytest.mark.asyncio
async def test_ollama_client_async_chat(mock_httpx_client):
    # Setup mock
    mock_instance = mock_httpx_client.return_value
    mock_response = MagicMock()
    mock_response.json.return_value = {
        'message': {'content': 'Async Hello'}
    }
    mock_response.raise_for_status = MagicMock()
    mock_instance.post = AsyncMock(return_value=mock_response)
    
    client = OllamaClient(async_mode=True)
    messages = [{"role": "user", "content": "Hi"}]
    
    response = await client.async_chat(messages)
    
    assert response == "Async Hello"
    mock_instance.post.assert_called_once()

def test_ollama_client_sync_embed(mock_ollama_lib):
    mocker_lib = MagicMock()
    # Need to mock the top level ollama module for sync embed if it uses it directly 
    # as per the design document sample.
    with pytest.MonkeyPatch().context() as mp:
        mp.setattr("ollama.embeddings", lambda **kwargs: {'embedding': [0.1, 0.2]})
        client = OllamaClient(async_mode=False)
        embedding = client.embed("text")
        assert embedding == [0.1, 0.2]
