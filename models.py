from typing import Optional
from pydantic import BaseModel, Field


class SearchCriteria(BaseModel):
    operacion: str
    rango_min: int
    rango_max: int
    recamaras: Optional[int] = None
    banios: Optional[int] = None
    colonias: list[str]


class Listing(BaseModel):
    portal: str
    title: str
    price: Optional[int] = None
    location: Optional[str] = None
    bedrooms: Optional[int] = None
    bathrooms: Optional[int] = None
    description: Optional[str] = None
    url: str


class ClassifiedListing(Listing):
    is_remate: bool = False
    remate_stage: Optional[str] = None
    risk_level: str = "unknown"
    include: bool = False
    reason: str = ""