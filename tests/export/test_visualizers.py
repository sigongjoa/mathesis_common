"""
Tests for visualization utilities.
"""
import pytest
from unittest.mock import MagicMock, patch


class TestVisualizers:
    """Tests for visualization functions."""

    @pytest.fixture
    def sample_data(self):
        """Sample data for visualization."""
        return {
            "labels": ["Concept A", "Concept B", "Concept C"],
            "values": [0.8, 0.6, 0.4]
        }

    def test_create_bar_chart(self, sample_data, tmp_path):
        """Test creating a bar chart."""
        try:
            from mathesis_core.export.visualizers import create_bar_chart

            output_path = tmp_path / "bar_chart.png"
            create_bar_chart(
                labels=sample_data["labels"],
                values=sample_data["values"],
                output_path=str(output_path)
            )

            assert output_path.exists()
        except ImportError:
            pytest.skip("Visualizers not available")

    def test_create_radar_chart(self, sample_data, tmp_path):
        """Test creating a radar chart."""
        try:
            from mathesis_core.export.visualizers import create_radar_chart

            output_path = tmp_path / "radar_chart.png"
            create_radar_chart(
                labels=sample_data["labels"],
                values=sample_data["values"],
                output_path=str(output_path)
            )

            assert output_path.exists()
        except ImportError:
            pytest.skip("Radar chart not available")

    def test_create_heatmap(self, tmp_path):
        """Test creating a heatmap."""
        try:
            from mathesis_core.export.visualizers import create_heatmap

            data = [[0.1, 0.2], [0.3, 0.4]]
            output_path = tmp_path / "heatmap.png"
            create_heatmap(
                data=data,
                x_labels=["A", "B"],
                y_labels=["X", "Y"],
                output_path=str(output_path)
            )

            assert output_path.exists()
        except ImportError:
            pytest.skip("Heatmap not available")

    def test_create_concept_graph(self, tmp_path):
        """Test creating a concept relationship graph."""
        try:
            from mathesis_core.export.visualizers import create_concept_graph

            nodes = ["Limit", "Derivative", "Integral"]
            edges = [("Limit", "Derivative"), ("Derivative", "Integral")]
            output_path = tmp_path / "concept_graph.png"

            create_concept_graph(
                nodes=nodes,
                edges=edges,
                output_path=str(output_path)
            )

            assert output_path.exists()
        except ImportError:
            pytest.skip("Concept graph not available")
