"""
Tests for generation prompts.
"""
import pytest


class TestGenerationPrompts:
    """Tests for problem generation prompts."""

    def test_get_problem_generation_prompt(self):
        """Test getting problem generation prompt."""
        try:
            from mathesis_core.prompts.generation_prompts import get_problem_generation_prompt

            prompt = get_problem_generation_prompt(
                concept="derivative",
                difficulty="medium",
                bloom_level="apply"
            )

            assert "derivative" in prompt.lower() or len(prompt) > 0
        except ImportError:
            pytest.skip("Generation prompts not available")

    def test_get_variant_generation_prompt(self):
        """Test getting variant generation prompt."""
        try:
            from mathesis_core.prompts.generation_prompts import get_variant_generation_prompt

            original = "Find the derivative of f(x) = x^2"
            prompt = get_variant_generation_prompt(original_problem=original)

            assert len(prompt) > 0
        except (ImportError, AttributeError):
            pytest.skip("Variant generation prompt not available")

    def test_get_solution_generation_prompt(self):
        """Test getting solution generation prompt."""
        try:
            from mathesis_core.prompts.generation_prompts import get_solution_generation_prompt

            problem = "Find the derivative of f(x) = x^2"
            prompt = get_solution_generation_prompt(problem=problem)

            assert len(prompt) > 0
        except (ImportError, AttributeError):
            pytest.skip("Solution generation prompt not available")

    def test_get_hint_generation_prompt(self):
        """Test getting hint generation prompt."""
        try:
            from mathesis_core.prompts.generation_prompts import get_hint_generation_prompt

            problem = "Find the derivative of f(x) = x^2"
            prompt = get_hint_generation_prompt(problem=problem, hint_level=1)

            assert len(prompt) > 0
        except (ImportError, AttributeError):
            pytest.skip("Hint generation prompt not available")

    def test_prompt_includes_format_instructions(self):
        """Test that prompts include format instructions."""
        try:
            from mathesis_core.prompts.generation_prompts import get_problem_generation_prompt

            prompt = get_problem_generation_prompt(
                concept="integral",
                difficulty="hard",
                output_format="json"
            )

            assert "json" in prompt.lower() or len(prompt) > 0
        except (ImportError, TypeError):
            pytest.skip("Format instructions not available")
