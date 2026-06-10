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
    estimated_usable_roof_area = round(area_m2 * usability_factor, 1)
    usable_roof_area = round(float(solar.usable_roof_area_m2 or estimated_usable_roof_area), 1)

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
    temperature_adjustment = temperature_score_adjustment(weather) if weather else 0.0
    lead_score = float(round(max(0, min(100, weighted_score + temperature_adjustment)), 1))
    opportunity = "high" if lead_score >= 75 else "medium" if lead_score >= 52 else "low"

    components = {
        "estimated_solar_potential": float(round(solar.potential_score, 1)),
        "usable_roof_area": float(round(roof_area_score, 1)),
        "no_existing_solar_panels": float(round(no_existing_panel_score, 1)),
        "building_type_priority": float(round(type_priority, 1)),
        "accessibility_proximity": float(round(accessibility, 1)),
    }
    if weather:
        components["temperature_fit"] = float(round(weather.temperature_fit_score, 1))

    explanation = {
        "weights": {
            "estimated_solar_potential": 0.30,
            "usable_roof_area": 0.25,
            "no_existing_solar_panels": 0.20,
            "building_type_priority": 0.15,
            "accessibility_proximity": 0.10,
        },
        "components": components,
        "adjustments": {
            "temperature_adjustment_points": float(round(temperature_adjustment, 1)),
        },
        "provider_notes": {
            "solar": solar.notes,
            "panel_detection": "Mocked panel-detection result designed for swap-in vision models.",
        },
        "solar_provider": {
            "provider": solar.provider,
            "data_quality": solar.data_quality,
            "annual_kwh": solar.annual_kwh,
            "usable_roof_area_m2": solar.usable_roof_area_m2,
            "annual_sunshine_hours": solar.annual_sunshine_hours,
            "max_panel_count": solar.max_panel_count,
            "panel_capacity_watts": solar.panel_capacity_watts,
            "annual_kwh_per_m2": solar.annual_kwh_per_m2,
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
        recommended_action=recommended_action(
            opportunity,
            normalized_type,
            panel_detection.has_existing_panels,
            weather.heat_risk_score if weather else None,
        ),
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


def temperature_score_adjustment(weather: WeatherMetrics) -> float:
    adjustment = (float(weather.temperature_fit_score) - 75) * 0.12
    if weather.heat_risk_score >= 85:
        adjustment -= 2.0
    elif weather.heat_risk_score >= 70:
        adjustment -= 0.8
    return float(round(max(-6, min(4, adjustment)), 1))


def recommended_action(opportunity: str, building_type: str, has_panels: bool, heat_risk: float | None = None) -> str:
    if has_panels:
        return "Deprioritize acquisition; route to upsell, maintenance, or battery-storage offer."
    if opportunity == "high":
        if heat_risk is not None and heat_risk >= 75:
            return "Prioritize outreach, but include heat derating, ventilation, and performance assumptions in the proposal."
        if building_type in HIGH_PRIORITY_TYPES:
            return "Assign to senior sales rep for commercial outreach and roof survey scheduling."
        return "Prioritize for outbound call and proposal-ready savings estimate."
    if opportunity == "medium":
        return "Add to nurture list; validate ownership and energy-bill profile before outreach."
    return "Keep in low-priority pool unless incentives, owner demand, or roof data improves."
