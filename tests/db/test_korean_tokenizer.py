"""
Tests for Korean tokenizer functionality.

Tests tokenization for Korean text in the RAG system.
"""
import pytest
from unittest.mock import MagicMock, patch


class TestKoreanTokenizer:
    """Tests for Korean tokenizer."""

    @pytest.fixture
    def sample_korean_texts(self):
        """Sample Korean texts for testing."""
        return [
            "수학은 재미있는 과목입니다.",
            "미분과 적분은 중요한 개념이다.",
            "함수의 극한을 구하시오.",
        ]

    def test_tokenize_korean_text(self, sample_korean_texts):
        """Test basic Korean text tokenization."""
        try:
            from mathesis_core.db.korean_tokenizer import KoreanTokenizer

            tokenizer = KoreanTokenizer()
            tokens = tokenizer.tokenize(sample_korean_texts[0])

            assert isinstance(tokens, list)
            assert len(tokens) > 0
        except ImportError:
            pytest.skip("Korean tokenizer not available")

    def test_tokenize_empty_string(self):
        """Test tokenizing empty string."""
        try:
            from mathesis_core.db.korean_tokenizer import KoreanTokenizer

            tokenizer = KoreanTokenizer()
            tokens = tokenizer.tokenize("")

            assert tokens == []
        except ImportError:
            pytest.skip("Korean tokenizer not available")

    def test_tokenize_mixed_korean_english(self):
        """Test tokenizing mixed Korean and English text."""
        try:
            from mathesis_core.db.korean_tokenizer import KoreanTokenizer

            tokenizer = KoreanTokenizer()
            tokens = tokenizer.tokenize("Python은 좋은 language입니다")

            assert isinstance(tokens, list)
            assert len(tokens) > 0
        except ImportError:
            pytest.skip("Korean tokenizer not available")

    def test_tokenize_math_expressions(self):
        """Test tokenizing text with mathematical expressions."""
        try:
            from mathesis_core.db.korean_tokenizer import KoreanTokenizer

            tokenizer = KoreanTokenizer()
            tokens = tokenizer.tokenize("x^2 + 2x + 1 = 0을 풀어라")

            assert isinstance(tokens, list)
        except ImportError:
            pytest.skip("Korean tokenizer not available")

    def test_batch_tokenize(self, sample_korean_texts):
        """Test batch tokenization of multiple texts."""
        try:
            from mathesis_core.db.korean_tokenizer import KoreanTokenizer

            tokenizer = KoreanTokenizer()
            batch_tokens = tokenizer.batch_tokenize(sample_korean_texts)

            assert len(batch_tokens) == len(sample_korean_texts)
            for tokens in batch_tokens:
                assert isinstance(tokens, list)
        except (ImportError, AttributeError):
            pytest.skip("Batch tokenize not available")
