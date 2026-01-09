"""
OCR Engine using Tesseract + Vision LLM.
"""
from typing import Dict, Any
from PIL import Image
import io
import pytesseract
from mathesis_core.llm.clients import LLMClient
from mathesis_core.llm.parsers import LLMJSONParser
from mathesis_core.exceptions import OCRError
import logging

logger = logging.getLogger(__name__)


class OCREngine:
    """
    OCR Engine using Tesseract + Vision LLM.
    Pure business logic, no dependencies on DB or FastAPI.
    """

    def __init__(self, llm_client: LLMClient):
        """
        Initialize OCR Engine.

        Args:
            llm_client: LLM client for vision analysis
        """
        self.llm = llm_client

    async def extract(self, image_bytes: bytes) -> Dict[str, Any]:
        """
        Extract text and LaTeX from image.

        Args:
            image_bytes: Raw image bytes (JPEG, PNG, etc.)

        Returns:
            {
                "text": str,              # Pure text content
                "latex": List[str],       # LaTeX expressions
                "combined": str,          # Text with inline LaTeX
                "has_math": bool,         # Whether math detected
                "confidence": float,      # 0.0-1.0
                "tesseract_fallback": str # Raw OCR result
            }

        Raises:
            OCRError: If extraction completely fails
        """
        try:
            # Step 1: Tesseract OCR
            image = Image.open(io.BytesIO(image_bytes))
            tesseract_text = pytesseract.image_to_string(image, lang='eng+kor')

            # Step 2: Vision LLM for refinement
            try:
                vision_result = await self._analyze_with_vision(image_bytes)
            except Exception as e:
                logger.warning(f"Vision LLM failed, using Tesseract only: {e}")
                vision_result = {
                    "text": tesseract_text,
                    "latex_expressions": [],
                    "combined_content": tesseract_text,
                    "has_mathematical_content": False,
                    "confidence": 0.5
                }

            return {
                "text": vision_result.get("text", tesseract_text),
                "latex": vision_result.get("latex_expressions", []),
                "combined": vision_result.get("combined_content", tesseract_text),
                "has_math": vision_result.get("has_mathematical_content", False),
                "confidence": vision_result.get("confidence", 0.8),
                "tesseract_fallback": tesseract_text
            }

        except Exception as e:
            logger.error(f"OCR extraction failed: {e}")
            raise OCRError(f"Failed to extract text from image: {str(e)}")

    async def _analyze_with_vision(self, image_bytes: bytes) -> Dict:
        """
        Call Vision LLM for refinement.

        Args:
            image_bytes: Raw image bytes

        Returns:
            Parsed JSON response from LLM
        """
        from mathesis_core.prompts.ocr_prompts import get_vision_prompt

        prompt = get_vision_prompt()

        # Note: For vision models, we would use analyze_image method
        # For now, using generate with base64 encoding
        # This is a placeholder - actual implementation depends on LLM provider
        response = await self.llm.generate(prompt, format="json")

        return LLMJSONParser.safe_parse(response, default={
            "text": "",
            "latex_expressions": [],
            "combined_content": "",
            "has_mathematical_content": False,
            "confidence": 0.0
        })
