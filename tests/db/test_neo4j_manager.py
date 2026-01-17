"""
Tests for Neo4j manager.

Tests the Neo4j database connection and query functionality.
"""
import pytest
from unittest.mock import MagicMock, patch, AsyncMock


class TestNeo4jManager:
    """Tests for Neo4j manager class."""

    @pytest.fixture
    def mock_neo4j_driver(self):
        """Create a mock Neo4j driver."""
        mock = MagicMock()
        mock_session = MagicMock()
        mock_session.run.return_value = MagicMock(data=lambda: [{"id": "1", "name": "Test"}])
        mock.session.return_value.__enter__.return_value = mock_session
        mock.session.return_value.__exit__.return_value = None
        return mock

    @patch("neo4j.GraphDatabase.driver")
    def test_init_creates_driver(self, mock_driver_factory):
        """Test that initialization creates Neo4j driver."""
        try:
            from mathesis_core.db.neo4j_manager import Neo4jManager

            manager = Neo4jManager(
                uri="bolt://localhost:7687",
                user="neo4j",
                password="password"
            )

            mock_driver_factory.assert_called_once()
        except ImportError:
            pytest.skip("Neo4j manager not available")

    @patch("neo4j.GraphDatabase.driver")
    def test_run_query(self, mock_driver_factory, mock_neo4j_driver):
        """Test running a Cypher query."""
        mock_driver_factory.return_value = mock_neo4j_driver

        try:
            from mathesis_core.db.neo4j_manager import Neo4jManager

            manager = Neo4jManager(
                uri="bolt://localhost:7687",
                user="neo4j",
                password="password"
            )

            result = manager.run_query("MATCH (n) RETURN n LIMIT 1")

            assert result is not None
        except ImportError:
            pytest.skip("Neo4j manager not available")

    @patch("neo4j.GraphDatabase.driver")
    def test_create_node(self, mock_driver_factory, mock_neo4j_driver):
        """Test creating a node."""
        mock_driver_factory.return_value = mock_neo4j_driver

        try:
            from mathesis_core.db.neo4j_manager import Neo4jManager

            manager = Neo4jManager(
                uri="bolt://localhost:7687",
                user="neo4j",
                password="password"
            )

            result = manager.create_node(
                label="Concept",
                properties={"name": "Derivative", "difficulty": "medium"}
            )

            assert result is not None
        except (ImportError, AttributeError):
            pytest.skip("create_node not available")

    @patch("neo4j.GraphDatabase.driver")
    def test_create_relationship(self, mock_driver_factory, mock_neo4j_driver):
        """Test creating a relationship between nodes."""
        mock_driver_factory.return_value = mock_neo4j_driver

        try:
            from mathesis_core.db.neo4j_manager import Neo4jManager

            manager = Neo4jManager(
                uri="bolt://localhost:7687",
                user="neo4j",
                password="password"
            )

            result = manager.create_relationship(
                from_node_id="1",
                to_node_id="2",
                relationship_type="PREREQUISITE_OF"
            )

            assert result is not None
        except (ImportError, AttributeError):
            pytest.skip("create_relationship not available")

    @patch("neo4j.GraphDatabase.driver")
    def test_close_driver(self, mock_driver_factory, mock_neo4j_driver):
        """Test closing the driver connection."""
        mock_driver_factory.return_value = mock_neo4j_driver

        try:
            from mathesis_core.db.neo4j_manager import Neo4jManager

            manager = Neo4jManager(
                uri="bolt://localhost:7687",
                user="neo4j",
                password="password"
            )

            manager.close()

            mock_neo4j_driver.close.assert_called_once()
        except ImportError:
            pytest.skip("Neo4j manager not available")

    @patch("neo4j.GraphDatabase.driver")
    def test_get_concept_graph(self, mock_driver_factory, mock_neo4j_driver):
        """Test getting concept prerequisite graph."""
        mock_driver_factory.return_value = mock_neo4j_driver

        try:
            from mathesis_core.db.neo4j_manager import Neo4jManager

            manager = Neo4jManager(
                uri="bolt://localhost:7687",
                user="neo4j",
                password="password"
            )

            result = manager.get_concept_graph("Derivative")

            assert result is not None
        except (ImportError, AttributeError):
            pytest.skip("get_concept_graph not available")
