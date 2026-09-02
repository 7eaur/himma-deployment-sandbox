from pydantic import BaseModel, ConfigDict, Field, field_validator
from typing import Any, Literal, Optional
from datetime import datetime
from decimal import Decimal
import re


class ResearcherLogin(BaseModel):
    username: str = Field(min_length=2, max_length=150)
    password: str = Field(min_length=1, max_length=200)


class StudentLogin(BaseModel):
    access_code: str

    @field_validator("access_code")
    @classmethod
    def normalize_access_code(cls, value: str) -> str:
        return value.strip()


class UserResponse(BaseModel):
    id: int
    username: str
    role: str
    model_config = ConfigDict(from_attributes=True)


class SupervisorProfileUpdateRequest(BaseModel):
    username: str = Field(min_length=2, max_length=150)

    @field_validator("username")
    @classmethod
    def normalize_username(cls, value: str) -> str:
        normalized = " ".join(value.split())
        if len(normalized) < 2:
            raise ValueError("اسم المشرف يجب أن يحتوي على حرفين على الأقل")
        if any(ord(character) < 32 for character in normalized):
            raise ValueError("اسم المشرف يحتوي على رموز غير مدعومة")
        return normalized


class SupervisorPasswordChangeRequest(BaseModel):
    current_password: str = Field(min_length=1, max_length=200)
    new_password: str = Field(min_length=8, max_length=200)


class SupervisorCreateRequest(BaseModel):
    username: str = Field(min_length=2, max_length=150)
    password: str = Field(min_length=8, max_length=200)

    @field_validator("username")
    @classmethod
    def normalize_supervisor_username(cls, value: str) -> str:
        return SupervisorProfileUpdateRequest.normalize_username(value)


class SupervisorResponse(BaseModel):
    id: int
    username: str
    is_active: bool
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class StudentCreateRequest(BaseModel):
    full_name: str = Field(min_length=2, max_length=80)
    grade_level: Literal[3] = 3
    access_code: Optional[str] = None

    @field_validator("full_name")
    @classmethod
    def normalize_full_name(cls, value: str) -> str:
        normalized = " ".join(value.split())
        if len(normalized) < 2:
            raise ValueError("اسم الطالب يجب أن يحتوي على حرفين على الأقل")
        if any(ord(character) < 32 for character in normalized):
            raise ValueError("اسم الطالب يحتوي على رموز غير مدعومة")
        return normalized

    @field_validator("access_code")
    @classmethod
    def validate_access_code(cls, value: Optional[str]) -> Optional[str]:
        if value is None or not value.strip():
            return None
        normalized = value.strip()
        if not re.fullmatch(r"\d{6}", normalized):
            raise ValueError("رمز دخول الطالب يجب أن يتكون من 6 أرقام")
        return normalized


class StudentUpdateRequest(BaseModel):
    full_name: Optional[str] = Field(default=None, min_length=2, max_length=80)
    is_active: Optional[bool] = None

    @field_validator("full_name")
    @classmethod
    def normalize_optional_full_name(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        return StudentCreateRequest.normalize_full_name(value)


class StudentAccessCodeUpdateRequest(BaseModel):
    access_code: Optional[str] = None

    @field_validator("access_code")
    @classmethod
    def validate_optional_access_code(cls, value: Optional[str]) -> Optional[str]:
        if value is None or not value.strip():
            return None
        normalized = value.strip()
        if not re.fullmatch(r"\d{6}", normalized):
            raise ValueError("رمز دخول الطالب يجب أن يتكون من 6 أرقام")
        return normalized


class StudentResponse(BaseModel):
    id: int
    full_name: str
    access_code: str
    grade_level: Literal[3]
    current_level: int
    status: Literal["active", "inactive"]
    posttest_enabled: bool
    posttest_eligible: bool
    core_completed_items: int = 0
    core_total_items: int = 10
    core_completed: bool = False
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class StudentPosttestAccessRequest(BaseModel):
    enabled: bool


class StudentProfileResponse(BaseModel):
    id: int
    full_name: str
    access_code: str
    grade_level: Literal[3]
    current_level: int
    status: Literal["active", "inactive"]
    posttest_enabled: bool
    next_action: Literal["resume", "pretest", "learning", "posttest", "completed"]
    active_session: Optional["AssessmentSessionResponse"] = None


class MeResponse(BaseModel):
    id: int
    role: str
    display_name: str


class AssessmentStartRequest(BaseModel):
    session_type: Literal["pretest", "posttest"]


class AssessmentSessionResponse(BaseModel):
    id: int
    session_type: str
    status: str
    elapsed_seconds: int
    started_at: datetime
    completed_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)


class AssessmentProgressResponse(BaseModel):
    completed_items: int
    total_items: int
    completed_steps: int
    total_steps: int
    has_pending_item: bool
    elapsed_seconds: int


class ContentOptionResponse(BaseModel):
    id: int
    text: str
    order_index: int
    model_config = ConfigDict(from_attributes=True)


class ContentAssetResponse(BaseModel):
    asset_id: str
    asset_type: str
    usage: Optional[str] = None
    semantic_text: Optional[str] = None
    url: str
    option_id: Optional[int] = None


# Legacy engine response retained for internal compatibility/tests. The student
# web app no longer consumes this payload.
class ContentStepResponse(BaseModel):
    id: int
    order_index: int
    prompt_text: str
    instruction_text: Optional[str] = None
    expected_reading_text: Optional[str] = None
    options: list[ContentOptionResponse] = Field(default_factory=list)
    assets: list[ContentAssetResponse] = Field(default_factory=list)
    media_gaps: list[dict[str, Any]] = Field(default_factory=list)
    model_config = ConfigDict(from_attributes=True)


class ContentItemResponse(BaseModel):
    id: int
    stable_key: str
    canonical_id: Optional[str] = None
    kind: str
    interaction_type: str
    title: Optional[str] = None
    source_method: Optional[str] = None
    steps: list[ContentStepResponse] = Field(default_factory=list)
    item_assets: list[ContentAssetResponse] = Field(default_factory=list)
    template_data: Optional[dict[str, Any]] = None
    model_config = ConfigDict(from_attributes=True)


# Clean student-view response. prompt_text/template_data are deliberately absent.
class AssessmentStimulusResponse(BaseModel):
    kind: str = "none"
    text: Optional[str] = None
    audio_target: Optional[str] = None


class AssessmentPresentationResponse(BaseModel):
    version: str
    question_number: int
    section: str
    skill: str
    encouragement: str
    question_text: str
    instruction_text: str
    interaction_type: str
    stimulus: AssessmentStimulusResponse = Field(default_factory=AssessmentStimulusResponse)
    media_semantics: Optional[dict[str, Any]] = None


class StudentContentStepResponse(BaseModel):
    id: int
    order_index: int
    expected_reading_text: Optional[str] = None
    required_selection_count: int = 0
    options: list[ContentOptionResponse] = Field(default_factory=list)
    assets: list[ContentAssetResponse] = Field(default_factory=list)
    media_gaps: list[dict[str, Any]] = Field(default_factory=list)


class AssessmentStudentViewResponse(BaseModel):
    id: int
    stable_key: str
    canonical_id: Optional[str] = None
    kind: str
    interaction_type: str
    title: Optional[str] = None
    steps: list[StudentContentStepResponse] = Field(default_factory=list)
    item_assets: list[ContentAssetResponse] = Field(default_factory=list)
    presentation: AssessmentPresentationResponse


class AttemptResponseSubmit(BaseModel):
    step_id: int
    selected_option_id: Optional[int] = None
    audio_storage_key: Optional[str] = None
    audio_file_size: Optional[int] = Field(default=None, gt=0)
    audio_mime_type: Optional[str] = None
    audio_duration_seconds: Optional[Decimal] = None
    elapsed_seconds: int = Field(default=0, ge=0, le=3600)


class AudioSubmissionReviewResponse(BaseModel):
    id: int
    storage_key: str
    status: str
    submitted_at: datetime
    model_config = ConfigDict(from_attributes=True)


class GradeAudioRequest(BaseModel):
    is_valid: bool
    target_units: Optional[int] = Field(default=None, gt=0)
    deletions: int = Field(default=0, ge=0)
    substitutions: int = Field(default=0, ge=0)
    insertions: int = Field(default=0, ge=0)
    pronunciation_notes: Optional[str] = None
    fluency_notes: Optional[str] = None
    time_notes: Optional[str] = None


class SessionFinishResponse(BaseModel):
    id: int
    final_score: Decimal
    assigned_level: int
