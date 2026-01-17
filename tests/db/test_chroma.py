"""
Tests for ChromaHybridStore.

Tests the ChromaDB-backed VectorStore with BM25 hybrid search.
"""
import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from typing import List


class TestChromaHybridStore:
    """Tests for ChromaHybridStore class."""

    @pytest.fixture
    def mock_ollama_client(self):
        """Create a mock OllamaClient."""
        mock = MagicMock()
        mock.embed = MagicMock(return_value=[0.1] * 384)
        return mock

    @pytest.fixture
    def mock_chroma_client(self):
        """Create a mock ChromaDB client."""
        mock = MagicMock()
        mock_collection = MagicMock()
        mock_collection.count.return_value = 0
        mock_collection.get.return_value = {"documents": [], "ids": []}
        mock_collection.add = MagicMock()
        mock_collection.query.return_value = {
            "ids": [["id1", "id2"]],
            "documents": [["doc1", "doc2"]],
            "metadatas": [[{"key": "value1"}, {"key": "value2"}]],
            "distances": [[0.1, 0.2]]
        }
        mock.get_or_create_collection.return_value = mock_collection
        return mock

    @patch("chromadb.PersistentClient")
    def test_init_creates_collection(self, mock_persistent_client, mock_ollama_client, mock_chroma_client):
        """Test that initialization creates a ChromaDB collection."""
        mock_persistent_client.return_value = mock_chroma_client

        from mathesis_core.db.chroma import ChromaHybridStore

        store = ChromaHybridStore(
            collection_name="test_collection",
            ollama_client=mock_ollama_client,
            persist_dir="./test_chroma_db"
        )

        mock_chroma_client.get_or_create_collection.assert_called_once()
        assert store.collection is not None

    @patch("chromadb.PersistentClient")
    def test_add_documents(self, mock_persistent_client, mock_ollama_client, mock_chroma_client):
        """Test adding documents to the store."""
        mock_persistent_client.return_value = mock_chroma_client

        from mathesis_core.db.chroma import ChromaHybridStore

        store = ChromaHybridStore(
            collection_name="test_collection",
            ollama_client=mock_ollama_client
        )

        texts = ["Document 1", "Document 2"]
        metadatas = [{"source": "test1"}, {"source": "test2"}]

        store.add_documents(texts, metadatas)

        store.collection.add.assert_called_once()

    @patch("chromadb.PersistentClient")
    def test_add_empty_documents_does_nothing(self, mock_persistent_client, mock_ollama_client, mock_chroma_client):
        """Test that adding empty documents list does nothing."""
        mock_persistent_client.return_value = mock_chroma_client

        from mathesis_core.db.chroma import ChromaHybridStore

        store = ChromaHybridStore(
            collection_name="test_collection",
            ollama_client=mock_ollama_client
        )

        store.add_documents([])

        store.collection.add.assert_not_called()

    @patch("chromadb.PersistentClient")
    def test_similarity_search(self, mock_persistent_client, mock_ollama_client, mock_chroma_client):
        """Test similarity search returns formatted results."""
        mock_persistent_client.return_value = mock_chroma_client

        from mathesis_core.db.chroma import ChromaHybridStore

        store = ChromaHybridStore(
            collection_name="test_collection",
            ollama_client=mock_ollama_client
        )

        results = store.similarity_search("test query", k=2)

        assert len(results) == 2
        assert results[0]["id"] == "id1"
        assert results[0]["text"] == "doc1"
        assert "metadata" in results[0]
        assert "score" in results[0]

    @patch("chromadb.PersistentClient")
    def test_hybrid_search_falls_back_to_vector_when_no_bm25(self, mock_persistent_client, mock_ollama_client, mock_chroma_client):
        """Test hybrid search falls back to vector search when BM25 not built."""
        mock_persistent_client.return_value = mock_chroma_client

        from mathesis_core.db.chroma import ChromaHybridStore

        store = ChromaHybridStore(
            collection_name="test_collection",
            ollama_client=mock_ollama_client
        )

        # BM25 should not be built on empty collection
        assert store.bm25 is None

        results = store.hybrid_search("test query", k=2)

        # Should fall back to similarity search
        assert len(results) == 2

    @patch("chromadb.PersistentClient")
    def test_refresh_bm25_builds_index_from_documents(self, mock_persistent_client, mock_ollama_client, mock_chroma_client):
        """Test that _refresh_bm25 builds index from existing documents."""
        # Setup mock to return documents
        mock_chroma_client.get_or_create_collection.return_value.count.return_value = 2
        mock_chroma_client.get_or_create_collection.return_value.get.return_value = {
            "documents": ["doc 1 text", "doc 2 text"],
            "ids": ["id1", "id2"]
        }
        mock_persistent_client.return_value = mock_chroma_client

        from mathesis_core.db.chroma import ChromaHybridStore

        store = ChromaHybridStore(
            collection_name="test_collection",
            ollama_client=mock_ollama_client
        )

        assert store.bm25 is not None
        assert len(store.doc_ids_for_bm25) == 2


class TestOllamaEmbeddingFunction:
    """Tests for the Ollama embedding function adapter."""

    def test_embedding_function_calls_ollama(self):
        """Test that embedding function properly calls OllamaClient."""
        mock_client = MagicMock()
        mock_client.embed = MagicMock(return_value=[0.1] * 384)

        with patch("chromadb.PersistentClient"):
            from mathesis_core.db.chroma import ChromaHybridStore

            with patch.object(ChromaHybridStore, "_refresh_bm25"):
                store = ChromaHybridStore(
                    collection_name="test",
                    ollama_client=mock_client
                )

                # Test the embedding function
                embedding_fn = store._create_embedding_fn(mock_client)
                result = embedding_fn(["test text"])

                mock_client.embed.assert_called_with("test text")
                assert len(result) == 1
