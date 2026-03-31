from typing import Any, Dict, List, Literal
from pydantic import BaseModel, Field, HttpUrl

class DetectExportTypeRequest(BaseModel):
    columns: List[str]
    sample_rows: List[Dict[str, Any]] = Field(default_factory=list)

class ProfileExportRequest(BaseModel):
    columns: List[str]
    sample_rows: List[Dict[str, Any]] = Field(default_factory=list)

class NormalizeItemSalesRequest(BaseModel):
    file_url: HttpUrl
    options: Dict[str, Any] = Field(default_factory=dict)

class PackageKnowledgeRequest(BaseModel):
    file_url: HttpUrl
    goal: Literal["custom_gpt_knowledge", "analysis"]
    options: Dict[str, Any] = Field(default_factory=dict)

class StandardEnvelope(BaseModel):
    success: bool = True
    source_type: str
    row_grain: str
    warnings: List[str] = Field(default_factory=list)
    assumptions: List[str] = Field(default_factory=list)
    lineage: Dict[str, Any] = Field(default_factory=dict)
    data: Dict[str, Any] = Field(default_factory=dict)
