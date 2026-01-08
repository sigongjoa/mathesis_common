import chromadb
from chromadb.config import Settings
from chromadb.api import ClientAPI
from chromadb.utils import embedding_functions
from rank_bm25 import BM25Okapi
import numpy as np
from typing import List, Dict, Any, Optional
import logging
from pathlib import Path

from .base import VectorStore
from ..llm.clients import OllamaClient

logger = logging.getLogger(__name__)

class ChromaHybridStore(VectorStore):
    """
    ChromaDB-backed VectorStore with in-memory BM25 support for Hybrid Search.
    Uses Reciprocal Rank Fusion (RRF) to combine results.
    """

    def __init__(
        self, 
        collection_name: str, 
        ollama_client: OllamaClient,
        persist_dir: str = "./chroma_db"
    ):
        self.client = chromadb.PersistentClient(path=persist_dir)
        
        # wrapped embedding function for Chroma
        self.embedding_fn = self._create_embedding_fn(ollama_client)
        
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            embedding_function=self.embedding_fn,
            metadata={"hnsw:space": "cosine"}
        )
        
        self.bm25: Optional[BM25Okapi] = None
        self.doc_ids_for_bm25: List[str] = []
        self.docs_for_bm25: List[str] = [] # mirroring doc_ids
        
        # Try to load existing data for BM25
        self._refresh_bm25()

    def _create_embedding_fn(self, ollama_client: OllamaClient):
        """Adapter for OllamaClient to be used by Chroma"""
        class OllamaEF(embedding_functions.EmbeddingFunction):
            def __call__(self, input: chromadb.Documents) -> chromadb.Embeddings:
                # Batch embedding support could be added to OllamaClient, 
                # but currently it's single item. We'll loop for safety.
                # If OllamaClient had batch support, we'd use it.
                embeddings = []
                for text in input:
                    embeddings.append(ollama_client.embed(text))
                return embeddings
        return OllamaEF()

    def _refresh_bm25(self):
        """Load all documents from collection to build BM25 index"""
        try:
            # Check count first
            count = self.collection.count()
            if count == 0:
                logger.info("Collection is empty. BM25 not built.")
                return

            # Fetch all documents
            result = self.collection.get()
            if result and result['documents']:
                self.docs_for_bm25 = result['documents']
                self.doc_ids_for_bm25 = result['ids']
                
                # Tokenize (simple whitespace for now, can be improved for Korean)
                tokenized_corpus = [doc.split(" ") for doc in self.docs_for_bm25]
                self.bm25 = BM25Okapi(tokenized_corpus)
                logger.info(f"BM25 index built with {count} documents.")
        except Exception as e:
            logger.error(f"Failed to refresh BM25: {e}")

    def add_documents(self, texts: List[str], metadatas: Optional[List[Dict[str, Any]]] = None) -> None:
        if not texts:
            return
            
        ids = [str(hash(text)) for text in texts] # Simple hash ID, usually UUID is better
        # Use UUIDs if not provided? Hash is deterministic which is good for avoiding dupes
        import uuid
        ids = [str(uuid.uuid4()) for _ in texts]

        # Add to Chroma
        self.collection.add(
            documents=texts,
            metadatas=metadatas,
            ids=ids
        )
        
        # Update BM25 immediately (incremental update is hard for BM25, so we rebuild or append)
        # BM25Okapi is static. We must rebuild or use a variant. 
        # For simplicity in this scale, we rebuild or just warn.
        # Let's perform a lightweight refresh.
        self._refresh_bm25()

    def similarity_search(self, query: str, k: int = 4) -> List[Dict[str, Any]]:
        results = self.collection.query(
            query_texts=[query],
            n_results=k
        )
        
        output = []
        if results['ids']:
            for i in range(len(results['ids'][0])):
                output.append({
                    "id": results['ids'][0][i],
                    "text": results['documents'][0][i],
                    "metadata": results['metadatas'][0][i] if results['metadatas'] else {},
                    "score": results['distances'][0][i] if results['distances'] else 0.0
                })
        return output

    def hybrid_search(self, query: str, k: int = 4, alpha: float = 0.5) -> List[Dict[str, Any]]:
        """
        Implements Reciprocal Rank Fusion (RRF).
        Alpha is ignored in RRF logic usually (k constant is used), 
        but kept for interface compatibility if we switch to weighted sum.
        """
        if not self.bm25:
             # Fallback to vector search if BM25 not ready
             return self.similarity_search(query, k)

        # 1. Vector Search
        vector_results = self.similarity_search(query, k=k*2) # Fetch more for fusion
        
        # 2. Keyword Search (BM25)
        tokenized_query = query.split(" ")
        bm25_scores = self.bm25.get_scores(tokenized_query)
        # Get top k indices
        top_n = min(len(bm25_scores), k*2)
        top_indices = np.argsort(bm25_scores)[::-1][:top_n]
        
        bm25_results = []
        for idx in top_indices:
            bm25_results.append({
                "id": self.doc_ids_for_bm25[idx],
                "text": self.docs_for_bm25[idx],
                "score": bm25_scores[idx]
            })

        # 3. RRF Fusion
        # RRF Score = 1 / (k + rank)
        rrf_k = 60
        doc_scores = {}
        doc_map = {} # Store full doc content to return

        # Process Vector Results
        for rank, item in enumerate(vector_results):
            doc_id = item['id']
            doc_map[doc_id] = item
            doc_scores[doc_id] = doc_scores.get(doc_id, 0) + (1 / (rrf_k + rank + 1))

        # Process BM25 Results
        for rank, item in enumerate(bm25_results):
            doc_id = item['id']
            if doc_id not in doc_map:
                # We need to fetch metadata for BM25-only hits if they weren't in vector hits
                # But since we have the index, we can probably construct it or fetch from DB by ID.
                # For efficiency/simplicity, we might skip or do a fetch.
                # Let's see if we have metadata in memory... we didn't store it in _refresh_bm25
                # So we must fetch from Chroma by ID.
                try:
                    # Get from DB is slow used in loop. 
                    # Optimization: Collect missing IDs and fetch once.
                    pass 
                except:
                    pass
            
            # For now, if it's not in doc_map (vector results), we might miss metadata.
            # Fix: let's do a bulk fetch for missing IDs after scoring.
            doc_scores[doc_id] = doc_scores.get(doc_id, 0) + (1 / (rrf_k + rank + 1))

        # Sort by RRF score
        sorted_ids = sorted(doc_scores.keys(), key=lambda x: doc_scores[x], reverse=True)[:k]
        
        # Fetch details for final verification/metadata
        final_results = []
        ids_to_fetch = [did for did in sorted_ids if did not in doc_map]
        
        fetched_docs = {}
        if ids_to_fetch:
            # Batch get
            resp = self.collection.get(ids=ids_to_fetch)
            if resp['ids']:
                for i, did in enumerate(resp['ids']):
                    fetched_docs[did] = {
                        "id": did,
                        "text": resp['documents'][i],
                        "metadata": resp['metadatas'][i]
                    }

        for did in sorted_ids:
            if did in doc_map:
                final_results.append(doc_map[did])
            elif did in fetched_docs:
                final_results.append(fetched_docs[did])
                
        return final_results
