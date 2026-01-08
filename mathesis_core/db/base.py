from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional

class VectorStore(ABC):
    """Abstract Base Class for Vector Store operations"""

    @abstractmethod
    def add_documents(self, texts: List[str], metadatas: Optional[List[Dict[str, Any]]] = None) -> None:
        """Add documents to the store"""
        pass

    @abstractmethod
    def similarity_search(self, query: str, k: int = 4) -> List[Dict[str, Any]]:
        """Search for similar documents using only vector similarity"""
        pass

    @abstractmethod
    def hybrid_search(self, query: str, k: int = 4, alpha: float = 0.5) -> List[Dict[str, Any]]:
        """
        Search using both vector and keyword matching (RRF or weighted).
        
        Args:
            query: The search query
            k: Number of results to return
            alpha: Weight for dense (vector) vs sparse (keyword). 1.0 = dense only, 0.0 = sparse only.
                   (Note: Implementation strategies vary, RRF is preferred for stability)
        """
        pass
