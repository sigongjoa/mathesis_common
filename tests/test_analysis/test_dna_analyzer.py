"""
Tests for DNAAnalyzer.
"""
import pytest
from unittest.mock import AsyncMock, Mock
from mathesis_core.analysis import DNAAnalyzer
from mathesis_core.llm.clients import LLMClient
from mathesis_core.exceptions import AnalysisError


@pytest.fixture
def mock_llm_client():
    """Create a mock LLM client with predefined responses."""
    client = Mock(spec=LLMClient)
    client.generate = AsyncMock(side_effect=[
        # Tags response
        '{"tags": [{"tag": "Algebra", "type": "concept", "confidence": 0.95}, {"tag": "Apply", "type": "cognitive_level", "confidence": 0.90}]}',
        # Metadata response
        '{"cognitive_level": "Apply", "difficulty_estimation": 0.6, "subject_area": "Mathematics", "estimated_time_minutes": 5}',
        # Curriculum response
        'Math.Algebra.Quadratics'
    ])
    return client


@pytest.mark.asyncio
async def test_dna_analyzer_extracts_tags(mock_llm_client):
    """Test that DNA analyzer extracts tags."""
    analyzer = DNAAnalyzer(mock_llm_client)

    dna = await analyzer.analyze("x^2 + 2x + 1 = 0을 풀어라")

    assert "tags" in dna
    assert len(dna["tags"]) > 0
    assert dna["tags"][0]["tag"] == "Algebra"
    assert dna["tags"][0]["type"] == "concept"
    assert dna["tags"][0]["confidence"] == 0.95


@pytest.mark.asyncio
async def test_dna_analyzer_extracts_metadata(mock_llm_client):
    """Test that DNA analyzer extracts metadata."""
    analyzer = DNAAnalyzer(mock_llm_client)

    dna = await analyzer.analyze("test question")

    assert "metadata" in dna
    assert "cognitive_level" in dna["metadata"]
    assert dna["metadata"]["cognitive_level"] == "Apply"
    assert "difficulty_estimation" in dna["metadata"]
    assert dna["metadata"]["difficulty_estimation"] == 0.6


@pytest.mark.asyncio
async def test_dna_analyzer_generates_curriculum_path(mock_llm_client):
    """Test that DNA analyzer generates curriculum path."""
    analyzer = DNAAnalyzer(mock_llm_client)

    dna = await analyzer.analyze("test question")

    assert "curriculum_path" in dna
    assert dna["curriculum_path"] == "Math.Algebra.Quadratics"


@pytest.mark.asyncio
async def test_dna_analyzer_generates_signature(mock_llm_client):
    """Test that DNA analyzer generates DNA signature."""
    analyzer = DNAAnalyzer(mock_llm_client)

    dna = await analyzer.analyze("test question")

    assert "dna_signature" in dna
    assert len(dna["dna_signature"]) == 16  # MD5 hash truncated to 16 chars
    assert isinstance(dna["dna_signature"], str)


@pytest.mark.asyncio
async def test_dna_analyzer_extracts_keywords(mock_llm_client):
    """Test that DNA analyzer extracts keywords."""
    analyzer = DNAAnalyzer(mock_llm_client)

    dna = await analyzer.analyze("x^2 + 2x + 1 = 0을 풀어라")

    assert "keywords" in dna
    assert isinstance(dna["keywords"], list)


@pytest.mark.asyncio
async def test_dna_analyzer_signature_consistency():
    """Test that similar problems get similar signatures."""
    client1 = Mock(spec=LLMClient)
    client1.generate = AsyncMock(side_effect=[
        '{"tags": [{"tag": "Algebra", "type": "concept"}]}',
        '{"cognitive_level": "Apply", "difficulty_estimation": 0.6}',
        'Math.Algebra'
    ])

    client2 = Mock(spec=LLMClient)
    client2.generate = AsyncMock(side_effect=[
        '{"tags": [{"tag": "Algebra", "type": "concept"}]}',
        '{"cognitive_level": "Apply", "difficulty_estimation": 0.6}',
        'Math.Algebra'
    ])

    analyzer1 = DNAAnalyzer(client1)
    analyzer2 = DNAAnalyzer(client2)

    dna1 = await analyzer1.analyze("x^2 + 2x + 1 = 0")
    dna2 = await analyzer2.analyze("x^2 + 3x + 2 = 0")

    # Same concept + cognitive level + difficulty should yield same signature
    assert dna1["dna_signature"] == dna2["dna_signature"]


@pytest.mark.asyncio
async def test_dna_analyzer_handles_llm_failure():
    """Test that DNA analyzer handles LLM failures gracefully."""
    client = Mock(spec=LLMClient)
    client.generate = AsyncMock(side_effect=Exception("LLM failed"))

    analyzer = DNAAnalyzer(client)

    with pytest.raises(AnalysisError):
        await analyzer.analyze("test question")
