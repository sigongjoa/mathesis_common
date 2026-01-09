"""
Analysis prompts for DNA extraction.
"""


def get_tagging_prompt(question_text: str) -> str:
    """
    Get prompt for tag extraction from question.

    Args:
        question_text: Question content

    Returns:
        Formatted prompt for LLM
    """
    return f"""Analyze this educational question and generate relevant tags.

Question:
{question_text}

Identify and categorize tags in these types:
1. subject: Main subject area (Math, Science, English, etc.)
2. concept: Specific concepts (Algebra, Geometry, Quadratics, etc.)
3. skill: Required skills (Problem Solving, Critical Thinking, etc.)
4. cognitive_level: Bloom's taxonomy (Remember, Understand, Apply, Analyze, Evaluate, Create)
5. difficulty: Difficulty level (Easy, Medium, Hard)

Return JSON array of tags with confidence scores (0.0-1.0):
{{
    "tags": [
        {{"tag": "Mathematics", "type": "subject", "confidence": 0.99}},
        {{"tag": "Algebra", "type": "concept", "confidence": 0.95}},
        {{"tag": "Apply", "type": "cognitive_level", "confidence": 0.90}}
    ]
}}

Be precise and assign high confidence (>0.9) only to clearly relevant tags."""


def get_metadata_prompt(question_text: str) -> str:
    """
    Get prompt for metadata extraction.

    Args:
        question_text: Question content

    Returns:
        Formatted prompt for LLM
    """
    return f"""Analyze this educational question and provide metadata.

Question:
{question_text}

Return JSON with exact fields:
{{
    "cognitive_level": "one of: Remember|Understand|Apply|Analyze|Evaluate|Create",
    "difficulty_estimation": 0.0-1.0 (0.0=easiest, 1.0=hardest),
    "estimated_time_minutes": integer (realistic time to solve),
    "subject_area": "Math|Science|English|Social Studies|etc",
    "curriculum_path": "Subject.Topic.Subtopic (e.g., Math.Algebra.Quadratics)",
    "requires_calculator": true/false,
    "language": "Korean|English|Mixed"
}}"""


def get_curriculum_prompt(question_text: str) -> str:
    """
    Get prompt for curriculum path suggestion.

    Args:
        question_text: Question content

    Returns:
        Formatted prompt for LLM
    """
    return f"""Given this question, suggest the most specific curriculum path in dot notation.

Question: {question_text}

Example paths:
- Math.Algebra.Linear_Equations
- Math.Geometry.Triangles.Pythagorean_Theorem
- Science.Physics.Mechanics.Kinematics
- Math.Calculus.Derivatives.Chain_Rule

Return ONLY the path string, no explanation."""
