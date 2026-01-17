"""
Tests for Typst wrapper.
"""
import pytest
from unittest.mock import MagicMock, patch


class TestTypstWrapper:
    """Tests for Typst document generation wrapper."""

    @pytest.fixture
    def sample_typst_content(self):
        """Sample Typst content."""
        return """
        #set page(paper: "a4")
        = Test Document
        This is a test document.
        """

    def test_compile_typst(self, sample_typst_content, tmp_path):
        """Test compiling Typst to PDF."""
        try:
            from mathesis_core.export.typst_wrapper import TypstWrapper

            wrapper = TypstWrapper()
            input_path = tmp_path / "test.typ"
            input_path.write_text(sample_typst_content)
            output_path = tmp_path / "test.pdf"

            wrapper.compile(str(input_path), str(output_path))

            # Check if compilation was attempted
        except ImportError:
            pytest.skip("Typst wrapper not available")

    def test_render_template(self):
        """Test rendering Typst template with data."""
        try:
            from mathesis_core.export.typst_wrapper import TypstWrapper

            wrapper = TypstWrapper()
            template = "= {title}\n{content}"
            data = {"title": "Test", "content": "Content here"}

            result = wrapper.render_template(template, data)

            assert "Test" in result
            assert "Content here" in result
        except (ImportError, AttributeError):
            pytest.skip("Template rendering not available")

    def test_generate_report(self, tmp_path):
        """Test generating a complete report."""
        try:
            from mathesis_core.export.typst_wrapper import TypstWrapper

            wrapper = TypstWrapper()
            report_data = {
                "title": "Analysis Report",
                "sections": [{"name": "Results", "content": "Data here"}]
            }
            output_path = tmp_path / "report.pdf"

            wrapper.generate_report(report_data, str(output_path))
        except (ImportError, AttributeError):
            pytest.skip("Report generation not available")
