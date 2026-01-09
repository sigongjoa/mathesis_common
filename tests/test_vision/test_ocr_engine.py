"""
Tests for OCREngine.
"""
import pytest
from unittest.mock import AsyncMock, Mock, patch
from mathesis_core.vision import OCREngine
from mathesis_core.llm.clients import LLMClient
from mathesis_core.exceptions import OCRError


@pytest.fixture
def mock_llm_client():
    """Create a mock LLM client."""
    client = Mock(spec=LLMClient)
    client.generate = AsyncMock(
        return_value='{"text": "test text", "latex_expressions": [], "combined_content": "test text", "has_mathematical_content": false, "confidence": 0.9}'
    )
    return client


@pytest.mark.asyncio
async def test_ocr_engine_extracts_text(mock_llm_client):
    """Test that OCR engine extracts text from image."""
    mock_image = Mock()
    with patch('PIL.Image.open', return_value=mock_image):
        with patch('pytesseract.image_to_string', return_value="test text"):
            ocr = OCREngine(mock_llm_client)
            test_image = b"fake_image_data"

            result = await ocr.extract(test_image)

            assert "text" in result
            assert "latex" in result
            assert "combined" in result
            assert "has_math" in result
            assert "tesseract_fallback" in result


@pytest.mark.asyncio
async def test_ocr_engine_returns_confidence(mock_llm_client):
    """Test that OCR engine returns confidence score."""
    mock_image = Mock()
    with patch('PIL.Image.open', return_value=mock_image):
        with patch('pytesseract.image_to_string', return_value="test"):
            ocr = OCREngine(mock_llm_client)
            result = await ocr.extract(b"test")

            assert "confidence" in result or "tesseract_fallback" in result


@pytest.mark.asyncio
async def test_ocr_engine_extracts_latex(mock_llm_client):
    """Test that OCR engine extracts LaTeX expressions."""
    mock_llm_client.generate = AsyncMock(
        return_value='{"text": "equation", "latex_expressions": ["x^2 + 2x + 1"], "combined_content": "$x^2 + 2x + 1$", "has_mathematical_content": true, "confidence": 0.95}'
    )

    mock_image = Mock()
    with patch('PIL.Image.open', return_value=mock_image):
        with patch('pytesseract.image_to_string', return_value="equation"):
            ocr = OCREngine(mock_llm_client)
            result = await ocr.extract(b"math_image")

            assert result["has_math"] == True
            assert len(result["latex"]) > 0
            assert "x^2" in result["latex"][0]


@pytest.mark.asyncio
async def test_ocr_engine_fallback_on_llm_failure(mock_llm_client):
    """Test that OCR engine falls back to Tesseract if LLM fails."""
    mock_llm_client.generate = AsyncMock(return_value="invalid json")

    mock_image = Mock()
    with patch('PIL.Image.open', return_value=mock_image):
        with patch('pytesseract.image_to_string', return_value="fallback text"):
            ocr = OCREngine(mock_llm_client)
            result = await ocr.extract(b"test")

            assert result["tesseract_fallback"] == "fallback text"
            assert result["text"] is not None


@pytest.mark.asyncio
async def test_ocr_engine_raises_error_on_complete_failure():
    """Test that OCR engine raises OCRError on complete failure."""
    mock_client = Mock(spec=LLMClient)
    mock_client.generate = AsyncMock(side_effect=Exception("LLM failed"))

    with patch('pytesseract.image_to_string', side_effect=Exception("Tesseract failed")):
        ocr = OCREngine(mock_client)

        with pytest.raises(OCRError):
            await ocr.extract(b"bad_image")
