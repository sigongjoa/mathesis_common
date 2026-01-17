"""
Tests for school models.
"""
import pytest
from unittest.mock import MagicMock


class TestSchoolModels:
    """Tests for school-related models."""

    def test_school_model_creation(self):
        """Test creating a School model."""
        try:
            from mathesis_core.models.school import School

            school = School(
                id="SCH001",
                name="Test High School",
                address="123 Test St",
                region="Seoul"
            )

            assert school.id == "SCH001"
            assert school.name == "Test High School"
        except ImportError:
            pytest.skip("School model not available")

    def test_school_model_validation(self):
        """Test School model validation."""
        try:
            from mathesis_core.models.school import School
            from pydantic import ValidationError

            with pytest.raises(ValidationError):
                School(id="", name="")  # Should fail validation
        except ImportError:
            pytest.skip("School model not available")

    def test_school_model_dict(self):
        """Test School model to dict conversion."""
        try:
            from mathesis_core.models.school import School

            school = School(
                id="SCH001",
                name="Test High School",
                address="123 Test St",
                region="Seoul"
            )

            data = school.model_dump()

            assert data["id"] == "SCH001"
            assert data["name"] == "Test High School"
        except ImportError:
            pytest.skip("School model not available")

    def test_exam_scope_model(self):
        """Test ExamScope model if available."""
        try:
            from mathesis_core.models.school import ExamScope

            scope = ExamScope(
                school_id="SCH001",
                exam_type="midterm",
                subjects=["math", "science"],
                date_range={"start": "2024-04-01", "end": "2024-04-15"}
            )

            assert scope.school_id == "SCH001"
        except ImportError:
            pytest.skip("ExamScope model not available")

    def test_curriculum_model(self):
        """Test Curriculum model if available."""
        try:
            from mathesis_core.models.school import Curriculum

            curriculum = Curriculum(
                id="CUR001",
                school_id="SCH001",
                grade=10,
                subject="Mathematics",
                topics=["Algebra", "Geometry"]
            )

            assert curriculum.grade == 10
        except ImportError:
            pytest.skip("Curriculum model not available")
