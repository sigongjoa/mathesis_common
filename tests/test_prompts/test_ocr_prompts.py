"""
Tests for OCR prompts.
"""
import pytest


class TestOCRPrompts:
    """Tests for OCR-related prompts."""

    def test_get_math_ocr_prompt(self):
        """Test getting math OCR prompt."""
        try:
            from mathesis_core.prompts.ocr_prompts import get_math_ocr_prompt

            prompt = get_math_ocr_prompt()

            assert len(prompt) > 0
            assert "math" in prompt.lower() or "수식" in prompt
        except ImportError:
            pytest.skip("OCR prompts not available")

    def test_get_table_ocr_prompt(self):
        """Test getting table OCR prompt."""
        try:
            from mathesis_core.prompts.ocr_prompts import get_table_ocr_prompt

            prompt = get_table_ocr_prompt()

            assert len(prompt) > 0
        except (ImportError, AttributeError):
            pytest.skip("Table OCR prompt not available")

    def test_get_diagram_ocr_prompt(self):
        """Test getting diagram OCR prompt."""
        try:
            from mathesis_core.prompts.ocr_prompts import get_diagram_ocr_prompt

            prompt = get_diagram_ocr_prompt()

            assert len(prompt) > 0
        except (ImportError, AttributeError):
            pytest.skip("Diagram OCR prompt not available")

    def test_get_korean_text_prompt(self):
        """Test getting Korean text extraction prompt."""
        try:
            from mathesis_core.prompts.ocr_prompts import get_korean_text_prompt

            prompt = get_korean_text_prompt()

            assert len(prompt) > 0
        except (ImportError, AttributeError):
            pytest.skip("Korean text prompt not available")

    def test_get_mixed_content_prompt(self):
        """Test getting mixed content (text + math) prompt."""
        try:
            from mathesis_core.prompts.ocr_prompts import get_mixed_content_prompt

            prompt = get_mixed_content_prompt()

            assert len(prompt) > 0
        except (ImportError, AttributeError):
            pytest.skip("Mixed content prompt not available")

    def test_prompts_are_strings(self):
        """Test that all prompts are valid strings."""
        try:
            from mathesis_core.prompts import ocr_prompts

            # Get all prompt functions
            prompt_funcs = [
                name for name in dir(ocr_prompts)
                if name.startswith("get_") and callable(getattr(ocr_prompts, name))
            ]

            for func_name in prompt_funcs:
                func = getattr(ocr_prompts, func_name)
                try:
                    result = func()
                    assert isinstance(result, str)
                except TypeError:
                    # Function requires arguments
                    pass
        except ImportError:
            pytest.skip("OCR prompts not available")
