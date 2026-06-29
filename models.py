from __future__ import annotations

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class SearchCriteria(BaseModel):
    criteria_id: str
    operacion: str
    rango_min: int
    rango_max: int
    recamaras: Optional[int] = None
    banios: Optional[int] = None
    colonias: list[str]
    state: str


class SearchResult(BaseModel):
    criteria_id: str
    query: str
    title: str
    snippet: str = ""
    url: str
    source_domain: str
    price: int | None = None
    price_source: str | None = None
    location: str | None = None
    bedrooms: int | None = None
    bathrooms: int | None = None


class PageContent(BaseModel):
    url: str
    title: str = ""
    text: str = ""
    status_code: Optional[int] = None
    fetch_error: Optional[str] = None
    html: str = ""


class Classification(BaseModel):
    criteria_id: str
    query: str
    title: str
    snippet: str
    url: str
    source_domain: str

    price: int | None = None
    price_source: str | None = None
    location: str | None = None
    bedrooms: int | None = None
    bathrooms: int | None = None

    is_remate: bool = False
    remate_stage: Optional[str] = None
    risk_level: str = "unknown"
    include: bool = False
    confidence: float = 0.0
    reason: str = ""
    red_flags: list[str] = Field(default_factory=list)
    matches_price_range: bool = False
    matches_bedrooms: bool = False
    matches_bathrooms: bool = False
    matches_location: bool = False 
    created_at: datetime = Field(default_factory=datetime.utcnow)

# class Classification(BaseModel):
#     criteria_id: str
#     query: str
#     title: str
#     snippet: str
#     url: str
#     source_domain: str

#     is_remate: bool = False
#     remate_stage: Optional[str] = None
#     risk_level: str = "unknown"
#     include: bool = False
#     confidence: float = 0.0
#     reason: str = ""
#     red_flags: list[str] = Field(default_factory=list)
#     created_at: datetime = Field(default_factory=datetime.utcnow)