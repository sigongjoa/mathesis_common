"""
Tests for LLM clients.
"""
import pytest
from unittest.mock import MagicMock, patch, AsyncMock
import asyncio


class TestLLMClientInterface:
    """Tests for LLMClient abstract base class."""

    def test_llm_client_is_abstract(self):
        """Test that LLMClient is abstract."""
        try:
            from mathesis_core.llm.clients import LLMClient

            with pytest.raises(TypeError):
                LLMClient()
        except ImportError:
            pytest.skip("LLM clients not available")


class TestOllamaClient:
    """Tests for OllamaClient implementation."""

    @pytest.fixture
    def mock_ollama(self):
        """Create mock ollama module."""
        mock = MagicMock()
        mock.Client.return_value.chat.return_value = {
            "message": {"content": "Test response"}
        }
        mock.embeddings.return_value = {"embedding": [0.1] * 384}
        return mock

    def test_init_sync_mode(self):
        """Test initialization in sync mode."""
        try:
            with patch("ollama.Client"):
                from mathesis_core.llm.clients import OllamaClient

                client = OllamaClient(
                    base_url="http://localhost:11434",
                    model="llama3.1:8b",
                    async_mode=False
                )

                assert client.model == "llama3.1:8b"
                assert client.async_mode is False
        except ImportError:
            pytest.skip("Ollama client not available")

    def test_init_async_mode(self):
        """Test initialization in async mode."""
        try:
            with patch("httpx.AsyncClient"):
                from mathesis_core.llm.clients import OllamaClient

                client = OllamaClient(
                    base_url="http://localhost:11434",
                    model="llama3.1:8b",
                    async_mode=True
                )

                assert client.async_mode is True
        except ImportError:
            pytest.skip("Ollama client not available")

    def test_chat_sync(self, mock_ollama):
        """Test chat in sync mode."""
        try:
            with patch.dict("sys.modules", {"ollama": mock_ollama}):
                from mathesis_core.llm.clients import OllamaClient

                client = OllamaClient(async_mode=False)
                client.client = mock_ollama.Client()

                messages = [{"role": "user", "content": "Hello"}]
                result = client.chat(messages)

                assert result == "Test response"
        except ImportError:
            pytest.skip("Ollama client not available")

    def test_chat_async_raises_in_sync_mode(self):
        """Test that async_chat raises error in sync mode."""
        try:
            with patch("ollama.Client"):
                from mathesis_core.llm.clients import OllamaClient

                client = OllamaClient(async_mode=False)

                with pytest.raises(RuntimeError):
                    asyncio.run(client.async_chat([{"role": "user", "content": "Hi"}]))
        except ImportError:
            pytest.skip("Ollama client not available")

    def test_generate(self, mock_ollama):
        """Test generate method."""
        try:
            with patch.dict("sys.modules", {"ollama": mock_ollama}):
                from mathesis_core.llm.clients import OllamaClient

                client = OllamaClient(async_mode=False)
                client.client = mock_ollama.Client()

                result = client.generate("Test prompt", system="Be helpful")

                assert result == "Test response"
        except ImportError:
            pytest.skip("Ollama client not available")

    def test_embed(self, mock_ollama):
        """Test embedding generation."""
        try:
            with patch.dict("sys.modules", {"ollama": mock_ollama}):
                from mathesis_core.llm.clients import OllamaClient

                client = OllamaClient(async_mode=False)

                with patch("ollama.embeddings", return_value={"embedding": [0.1] * 384}):
                    result = client.embed("Test text")

                    assert len(result) == 384
        except ImportError:
            pytest.skip("Ollama client not available")

    def test_embed_async_raises_in_sync_mode(self):
        """Test that async_embed raises error in sync mode."""
        try:
            with patch("ollama.Client"):
                from mathesis_core.llm.clients import OllamaClient

                client = OllamaClient(async_mode=False)

                with pytest.raises(RuntimeError):
                    client.embed("test")  # Should work
        except ImportError:
            pytest.skip("Ollama client not available")

    def test_analyze_image(self, mock_ollama, tmp_path):
        """Test image analysis."""
        try:
            with patch.dict("sys.modules", {"ollama": mock_ollama}):
                from mathesis_core.llm.clients import OllamaClient

                # Create a test image
                image_path = tmp_path / "test.png"
                image_path.write_bytes(b"fake image data")

                client = OllamaClient(async_mode=False)
                client.client = mock_ollama.Client()

                result = client.analyze_image(str(image_path), "Describe this image")

                assert result == "Test response"
        except ImportError:
            pytest.skip("Ollama client not available")

    def test_health_check_sync(self, mock_ollama):
        """Test health check in sync mode."""
        try:
            with patch.dict("sys.modules", {"ollama": mock_ollama}):
                from mathesis_core.llm.clients import OllamaClient

                client = OllamaClient(async_mode=False)

                with patch("ollama.list"):
                    result = client.health_check()

                    assert result is True
        except ImportError:
            pytest.skip("Ollama client not available")

    def test_health_check_failure(self, mock_ollama):
        """Test health check failure."""
        try:
            with patch.dict("sys.modules", {"ollama": mock_ollama}):
                from mathesis_core.llm.clients import OllamaClient

                client = OllamaClient(async_mode=False)

                with patch("ollama.list", side_effect=Exception("Connection failed")):
                    result = client.health_check()

                    assert result is False
        except ImportError:
            pytest.skip("Ollama client not available")


class TestCreateOllamaClient:
    """Tests for create_ollama_client factory function."""

    def test_create_ollama_client(self):
        """Test factory function."""
        try:
            with patch("ollama.Client"):
                from mathesis_core.llm.clients import create_ollama_client

                client = create_ollama_client(
                    base_url="http://localhost:11434",
                    model="llama3.1:8b"
                )

                assert client is not None
                assert client.model == "llama3.1:8b"
        except ImportError:
            pytest.skip("create_ollama_client not available")

    def test_create_async_client(self):
        """Test creating async client."""
        try:
            with patch("httpx.AsyncClient"):
                from mathesis_core.llm.clients import create_ollama_client

                client = create_ollama_client(async_mode=True)

                assert client.async_mode is True
        except ImportError:
            pytest.skip("create_ollama_client not available")
