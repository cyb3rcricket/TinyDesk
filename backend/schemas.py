from pydantic import BaseModel, ConfigDict, Field, field_validator

CATEGORIES = ("Access", "Network", "Hardware", "Software", "Email", "Other")
PRIORITIES = ("Low", "Medium", "High")
STATUSES = ("New", "In Progress", "Waiting on User", "Resolved")
RECENT_ACTIVITY_LIMIT = 10
MODEL_TEXT_LIMIT = 4000
# Saved notes can be longer than the model input. Reject only a payload the
# byte cap would not already stop, and bound a copy for the model.
REQUEST_ACTIVITY_LIMIT = 5000
REQUEST_TEXT_LIMIT = 200_000

ANALYSIS_SCHEMA = {
    "type": "object",
    "properties": {
        "summary": {"type": "string"},
        "suggestedCategory": {"type": "string", "enum": list(CATEGORIES)},
        "followUps": {"type": "array", "items": {"type": "string"}},
        "draft": {"type": "string"},
    },
    "required": ["summary", "suggestedCategory", "followUps", "draft"],
}


class ActivityItem(BaseModel):
    model_config = ConfigDict(extra="ignore", str_strip_whitespace=True)

    kind: str = Field(default="", max_length=32)
    body: str = Field(default="", max_length=REQUEST_TEXT_LIMIT)
    at: str = Field(default="", max_length=64)


class TicketRequest(BaseModel):
    model_config = ConfigDict(extra="ignore", str_strip_whitespace=True)

    id: str = Field(min_length=1, max_length=40)
    subject: str = Field(min_length=1, max_length=200)
    description: str = Field(min_length=1, max_length=5000)
    requester: str = Field(default="", max_length=120)
    department: str = Field(default="", max_length=120)
    category: str = Field(min_length=1, max_length=40)
    priority: str = Field(min_length=1, max_length=40)
    status: str = Field(min_length=1, max_length=40)
    resolutionNote: str = Field(default="", max_length=REQUEST_TEXT_LIMIT)
    activity: list[ActivityItem] = Field(default_factory=list, max_length=REQUEST_ACTIVITY_LIMIT)

    @field_validator("category")
    @classmethod
    def category_allowed(cls, value: str) -> str:
        if value not in CATEGORIES:
            raise ValueError("category is not allowed")
        return value

    @field_validator("priority")
    @classmethod
    def priority_allowed(cls, value: str) -> str:
        if value not in PRIORITIES:
            raise ValueError("priority is not allowed")
        return value

    @field_validator("status")
    @classmethod
    def status_allowed(cls, value: str) -> str:
        if value not in STATUSES:
            raise ValueError("status is not allowed")
        return value


class ModelAnalysis(BaseModel):
    model_config = ConfigDict(extra="ignore", str_strip_whitespace=True)

    summary: str = Field(min_length=1, max_length=4000)
    suggestedCategory: str = Field(min_length=1, max_length=40)
    followUps: list[str] = Field(default_factory=list, max_length=20)
    draft: str = Field(min_length=1, max_length=8000)

    @field_validator("suggestedCategory")
    @classmethod
    def category_allowed(cls, value: str) -> str:
        if value not in CATEGORIES:
            raise ValueError("category is not allowed")
        return value

    @field_validator("summary", "draft")
    @classmethod
    def require_text(cls, value: str) -> str:
        text = value.strip()
        if not text:
            raise ValueError("text is empty")
        return text

    @field_validator("followUps")
    @classmethod
    def clean_followups(cls, value: list[str]) -> list[str]:
        cleaned: list[str] = []
        for item in value:
            text = item.strip()
            if not text:
                continue
            if len(text) > 500:
                raise ValueError("follow-up is too long")
            cleaned.append(text)
            if len(cleaned) == 6:
                break
        return cleaned


class AnalysisResponse(BaseModel):
    available: bool
    summary: str | None = None
    suggestedCategory: str | None = None
    followUps: list[str] | None = None
    draft: str | None = None
    message: str | None = None
