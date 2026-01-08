import logging
import os
from neo4j import GraphDatabase, Driver
from typing import Optional

logger = logging.getLogger(__name__)

class Neo4jManager:
    """
    Singleton Manager for Neo4j Connection.
    Shared by Logic Engine (Node 1) and Report Node (Node 5).
    """
    _instance = None
    _driver: Optional[Driver] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Neo4jManager, cls).__new__(cls)
        return cls._instance

    def initialize(self, uri: str = None, username: str = None, password: str = None):
        """Initialize the driver if not already initialized."""
        if self._driver is not None:
            return

        _uri = uri or os.getenv("NEO4J_URI", "bolt://localhost:7687")
        _user = username or os.getenv("NEO4J_USERNAME", "neo4j")
        _pass = password or os.getenv("NEO4J_PASSWORD", "password")

        try:
            self._driver = GraphDatabase.driver(_uri, auth=(_user, _pass))
            self._driver.verify_connectivity()
            logger.info(f"Connected to Neo4j at {_uri}")
        except Exception as e:
            logger.error(f"Failed to connect to Neo4j: {e}")
            self._driver = None

    def get_driver(self) -> Optional[Driver]:
        """Returns the active driver instance."""
        if self._driver is None:
            self.initialize()
        return self._driver

    def close(self):
        if self._driver:
            self._driver.close()
            self._driver = None
            logger.info("Neo4j connection closed")

# Global instance accessor
neo4j_manager = Neo4jManager()
