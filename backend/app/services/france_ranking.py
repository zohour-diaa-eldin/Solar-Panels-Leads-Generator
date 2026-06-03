from __future__ import annotations

import asyncio

from app.config import Settings
from app.schemas.france import FranceAreaRank, FranceRankAreasResponse
from app.services.france_region_provider import FranceRegionProvider, FranceSalesArea
from app.services.pvgis_provider import PVGISMetrics, PVGISProvider, fallback_pvgis_metrics
from app.services.weather_provider import WeatherMetrics, WeatherProvider, fallback_weather_metrics


class FranceRankingService:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.region_provider = FranceRegionProvider()
        self.pvgis_provider = PVGISProvider(settings)
        self.weather_provider = WeatherProvider(settings)

    async def rank_areas(
        self,
        limit: int,
        include_weather: bool = True,
        include_pvgis: bool = True,
    ) -> FranceRankAreasResponse:
        areas = self.region_provider.list_sales_areas()
        ranked = await asyncio.gather(
            *(self._rank_area(area, include_weather=include_weather, include_pvgis=include_pvgis) for area in areas)
        )
        ranked_areas = sorted(ranked, key=lambda item: item.overall_score, reverse=True)[:limit]
        return FranceRankAreasResponse(
            areas=ranked_areas,
            source_notes=[
                "Sales areas are curated French city/industrial-zone candidates for MVP country screening.",
                "Solar data uses PVGIS PVcalc when available; fallback estimates are flagged per area.",
                "Temperature data uses Open-Meteo historical archive when available; fallback estimates are flagged per area.",
            ],
        )

    async def _rank_area(self, area: FranceSalesArea, include_weather: bool, include_pvgis: bool) -> FranceAreaRank:
        pvgis = (
            await self.pvgis_provider.get_metrics(area.latitude, area.longitude)
            if include_pvgis
            else fallback_pvgis_metrics(area.latitude, area.longitude)
        )
        weather = (
            await self.weather_provider.get_temperature_metrics(area.latitude, area.longitude)
            if include_weather
            else fallback_weather_metrics(area.latitude)
        )
        return rank_area(area, pvgis, weather)


def rank_area(area: FranceSalesArea, pvgis: PVGISMetrics, weather: WeatherMetrics) -> FranceAreaRank:
    overall = (
        pvgis.solar_score * 0.35
        + pv_output_score(pvgis.estimated_pv_output_kwh_kwp) * 0.20
        + weather.temperature_fit_score * 0.15
        + area.commercial_priority_score * 0.15
        + area.roof_area_proxy_score * 0.10
        + area.accessibility_score * 0.05
    )
    data_sources = [pvgis.provider, weather.provider, "curated_france_sales_areas"]
    data_quality = "live" if pvgis.data_quality == "live" and weather.data_quality == "live" else "mixed_or_fallback"
    return FranceAreaRank(
        id=area.id,
        name=area.name,
        region=area.region,
        department=area.department,
        segment=area.segment,
        latitude=area.latitude,
        longitude=area.longitude,
        bbox=area.bbox,
        overall_score=float(round(overall, 1)),
        solar_score=pvgis.solar_score,
        temperature_fit_score=weather.temperature_fit_score,
        commercial_priority_score=float(area.commercial_priority_score),
        roof_area_proxy_score=float(area.roof_area_proxy_score),
        accessibility_score=float(area.accessibility_score),
        annual_irradiation_kwh_m2=pvgis.annual_irradiation_kwh_m2,
        estimated_pv_output_kwh_kwp=pvgis.estimated_pv_output_kwh_kwp,
        average_annual_temp_c=weather.average_annual_temp_c,
        summer_max_temp_c=weather.summer_max_temp_c,
        heat_risk_score=weather.heat_risk_score,
        recommended_action=recommended_action(area, overall, weather.heat_risk_score),
        rationale=rationale(area, pvgis, weather),
        data_sources=data_sources,
        data_quality=data_quality,
    )


def pv_output_score(value: float | None) -> float:
    if value is None:
        return 55.0
    return float(round(max(35, min(100, (float(value) - 850) / (1600 - 850) * 100)), 1))


def rationale(area: FranceSalesArea, pvgis: PVGISMetrics, weather: WeatherMetrics) -> list[str]:
    notes = [
        f"Commercial/roof proxy is strong for {area.segment.replace('_', ' ')}.",
        f"Solar score {pvgis.solar_score:.1f} from {pvgis.provider}.",
        f"Temperature fit {weather.temperature_fit_score:.1f}; heat risk {weather.heat_risk_score:.1f}.",
    ]
    if pvgis.estimated_pv_output_kwh_kwp:
        notes.append(f"Estimated annual PV output is {pvgis.estimated_pv_output_kwh_kwp:.0f} kWh/kWp.")
    if weather.summer_max_temp_c:
        notes.append(f"Summer max temperature sample is {weather.summer_max_temp_c:.1f} C.")
    return notes


def recommended_action(area: FranceSalesArea, overall_score: float, heat_risk: float) -> str:
    if overall_score >= 82:
        return "Prioritize for sales pilot; analyze top commercial and industrial bboxes first."
    if heat_risk > 75:
        return "Good solar market, but include heat-performance assumptions in proposals."
    if area.commercial_priority_score >= 90:
        return "Strong market density; validate rooftop inventory despite moderate solar score."
    return "Keep in second-wave prospecting list and compare incentives or owner demand."
