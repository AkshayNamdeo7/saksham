from typing import Optional

from pydantic import BaseModel, Field, field_validator


class SchemeBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=200)
    slug: str = Field(..., min_length=2, max_length=200)
    description: str = ""
    category: str = Field(..., description="micro_finance|term_loan|education")
    purpose: str = Field(..., description="business|self_employment|education")
    max_loan: float = Field(ge=0)
    min_loan: float = Field(ge=0)
    interest_rate: float = Field(ge=0, le=100)
    tenure_months: int = Field(ge=1)
    moratorium_months: int = Field(ge=0)
    income_threshold: Optional[float] = Field(default=None, ge=0)
    project_min: Optional[float] = Field(default=None, ge=0)
    project_max: Optional[float] = Field(default=None, ge=0)
    education_focus: bool = False
    eligibility_notes: str = ""
    required_documents: str = ""
    partner_required: bool = True
    active: bool = True
    is_demo: bool = True

    @field_validator("max_loan")
    @classmethod
    def validate_max_loan(cls, v):
        if v <= 0:
            raise ValueError("max_loan must be greater than 0")
        return v


class SchemeCreate(SchemeBase):
    document_keys: Optional[list[str]] = []


class SchemeUpdate(BaseModel):
    name: Optional[str] = None
    slug: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    purpose: Optional[str] = None
    max_loan: Optional[float] = Field(default=None, ge=0)
    min_loan: Optional[float] = Field(default=None, ge=0)
    interest_rate: Optional[float] = Field(default=None, ge=0, le=100)
    tenure_months: Optional[int] = Field(default=None, ge=1)
    moratorium_months: Optional[int] = Field(default=None, ge=0)
    income_threshold: Optional[float] = Field(default=None, ge=0)
    project_min: Optional[float] = Field(default=None, ge=0)
    project_max: Optional[float] = Field(default=None, ge=0)
    education_focus: Optional[bool] = None
    eligibility_notes: Optional[str] = None
    required_documents: Optional[str] = None
    partner_required: Optional[bool] = None
    active: Optional[bool] = None
    document_keys: Optional[list[str]] = None


class SchemeOut(SchemeBase):
    id: int
    document_keys: list[str] = []

    class Config:
        from_attributes = True


class DocumentOut(BaseModel):
    id: int
    key: str
    name: str
    name_hi: Optional[str]
    description: str
    is_required: bool
    applies_to: str

    class Config:
        from_attributes = True


class PartnerBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=200)
    type: str = Field(..., description="SCA|PSB|RRB|NBFC-MFI")
    state: str = ""
    district: str = ""
    city: str = ""
    address: str = ""
    latitude: float = 0
    longitude: float = 0
    status: str = "accepting"
    capacity_pct: int = Field(default=100, ge=0, le=100)
    fund_utilization_pct: float = Field(default=0, ge=0)
    npa_indicator: str = "low"
    phone: str = ""
    email: Optional[str] = None
    accepting_applications: bool = True
    scheme_slugs: Optional[list[str]] = []


class PartnerCreate(PartnerBase):
    pass


class PartnerUpdate(BaseModel):
    name: Optional[str] = None
    type: Optional[str] = None
    state: Optional[str] = None
    district: Optional[str] = None
    city: Optional[str] = None
    address: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    status: Optional[str] = None
    capacity_pct: Optional[int] = Field(default=None, ge=0, le=100)
    fund_utilization_pct: Optional[float] = Field(default=None, ge=0)
    npa_indicator: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    accepting_applications: Optional[bool] = None
    scheme_slugs: Optional[list[str]] = None


class PartnerOut(PartnerBase):
    id: int
    scheme_slugs: list[str] = []
    is_demo: bool = True

    class Config:
        from_attributes = True


class EligibilityCheckRequest(BaseModel):
    age: Optional[int] = Field(default=None, ge=18, le=100)
    state: Optional[str] = None
    district: Optional[str] = None
    city: Optional[str] = None
    annual_family_income: Optional[float] = Field(default=None, ge=0)
    purpose: str = Field(..., description="business|self_employment|education")
    project_type: Optional[str] = None
    project_cost: Optional[float] = Field(default=None, ge=0)
    education_level: Optional[str] = None
    course_type: Optional[str] = None
    institution_type: Optional[str] = None
    education_cost: Optional[float] = Field(default=None, ge=0)
    requested_loan: Optional[float] = Field(default=None, ge=0)

    @field_validator("purpose")
    @classmethod
    def validate_purpose(cls, v):
        allowed = {"business", "self_employment", "education"}
        if v not in allowed:
            raise ValueError("purpose must be one of business, self_employment, education")
        return v


class RecommendRequest(BaseModel):
    profile: EligibilityCheckRequest
    scheme_ids: Optional[list[int]] = None


class LoanCalcRequest(BaseModel):
    principal: float = Field(..., gt=0)
    annual_rate: float = Field(..., ge=0)
    tenure: float = Field(..., gt=0)
    tenure_unit: str = Field("months", pattern="^(months|years)$")
    moratorium_months: int = Field(default=0, ge=0)
    scheme_max_loan: Optional[float] = Field(default=None, ge=0)


class PartnerRecommendRequest(BaseModel):
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    district: Optional[str] = None
    state: Optional[str] = None
    scheme_id: Optional[int] = None
    purpose: Optional[str] = None
    loan_amount: Optional[float] = Field(default=None, ge=0)
    limit: int = Field(default=5, ge=1, le=20)


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=2000)
    language: str = Field("en", pattern="^(en|hi)$")
    history: Optional[list[dict]] = []


class AdminLoginRequest(BaseModel):
    username: str = Field(..., min_length=1)
    password: str = Field(..., min_length=1)


class ErrorResponse(BaseModel):
    detail: str
