import chromadb
from chromadb.config import Settings
from chromadb.utils import embedding_functions
import numpy as np
from typing import List, Dict, Any, Optional
import logging
import json

from .base import VectorStore
from ..llm.clients import OllamaClient
from .korean_tokenizer import KoreanBM25

logger = logging.getLogger(__name__)

class HierarchicalChromaStore(VectorStore):
    """
    Parent-Child 관계를 지원하는 계층적 ChromaDB Store

    구조:
    - child_collection: 작은 청크 (테이블, 섹션 일부) - 검색용
    - parent_collection: 큰 문맥 (전체 섹션) - 생성용
    - BM25: 한국어 키워드 검색
    """

    def __init__(
        self,
        collection_prefix: str,
        ollama_client: OllamaClient,
        persist_dir: str = "./chroma_hierarchical"
    ):
        self.client = chromadb.PersistentClient(path=persist_dir)
        self.embedding_fn = self._create_embedding_fn(ollama_client)

        # Child Collection (검색용)
        self.child_collection = self.client.get_or_create_collection(
            name=f"{collection_prefix}_child",
            embedding_function=self.embedding_fn,
            metadata={"hnsw:space": "cosine", "description": "Small chunks for precise retrieval"}
        )

        # Parent Collection (생성용)
        self.parent_collection = self.client.get_or_create_collection(
            name=f"{collection_prefix}_parent",
            embedding_function=self.embedding_fn,
            metadata={"hnsw:space": "cosine", "description": "Large contexts for generation"}
        )

        # BM25 인덱스 (한국어 최적화)
        self.bm25_child: Optional[KoreanBM25] = None
        self.child_doc_ids: List[str] = []
        self.child_docs: List[str] = []

        self._refresh_bm25()

    def _create_embedding_fn(self, ollama_client: OllamaClient):
        """OllamaClient를 Chroma embedding function으로 변환"""
        class OllamaEF(embedding_functions.EmbeddingFunction):
            def __call__(self, input: chromadb.Documents) -> chromadb.Embeddings:
                embeddings = []
                for text in input:
                    embeddings.append(ollama_client.embed(text))
                return embeddings
        return OllamaEF()

    def _refresh_bm25(self):
        """Child 컬렉션에서 BM25 인덱스 재구축"""
        try:
            count = self.child_collection.count()
            if count == 0:
                logger.info("Child collection is empty. BM25 not built.")
                return

            result = self.child_collection.get()
            if result and result['documents']:
                self.child_docs = result['documents']
                self.child_doc_ids = result['ids']

                # 한국어 BM25 구축
                self.bm25_child = KoreanBM25(use_morphs=True)
                self.bm25_child.fit(self.child_docs)
                logger.info(f"Korean BM25 index built with {count} child documents.")
        except Exception as e:
            logger.error(f"Failed to refresh BM25: {e}")

    def add_hierarchical_document(
        self,
        enhanced_json: dict
    ) -> int:
        """
        Enhanced JSON 형식의 문서를 계층적으로 저장

        Args:
            enhanced_json: EnhancedJSONGenerator가 생성한 JSON

        Returns:
            추가된 청크 수
        """
        doc_metadata = enhanced_json["document_metadata"]
        sections = enhanced_json["sections"]

        child_count = 0
        parent_count = 0

        for section in sections:
            section_id = section["section_id"]

            # Parent 저장 (전체 섹션)
            parent_text = self._build_parent_text(section)
            parent_id = f"parent_{section_id}"

            parent_meta = {
                "type": "parent",
                "section_id": section_id,
                "section_title": section["section_title"],
                "document_id": doc_metadata["document_id"],
                "school_name": doc_metadata.get("school_name", ""),
                "year": str(doc_metadata.get("year", "")),
                "grade": str(doc_metadata.get("grade", "")),
                "subject": doc_metadata.get("subject", "")
            }

            self.parent_collection.add(
                ids=[parent_id],
                documents=[parent_text],
                metadatas=[parent_meta]
            )
            parent_count += 1

            # Child 저장 (각 테이블을 독립적인 청크로)
            for table in section["tables"]:
                table_id = table["table_id"]
                child_id = f"child_{table_id}"

                # 테이블을 마크다운 + 구조화 데이터로 표현
                child_text = self._build_child_text(table, section)

                child_meta = {
                    "type": "child",
                    "parent_id": parent_id,
                    "table_id": table_id,
                    "section_id": section_id,
                    "section_title": section["section_title"],
                    "document_id": doc_metadata["document_id"],
                    "school_name": doc_metadata.get("school_name", ""),
                    "year": str(doc_metadata.get("year", "")),
                    "grade": str(doc_metadata.get("grade", ""))
                }

                self.child_collection.add(
                    ids=[child_id],
                    documents=[child_text],
                    metadatas=[child_meta]
                )
                child_count += 1

        # BM25 재구축
        self._refresh_bm25()

        logger.info(f"Added {parent_count} parents, {child_count} children")
        return child_count + parent_count

    def _build_parent_text(self, section: dict) -> str:
        """섹션 전체를 하나의 텍스트로 결합"""
        parts = [f"# {section['section_title']}\n"]

        if section['content']:
            parts.append(section['content'])

        for table in section['tables']:
            parts.append(f"\n## {table['table_caption']}\n")
            parts.append(table['markdown'])

            # 구조화 데이터도 포함
            if table['structured_data']:
                parts.append(f"\n구조화 데이터: {json.dumps(table['structured_data'], ensure_ascii=False)}")

        return "\n".join(parts)

    def _build_child_text(self, table: dict, section: dict) -> str:
        """테이블을 검색 최적화된 텍스트로 변환"""
        parts = [
            f"섹션: {section['section_title']}",
            f"표: {table['table_caption']}",
            "",
            table['markdown'],
            "",
            f"구조화 데이터: {json.dumps(table['structured_data'], ensure_ascii=False)}"
        ]

        # Q&A 쌍도 포함 (검색 향상)
        if table['queryable_facts']:
            parts.append("\n자주 묻는 질문:")
            for qa in table['queryable_facts']:
                parts.append(f"Q: {qa['question']} A: {qa['answer']}")

        return "\n".join(parts)

    def query_with_parent_context(
        self,
        question: str,
        k: int = 3,
        use_hybrid: bool = True
    ) -> dict:
        """
        Child에서 검색 → Parent 컨텍스트 반환

        Returns:
            {
                "matched_children": [...],
                "parent_contexts": [...],
                "parent_ids": [...]
            }
        """
        # 1. Child에서 검색
        if use_hybrid and self.bm25_child:
            child_results = self._hybrid_search_child(question, k=k)
        else:
            child_results = self._vector_search_child(question, k=k)

        # 2. Parent ID 추출
        parent_ids = set()
        for result in child_results:
            parent_id = result["metadata"].get("parent_id")
            if parent_id:
                parent_ids.add(parent_id)

        # 3. Parent 문서 가져오기
        parent_docs = []
        if parent_ids:
            parent_data = self.parent_collection.get(ids=list(parent_ids))

            for i, pid in enumerate(parent_data["ids"]):
                parent_docs.append({
                    "id": pid,
                    "text": parent_data["documents"][i],
                    "metadata": parent_data["metadatas"][i]
                })

        return {
            "matched_children": child_results,
            "parent_contexts": parent_docs,
            "parent_ids": list(parent_ids)
        }

    def _vector_search_child(self, query: str, k: int) -> List[dict]:
        """Child 컬렉션에서 벡터 검색"""
        results = self.child_collection.query(
            query_texts=[query],
            n_results=k
        )

        output = []
        if results['ids']:
            for i in range(len(results['ids'][0])):
                output.append({
                    "id": results['ids'][0][i],
                    "text": results['documents'][0][i],
                    "metadata": results['metadatas'][0][i],
                    "score": results['distances'][0][i] if results['distances'] else 0.0
                })
        return output

    def _hybrid_search_child(self, query: str, k: int, alpha: float = 0.5) -> List[dict]:
        """Child 컬렉션에서 하이브리드 검색 (Vector + BM25)"""
        if not self.bm25_child:
            return self._vector_search_child(query, k)

        # 1. Vector Search
        vector_results = self._vector_search_child(query, k=k*2)

        # 2. BM25 Search (Korean)
        bm25_scores = np.array(self.bm25_child.get_scores(query))
        top_n = min(len(bm25_scores), k*2)
        top_indices = np.argsort(bm25_scores)[::-1][:top_n]

        bm25_results = []
        for idx in top_indices:
            bm25_results.append({
                "id": self.child_doc_ids[idx],
                "text": self.child_docs[idx],
                "score": bm25_scores[idx]
            })

        # 3. RRF Fusion
        rrf_k = 60
        doc_scores = {}
        doc_map = {}

        for rank, item in enumerate(vector_results):
            doc_id = item['id']
            doc_map[doc_id] = item
            doc_scores[doc_id] = doc_scores.get(doc_id, 0) + (1 / (rrf_k + rank + 1))

        for rank, item in enumerate(bm25_results):
            doc_id = item['id']
            doc_scores[doc_id] = doc_scores.get(doc_id, 0) + (1 / (rrf_k + rank + 1))

        # 4. 정렬
        sorted_ids = sorted(doc_scores.keys(), key=lambda x: doc_scores[x], reverse=True)[:k]

        # 5. 최종 결과 (메타데이터 보완)
        final_results = []
        ids_to_fetch = [did for did in sorted_ids if did not in doc_map]

        if ids_to_fetch:
            fetched = self.child_collection.get(ids=ids_to_fetch)
            for i, did in enumerate(fetched['ids']):
                doc_map[did] = {
                    "id": did,
                    "text": fetched['documents'][i],
                    "metadata": fetched['metadatas'][i]
                }

        for did in sorted_ids:
            if did in doc_map:
                final_results.append(doc_map[did])

        return final_results

    def add_documents(self, texts: List[str], metadatas: Optional[List[Dict[str, Any]]] = None) -> None:
        """Base class compatibility"""
        raise NotImplementedError("Use add_hierarchical_document() instead")

    def similarity_search(self, query: str, k: int = 4) -> List[Dict[str, Any]]:
        """Base class compatibility"""
        return self._vector_search_child(query, k)

    def hybrid_search(self, query: str, k: int = 4, alpha: float = 0.5) -> List[Dict[str, Any]]:
        """Base class compatibility"""
        return self._hybrid_search_child(query, k, alpha)
