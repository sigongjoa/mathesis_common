"""
인지 진단 프롬프트 템플릿

Zero-Shot CoT 기반 오개념 진단 프롬프트
"""

from typing import Optional


class DiagnosisPrompts:
    """인지 진단용 프롬프트 템플릿"""

    @staticmethod
    def cognitive_diagnosis_prompt(
        subject: str,
        question_content: str,
        student_answer: str,
        correct_answer: Optional[str] = None
    ) -> str:
        """
        Zero-Shot CoT 오개념 진단 프롬프트

        Args:
            subject: 과목명 (예: "수학", "물리학")
            question_content: 문제 내용
            student_answer: 학생 답안 (OCR 추출 텍스트 포함 가능)
            correct_answer: 정답 (선택사항)

        Returns:
            완성된 프롬프트 문자열
        """
        correct_answer_section = ""
        if correct_answer:
            correct_answer_section = f"""
## 정답
{correct_answer}
"""

        return f"""# Role Definition
당신은 20년 경력의 {subject} 교육 전문가이자 인지 심리학자입니다.

# Task
아래 학생의 답안을 분석하여, 단순한 채점이 아닌 **'사고 과정의 오류'**를 진단하십시오.
학생이 왜 그런 답을 도출했는지 역추적하여 구체적인 피드백을 제공해야 합니다.

## 문제
{question_content}
{correct_answer_section}
## 학생 답안
{student_answer}

# Analysis Instructions (Chain of Thought)
다음 단계를 순서대로 수행하십시오:

1. **논리 재구성**: 학생이 답안을 작성하면서 거쳤을 단계별 논리를 추론하십시오.
2. **오류 지점 포착**: 논리 전개 과정 중 어디서 첫 번째 오류가 발생했는지 찾으십시오.
3. **오류 유형 분류**: 다음 중 하나로 분류하십시오:
   - calculation_slip: 단순 계산 실수 (개념은 알지만 연산 오류)
   - knowledge_gap: 개념 부족 (해당 개념을 모름)
   - misconception: 오개념 (잘못된 규칙이나 공식 적용)
   - procedural_error: 절차적 오류 (순서나 방법 오류)
   - comprehension_error: 문제 이해 오류 (문제를 잘못 이해함)
   - guessing: 추측/찍기
   - partial_understanding: 부분적 이해 (일부만 이해)
4. **관련 개념 추출**: 이 문제에서 다루는 핵심 개념들을 나열하십시오.
5. **최종 진단**: 학생에게 해줄 수 있는 구체적인 피드백을 작성하십시오.

# Output Format (JSON)
반드시 다음 JSON 형식으로만 응답하십시오:
```json
{{
    "is_correct": true/false,
    "reasoning_trace": "학생의 추론 과정 역추적 설명",
    "error_location": "오류가 발생한 구체적 지점 (정답일 경우 null)",
    "error_type": "오류 유형 (정답일 경우 null)",
    "concepts_involved": ["개념1", "개념2", ...],
    "feedback": "학생에게 제공할 구체적 피드백",
    "recommendation": "다음 학습 추천",
    "confidence": 0.0-1.0,
    "kg_operations": [
        {{
            "operation": "create/update",
            "relation": "mastered/understands/struggles_with/misconceives",
            "concept": "개념명",
            "strength": 0.0-1.0
        }}
    ]
}}
```
"""

    @staticmethod
    def knowledge_graph_extraction_prompt(
        diagnosis_result: str
    ) -> str:
        """
        진단 결과에서 지식 그래프 업데이트 데이터 추출

        Args:
            diagnosis_result: 이전 진단 결과 텍스트

        Returns:
            PKG 업데이트용 프롬프트
        """
        return f"""# Task
학생의 답안 분석 결과를 바탕으로 '개인 지식 그래프(PKG)'를 업데이트할 데이터를 추출하십시오.

# Input Analysis
{diagnosis_result}

# Extraction Rules
1. 학생이 완벽히 이해한 개념은 'mastered' 관계 (strength: 0.9-1.0)
2. 학생이 이해하지만 실수하는 개념은 'understands' 관계 (strength: 0.6-0.8)
3. 학생이 어려워하는 개념은 'struggles_with' 관계 (strength: 0.3-0.5)
4. 학생이 오개념을 가진 경우 'misconceives' 관계 (strength: 0.1-0.3)
5. 관계의 강도(strength)를 0.0에서 1.0 사이로 추정하십시오.

# Output Format (JSON)
```json
{{
    "operations": [
        {{
            "operation": "create/update",
            "relation": "mastered/understands/struggles_with/misconceives",
            "concept": "개념명",
            "strength": 0.0-1.0
        }}
    ]
}}
```
"""

    @staticmethod
    def batch_diagnosis_prompt(
        subject: str,
        attempts: list
    ) -> str:
        """
        여러 문제에 대한 일괄 진단 프롬프트

        Args:
            subject: 과목명
            attempts: [{"question": str, "student_answer": str, "correct_answer": str}] 리스트

        Returns:
            일괄 진단 프롬프트
        """
        attempts_text = ""
        for i, attempt in enumerate(attempts, 1):
            attempts_text += f"""
### 문제 {i}
**문제**: {attempt.get('question', '')}
**학생 답안**: {attempt.get('student_answer', '')}
**정답**: {attempt.get('correct_answer', 'N/A')}
"""

        return f"""# Role Definition
당신은 20년 경력의 {subject} 교육 전문가입니다.

# Task
아래 학생의 여러 문제 풀이를 종합적으로 분석하여 학습 패턴을 진단하십시오.

## 문제 풀이 기록
{attempts_text}

# Analysis Instructions
1. 각 문제별 오류 유형 분석
2. 반복되는 오류 패턴 식별
3. 강점과 약점 개념 파악
4. 종합적인 학습 상태 진단

# Output Format (JSON)
```json
{{
    "individual_results": [
        {{
            "question_index": 1,
            "is_correct": true/false,
            "error_type": "오류유형 또는 null",
            "concepts": ["개념1", "개념2"]
        }}
    ],
    "pattern_analysis": {{
        "recurring_errors": ["반복되는 오류 패턴"],
        "strong_concepts": ["강점 개념"],
        "weak_concepts": ["약점 개념"],
        "misconceptions": ["오개념"]
    }},
    "overall_diagnosis": "종합 진단 결과",
    "learning_path": ["추천 학습 순서"],
    "kg_operations": [
        {{
            "operation": "update",
            "relation": "relation_type",
            "concept": "개념명",
            "strength": 0.0-1.0
        }}
    ]
}}
```
"""

    @staticmethod
    def rubric_based_evaluation_prompt(
        subject: str,
        question_content: str,
        student_answer: str,
        rubric: dict
    ) -> str:
        """
        루브릭 기반 평가 프롬프트

        Args:
            subject: 과목명
            question_content: 문제 내용
            student_answer: 학생 답안
            rubric: 평가 루브릭 {"criterion": {"max_score": int, "description": str}}

        Returns:
            루브릭 평가 프롬프트
        """
        rubric_text = ""
        for criterion, details in rubric.items():
            rubric_text += f"- **{criterion}** (0-{details['max_score']}점): {details['description']}\n"

        return f"""# Role Definition
당신은 {subject} 평가 전문가입니다.

# Task
아래 학생의 답안을 주어진 루브릭에 따라 평가하십시오.

## 문제
{question_content}

## 학생 답안
{student_answer}

## 평가 루브릭
{rubric_text}

# Instructions
각 평가 항목에 대해:
1. 점수 부여 (0점부터 최대 점수까지)
2. 점수 부여 근거 설명
3. 개선을 위한 피드백 제공

# Output Format (JSON)
```json
{{
    "scores": {{
        "criterion_name": {{
            "score": 점수,
            "max_score": 최대점수,
            "rationale": "점수 부여 근거",
            "feedback": "개선 피드백"
        }}
    }},
    "total_score": 총점,
    "total_max_score": 총 최대점수,
    "overall_feedback": "종합 피드백",
    "concepts_to_review": ["복습 필요한 개념들"]
}}
```
"""
