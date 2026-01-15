"""
생성형 인지 진단 서비스 (Generative Cognitive Diagnosis)

LLM을 활용한 Zero-shot 학습자 인지 상태 진단
BKT/IRT를 대체하는 의미론적 진단 시스템
"""

import json
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime

from mathesis_core.llm.clients import LLMClient, OllamaClient
from .models import (
    DiagnosisResult,
    ErrorType,
    KnowledgeGraphOperation,
    RelationType,
    StudentKnowledgeProfile,
    ConceptMastery
)
from .prompts import DiagnosisPrompts

logger = logging.getLogger(__name__)


class CognitiveDiagnosisService:
    """
    LLM 기반 생성형 인지 진단 서비스

    특징:
    - Zero-shot 진단: 사전 데이터 없이 즉시 진단 가능
    - Chain of Thought: 단계별 추론으로 정확한 오류 분석
    - Personal Knowledge Graph: 학생별 지식 상태 그래프 구축

    Example:
        >>> from mathesis_core.llm.clients import create_ollama_client
        >>> client = create_ollama_client(model="llama3.1:8b")
        >>> service = CognitiveDiagnosisService(client)
        >>> result = service.diagnose(
        ...     student_id="student_123",
        ...     question_content="x^2 + 2x + 1을 인수분해하시오",
        ...     student_answer="(x+1)(x-1)",
        ...     correct_answer="(x+1)^2"
        ... )
        >>> print(result.error_type)  # ErrorType.MISCONCEPTION
    """

    def __init__(
        self,
        llm_client: LLMClient,
        subject: str = "수학",
        temperature: float = 0.3
    ):
        """
        Args:
            llm_client: LLM 클라이언트 (OllamaClient 등)
            subject: 과목명 (기본값: 수학)
            temperature: LLM 온도 (낮을수록 일관성 높음)
        """
        self.llm_client = llm_client
        self.subject = subject
        self.temperature = temperature
        self._profiles: Dict[str, StudentKnowledgeProfile] = {}

    def diagnose(
        self,
        student_id: str,
        question_content: str,
        student_answer: str,
        correct_answer: Optional[str] = None,
        question_id: Optional[str] = None,
        update_profile: bool = True
    ) -> DiagnosisResult:
        """
        학생 답안 인지 진단 (동기)

        Args:
            student_id: 학생 ID
            question_content: 문제 내용
            student_answer: 학생 답안 (OCR 텍스트 포함 가능)
            correct_answer: 정답 (선택사항)
            question_id: 문제 ID (선택사항)
            update_profile: 프로필 자동 업데이트 여부

        Returns:
            DiagnosisResult: 진단 결과
        """
        # 프롬프트 생성
        prompt = DiagnosisPrompts.cognitive_diagnosis_prompt(
            subject=self.subject,
            question_content=question_content,
            student_answer=student_answer,
            correct_answer=correct_answer
        )

        # LLM 호출
        try:
            response = self.llm_client.generate(
                prompt=prompt,
                temperature=self.temperature
            )
            result = self._parse_diagnosis_response(
                response=response,
                student_id=student_id,
                question_id=question_id,
                question_content=question_content,
                student_answer=student_answer,
                correct_answer=correct_answer
            )
        except Exception as e:
            logger.error(f"LLM diagnosis failed: {e}")
            result = self._create_fallback_result(
                student_id=student_id,
                question_id=question_id,
                question_content=question_content,
                student_answer=student_answer,
                correct_answer=correct_answer,
                error=str(e)
            )

        # 프로필 업데이트
        if update_profile:
            self._update_student_profile(student_id, result)

        return result

    async def diagnose_async(
        self,
        student_id: str,
        question_content: str,
        student_answer: str,
        correct_answer: Optional[str] = None,
        question_id: Optional[str] = None,
        update_profile: bool = True
    ) -> DiagnosisResult:
        """
        학생 답안 인지 진단 (비동기)

        Args:
            student_id: 학생 ID
            question_content: 문제 내용
            student_answer: 학생 답안
            correct_answer: 정답 (선택사항)
            question_id: 문제 ID (선택사항)
            update_profile: 프로필 자동 업데이트 여부

        Returns:
            DiagnosisResult: 진단 결과
        """
        if not isinstance(self.llm_client, OllamaClient) or not self.llm_client.async_mode:
            # 동기 모드로 폴백
            return self.diagnose(
                student_id=student_id,
                question_content=question_content,
                student_answer=student_answer,
                correct_answer=correct_answer,
                question_id=question_id,
                update_profile=update_profile
            )

        # 프롬프트 생성
        prompt = DiagnosisPrompts.cognitive_diagnosis_prompt(
            subject=self.subject,
            question_content=question_content,
            student_answer=student_answer,
            correct_answer=correct_answer
        )

        # 비동기 LLM 호출
        try:
            messages = [{"role": "user", "content": prompt}]
            response = await self.llm_client.async_chat(
                messages=messages,
                temperature=self.temperature
            )
            result = self._parse_diagnosis_response(
                response=response,
                student_id=student_id,
                question_id=question_id,
                question_content=question_content,
                student_answer=student_answer,
                correct_answer=correct_answer
            )
        except Exception as e:
            logger.error(f"Async LLM diagnosis failed: {e}")
            result = self._create_fallback_result(
                student_id=student_id,
                question_id=question_id,
                question_content=question_content,
                student_answer=student_answer,
                correct_answer=correct_answer,
                error=str(e)
            )

        # 프로필 업데이트
        if update_profile:
            self._update_student_profile(student_id, result)

        return result

    def diagnose_batch(
        self,
        student_id: str,
        attempts: List[Dict[str, str]]
    ) -> Dict[str, Any]:
        """
        여러 문제에 대한 일괄 진단

        Args:
            student_id: 학생 ID
            attempts: [{"question": str, "student_answer": str, "correct_answer": str}]

        Returns:
            일괄 진단 결과
        """
        prompt = DiagnosisPrompts.batch_diagnosis_prompt(
            subject=self.subject,
            attempts=attempts
        )

        try:
            response = self.llm_client.generate(
                prompt=prompt,
                temperature=self.temperature
            )
            result = self._parse_batch_response(response, student_id)
        except Exception as e:
            logger.error(f"Batch diagnosis failed: {e}")
            result = {
                "error": str(e),
                "individual_results": [],
                "pattern_analysis": {},
                "overall_diagnosis": "진단 실패"
            }

        return result

    def evaluate_with_rubric(
        self,
        question_content: str,
        student_answer: str,
        rubric: Dict[str, Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        루브릭 기반 평가

        Args:
            question_content: 문제 내용
            student_answer: 학생 답안
            rubric: {"criterion": {"max_score": int, "description": str}}

        Returns:
            루브릭 평가 결과
        """
        prompt = DiagnosisPrompts.rubric_based_evaluation_prompt(
            subject=self.subject,
            question_content=question_content,
            student_answer=student_answer,
            rubric=rubric
        )

        try:
            response = self.llm_client.generate(
                prompt=prompt,
                temperature=self.temperature
            )
            return self._parse_rubric_response(response)
        except Exception as e:
            logger.error(f"Rubric evaluation failed: {e}")
            return {"error": str(e)}

    def get_student_profile(self, student_id: str) -> StudentKnowledgeProfile:
        """
        학생 지식 프로필 조회

        Args:
            student_id: 학생 ID

        Returns:
            StudentKnowledgeProfile: 학생의 PKG 기반 프로필
        """
        if student_id not in self._profiles:
            self._profiles[student_id] = StudentKnowledgeProfile(student_id=student_id)
        return self._profiles[student_id]

    def get_weak_concepts(self, student_id: str, threshold: float = 0.5) -> List[str]:
        """
        약점 개념 조회

        Args:
            student_id: 학생 ID
            threshold: 약점 판단 임계값 (기본 0.5)

        Returns:
            약점 개념 리스트
        """
        profile = self.get_student_profile(student_id)
        return [
            concept for concept, mastery in profile.concepts.items()
            if mastery.strength < threshold
        ]

    def get_recommendations(self, student_id: str) -> List[str]:
        """
        학습 추천 생성

        Args:
            student_id: 학생 ID

        Returns:
            추천 학습 내용 리스트
        """
        profile = self.get_student_profile(student_id)
        recommendations = []

        # 약점 개념 우선 학습
        for concept in profile.weak_concepts:
            recommendations.append(f"'{concept}' 개념 복습 필요")

        # 오개념 교정
        for concept in profile.misconception_concepts:
            recommendations.append(f"'{concept}' 오개념 교정 필요")

        return recommendations

    def _parse_diagnosis_response(
        self,
        response: str,
        student_id: str,
        question_id: Optional[str],
        question_content: str,
        student_answer: str,
        correct_answer: Optional[str]
    ) -> DiagnosisResult:
        """LLM 응답 파싱"""
        try:
            # JSON 추출
            json_str = self._extract_json(response)
            data = json.loads(json_str)

            # 오류 유형 파싱
            error_type = None
            if data.get("error_type"):
                try:
                    error_type = ErrorType(data["error_type"])
                except ValueError:
                    error_type = ErrorType.KNOWLEDGE_GAP

            # KG 연산 파싱
            kg_operations = []
            for op in data.get("kg_operations", []):
                try:
                    kg_operations.append(KnowledgeGraphOperation(
                        operation=op.get("operation", "update"),
                        relation=RelationType(op.get("relation", "struggles_with")),
                        concept=op.get("concept", ""),
                        strength=float(op.get("strength", 0.5)),
                        evidence=question_id
                    ))
                except (ValueError, KeyError) as e:
                    logger.warning(f"Failed to parse KG operation: {e}")

            return DiagnosisResult(
                student_id=student_id,
                question_id=question_id,
                question_content=question_content,
                student_answer=student_answer,
                correct_answer=correct_answer,
                is_correct=data.get("is_correct", False),
                error_type=error_type,
                reasoning_trace=data.get("reasoning_trace", ""),
                error_location=data.get("error_location"),
                feedback=data.get("feedback", ""),
                recommendation=data.get("recommendation", ""),
                kg_operations=kg_operations,
                confidence=float(data.get("confidence", 0.5)),
                concepts_involved=data.get("concepts_involved", [])
            )

        except (json.JSONDecodeError, KeyError) as e:
            logger.error(f"Failed to parse LLM response: {e}")
            return self._create_fallback_result(
                student_id=student_id,
                question_id=question_id,
                question_content=question_content,
                student_answer=student_answer,
                correct_answer=correct_answer,
                error=f"Parse error: {e}"
            )

    def _parse_batch_response(self, response: str, student_id: str) -> Dict[str, Any]:
        """일괄 진단 응답 파싱"""
        try:
            json_str = self._extract_json(response)
            data = json.loads(json_str)

            # KG 연산 적용
            profile = self.get_student_profile(student_id)
            for op in data.get("kg_operations", []):
                try:
                    operation = KnowledgeGraphOperation(
                        operation=op.get("operation", "update"),
                        relation=RelationType(op.get("relation", "struggles_with")),
                        concept=op.get("concept", ""),
                        strength=float(op.get("strength", 0.5))
                    )
                    profile.apply_operation(operation)
                except (ValueError, KeyError):
                    pass

            return data

        except (json.JSONDecodeError, KeyError) as e:
            logger.error(f"Failed to parse batch response: {e}")
            return {"error": str(e)}

    def _parse_rubric_response(self, response: str) -> Dict[str, Any]:
        """루브릭 평가 응답 파싱"""
        try:
            json_str = self._extract_json(response)
            return json.loads(json_str)
        except (json.JSONDecodeError, KeyError) as e:
            logger.error(f"Failed to parse rubric response: {e}")
            return {"error": str(e)}

    def _extract_json(self, text: str) -> str:
        """텍스트에서 JSON 추출"""
        # ```json ... ``` 블록 추출
        if "```json" in text:
            start = text.find("```json") + 7
            end = text.find("```", start)
            if end > start:
                return text[start:end].strip()

        # { ... } 직접 추출
        start = text.find("{")
        end = text.rfind("}") + 1
        if start >= 0 and end > start:
            return text[start:end]

        return text

    def _create_fallback_result(
        self,
        student_id: str,
        question_id: Optional[str],
        question_content: str,
        student_answer: str,
        correct_answer: Optional[str],
        error: str
    ) -> DiagnosisResult:
        """폴백 진단 결과 생성"""
        # 간단한 정답 비교 (폴백)
        is_correct = False
        if correct_answer:
            # 공백 제거 후 비교
            is_correct = (
                student_answer.replace(" ", "").lower() ==
                correct_answer.replace(" ", "").lower()
            )

        return DiagnosisResult(
            student_id=student_id,
            question_id=question_id,
            question_content=question_content,
            student_answer=student_answer,
            correct_answer=correct_answer,
            is_correct=is_correct,
            error_type=None if is_correct else ErrorType.KNOWLEDGE_GAP,
            reasoning_trace=f"Fallback diagnosis due to error: {error}",
            error_location=None,
            feedback="진단 시스템에 일시적인 문제가 발생했습니다. 다시 시도해주세요.",
            recommendation="",
            confidence=0.1
        )

    def _update_student_profile(self, student_id: str, result: DiagnosisResult):
        """학생 프로필 업데이트"""
        profile = self.get_student_profile(student_id)

        # 시도 횟수 업데이트
        profile.total_attempts += 1
        if result.is_correct:
            profile.total_correct += 1

        # 진단 이력 추가
        profile.diagnosis_history.append(result)

        # KG 연산 적용
        for op in result.kg_operations:
            profile.apply_operation(op)

        # 개념별 통계 업데이트
        for concept in result.concepts_involved:
            if concept not in profile.concepts:
                profile.concepts[concept] = ConceptMastery(
                    concept=concept,
                    relation=RelationType.NOT_ATTEMPTED,
                    strength=0.5
                )
            mastery = profile.concepts[concept]
            mastery.attempt_count += 1
            if result.is_correct:
                mastery.correct_count += 1
            mastery.last_attempt = datetime.now()

        profile.updated_at = datetime.now()


def create_diagnosis_service(
    base_url: str = "http://localhost:11434",
    model: str = "llama3.1:8b",
    subject: str = "수학",
    async_mode: bool = False
) -> CognitiveDiagnosisService:
    """
    인지 진단 서비스 팩토리 함수

    Args:
        base_url: Ollama 서버 URL
        model: 사용할 모델
        subject: 과목명
        async_mode: 비동기 모드 여부

    Returns:
        CognitiveDiagnosisService 인스턴스
    """
    from mathesis_core.llm.clients import create_ollama_client

    client = create_ollama_client(
        base_url=base_url,
        model=model,
        async_mode=async_mode
    )

    return CognitiveDiagnosisService(
        llm_client=client,
        subject=subject
    )
