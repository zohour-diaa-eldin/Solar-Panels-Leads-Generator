from pydantic import BaseModel, Field

from app.schemas.project import Bbox


class FranceRankAreasRequest(BaseModel):
    limit: int = Field(default=12, ge=1, le=30)
    include_weather: bool = True
    include_pvgis: bool = True


class FranceAreaRank(BaseModel):
    id: str
    name: str
    region: str
    department: str
    segment: str
    latitude: float
    longitude: float
    bbox: Bbox
    overall_score: float
    solar_score: float
    temperature_fit_score: float
    commercial_priority_score: float
    roof_area_proxy_score: float
    accessibility_score: float
    annual_irradiation_kwh_m2: float | None
    estimated_pv_output_kwh_kwp: float | None
    average_annual_temp_c: float | None
    summer_max_temp_c: float | None
    heat_risk_score: float
    recommended_action: str
    rationale: list[str]
    data_sources: list[str]
    data_quality: str


class FranceRankAreasResponse(BaseModel):
    country: str = "France"
    analysis_level: str = "city_or_sales_area"
    areas: list[FranceAreaRank]
    source_notes: list[str]
