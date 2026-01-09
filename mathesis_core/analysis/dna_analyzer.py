"""
DNA Analyzer - Extract problem DNA (concepts, difficulty, tags).
"""
from typing import Dict, List
import hashlib
import re
from mathesis_core.llm.clients import LLMClient
from mathesis_core.llm.parsers import LLMJSONParser
from mathesis_core.exceptions import AnalysisError
import logging

logger = logging.getLogger(__name__)


class DNAAnalyzer:
    """
    DNA Analyzer - Extract problem DNA (concepts, difficulty, tags).
    Pure business logic, reusable across all nodes.
    """

    def __init__(self, llm_client: LLMClient):
        """
        Initialize DNA Analyzer.

        Args:
            llm_client: LLM client for analysis
        """
        self.llm = llm_client

    async def analyze(self, question_text: str) -> Dict:
        """
        Analyze question and extract DNA.

        Args:
            question_text: Question content (may contain LaTeX)

        Returns:
            {
                "tags": List[Dict],         # [{"tag": str, "type": str, "confidence": float}]
                "metadata": Dict,           # {cognitive_level, difficulty, subject_area, ...}
                "curriculum_path": str,     # "Math.Algebra.Quadratics"
                "dna_signature": str,       # Unique hash for similarity search
                "keywords": List[str]       # Extracted keywords
            }

        Raises:
            AnalysisError: If analysis fails
        """
        try:
            # Extract tags
            tags = await self._extract_tags(question_text)

            # Extract metadata
            metadata = await self._extract_metadata(question_text)

            # Suggest curriculum
            curriculum_path = await self._suggest_curriculum(question_text)

            # Compute signature
            dna_signature = self._compute_signature(tags, metadata)

            # Extract keywords
            keywords = self._extract_keywords(question_text, tags)

            return {
                "tags": tags,
                "metadata": metadata,
                "curriculum_path": curriculum_path,
                "dna_signature": dna_signature,
                "keywords": keywords
            }

        except Exception as e:
            logger.error(f"DNA analysis failed: {e}")
            raise AnalysisError(f"Failed to analyze question: {str(e)}")

    async def _extract_tags(self, text: str) -> List[Dict]:
        """
        Extract tags using LLM.

        Args:
            text: Question text

        Returns:
            List of tag dictionaries
        """
        from mathesis_core.prompts.analysis_prompts import get_tagging_prompt

        prompt = get_tagging_prompt(text)
        response = await self.llm.generate(prompt, format="json", temperature=0.3)

        result = LLMJSONParser.safe_parse(response, default={"tags": []})
        return result.get("tags", [])

    async def _extract_metadata(self, text: str) -> Dict:
        """
        Extract metadata using LLM.

        Args:
            text: Question text

        Returns:
            Metadata dictionary
        """
        from mathesis_core.prompts.analysis_prompts import get_metadata_prompt

        prompt = get_metadata_prompt(text)
        response = await self.llm.generate(prompt, format="json", temperature=0.2)

        return LLMJSONParser.safe_parse(response, default={
            "cognitive_level": "Apply",
            "difficulty_estimation": 0.5,
            "subject_area": "General",
            "estimated_time_minutes": 5
        })

    async def _suggest_curriculum(self, text: str) -> str:
        """
        Suggest curriculum path using LLM.

        Args:
            text: Question text

        Returns:
            Curriculum path string (e.g., "Math.Algebra.Quadratics")
        """
        from mathesis_core.prompts.analysis_prompts import get_curriculum_prompt

        prompt = get_curriculum_prompt(text)
        path = await self.llm.generate(prompt, temperature=0.1)

        # Clean up response (remove quotes, take first line)
        cleaned_path = path.strip().strip('"\'').split('\n')[0]
        return cleaned_path if '.' in cleaned_path else "General.Unknown"

    def _compute_signature(self, tags: List[Dict], metadata: Dict) -> str:
        """
        Compute DNA signature for similarity search.

        Signature = MD5(sorted_concepts + cognitive_level + difficulty)

        Args:
            tags: List of tag dictionaries
            metadata: Metadata dictionary

        Returns:
            16-character hash string
        """
        # Extract concept tags and sort them
        concept_tags = [t["tag"] for t in tags if t.get("type") == "concept"]
        concept_tags.sort()

        cognitive = metadata.get("cognitive_level", "Apply")
        difficulty = metadata.get("difficulty_estimation", 0.5)

        # Create signature string
        signature_str = f"{','.join(concept_tags)}|{cognitive}|{difficulty:.1f}"

        # Return truncated MD5 hash
        return hashlib.md5(signature_str.encode()).hexdigest()[:16]

    def _extract_keywords(self, text: str, tags: List[Dict]) -> List[str]:
        """
        Extract keywords from text and tags.

        Args:
            text: Question text
            tags: List of tag dictionaries

        Returns:
            List of keyword strings (max 10)
        """
        keywords = set()

        # Add tag names
        for tag in tags:
            keywords.add(tag["tag"].lower())

        # Simple keyword extraction from text
        # Remove special characters and split into words
        words = re.findall(r'\w+', text.lower())
        keywords.update([w for w in words if len(w) > 3])

        return list(keywords)[:10]  # Limit to 10 keywords
