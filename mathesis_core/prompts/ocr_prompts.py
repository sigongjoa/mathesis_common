"""
OCR and Vision prompts.
"""


def get_vision_prompt() -> str:
    """
    Get prompt for vision-based OCR and math extraction.

    Returns:
        Formatted prompt for vision LLM
    """
    return """Analyze this image and extract:
1. All text content (Korean and English)
2. All mathematical expressions in LaTeX format
3. Structure and formatting

Return in this exact JSON format:
{
    "text": "extracted plain text",
    "latex_expressions": ["\\\\frac{1}{2}", "x^2 + y^2 = z^2"],
    "combined_content": "full content with $latex$ inline and $$latex$$ display math",
    "has_mathematical_content": true/false,
    "confidence": 0.0-1.0
}

IMPORTANT: Use double backslashes in LaTeX (\\\\frac, not \\frac)."""
