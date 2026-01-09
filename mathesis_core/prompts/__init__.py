"""
Prompts module for mathesis-core.
Centralized prompt templates for all LLM interactions.
"""

from mathesis_core.prompts.analysis_prompts import (
    get_tagging_prompt,
    get_metadata_prompt,
    get_curriculum_prompt,
)
from mathesis_core.prompts.ocr_prompts import (
    get_vision_prompt,
)
from mathesis_core.prompts.generation_prompts import (
    get_twin_question_prompt,
    get_error_solution_prompt,
    get_correct_solution_prompt,
    get_problem_variation_prompt,
)

__all__ = [
    "get_tagging_prompt",
    "get_metadata_prompt",
    "get_curriculum_prompt",
    "get_vision_prompt",
    "get_twin_question_prompt",
    "get_error_solution_prompt",
    "get_correct_solution_prompt",
    "get_problem_variation_prompt",
]
