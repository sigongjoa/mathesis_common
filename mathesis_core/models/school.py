
from pydantic import BaseModel, Field
from typing import List, Optional, Dict

class Subject(BaseModel):
    """Subject within a curriculum"""
    name: str
    code: Optional[str] = None
    credit: float = 0.0
    semester: int = 1

class Curriculum(BaseModel):
    """Curriculum for a grade/year"""
    year: int
    grade: int
    subjects: List[Subject] = []

class AchievementStat(BaseModel):
    """Academic achievement statistics"""
    grade: int
    semester: int
    subject: str
    mean: float
    std_dev: float
    grade_distribution: Dict[str, float]  # A, B, C, D, E ratios

class SchoolData(BaseModel):
    """Aggregated school data"""
    school_code: str
    school_name: str
    address: Optional[str] = None
    founding_date: Optional[str] = None
    curriculum: List[Curriculum] = []
    achievement_stats: List[AchievementStat] = []
