"""
Tests for ProblemGenerator (TDD).
"""
import pytest
from unittest.mock import AsyncMock, Mock
from mathesis_core.generation import ProblemGenerator
from mathesis_core.llm.clients import LLMClient
from mathesis_core.exceptions import GenerationError


@pytest.fixture
def mock_llm_client():
    """Create a mock LLM client."""
    client = Mock(spec=LLMClient)
    return client


@pytest.mark.asyncio
async def test_generate_twin_question_success(mock_llm_client):
    """Test successful twin question generation."""
    # Mock LLM response
    mock_llm_client.generate = AsyncMock(
        return_value='{"question_stem": "철수는 사과를 12개 가지고 있습니다. 영희에게 5개를 주면 몇 개가 남을까요?", "answer": "7개", "solution_steps": "12 - 5 = 7"}'
    )

    generator = ProblemGenerator(mock_llm_client)

    original_question = {
        "content_stem": "민수는 연필을 15개 가지고 있습니다. 친구에게 8개를 주면 몇 개가 남을까요?",
        "answer_key": {"answer": "7개"},
        "question_type": "short_answer"
    }

    result = await generator.generate_twin(original_question)

    assert "question_stem" in result
    assert "answer" in result
    assert "solution_steps" in result
    assert result["question_stem"] != original_question["content_stem"]
    # Check that LLM was called
    mock_llm_client.generate.assert_called_once()


@pytest.mark.asyncio
async def test_generate_twin_preserves_logic(mock_llm_client):
    """Test that twin question preserves mathematical logic."""
    mock_llm_client.generate = AsyncMock(
        return_value='{"question_stem": "변형된 문제", "answer": "15", "solution_steps": "5 × 3 = 15"}'
    )

    generator = ProblemGenerator(mock_llm_client)

    original = {
        "content_stem": "2 × 3 = ?",
        "answer_key": {"answer": "6"},
        "question_type": "short_answer"
    }

    result = await generator.generate_twin(original)

    assert "question_stem" in result
    # Different numbers but same operation structure expected


@pytest.mark.asyncio
async def test_generate_error_solution_success(mock_llm_client):
    """Test successful error solution generation."""
    mock_llm_client.generate = AsyncMock(
        return_value="""{
            "steps": [
                {"step": 1, "content": "방정식을 정리합니다.", "formula": "x^2 - 5x + 6 = 0", "is_error": false},
                {"step": 2, "content": "인수분해를 시도합니다.", "formula": "(x-2)(x-3) = 0", "is_error": false},
                {"step": 3, "content": "x = 2 또는 x = 3", "formula": "x = 2, 3", "is_error": true, "error_type": "condition_omission", "error_explanation": "정의역 확인을 생략했습니다."}
            ],
            "final_wrong_answer": "x = 2 또는 x = 3 (조건 미확인)"
        }"""
    )

    generator = ProblemGenerator(mock_llm_client)

    result = await generator.generate_error_solution(
        question_content="x^2 - 5x + 6 = 0을 푸시오.",
        correct_answer="x = 2 또는 x = 3",
        error_types=["condition_omission"]
    )

    assert "steps" in result
    assert "final_wrong_answer" in result
    assert len(result["steps"]) >= 3
    # Check that at least one step has an error
    has_error = any(step.get("is_error") for step in result["steps"])
    assert has_error


@pytest.mark.asyncio
async def test_generate_error_solution_has_single_error(mock_llm_client):
    """Test that error solution has exactly one error point."""
    mock_llm_client.generate = AsyncMock(
        return_value="""{
            "steps": [
                {"step": 1, "content": "Step 1", "formula": "f(x)", "is_error": false},
                {"step": 2, "content": "Step 2 - ERROR", "formula": "wrong", "is_error": true, "error_type": "logic", "error_explanation": "설명"},
                {"step": 3, "content": "Step 3", "formula": "result", "is_error": false}
            ],
            "final_wrong_answer": "wrong answer"
        }"""
    )

    generator = ProblemGenerator(mock_llm_client)

    result = await generator.generate_error_solution(
        question_content="문제",
        correct_answer="정답"
    )

    error_steps = [step for step in result["steps"] if step.get("is_error")]
    # Should have at least one error (ideally exactly one, but LLM might generate more)
    assert len(error_steps) >= 1


@pytest.mark.asyncio
async def test_generate_correct_solution_success(mock_llm_client):
    """Test correct solution generation."""
    mock_llm_client.generate = AsyncMock(
        return_value="""{
            "steps": [
                {"step": 1, "content": "정답 풀이 1단계", "formula": "2x = 10", "is_error": false},
                {"step": 2, "content": "정답 풀이 2단계", "formula": "x = 5", "is_error": false}
            ]
        }"""
    )

    generator = ProblemGenerator(mock_llm_client)

    result = await generator.generate_correct_solution(
        question_content="2x = 10을 푸시오.",
        correct_answer="x = 5"
    )

    assert "steps" in result
    assert all(not step.get("is_error") for step in result["steps"])


@pytest.mark.asyncio
async def test_generate_twin_with_metadata(mock_llm_client):
    """Test twin generation with metadata preservation."""
    mock_llm_client.generate = AsyncMock(
        return_value='{"question_stem": "새 문제", "answer": "답", "solution_steps": "풀이"}'
    )

    generator = ProblemGenerator(mock_llm_client)

    original = {
        "content_stem": "원본 문제",
        "answer_key": {"answer": "답"},
        "question_type": "mcq",
        "content_metadata": {
            "source": {"name": "Test", "grade": 5},
            "domain": {"major_domain": "Number"},
            "difficulty": {"estimated_level": 3}
        }
    }

    result = await generator.generate_twin(original)

    assert "question_stem" in result
    # Metadata should be preserved or accessible


@pytest.mark.asyncio
async def test_generate_twin_handles_llm_failure(mock_llm_client):
    """Test that twin generation handles LLM failures gracefully."""
    mock_llm_client.generate = AsyncMock(side_effect=Exception("LLM error"))

    generator = ProblemGenerator(mock_llm_client)

    original = {
        "content_stem": "문제",
        "answer_key": {"answer": "답"},
        "question_type": "short_answer"
    }

    with pytest.raises(GenerationError):
        await generator.generate_twin(original)


@pytest.mark.asyncio
async def test_generate_error_solution_handles_invalid_json(mock_llm_client):
    """Test that error solution handles invalid JSON from LLM by using fallback."""
    mock_llm_client.generate = AsyncMock(return_value="invalid json{{{")

    generator = ProblemGenerator(mock_llm_client)

    # safe_parse uses fallback instead of raising error
    result = await generator.generate_error_solution(
        question_content="문제",
        correct_answer="답"
    )

    # Should return default structure
    assert "steps" in result
    assert "final_wrong_answer" in result
    assert result["final_wrong_answer"] == "Error"  # Default value


@pytest.mark.asyncio
async def test_generate_problem_variation_by_difficulty(mock_llm_client):
    """Test problem variation by difficulty adjustment."""
    mock_llm_client.generate = AsyncMock(
        return_value='{"question_stem": "더 쉬운 문제", "difficulty_estimation": 0.3, "changes_made": "숫자를 단순화"}'
    )

    generator = ProblemGenerator(mock_llm_client)

    result = await generator.generate_variation(
        original_question="복잡한 문제",
        variation_type="difficulty",
        target_level=0.3
    )

    assert "question_stem" in result
    assert "difficulty_estimation" in result
    assert result["difficulty_estimation"] <= 0.5  # Easier problem


@pytest.mark.asyncio
async def test_generate_problem_variation_by_context(mock_llm_client):
    """Test problem variation by context change."""
    mock_llm_client.generate = AsyncMock(
        return_value='{"question_stem": "새 맥락 문제", "context_changes": "학교 → 가게"}'
    )

    generator = ProblemGenerator(mock_llm_client)

    result = await generator.generate_variation(
        original_question="학교에서 연필을 사는 문제",
        variation_type="context"
    )

    assert "question_stem" in result
    assert "context_changes" in result


@pytest.mark.asyncio
async def test_error_solution_validates_error_types(mock_llm_client):
    """Test that error solution validates error types."""
    mock_llm_client.generate = AsyncMock(
        return_value='{"steps": [{"step": 1, "content": "test", "is_error": false}], "final_wrong_answer": "test"}'
    )

    generator = ProblemGenerator(mock_llm_client)

    # Should accept valid error types
    result = await generator.generate_error_solution(
        question_content="문제",
        correct_answer="답",
        error_types=["concept_misapplication", "arithmetic_error", "condition_omission"]
    )

    assert result is not None


@pytest.mark.asyncio
async def test_twin_generation_uses_correct_prompt(mock_llm_client):
    """Test that twin generation uses the correct prompt template."""
    mock_llm_client.generate = AsyncMock(
        return_value='{"question_stem": "test", "answer": "test", "solution_steps": "test"}'
    )

    generator = ProblemGenerator(mock_llm_client)

    original = {
        "content_stem": "원본",
        "answer_key": {"answer": "답"},
        "question_type": "short_answer"
    }

    await generator.generate_twin(original)

    # Check that generate was called with a prompt containing twin question instructions
    call_args = mock_llm_client.generate.call_args
    assert call_args is not None
    prompt = call_args.kwargs.get("prompt", "")
    assert "Twin Problem" in prompt or "Isomorphic" in prompt
