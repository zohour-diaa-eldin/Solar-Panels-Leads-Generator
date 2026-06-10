from __future__ import annotations

import logging
from dataclasses import dataclass

import httpx

from app.config import Settings
from app.services.france_region_provider import is_france_coordinate
from app.services.pvgis_provider import PVGISMetrics, PVGISProvider

logger = logging.getLogger(__name__)


@dataclass
class SolarPotential:
    potential_score: float
    annual_kwh: float | None
    provider: str
    notes: str
    usable_roof_area_m2: float | None = None
    annual_sunshine_hours: float | None = None
    max_panel_count: int | None = None
    panel_capacity_watts: float | None = None
    annual_kwh_per_m2: float | None = None
    data_quality: str = "estimated"


class SolarProvider:
    async def get_building_potential(self, latitude: float, longitude: float, roof_area_m2: float) -> SolarPotential:
        raise NotImplementedError


class MockSolarProvider(SolarProvider):
    async def get_building_potential(self, latitude: float, longitude: float, roof_area_m2: float) -> SolarPotential:
        latitude = float(latitude)
        longitude = float(longitude)
        roof_area_m2 = float(roof_area_m2)
        # Cairo and other sunny regions should look strong in demo mode while still varying by site.
        latitude_factor = max(0.45, 1 - abs(latitude - 26.8) / 80)
        area_factor = min(1.0, roof_area_m2 / 450)
        orientation_noise = ((abs(latitude * 13.7 + longitude * 7.1) % 1) - 0.5) * 8
        potential_score = min(100, max(35, 58 + latitude_factor * 24 + area_factor * 18 + orientation_noise))
        annual_kwh = roof_area_m2 * 190 * (potential_score / 100)
        return SolarPotential(
            potential_score=float(round(potential_score, 1)),
            annual_kwh=float(round(annual_kwh, 0)),
            provider="mock",
            notes="Mocked solar potential from roof area and location. Set GOOGLE_SOLAR_API_KEY for live lookup.",
            usable_roof_area_m2=None,
            data_quality="mock",
        )


class GoogleSolarProvider(SolarProvider):
    def __init__(self, api_key: str):
        self.api_key = api_key

    async def get_building_potential(self, latitude: float, longitude: float, roof_area_m2: float) -> SolarPotential:
        latitude = float(latitude)
        longitude = float(longitude)
        roof_area_m2 = float(roof_area_m2)
        url = "https://solar.googleapis.com/v1/buildingInsights:findClosest"
        params = {
            "location.latitude": latitude,
            "location.longitude": longitude,
            "requiredQuality": "LOW",
            "key": self.api_key,
        }
        async with httpx.AsyncClient(timeout=12) as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            data = response.json()

        solar = data.get("solarPotential", {})
        if not solar:
            raise ValueError("Google Solar response did not include solarPotential")

        max_area = float(solar.get("maxArrayAreaMeters2") or roof_area_m2 or 0)
        annual_sunshine_hours = solar.get("maxSunshineHoursPerYear")
        max_panels = solar.get("maxArrayPanelsCount")
        panel_capacity_watts = solar.get("panelCapacityWatts")
        panel_configs = solar.get("solarPanelConfigs") or []
        annual_kwh = None
        if panel_configs:
            best_config = max(panel_configs, key=lambda item: float(item.get("yearlyEnergyDcKwh") or 0))
            annual_kwh = float(best_config.get("yearlyEnergyDcKwh") or 0)

        annual_kwh_per_m2 = annual_kwh / max(max_area, 1) if annual_kwh and max_area else None
        area_score = scaled_score(max_area, low=70, high=360)
        density_score = scaled_score(annual_kwh_per_m2, low=95, high=210) if annual_kwh_per_m2 else area_score
        sunshine_score = (
            scaled_score(float(annual_sunshine_hours), low=900, high=1900)
            if annual_sunshine_hours
            else density_score
        )
        potential_score = round(max(35, min(100, area_score * 0.15 + density_score * 0.55 + sunshine_score * 0.30)), 1)
        return SolarPotential(
            potential_score=float(potential_score),
            annual_kwh=float(round(annual_kwh, 0)) if annual_kwh else None,
            provider="google_solar",
            notes="Google Solar API buildingInsights result with rooftop area, sunshine, and panel configuration signals.",
            usable_roof_area_m2=float(round(max_area, 1)) if max_area else None,
            annual_sunshine_hours=float(round(float(annual_sunshine_hours), 1)) if annual_sunshine_hours else None,
            max_panel_count=int(max_panels) if max_panels is not None else None,
            panel_capacity_watts=float(panel_capacity_watts) if panel_capacity_watts is not None else None,
            annual_kwh_per_m2=float(round(annual_kwh_per_m2, 1)) if annual_kwh_per_m2 else None,
            data_quality="google_building_insights",
        )


class FranceAwareSolarProvider(SolarProvider):
    def __init__(self, settings: Settings):
        self.mock_provider = MockSolarProvider()
        self.pvgis_provider = PVGISProvider(settings)
        self._pvgis_cache: dict[tuple[float, float], PVGISMetrics] = {}

    async def get_building_potential(self, latitude: float, longitude: float, roof_area_m2: float) -> SolarPotential:
        latitude = float(latitude)
        longitude = float(longitude)
        roof_area_m2 = float(roof_area_m2)
        if not is_france_coordinate(latitude, longitude):
            return await self.mock_provider.get_building_potential(latitude, longitude, roof_area_m2)

        key = (round(latitude, 2), round(longitude, 2))
        if key not in self._pvgis_cache:
            self._pvgis_cache[key] = await self.pvgis_provider.get_metrics(latitude, longitude)
        metrics = self._pvgis_cache[key]

        kwp_capacity_estimate = max(0.5, roof_area_m2 * 0.14)
        annual_kwh = (
            kwp_capacity_estimate * metrics.estimated_pv_output_kwh_kwp
            if metrics.estimated_pv_output_kwh_kwp is not None
            else None
        )
        return SolarPotential(
            potential_score=float(metrics.solar_score),
            annual_kwh=float(round(annual_kwh, 0)) if annual_kwh is not None else None,
            provider=metrics.provider,
            notes=metrics.notes,
            usable_roof_area_m2=None,
            data_quality=metrics.data_quality,
        )


class HybridSolarProvider(SolarProvider):
    def __init__(self, settings: Settings):
        self.google_provider = GoogleSolarProvider(settings.google_solar_api_key or "")
        self.france_provider = FranceAwareSolarProvider(settings)

    async def get_building_potential(self, latitude: float, longitude: float, roof_area_m2: float) -> SolarPotential:
        try:
            return await self.google_provider.get_building_potential(latitude, longitude, roof_area_m2)
        except Exception as exc:  # noqa: BLE001 - Google coverage and API quotas vary by building.
            logger.warning("Google Solar lookup failed; falling back to regional provider: %s", type(exc).__name__)
            fallback = await self.france_provider.get_building_potential(latitude, longitude, roof_area_m2)
            fallback.notes = f"{fallback.notes} Google Solar lookup unavailable for this building, so fallback data was used."
            return fallback


def get_solar_provider(settings: Settings) -> SolarProvider:
    if settings.google_solar_api_key:
        return HybridSolarProvider(settings)
    return FranceAwareSolarProvider(settings)


def scaled_score(value: float | None, low: float, high: float) -> float:
    if value is None:
        return 55.0
    score = (float(value) - low) / (high - low) * 100
    return float(round(max(35, min(100, score)), 1))
