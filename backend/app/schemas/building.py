from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel


class BuildingRead(BaseModel):
    id: UUID
    project_id: UUID
    osm_id: str | None
    area_m2: float
    usable_roof_area_m2: float
    building_type: str
    address: str | None
    source: str
    lead_score: float
    opportunity_level: str
    estimated_solar_potential: float
    has_existing_panels: bool
    panel_confidence: float
    type_priority_score: float
    accessibility_score: float
    scoring_explanation: dict[str, Any]
    recommended_action: str


class BuildingFeature(BaseModel):
    type: Literal["Feature"] = "Feature"
    geometry: dict[str, Any]
    properties: BuildingRead


class BuildingFeatureCollection(BaseModel):
    type: Literal["FeatureCollection"] = "FeatureCollection"
    features: list[BuildingFeature]
