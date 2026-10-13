from pydantic import BaseModel, Field

class Paper(BaseModel):
    title: str = Field(min_length=3)
    text: str = Field(min_length=40)

class AuditRequest(BaseModel):
    question: str = Field(min_length=5)
    papers: list[Paper] = Field(min_length=1, max_length=10)

class Evidence(BaseModel):
    paper: str
    sentence: str
    score: float

class AuditResult(BaseModel):
    question: str
    evidence: list[Evidence]
    paper_assessments: list[dict]
    cross_paper_findings: list[str]
    experiment_plan: list[dict]
    executive_summary: str
    llm_summary: str | None = None
