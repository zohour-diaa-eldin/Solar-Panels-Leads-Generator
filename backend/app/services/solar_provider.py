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
        try:
            async with httpx.AsyncClient(timeout=12) as client:
                response = await client.get(url, params=params)
                response.raise_for_status()
                data = response.json()
        except Exception as exc:  # noqa: BLE001 - live provider should degrade to deterministic scoring.
            logger.warning("Google Solar lookup failed, using local estimate: %s", exc)
            return await MockSolarProvider().get_building_potential(latitude, longitude, roof_area_m2)

        solar = data.get("solarPotential", {})
        max_area = float(solar.get("maxArrayAreaMeters2") or roof_area_m2 or 0)
        panel_configs = solar.get("solarPanelConfigs") or []
        annual_kwh = None
        if panel_configs:
            annual_kwh = float(panel_configs[-1].get("yearlyEnergyDcKwh") or 0)

        area_score = min(100, (max_area / max(roof_area_m2, 1)) * 85)
        energy_score = min(100, ((annual_kwh or 0) / max(roof_area_m2 * 210, 1)) * 100) if annual_kwh else area_score
        potential_score = round(max(35, min(100, area_score * 0.45 + energy_score * 0.55)), 1)
        return SolarPotential(
            potential_score=float(potential_score),
            annual_kwh=float(round(annual_kwh, 0)) if annual_kwh else None,
            provider="google_solar",
            notes="Google Solar API buildingInsights result.",
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
        )


def get_solar_provider(settings: Settings) -> SolarProvider:
    if settings.google_solar_api_key:
        return GoogleSolarProvider(settings.google_solar_api_key)
    return FranceAwareSolarProvider(settings)
