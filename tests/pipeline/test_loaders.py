"""
Tests for document loaders.
"""
import pytest
from unittest.mock import MagicMock, patch
from pathlib import Path


class TestDocumentLoaders:
    """Tests for document loading utilities."""

    @pytest.fixture
    def sample_pdf_path(self, tmp_path):
        """Create a sample PDF path (mock)."""
        pdf_path = tmp_path / "test.pdf"
        pdf_path.write_bytes(b"%PDF-1.4 test content")
        return pdf_path

    @pytest.fixture
    def sample_hwp_path(self, tmp_path):
        """Create a sample HWP path (mock)."""
        hwp_path = tmp_path / "test.hwp"
        hwp_path.write_bytes(b"HWP test content")
        return hwp_path

    def test_load_pdf(self, sample_pdf_path):
        """Test loading PDF document."""
        try:
            from mathesis_core.pipeline.loaders import load_pdf

            with patch("pypdf.PdfReader") as mock_reader:
                mock_page = MagicMock()
                mock_page.extract_text.return_value = "Test content"
                mock_reader.return_value.pages = [mock_page]

                result = load_pdf(str(sample_pdf_path))

                assert result is not None
        except ImportError:
            pytest.skip("PDF loader not available")

    def test_load_hwp(self, sample_hwp_path):
        """Test loading HWP document."""
        try:
            from mathesis_core.pipeline.loaders import load_hwp

            with patch("olefile.OleFileIO") as mock_ole:
                mock_ole.return_value.openstream.return_value.read.return_value = b"content"

                result = load_hwp(str(sample_hwp_path))

                assert result is not None
        except ImportError:
            pytest.skip("HWP loader not available")

    def test_load_text(self, tmp_path):
        """Test loading plain text document."""
        try:
            from mathesis_core.pipeline.loaders import load_text

            text_path = tmp_path / "test.txt"
            text_path.write_text("Test content here")

            result = load_text(str(text_path))

            assert result == "Test content here"
        except ImportError:
            pytest.skip("Text loader not available")

    def test_load_document_auto_detect(self, sample_pdf_path):
        """Test auto-detecting document type."""
        try:
            from mathesis_core.pipeline.loaders import load_document

            with patch("mathesis_core.pipeline.loaders.load_pdf") as mock_load:
                mock_load.return_value = "PDF content"

                result = load_document(str(sample_pdf_path))

                mock_load.assert_called_once()
        except ImportError:
            pytest.skip("Auto loader not available")

    def test_load_unsupported_format(self, tmp_path):
        """Test handling unsupported format."""
        try:
            from mathesis_core.pipeline.loaders import load_document

            unsupported_path = tmp_path / "test.xyz"
            unsupported_path.write_text("content")

            with pytest.raises((ValueError, NotImplementedError)):
                load_document(str(unsupported_path))
        except ImportError:
            pytest.skip("Loader not available")
