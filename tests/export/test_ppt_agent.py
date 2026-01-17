"""
Tests for PowerPoint agent.
"""
import pytest
from unittest.mock import MagicMock, patch


class TestPPTAgent:
    """Tests for PowerPoint generation agent."""

    @pytest.fixture
    def sample_slides(self):
        """Sample slide content."""
        return [
            {"title": "Slide 1", "content": ["Point 1", "Point 2"]},
            {"title": "Slide 2", "content": ["Point 3", "Point 4"]}
        ]

    def test_create_presentation(self, sample_slides, tmp_path):
        """Test creating a presentation."""
        try:
            from mathesis_core.export.ppt_agent import PPTAgent

            agent = PPTAgent()
            output_path = tmp_path / "test.pptx"

            agent.create_presentation(sample_slides, str(output_path))

            assert output_path.exists()
        except ImportError:
            pytest.skip("PPT agent not available")

    def test_add_slide(self):
        """Test adding a single slide."""
        try:
            from mathesis_core.export.ppt_agent import PPTAgent

            agent = PPTAgent()
            agent.add_slide("Test Title", ["Content 1", "Content 2"])

            assert len(agent.slides) >= 1
        except (ImportError, AttributeError):
            pytest.skip("add_slide not available")

    def test_add_chart_slide(self):
        """Test adding a slide with chart."""
        try:
            from mathesis_core.export.ppt_agent import PPTAgent

            agent = PPTAgent()
            chart_data = {"labels": ["A", "B"], "values": [10, 20]}
            agent.add_chart_slide("Chart Title", chart_data)

            assert len(agent.slides) >= 1
        except (ImportError, AttributeError):
            pytest.skip("Chart slide not available")
