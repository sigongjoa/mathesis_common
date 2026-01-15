"""
인지 진단 서비스 테스트

Mock LLM을 사용한 단위 테스트 및 실제 Ollama 연동 통합 테스트
"""

import pytest
import json
from unittest.mock import Mock, patch
from datetime import datetime

from mathesis_core.diagnosis import (
    CognitiveDiagnosisService,
    DiagnosisResult,
    ErrorType,
    KnowledgeGraphOperation,
    StudentKnowledgeProfile,
    DiagnosisPrompts
)
from mathesis_core.diagnosis.models import RelationType, ConceptMastery


class MockLLMClient:
    """테스트용 Mock LLM 클라이언트"""

    def __init__(self, response: str = None):
        self.response = response or self._default_response()

    def _default_response(self) -> str:
        return json.dumps({
            "is_correct": False,
            "reasoning_trace": "학생은 인수분해 공식을 잘못 적용했습니다.",
            "error_location": "(x+1)(x-1) 부분",
            "error_type": "misconception",
            "concepts_involved": ["인수분해", "완전제곱식"],
            "feedback": "완전제곱식 (a+b)^2 = a^2 + 2ab + b^2 공식을 다시 확인해보세요.",
            "recommendation": "완전제곱식 개념 복습",
            "confidence": 0.85,
            "kg_operations": [
                {
                    "operation": "update",
                    "relation": "misconceives",
                    "concept": "완전제곱식",
                    "strength": 0.3
                },
                {
                    "operation": "update",
                    "relation": "struggles_with",
                    "concept": "인수분해",
                    "strength": 0.4
                }
            ]
        })

    def generate(self, prompt: str, **kwargs) -> str:
        return self.response

    def chat(self, messages: list, **kwargs) -> str:
        return self.response


# ============== 단위 테스트 ==============

class TestDiagnosisModels:
    """데이터 모델 테스트"""

    def test_error_type_enum(self):
        """ErrorType enum 테스트"""
        assert ErrorType.MISCONCEPTION.value == "misconception"
        assert ErrorType.CALCULATION_SLIP.value == "calculation_slip"
        assert ErrorType.KNOWLEDGE_GAP.value == "knowledge_gap"

    def test_relation_type_enum(self):
        """RelationType enum 테스트"""
        assert RelationType.MASTERED.value == "mastered"
        assert RelationType.STRUGGLES_WITH.value == "struggles_with"
        assert RelationType.MISCONCEIVES.value == "misconceives"

    def test_kg_operation_creation(self):
        """KG Operation 생성 테스트"""
        op = KnowledgeGraphOperation(
            operation="update",
            relation=RelationType.MASTERED,
            concept="이차방정식",
            strength=0.9,
            evidence="q_001"
        )

        assert op.operation == "update"
        assert op.relation == RelationType.MASTERED
        assert op.concept == "이차방정식"
        assert op.strength == 0.9
        assert op.evidence == "q_001"

    def test_kg_operation_to_dict(self):
        """KG Operation 직렬화 테스트"""
        op = KnowledgeGraphOperation(
            operation="create",
            relation=RelationType.UNDERSTANDS,
            concept="삼각함수",
            strength=0.7
        )

        data = op.to_dict()
        assert data["operation"] == "create"
        assert data["relation"] == "understands"
        assert data["concept"] == "삼각함수"
        assert data["strength"] == 0.7

    def test_diagnosis_result_creation(self):
        """DiagnosisResult 생성 테스트"""
        result = DiagnosisResult(
            student_id="student_123",
            question_id="q_001",
            question_content="x^2 + 2x + 1을 인수분해하시오",
            student_answer="(x+1)(x-1)",
            correct_answer="(x+1)^2",
            is_correct=False,
            error_type=ErrorType.MISCONCEPTION,
            reasoning_trace="완전제곱식 공식 오적용",
            error_location="(x+1)(x-1)",
            feedback="완전제곱식 공식을 확인하세요",
            recommendation="완전제곱식 복습"
        )

        assert result.student_id == "student_123"
        assert result.is_correct is False
        assert result.error_type == ErrorType.MISCONCEPTION

    def test_diagnosis_result_to_dict(self):
        """DiagnosisResult 직렬화 테스트"""
        result = DiagnosisResult(
            student_id="student_123",
            question_id="q_001",
            question_content="문제",
            student_answer="답안",
            correct_answer="정답",
            is_correct=True,
            error_type=None,
            reasoning_trace="정확한 풀이",
            error_location=None,
            feedback="잘했습니다!",
            recommendation=""
        )

        data = result.to_dict()
        assert data["student_id"] == "student_123"
        assert data["is_correct"] is True
        assert data["error_type"] is None


class TestStudentKnowledgeProfile:
    """학생 지식 프로필 테스트"""

    def test_profile_creation(self):
        """프로필 생성 테스트"""
        profile = StudentKnowledgeProfile(student_id="student_123")
        assert profile.student_id == "student_123"
        assert len(profile.concepts) == 0
        assert profile.total_attempts == 0

    def test_apply_operation(self):
        """KG 연산 적용 테스트"""
        profile = StudentKnowledgeProfile(student_id="student_123")

        op = KnowledgeGraphOperation(
            operation="create",
            relation=RelationType.UNDERSTANDS,
            concept="미분",
            strength=0.7
        )

        profile.apply_operation(op)

        assert "미분" in profile.concepts
        assert profile.concepts["미분"].relation == RelationType.UNDERSTANDS
        assert profile.concepts["미분"].strength == 0.7

    def test_apply_update_operation(self):
        """KG 업데이트 연산 테스트 (EMA 적용)"""
        profile = StudentKnowledgeProfile(student_id="student_123")

        # 초기 생성
        op1 = KnowledgeGraphOperation(
            operation="create",
            relation=RelationType.UNDERSTANDS,
            concept="적분",
            strength=0.5
        )
        profile.apply_operation(op1)

        # 업데이트 (EMA alpha=0.3)
        op2 = KnowledgeGraphOperation(
            operation="update",
            relation=RelationType.MASTERED,
            concept="적분",
            strength=1.0
        )
        profile.apply_operation(op2)

        # 0.3 * 1.0 + 0.7 * 0.5 = 0.65
        assert profile.concepts["적분"].strength == pytest.approx(0.65, rel=0.01)
        assert profile.concepts["적분"].relation == RelationType.MASTERED

    def test_weak_concepts(self):
        """약점 개념 조회 테스트"""
        profile = StudentKnowledgeProfile(student_id="student_123")

        profile.concepts["강점개념"] = ConceptMastery(
            concept="강점개념",
            relation=RelationType.MASTERED,
            strength=0.9
        )
        profile.concepts["약점개념"] = ConceptMastery(
            concept="약점개념",
            relation=RelationType.STRUGGLES_WITH,
            strength=0.3
        )

        weak = profile.weak_concepts
        assert "약점개념" in weak
        assert "강점개념" not in weak

    def test_strong_concepts(self):
        """강점 개념 조회 테스트"""
        profile = StudentKnowledgeProfile(student_id="student_123")

        profile.concepts["강점개념"] = ConceptMastery(
            concept="강점개념",
            relation=RelationType.MASTERED,
            strength=0.9
        )
        profile.concepts["약점개념"] = ConceptMastery(
            concept="약점개념",
            relation=RelationType.STRUGGLES_WITH,
            strength=0.3
        )

        strong = profile.strong_concepts
        assert "강점개념" in strong
        assert "약점개념" not in strong

    def test_to_graph_data(self):
        """시각화용 그래프 데이터 생성 테스트"""
        profile = StudentKnowledgeProfile(student_id="student_123")
        profile.concepts["미분"] = ConceptMastery(
            concept="미분",
            relation=RelationType.MASTERED,
            strength=0.9
        )

        graph = profile.to_graph_data()

        assert len(graph["nodes"]) == 2  # student + 1 concept
        assert len(graph["edges"]) == 1


class TestDiagnosisPrompts:
    """프롬프트 템플릿 테스트"""

    def test_cognitive_diagnosis_prompt(self):
        """인지 진단 프롬프트 생성 테스트"""
        prompt = DiagnosisPrompts.cognitive_diagnosis_prompt(
            subject="수학",
            question_content="x^2 + 2x + 1을 인수분해하시오",
            student_answer="(x+1)(x-1)",
            correct_answer="(x+1)^2"
        )

        assert "수학" in prompt
        assert "x^2 + 2x + 1" in prompt
        assert "(x+1)(x-1)" in prompt
        assert "(x+1)^2" in prompt
        assert "Chain of Thought" in prompt
        assert "JSON" in prompt

    def test_batch_diagnosis_prompt(self):
        """일괄 진단 프롬프트 생성 테스트"""
        attempts = [
            {"question": "1+1=?", "student_answer": "2", "correct_answer": "2"},
            {"question": "2*3=?", "student_answer": "5", "correct_answer": "6"}
        ]

        prompt = DiagnosisPrompts.batch_diagnosis_prompt(
            subject="수학",
            attempts=attempts
        )

        assert "문제 1" in prompt
        assert "문제 2" in prompt
        assert "1+1" in prompt
        assert "2*3" in prompt


class TestCognitiveDiagnosisService:
    """인지 진단 서비스 테스트"""

    def test_diagnose_with_mock(self):
        """Mock LLM을 사용한 진단 테스트"""
        mock_client = MockLLMClient()
        service = CognitiveDiagnosisService(
            llm_client=mock_client,
            subject="수학"
        )

        result = service.diagnose(
            student_id="student_123",
            question_content="x^2 + 2x + 1을 인수분해하시오",
            student_answer="(x+1)(x-1)",
            correct_answer="(x+1)^2"
        )

        assert isinstance(result, DiagnosisResult)
        assert result.student_id == "student_123"
        assert result.is_correct is False
        assert result.error_type == ErrorType.MISCONCEPTION
        assert "완전제곱식" in result.feedback

    def test_diagnose_correct_answer(self):
        """정답인 경우 진단 테스트"""
        response = json.dumps({
            "is_correct": True,
            "reasoning_trace": "정확한 풀이입니다.",
            "error_location": None,
            "error_type": None,
            "concepts_involved": ["인수분해"],
            "feedback": "훌륭합니다!",
            "recommendation": "",
            "confidence": 0.95,
            "kg_operations": [
                {
                    "operation": "update",
                    "relation": "mastered",
                    "concept": "인수분해",
                    "strength": 0.9
                }
            ]
        })

        mock_client = MockLLMClient(response=response)
        service = CognitiveDiagnosisService(llm_client=mock_client)

        result = service.diagnose(
            student_id="student_123",
            question_content="x^2 + 2x + 1을 인수분해하시오",
            student_answer="(x+1)^2",
            correct_answer="(x+1)^2"
        )

        assert result.is_correct is True
        assert result.error_type is None

    def test_profile_update(self):
        """프로필 자동 업데이트 테스트"""
        mock_client = MockLLMClient()
        service = CognitiveDiagnosisService(llm_client=mock_client)

        # 첫 번째 진단
        service.diagnose(
            student_id="student_123",
            question_content="문제1",
            student_answer="답안1"
        )

        profile = service.get_student_profile("student_123")

        assert profile.total_attempts == 1
        assert len(profile.diagnosis_history) == 1
        assert "완전제곱식" in profile.concepts
        assert "인수분해" in profile.concepts

    def test_get_weak_concepts(self):
        """약점 개념 조회 테스트"""
        mock_client = MockLLMClient()
        service = CognitiveDiagnosisService(llm_client=mock_client)

        service.diagnose(
            student_id="student_123",
            question_content="문제",
            student_answer="답안"
        )

        weak = service.get_weak_concepts("student_123", threshold=0.5)
        assert "완전제곱식" in weak  # strength=0.3

    def test_get_recommendations(self):
        """학습 추천 테스트"""
        mock_client = MockLLMClient()
        service = CognitiveDiagnosisService(llm_client=mock_client)

        service.diagnose(
            student_id="student_123",
            question_content="문제",
            student_answer="답안"
        )

        recommendations = service.get_recommendations("student_123")
        assert len(recommendations) > 0

    def test_fallback_on_invalid_response(self):
        """잘못된 LLM 응답 시 폴백 테스트"""
        mock_client = MockLLMClient(response="invalid json response")
        service = CognitiveDiagnosisService(llm_client=mock_client)

        result = service.diagnose(
            student_id="student_123",
            question_content="문제",
            student_answer="답안",
            correct_answer="정답"
        )

        # 폴백 결과 확인
        assert result.confidence == 0.1
        assert "Fallback" in result.reasoning_trace


# ============== 통합 테스트 (실제 Ollama 필요) ==============

@pytest.mark.integration
class TestOllamaIntegration:
    """실제 Ollama 연동 통합 테스트"""

    @pytest.fixture
    def service(self):
        """실제 Ollama 클라이언트 생성"""
        try:
            from mathesis_core.diagnosis import create_diagnosis_service
            return create_diagnosis_service(
                base_url="http://localhost:11434",
                model="llama3.1:8b"
            )
        except Exception:
            pytest.skip("Ollama not available")

    def test_real_diagnosis(self, service):
        """실제 LLM 진단 테스트"""
        result = service.diagnose(
            student_id="test_student",
            question_content="x^2 - 4를 인수분해하시오",
            student_answer="(x+2)(x+2)",
            correct_answer="(x+2)(x-2)"
        )

        assert isinstance(result, DiagnosisResult)
        assert result.student_id == "test_student"
        # LLM이 오답으로 판단해야 함
        assert result.is_correct is False or "오류" in result.feedback.lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
