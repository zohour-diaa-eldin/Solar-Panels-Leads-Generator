from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


class Bbox(BaseModel):
    south: float = Field(..., ge=-90, le=90)
    west: float = Field(..., ge=-180, le=180)
    north: float = Field(..., ge=-90, le=90)
    east: float = Field(..., ge=-180, le=180)

    @field_validator("north")
    @classmethod
    def validate_latitude_order(cls, value: float, info) -> float:
        south = info.data.get("south")
        if south is not None and value <= south:
            raise ValueError("north must be greater than south")
        return value

    @field_validator("east")
    @classmethod
    def validate_longitude_order(cls, value: float, info) -> float:
        west = info.data.get("west")
        if west is not None and value <= west:
            raise ValueError("east must be greater than west")
        return value


class ProjectCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=160)
    city: str | None = Field(default=None, max_length=120)
    bbox: Bbox | None = None


class ProjectRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    city: str | None
    status: str
    bbox: dict | None
    created_at: datetime
    updated_at: datetime


class AnalyzeBboxRequest(BaseModel):
    bbox: Bbox
    limit: int = Field(default=220, ge=1, le=600)


class AnalyzeBboxResponse(BaseModel):
    project_id: UUID
    fetched_count: int
    analyzed_count: int
    source: str
    message: str


class SummaryLead(BaseModel):
    id: UUID
    osm_id: str | None
    address: str | None
    building_type: str
    area_m2: float
    usable_roof_area_m2: float
    lead_score: float
    opportunity_level: str
    estimated_solar_potential: float
    recommended_action: str


class ProjectSummary(BaseModel):
    project_id: UUID
    total_buildings: int
    high_opportunity_count: int
    medium_opportunity_count: int
    low_opportunity_count: int
    estimated_total_roof_area_m2: float
    top_leads: list[SummaryLead]
