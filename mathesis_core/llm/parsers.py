import json
import re
from typing import Any, Dict, List, Type, Optional
from pydantic import BaseModel
import logging

logger = logging.getLogger(__name__)

class LLMJSONParser:
    """
    Utility for extracting and validating JSON from LLM responses.
    Integrates logic from all existing nodes.
    """

    @staticmethod
    def parse(
        response: str,
        schema: Optional[Type[BaseModel]] = None,
        required_keys: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Parse JSON from LLM response reliably.
        """
        # Step 1: Remove markdown code blocks
        cleaned = LLMJSONParser._remove_markdown(response)

        # Step 2: Extract outer JSON object or array
        cleaned = LLMJSONParser._extract_outer_json(cleaned)

        # Step 3: Try standard JSON parsing
        try:
            data = json.loads(cleaned)
        except json.JSONDecodeError:
            # Step 4: Regex fallback
            try:
                data = LLMJSONParser._regex_extract(response)
            except Exception as e:
                logger.error(f"All JSON extraction methods failed: {e}")
                raise ValueError(f"Could not parse valid JSON from LLM response: {response[:100]}...")

        # Step 5: Validate required keys
        if required_keys:
            missing_keys = [key for key in required_keys if key not in data]
            if missing_keys:
                raise ValueError(f"Missing required keys: {missing_keys}")

        # Step 6: Validate with Pydantic schema
        if schema:
            # Handle list responses if schema is for items
            if isinstance(data, list):
                # If it's a list, we might want to validate each item if possible, 
                # but for now, we follow the design of returning the dict/list.
                # Usually schema is for the root object.
                pass
            
            validated = schema(**data)
            return validated.model_dump() # Pydantic v2

        return data

    @staticmethod
    def _remove_markdown(text: str) -> str:
        text = text.strip()
        if text.startswith("```"):
            # Remove ```json or just ```
            text = re.sub(r'^```(?:json)?\s*', '', text)
            # Remove trailing ```
            text = re.sub(r'\s*```$', '', text)
        return text.strip()

    @staticmethod
    def _extract_outer_json(text: str) -> str:
        # Look for { ... } or [ ... ]
        start_obj = text.find("{")
        end_obj = text.rfind("}")
        
        start_arr = text.find("[")
        end_arr = text.rfind("]")
        
        # Decide which one is more likely to be the root
        if start_obj != -1 and end_obj != -1:
            if start_arr == -1 or start_obj < start_arr:
                return text[start_obj:end_obj+1]
        
        if start_arr != -1 and end_arr != -1:
            return text[start_arr:end_arr+1]
            
        return text

    @staticmethod
    def _regex_extract(text: str) -> Dict[str, Any]:
        match = re.search(r'\{.*\}', text, re.DOTALL)
        if match:
            return json.loads(match.group(0))
        
        match = re.search(r'\[.*\]', text, re.DOTALL)
        if match:
            return json.loads(match.group(0))
            
        raise ValueError("No JSON-like structure found via regex")

    @staticmethod
    def safe_parse(
        response: str,
        default: Any = None,
        schema: Optional[Type[BaseModel]] = None
    ) -> Any:
        try:
            return LLMJSONParser.parse(response, schema=schema)
        except Exception as e:
            logger.warning(f"Safe parse failed: {e}. Using default.")
            return default if default is not None else {}
