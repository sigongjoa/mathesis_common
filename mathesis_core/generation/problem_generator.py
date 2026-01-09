"""
Problem Generator for mathesis-core.

Generates:
1. Twin questions (isomorphic problems with same logic, different context)
2. Error solutions (intentionally incorrect solutions for learning)
3. Correct solutions (model answers)
4. Problem variations (difficulty/context/concept adjustments)
"""
import logging
from typing import Dict, Any, List, Optional
from mathesis_core.llm.clients import LLMClient
from mathesis_core.llm.parsers import LLMJSONParser
from mathesis_core.prompts.generation_prompts import (
    get_twin_question_prompt,
    get_error_solution_prompt,
    get_correct_solution_prompt,
    get_problem_variation_prompt,
)
from mathesis_core.exceptions import GenerationError

logger = logging.getLogger(__name__)


class ProblemGenerator:
    """
    Problem Generator using LLM for educational content creation.

    Supports:
    - Twin question generation (isomorphic problems)
    - Error solution generation (common mistakes)
    - Correct solution generation (model answers)
    - Problem variations (difficulty, context, concept)
    """

    def __init__(self, llm_client: LLMClient):
        """
        Initialize ProblemGenerator with LLM client.

        Args:
            llm_client: LLMClient instance for generation
        """
        self.llm = llm_client
        logger.info("ProblemGenerator initialized")

    async def generate_twin(
        self,
        original_question: Dict[str, Any],
        preserve_metadata: bool = True
    ) -> Dict[str, Any]:
        """
        Generate a twin (isomorphic) question.

        Twin questions have the same mathematical logic and solving steps,
        but different story context, numbers, and wording.

        Args:
            original_question: Original question dict with keys:
                - content_stem: Question text
                - answer_key: Answer dict
                - question_type: Type of question
                - content_metadata (optional): Metadata dict
            preserve_metadata: Whether to preserve original metadata

        Returns:
            Dict with keys:
                - question_stem: New question text
                - answer: New answer
                - solution_steps: Solution explanation
                - metadata (if preserve_metadata=True): Original metadata

        Raises:
            GenerationError: If generation fails
        """
        try:
            original_text = original_question.get("content_stem", "")
            metadata = original_question.get("content_metadata")

            # Get prompt
            prompt = get_twin_question_prompt(original_text, metadata)

            # Generate using LLM
            response = await self.llm.generate(
                prompt=prompt,
                format="json",
                temperature=0.7  # Some creativity for variations
            )

            # Parse JSON response
            result = LLMJSONParser.safe_parse(
                response,
                default={
                    "question_stem": original_text,
                    "answer": original_question.get("answer_key", {}).get("answer", ""),
                    "solution_steps": "Generation failed"
                }
            )

            # Validate required keys
            required_keys = ["question_stem", "answer", "solution_steps"]
            for key in required_keys:
                if key not in result:
                    logger.warning(f"Missing key '{key}' in twin generation result, using default")
                    result[key] = result.get(key, "")

            # Preserve metadata if requested
            if preserve_metadata and metadata:
                result["metadata"] = metadata

            logger.info(f"Generated twin question successfully")
            return result

        except Exception as e:
            logger.error(f"Twin generation failed: {e}")
            raise GenerationError(f"Failed to generate twin question: {str(e)}")

    async def generate_error_solution(
        self,
        question_content: str,
        correct_answer: str,
        error_types: Optional[List[str]] = None,
        difficulty: int = 2
    ) -> Dict[str, Any]:
        """
        Generate an intentionally incorrect solution demonstrating common errors.

        Args:
            question_content: Question text
            correct_answer: Correct answer for reference
            error_types: List of error types to include (e.g., "concept_misapplication", "arithmetic_error", "condition_omission")
            difficulty: Solution complexity level (1-5)

        Returns:
            Dict with keys:
                - steps: List of solution steps with error markers
                - final_wrong_answer: The incorrect final answer

        Raises:
            GenerationError: If generation fails
        """
        try:
            # Validate error types if provided
            if error_types:
                valid_types = {
                    "concept_misapplication",
                    "arithmetic_error",
                    "condition_omission",
                    "logic_leap",
                    "sign_error",
                    "unit_confusion"
                }
                for et in error_types:
                    if et not in valid_types:
                        logger.warning(f"Unknown error type: {et}")

            # Get prompt
            prompt = get_error_solution_prompt(
                question_content,
                correct_answer,
                error_types,
                difficulty
            )

            # Generate using LLM
            response = await self.llm.generate(
                prompt=prompt,
                format="json",
                temperature=0.5  # Balanced creativity
            )

            # Parse JSON response
            result = LLMJSONParser.safe_parse(
                response,
                default={
                    "steps": [
                        {
                            "step": 1,
                            "content": "Generation failed",
                            "is_error": False
                        }
                    ],
                    "final_wrong_answer": "Error"
                }
            )

            # Validate required keys
            if "steps" not in result or "final_wrong_answer" not in result:
                logger.warning("Missing keys in error solution result, using default")
                result.setdefault("steps", [])
                result.setdefault("final_wrong_answer", "Error")

            # Validate that at least one step has an error
            has_error = any(step.get("is_error") for step in result.get("steps", []))
            if not has_error:
                logger.warning("Generated error solution has no error markers")

            logger.info(f"Generated error solution with {len(result['steps'])} steps")
            return result

        except Exception as e:
            logger.error(f"Error solution generation failed: {e}")
            raise GenerationError(f"Failed to generate error solution: {str(e)}")

    async def generate_correct_solution(
        self,
        question_content: str,
        correct_answer: str
    ) -> Dict[str, Any]:
        """
        Generate a correct model solution.

        Args:
            question_content: Question text
            correct_answer: Correct answer

        Returns:
            Dict with key:
                - steps: List of correct solution steps

        Raises:
            GenerationError: If generation fails
        """
        try:
            # Get prompt
            prompt = get_correct_solution_prompt(question_content, correct_answer)

            # Generate using LLM
            response = await self.llm.generate(
                prompt=prompt,
                format="json",
                temperature=0.3  # More deterministic for correct solutions
            )

            # Parse JSON response
            result = LLMJSONParser.safe_parse(
                response,
                default={
                    "steps": [
                        {
                            "step": 1,
                            "content": correct_answer,
                            "is_error": False
                        }
                    ]
                }
            )

            # Validate required keys
            if "steps" not in result:
                logger.warning("Missing 'steps' key in correct solution result, using default")
                result["steps"] = result.get("steps", [])

            logger.info(f"Generated correct solution with {len(result['steps'])} steps")
            return result

        except Exception as e:
            logger.error(f"Correct solution generation failed: {e}")
            raise GenerationError(f"Failed to generate correct solution: {str(e)}")

    async def generate_variation(
        self,
        original_question: str,
        variation_type: str = "difficulty",
        target_level: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Generate a problem variation.

        Args:
            original_question: Original question text
            variation_type: Type of variation ("difficulty", "context", "concept")
            target_level: Target difficulty level (0.0-1.0) for difficulty variations

        Returns:
            Dict with variation details (keys depend on variation_type)

        Raises:
            GenerationError: If generation fails
            ValueError: If variation_type is invalid
        """
        try:
            valid_types = {"difficulty", "context", "concept"}
            if variation_type not in valid_types:
                raise ValueError(f"Invalid variation_type: {variation_type}. Must be one of {valid_types}")

            # Get prompt
            prompt = get_problem_variation_prompt(
                original_question,
                variation_type,
                target_level
            )

            # Generate using LLM
            response = await self.llm.generate(
                prompt=prompt,
                format="json",
                temperature=0.6
            )

            # Parse JSON response
            result = LLMJSONParser.safe_parse(
                response,
                default={
                    "question_stem": original_question,
                    "variation_failed": True
                }
            )

            # Validate required keys
            if "question_stem" not in result:
                logger.warning("Missing 'question_stem' in variation result, using default")
                result["question_stem"] = original_question

            logger.info(f"Generated {variation_type} variation successfully")
            return result

        except ValueError as e:
            raise e
        except Exception as e:
            logger.error(f"Problem variation generation failed: {e}")
            raise GenerationError(f"Failed to generate problem variation: {str(e)}")
