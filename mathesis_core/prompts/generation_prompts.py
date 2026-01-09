"""
Generation Prompts for Problem Generator.

These prompts are used for:
1. Twin question generation (isomorphic problems)
2. Error solution generation (intentionally incorrect solutions)
3. Correct solution generation (model answers)
"""
from typing import List, Dict, Any, Optional


def get_twin_question_prompt(
    original_text: str,
    metadata: Optional[Dict[str, Any]] = None
) -> str:
    """
    Get prompt for generating twin (isomorphic) questions.

    Twin questions have the same mathematical logic and solving steps,
    but different story context, numbers, and wording.

    Args:
        original_text: Original question text
        metadata: Optional metadata (domain, source, difficulty)

    Returns:
        Prompt string for LLM
    """
    return f"""You are an expert Math Item Writer for Elementary Advanced Math (Olympiad level).
Your task is to create a "Twin Problem" (Isomorphic Problem) based on the original problem.

**Rules (Strict):**
1. **Logic**: Keep the EXACT SAME mathematical logic, formula, and solving steps.
2. **Variation**: Change the story context (objects, names) and numbers.
3. **Language**: Output must be in **Natural Korean (한국어)**.
4. **Format**: Respond ONLY in JSON format.

Original Problem:
{original_text}

Target JSON Structure:
{{
    "question_stem": "The new problem text...",
    "answer": "The final answer (e.g. '15개')",
    "solution_steps": "Step-by-step explanation of the solution"
}}"""


def get_error_solution_prompt(
    question_content: str,
    correct_answer: str,
    error_types: Optional[List[str]] = None,
    difficulty: int = 2
) -> str:
    """
    Get prompt for generating intentionally incorrect solutions.

    These solutions demonstrate common student mistakes for educational purposes.

    Args:
        question_content: Question text
        correct_answer: Correct answer for reference
        error_types: Types of errors to include (e.g., "concept_misapplication", "arithmetic_error")
        difficulty: Solution complexity level (1-5)

    Returns:
        Prompt string for LLM
    """
    error_desc = ""
    if error_types:
        error_desc = f"\n주요 오류 유형: {', '.join(error_types)}"

    return f"""당신은 대한민국 수능 수학(CSAT) 및 내신 수학 전문 강사입니다.
다음 문제에 대해 학생들이 **개념적으로 가장 자주 틀리는(오개념)** 풀이 과정을 시뮬레이션해야 합니다.
{error_desc}

[오류 풀이 생성 규칙]
1. 단순 계산 실수보다 **논리적 오류(Logic Leap)**나 **조건 누락(Condition Omission)**을 우선하세요.
   - 예: 로그의 진수 조건($x>0$) 누락, 나눗셈에서 0이 아닌 조건 누락, 무연근 확인 생략 등.
2. 풀이는 4~7단계로 상세히 구성하세요.
3. 오류는 단 **한 곳**에서 발생해야 하며, 그 전까지는 완벽해야 합니다.
4. 오류 발생 이후의 과정은 그 오류를 기반으로 논리적으로 전개되어야 합니다(오답 도출).
5. 말투는 정중한 '해요체'를 사용하세요.

[입력 문제]
문제: {question_content}
정답: {correct_answer}

[출력 형식 (JSON)]
{{
  "steps": [
    {{
      "step": 1,
      "content": "문제에서 주어진 조건을 식으로 나타내면...",
      "formula": "log_2(x-1) = 3",
      "is_error": false
    }},
    {{
      "step": 2,
      "content": "로그의 정의에 따라 진수를 구합니다.",
      "formula": "x-1 = 2^3 = 8",
      "is_error": false
    }},
    {{
      "step": 3,
      "content": "따라서 x는 9입니다. 하지만 진수 조건을 확인하지 않는 실수를 범함.",
      "formula": "x = 9",
      "is_error": true,
      "error_type": "condition_omission",
      "error_explanation": "로그가 정의되려면 진수가 0보다 커야 한다는 조건(x-1>0)을 먼저 확인했어야 합니다. 이 문제에서는 우연히 답이 같을 수 있지만, 부등식이나 다른 상황에서는 치명적입니다."
    }}
  ],
  "final_wrong_answer": "오답 결과 (숫자 또는 식)"
}}

JSON만 출력하세요."""


def get_correct_solution_prompt(
    question_content: str,
    correct_answer: str
) -> str:
    """
    Get prompt for generating correct model solutions.

    Args:
        question_content: Question text
        correct_answer: Correct answer

    Returns:
        Prompt string for LLM
    """
    return f"""다음 문제에 대한 **완벽하게 정확한** 모범 풀이를 생성하세요.

문제: {question_content}
정답: {correct_answer}

출력 형식 (JSON):
{{
  "steps": [
    {{
      "step": 1,
      "content": "단계 설명",
      "formula": "수식 (선택)",
      "is_error": false
    }}
  ]
}}"""


def get_problem_variation_prompt(
    original_question: str,
    variation_type: str = "difficulty",
    target_level: Optional[float] = None
) -> str:
    """
    Get prompt for generating problem variations.

    Args:
        original_question: Original question text
        variation_type: Type of variation ("difficulty", "context", "concept")
        target_level: Target difficulty level (0.0-1.0) if variation_type is "difficulty"

    Returns:
        Prompt string for LLM
    """
    if variation_type == "difficulty" and target_level is not None:
        level_desc = "더 쉽게" if target_level < 0.5 else "더 어렵게"
        return f"""다음 문제를 {level_desc} 변형하세요 (난이도 목표: {target_level:.1f}).

원본 문제:
{original_question}

변형 규칙:
- 동일한 개념을 유지
- 난이도를 조정 (숫자 복잡도, 단계 수 조정)
- 한국어로 출력

JSON 형식:
{{
    "question_stem": "변형된 문제",
    "difficulty_estimation": {target_level},
    "changes_made": "어떤 부분을 변경했는지 설명"
}}"""

    elif variation_type == "context":
        return f"""다음 문제의 스토리 맥락을 변경하되, 수학적 구조는 유지하세요.

원본 문제:
{original_question}

변형 규칙:
- 수학적 로직은 동일
- 스토리 배경, 등장 인물/사물만 변경
- 한국어로 출력

JSON 형식:
{{
    "question_stem": "새로운 맥락의 문제",
    "context_changes": "어떤 맥락으로 변경했는지"
}}"""

    else:  # concept variation
        return f"""다음 문제와 유사하지만 다른 개념을 활용하는 문제를 생성하세요.

원본 문제:
{original_question}

변형 규칙:
- 문제 형식은 유사
- 다른 수학 개념 사용
- 한국어로 출력

JSON 형식:
{{
    "question_stem": "새로운 개념의 문제",
    "concept_used": "사용된 수학 개념",
    "difficulty_estimation": 0.0-1.0
}}"""
