"""Assessment schemas for LMS add-on"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class AssessmentType(str, Enum):
    QUIZ = "quiz"
    EXAM = "exam"
    ASSIGNMENT = "assignment"


class Question(BaseModel):
    """Schema for a single question"""
    id: str
    question: str
    type: str  # multiple_choice, true_false, short_answer, essay
    options: Optional[List[str]] = None
    correct_answer: Optional[str] = None
    points: float = 1.0


class AssessmentBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    assessment_type: AssessmentType = AssessmentType.QUIZ
    passing_score: float = Field(default=70.0, ge=0, le=100)
    time_limit_minutes: Optional[int] = Field(None, ge=1)
    max_attempts: int = Field(default=3, ge=1)


class AssessmentCreate(AssessmentBase):
    """Schema for creating an assessment"""
    course_id: int
    questions: List[Question]


class AssessmentUpdate(BaseModel):
    """Schema for updating an assessment"""
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    assessment_type: Optional[AssessmentType] = None
    questions: Optional[List[Question]] = None
    passing_score: Optional[float] = Field(None, ge=0, le=100)
    time_limit_minutes: Optional[int] = Field(None, ge=1)
    max_attempts: Optional[int] = Field(None, ge=1)


class AssessmentResponse(AssessmentBase):
    """Schema for assessment response (without correct answers)"""
    id: int
    course_id: int
    questions: List[Dict[str, Any]]  # Questions without correct answers for students
    created_at: datetime
    
    class Config:
        from_attributes = True


class AssessmentSubmit(BaseModel):
    """Schema for submitting an assessment"""
    answers: Dict[str, str]  # question_id -> answer


class AssessmentSubmissionResponse(BaseModel):
    """Schema for assessment submission response"""
    id: int
    assessment_id: int
    user_id: int
    score: float
    passed: bool
    attempt_number: int
    submitted_at: datetime
    graded_at: Optional[datetime] = None
    feedback: Optional[str] = None
    
    class Config:
        from_attributes = True


class AssessmentResultDetail(AssessmentSubmissionResponse):
    """Detailed assessment result with question-by-question breakdown"""
    total_questions: int
    correct_answers: int
    answers: Dict[str, Any]
