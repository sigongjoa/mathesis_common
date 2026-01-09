"""
Tests for analysis prompts.
"""
import pytest
from mathesis_core.prompts.analysis_prompts import (
    get_tagging_prompt,
    get_metadata_prompt,
    get_curriculum_prompt,
)


def test_tagging_prompt_includes_question_text():
    """Test that tagging prompt includes the question text."""
    question = "x^2 + 2x + 1 = 0을 풀어라"
    prompt = get_tagging_prompt(question)

    assert question in prompt
    assert "tags" in prompt.lower()
    assert "json" in prompt.lower()


def test_tagging_prompt_includes_tag_types():
    """Test that tagging prompt specifies tag types."""
    question = "테스트 문제"
    prompt = get_tagging_prompt(question)

    assert "subject" in prompt.lower()
    assert "concept" in prompt.lower()
    assert "cognitive_level" in prompt.lower()
    assert "confidence" in prompt.lower()


def test_metadata_prompt_includes_question_text():
    """Test that metadata prompt includes the question text."""
    question = "테스트 문제"
    prompt = get_metadata_prompt(question)

    assert question in prompt
    assert "json" in prompt.lower()


def test_metadata_prompt_includes_required_fields():
    """Test that metadata prompt specifies required fields."""
    question = "테스트 문제"
    prompt = get_metadata_prompt(question)

    assert "cognitive_level" in prompt
    assert "difficulty" in prompt
    assert "subject_area" in prompt
    assert "curriculum_path" in prompt


def test_curriculum_prompt_requests_ltree_format():
    """Test that curriculum prompt requests ltree format."""
    question = "이차방정식"
    prompt = get_curriculum_prompt(question)

    assert question in prompt
    assert "Math" in prompt or "curriculum" in prompt.lower()
    assert "path" in prompt.lower()
    assert "." in prompt  # Dot notation example


def test_curriculum_prompt_provides_examples():
    """Test that curriculum prompt provides format examples."""
    question = "테스트"
    prompt = get_curriculum_prompt(question)

    assert "Math.Algebra" in prompt or "example" in prompt.lower()
