from __future__ import annotations

from dataclasses import dataclass

from app.services.panel_detection_provider import PanelDetection
from app.services.solar_provider import SolarPotential
from app.services.weather_provider import WeatherMetrics


HIGH_PRIORITY_TYPES = {"industrial", "commercial", "warehouse", "school", "hospital", "retail", "office"}
MEDIUM_PRIORITY_TYPES = {"residential", "apartment", "apartments", "house"}


@dataclass
class LeadScore:
    lead_score: float
    opportunity_level: str
    usable_roof_area_m2: float
    type_priority_score: float
    accessibility_score: float
    scoring_explanation: dict
    recommended_action: str


def score_building(
    area_m2: float,
    building_type: str,
    solar: SolarPotential,
    panel_detection: PanelDetection,
    latitude: float,
    longitude: float,
    weather: WeatherMetrics | None = None,
) -> LeadScore:
    area_m2 = float(area_m2)
    latitude = float(latitude)
    longitude = float(longitude)
    solar.potential_score = float(solar.potential_score)
    normalized_type = (building_type or "unknown").lower()
    usability_factor = roof_usability_factor(normalized_type)
    usable_roof_area = round(area_m2 * usability_factor, 1)

    roof_area_score = min(100, (usable_roof_area / 300) * 100)
    no_existing_panel_score = 18 if panel_detection.has_existing_panels else 100
    type_priority = building_type_priority(normalized_type)
    accessibility = accessibility_proxy(latitude, longitude, area_m2)

    weighted_score = (
        solar.potential_score * 0.30
        + roof_area_score * 0.25
        + no_existing_panel_score * 0.20
        + type_priority * 0.15
        + accessibility * 0.10
    )
    lead_score = float(round(weighted_score, 1))
    opportunity = "high" if lead_score >= 75 else "medium" if lead_score >= 52 else "low"

    explanation = {
        "weights": {
            "estimated_solar_potential": 0.30,
            "usable_roof_area": 0.25,
            "no_existing_solar_panels": 0.20,
            "building_type_priority": 0.15,
            "accessibility_proximity": 0.10,
        },
        "components": {
            "estimated_solar_potential": float(round(solar.potential_score, 1)),
            "usable_roof_area": float(round(roof_area_score, 1)),
            "no_existing_solar_panels": float(round(no_existing_panel_score, 1)),
            "building_type_priority": float(round(type_priority, 1)),
            "accessibility_proximity": float(round(accessibility, 1)),
        },
        "provider_notes": {
            "solar": solar.notes,
            "panel_detection": "Mocked panel-detection result designed for swap-in vision models.",
        },
    }
    if weather:
        explanation["environment"] = {
            "average_annual_temp_c": weather.average_annual_temp_c,
            "summer_max_temp_c": weather.summer_max_temp_c,
            "heat_risk_score": weather.heat_risk_score,
            "temperature_fit_score": weather.temperature_fit_score,
            "weather_provider": weather.provider,
        }
        explanation["provider_notes"]["weather"] = weather.notes

    return LeadScore(
        lead_score=lead_score,
        opportunity_level=opportunity,
        usable_roof_area_m2=float(usable_roof_area),
        type_priority_score=float(round(type_priority, 1)),
        accessibility_score=float(round(accessibility, 1)),
        scoring_explanation=explanation,
        recommended_action=recommended_action(opportunity, normalized_type, panel_detection.has_existing_panels),
    )


def roof_usability_factor(building_type: str) -> float:
    if building_type in {"industrial", "warehouse"}:
        return 0.78
    if building_type in {"commercial", "retail", "office", "school", "hospital"}:
        return 0.68
    if building_type in {"apartment", "apartments"}:
        return 0.54
    if building_type in {"residential", "house"}:
        return 0.50
    return 0.46


def building_type_priority(building_type: str) -> float:
    if building_type in HIGH_PRIORITY_TYPES:
        return 95
    if building_type in MEDIUM_PRIORITY_TYPES:
        return 62
    return 42


def accessibility_proxy(latitude: float, longitude: float, area_m2: float) -> float:
    density_proxy = 86 - min(abs(latitude % 0.04 - 0.02) * 500, 14)
    size_bonus = min(12, area_m2 / 90)
    coordinate_variation = ((abs(latitude * 31 + longitude * 17) % 1) - 0.5) * 8
    return float(max(45, min(98, density_proxy + size_bonus + coordinate_variation)))


def recommended_action(opportunity: str, building_type: str, has_panels: bool) -> str:
    if has_panels:
        return "Deprioritize acquisition; route to upsell, maintenance, or battery-storage offer."
    if opportunity == "high":
        if building_type in HIGH_PRIORITY_TYPES:
            return "Assign to senior sales rep for commercial outreach and roof survey scheduling."
        return "Prioritize for outbound call and proposal-ready savings estimate."
    if opportunity == "medium":
        return "Add to nurture list; validate ownership and energy-bill profile before outreach."
    return "Keep in low-priority pool unless incentives, owner demand, or roof data improves."
