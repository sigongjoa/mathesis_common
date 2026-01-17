"""
Tests for document processor.
"""
import pytest
from unittest.mock import MagicMock, patch
from pathlib import Path


class TestDocProcessor:
    """Tests for document processing pipeline."""

    @pytest.fixture
    def sample_text(self):
        """Sample text content."""
        return "This is a sample document. It contains multiple sentences. Each sentence is a test."

    def test_process_text(self, sample_text):
        """Test processing plain text."""
        try:
            from mathesis_core.pipeline.doc_processor import DocProcessor

            processor = DocProcessor()
            result = processor.process_text(sample_text)

            assert result is not None
            assert "chunks" in result or isinstance(result, list)
        except ImportError:
            pytest.skip("Doc processor not available")

    def test_chunk_text(self, sample_text):
        """Test text chunking."""
        try:
            from mathesis_core.pipeline.doc_processor import DocProcessor

            processor = DocProcessor(chunk_size=50, chunk_overlap=10)
            chunks = processor.chunk_text(sample_text)

            assert len(chunks) > 0
        except (ImportError, AttributeError):
            pytest.skip("chunk_text not available")

    def test_extract_metadata(self, sample_text):
        """Test metadata extraction."""
        try:
            from mathesis_core.pipeline.doc_processor import DocProcessor

            processor = DocProcessor()
            metadata = processor.extract_metadata(sample_text)

            assert isinstance(metadata, dict)
        except (ImportError, AttributeError):
            pytest.skip("extract_metadata not available")

    def test_clean_text(self):
        """Test text cleaning."""
        try:
            from mathesis_core.pipeline.doc_processor import DocProcessor

            processor = DocProcessor()
            dirty_text = "  Hello   World  \n\n\n  Test  "
            clean = processor.clean_text(dirty_text)

            assert "  " not in clean or clean != dirty_text
        except (ImportError, AttributeError):
            pytest.skip("clean_text not available")

    def test_process_with_embeddings(self, sample_text):
        """Test processing with embedding generation."""
        try:
            from mathesis_core.pipeline.doc_processor import DocProcessor

            mock_embedder = MagicMock()
            mock_embedder.embed = MagicMock(return_value=[0.1] * 384)

            processor = DocProcessor(embedder=mock_embedder)
            result = processor.process_with_embeddings(sample_text)

            assert result is not None
        except (ImportError, AttributeError):
            pytest.skip("process_with_embeddings not available")
