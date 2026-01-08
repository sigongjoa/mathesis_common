import logging
from typing import List, Optional
import re

logger = logging.getLogger(__name__)

class KoreanTokenizer:
    """
    한국어 텍스트 토크나이징
    - Mecab 사용 가능하면 형태소 분석
    - 불가능하면 공백 + 간단한 정규화
    """

    def __init__(self, use_morphs: bool = True):
        self.use_morphs = use_morphs
        self.tokenizer = None

        if use_morphs:
            try:
                from konlpy.tag import Mecab
                self.tokenizer = Mecab()
                logger.info("Korean tokenizer initialized with Mecab")
            except ImportError:
                logger.warning("Mecab not available, trying Okt...")
                try:
                    from konlpy.tag import Okt
                    self.tokenizer = Okt()
                    logger.info("Korean tokenizer initialized with Okt")
                except ImportError:
                    logger.warning("konlpy not available. Using simple whitespace tokenizer.")
                    self.tokenizer = None
        else:
            logger.info("Using simple whitespace tokenizer (no morphs)")

    def tokenize(self, text: str) -> List[str]:
        """텍스트를 토큰 리스트로 변환"""
        if not text:
            return []

        # 형태소 분석 가능한 경우
        if self.tokenizer:
            try:
                # 명사, 동사, 형용사만 추출
                morphs = self.tokenizer.pos(text)
                tokens = [
                    word for word, pos in morphs
                    if pos in ['NNG', 'NNP', 'VV', 'VA', 'MAG', 'NR']  # 명사, 동사, 형용사, 부사, 숫자
                ]
                return tokens
            except Exception as e:
                logger.error(f"Morphological analysis failed: {e}. Falling back to simple tokenizer.")

        # 폴백: 간단한 공백 분리 + 정규화
        return self._simple_tokenize(text)

    def _simple_tokenize(self, text: str) -> List[str]:
        """간단한 공백 기반 토큰화 + 조사 제거 시도"""
        # 1. 소문자화 (알파벳만)
        text = text.lower()

        # 2. 특수문자 제거 (숫자, 한글, 알파벳, 공백만 유지)
        text = re.sub(r'[^가-힣a-z0-9\s%]', ' ', text)

        # 3. 공백으로 분리
        tokens = text.split()

        # 4. 불용어 및 조사 간단 제거 (휴리스틱)
        filtered = []
        stopwords = {'은', '는', '이', '가', '을', '를', '의', '에', '와', '과', '도', '만', '로', '으로'}

        for token in tokens:
            # 너무 짧은 토큰 제거
            if len(token) < 2:
                continue

            # 조사로 끝나는 경우 제거 시도
            for josa in stopwords:
                if token.endswith(josa) and len(token) > len(josa):
                    token = token[:-len(josa)]
                    break

            if token and token not in stopwords:
                filtered.append(token)

        return filtered

    def tokenize_batch(self, texts: List[str]) -> List[List[str]]:
        """배치 토큰화"""
        return [self.tokenize(text) for text in texts]


class KoreanBM25:
    """한국어 최적화 BM25"""

    def __init__(self, use_morphs: bool = True):
        try:
            from rank_bm25 import BM25Okapi
            self.BM25Okapi = BM25Okapi
        except ImportError:
            raise ImportError("rank-bm25 required. Install: pip install rank-bm25")

        self.tokenizer = KoreanTokenizer(use_morphs=use_morphs)
        self.bm25: Optional['BM25Okapi'] = None
        self.corpus_tokenized: List[List[str]] = []

    def fit(self, documents: List[str]):
        """문서 색인 구축"""
        self.corpus_tokenized = self.tokenizer.tokenize_batch(documents)
        self.bm25 = self.BM25Okapi(self.corpus_tokenized)
        logger.info(f"BM25 index built with {len(documents)} documents")

    def search(self, query: str, top_k: int = 5) -> List[int]:
        """검색 (인덱스 반환)"""
        if not self.bm25:
            raise ValueError("BM25 index not built. Call fit() first.")

        query_tokens = self.tokenizer.tokenize(query)
        scores = self.bm25.get_scores(query_tokens)

        import numpy as np
        top_indices = np.argsort(scores)[::-1][:top_k]
        return top_indices.tolist()

    def get_scores(self, query: str) -> List[float]:
        """모든 문서에 대한 스코어 반환"""
        if not self.bm25:
            raise ValueError("BM25 index not built. Call fit() first.")

        query_tokens = self.tokenizer.tokenize(query)
        return self.bm25.get_scores(query_tokens).tolist()
