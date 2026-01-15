"""
인지 진단 데이터 모델

Personal Knowledge Graph (PKG) 및 진단 결과 스키마
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from enum import Enum
from datetime import datetime


class ErrorType(str, Enum):
    """오류 유형 분류"""
    CALCULATION_SLIP = "calculation_slip"       # 단순 계산 실수
    KNOWLEDGE_GAP = "knowledge_gap"             # 개념 부족
    MISCONCEPTION = "misconception"             # 오개념 (잘못된 규칙 적용)
    PROCEDURAL_ERROR = "procedural_error"       # 절차적 오류
    COMPREHENSION_ERROR = "comprehension_error" # 문제 이해 오류
    GUESSING = "guessing"                       # 추측/찍기
    PARTIAL_UNDERSTANDING = "partial_understanding"  # 부분적 이해


class RelationType(str, Enum):
    """지식 그래프 관계 유형"""
    MASTERED = "mastered"                # 완전히 이해함
    UNDERSTANDS = "understands"          # 이해함 (약간의 실수 가능)
    STRUGGLES_WITH = "struggles_with"    # 어려워함
    MISCONCEIVES = "misconceives"        # 오개념 보유
    NOT_ATTEMPTED = "not_attempted"      # 아직 시도 안 함


@dataclass
class KnowledgeGraphOperation:
    """지식 그래프 업데이트 연산"""
    operation: str  # "create", "update", "delete"
    relation: RelationType
    concept: str
    strength: float  # 0.0 ~ 1.0
    evidence: Optional[str] = None  # 근거가 되는 문제 ID 또는 설명
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "operation": self.operation,
            "relation": self.relation.value,
            "concept": self.concept,
            "strength": self.strength,
            "evidence": self.evidence,
            "timestamp": self.timestamp.isoformat()
        }


@dataclass
class DiagnosisResult:
    """인지 진단 결과"""
    # 기본 정보
    student_id: str
    question_id: Optional[str]
    question_content: str
    student_answer: str
    correct_answer: Optional[str]
    is_correct: bool

    # 진단 결과
    error_type: Optional[ErrorType]
    reasoning_trace: str  # LLM의 추론 과정
    error_location: Optional[str]  # 오류 발생 지점

    # 피드백
    feedback: str  # 학생에게 제공할 피드백
    recommendation: str  # 다음 학습 추천

    # 지식 그래프 업데이트
    kg_operations: List[KnowledgeGraphOperation] = field(default_factory=list)

    # 메타데이터
    confidence: float = 0.0  # LLM 진단 신뢰도
    concepts_involved: List[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "student_id": self.student_id,
            "question_id": self.question_id,
            "question_content": self.question_content,
            "student_answer": self.student_answer,
            "correct_answer": self.correct_answer,
            "is_correct": self.is_correct,
            "error_type": self.error_type.value if self.error_type else None,
            "reasoning_trace": self.reasoning_trace,
            "error_location": self.error_location,
            "feedback": self.feedback,
            "recommendation": self.recommendation,
            "kg_operations": [op.to_dict() for op in self.kg_operations],
            "confidence": self.confidence,
            "concepts_involved": self.concepts_involved,
            "timestamp": self.timestamp.isoformat()
        }


@dataclass
class ConceptMastery:
    """개념별 숙련도"""
    concept: str
    relation: RelationType
    strength: float  # 0.0 ~ 1.0
    attempt_count: int = 0
    correct_count: int = 0
    last_attempt: Optional[datetime] = None
    misconceptions: List[str] = field(default_factory=list)  # 관련 오개념들

    @property
    def accuracy(self) -> float:
        if self.attempt_count == 0:
            return 0.0
        return self.correct_count / self.attempt_count


@dataclass
class StudentKnowledgeProfile:
    """학생 개인 지식 프로파일 (PKG 기반)"""
    student_id: str
    concepts: Dict[str, ConceptMastery] = field(default_factory=dict)
    diagnosis_history: List[DiagnosisResult] = field(default_factory=list)

    # 통계
    total_attempts: int = 0
    total_correct: int = 0

    # 메타데이터
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    @property
    def overall_accuracy(self) -> float:
        if self.total_attempts == 0:
            return 0.0
        return self.total_correct / self.total_attempts

    @property
    def weak_concepts(self) -> List[str]:
        """약점 개념 목록 (strength < 0.5)"""
        return [
            concept for concept, mastery in self.concepts.items()
            if mastery.strength < 0.5
        ]

    @property
    def strong_concepts(self) -> List[str]:
        """강점 개념 목록 (strength >= 0.8)"""
        return [
            concept for concept, mastery in self.concepts.items()
            if mastery.strength >= 0.8
        ]

    @property
    def misconception_concepts(self) -> List[str]:
        """오개념 보유 개념 목록"""
        return [
            concept for concept, mastery in self.concepts.items()
            if mastery.relation == RelationType.MISCONCEIVES
        ]

    def apply_operation(self, operation: KnowledgeGraphOperation):
        """지식 그래프 연산 적용"""
        concept = operation.concept

        if operation.operation == "create" or operation.operation == "update":
            if concept not in self.concepts:
                self.concepts[concept] = ConceptMastery(
                    concept=concept,
                    relation=operation.relation,
                    strength=operation.strength
                )
            else:
                # 기존 개념 업데이트
                existing = self.concepts[concept]
                existing.relation = operation.relation
                # Exponential moving average로 strength 업데이트
                alpha = 0.3
                existing.strength = alpha * operation.strength + (1 - alpha) * existing.strength
                existing.last_attempt = operation.timestamp

        elif operation.operation == "delete":
            if concept in self.concepts:
                del self.concepts[concept]

        self.updated_at = datetime.now()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "student_id": self.student_id,
            "concepts": {
                k: {
                    "concept": v.concept,
                    "relation": v.relation.value,
                    "strength": v.strength,
                    "attempt_count": v.attempt_count,
                    "correct_count": v.correct_count,
                    "accuracy": v.accuracy,
                    "misconceptions": v.misconceptions
                }
                for k, v in self.concepts.items()
            },
            "total_attempts": self.total_attempts,
            "total_correct": self.total_correct,
            "overall_accuracy": self.overall_accuracy,
            "weak_concepts": self.weak_concepts,
            "strong_concepts": self.strong_concepts,
            "misconception_concepts": self.misconception_concepts,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }

    def to_graph_data(self) -> Dict[str, Any]:
        """시각화용 그래프 데이터 생성"""
        nodes = []
        edges = []

        # 학생 노드
        nodes.append({
            "id": self.student_id,
            "label": "Student",
            "type": "student"
        })

        # 개념 노드 및 엣지
        for concept, mastery in self.concepts.items():
            # 개념 노드
            nodes.append({
                "id": concept,
                "label": concept,
                "type": "concept",
                "strength": mastery.strength
            })

            # 학생-개념 엣지
            edges.append({
                "source": self.student_id,
                "target": concept,
                "relation": mastery.relation.value,
                "strength": mastery.strength
            })

        return {"nodes": nodes, "edges": edges}
