from __future__ import annotations

import logging
from dataclasses import dataclass

import httpx

from app.config import Settings

logger = logging.getLogger(__name__)


@dataclass
class PVGISMetrics:
    annual_irradiation_kwh_m2: float | None
    estimated_pv_output_kwh_kwp: float | None
    solar_score: float
    provider: str
    data_quality: str
    notes: str


class PVGISProvider:
    def __init__(self, settings: Settings):
        self.settings = settings

    async def get_metrics(self, latitude: float, longitude: float) -> PVGISMetrics:
        params = {
            "lat": float(latitude),
            "lon": float(longitude),
            "peakpower": 1,
            "loss": 14,
            "pvtechchoice": "crystSi",
            "mountingplace": "building",
            "optimalangles": 1,
            "outputformat": "json",
        }
        try:
            async with httpx.AsyncClient(timeout=self.settings.external_api_timeout_seconds) as client:
                response = await client.get(self.settings.pvgis_url, params=params)
                response.raise_for_status()
                payload = response.json()
            return parse_pvgis_response(payload)
        except Exception as exc:  # noqa: BLE001 - ranking should degrade gracefully for demos.
            logger.warning("PVGIS lookup failed for %.4f, %.4f: %s", latitude, longitude, exc)
            return fallback_pvgis_metrics(latitude, longitude)


def parse_pvgis_response(payload: dict) -> PVGISMetrics:
    outputs = payload.get("outputs", {})
    totals = (outputs.get("totals") or {}).get("fixed") or {}
    monthly = (outputs.get("monthly") or {}).get("fixed") or []

    pv_output = totals.get("E_y")
    irradiation = totals.get("H(i)_y")
    if pv_output is None and monthly:
        pv_output = sum(float(row.get("E_m") or 0) for row in monthly)
    if irradiation is None and monthly:
        irradiation = sum(float(row.get("H(i)_m") or 0) for row in monthly)

    pv_output_float = float(pv_output) if pv_output is not None else None
    irradiation_float = float(irradiation) if irradiation is not None else None
    score_value = pv_output_float if pv_output_float is not None else irradiation_float
    score = normalize_solar_score(score_value)

    return PVGISMetrics(
        annual_irradiation_kwh_m2=round(irradiation_float, 1) if irradiation_float is not None else None,
        estimated_pv_output_kwh_kwp=round(pv_output_float, 1) if pv_output_float is not None else None,
        solar_score=score,
        provider="pvgis",
        data_quality="live",
        notes="PVGIS PVcalc live result for 1 kWp rooftop system with 14% losses and optimal fixed angles.",
    )


def fallback_pvgis_metrics(latitude: float, longitude: float) -> PVGISMetrics:
    lat = float(latitude)
    southness = max(0, min(1, (51.5 - lat) / 8.6))
    mediterranean_bonus = 0.08 if longitude > 2.0 and lat < 44.8 else 0
    pv_output = 900 + southness * 520 + mediterranean_bonus * 180
    irradiation = pv_output * 1.22
    return PVGISMetrics(
        annual_irradiation_kwh_m2=round(irradiation, 1),
        estimated_pv_output_kwh_kwp=round(pv_output, 1),
        solar_score=normalize_solar_score(pv_output),
        provider="pvgis_fallback",
        data_quality="estimated_fallback",
        notes="Fallback estimate derived from France latitude band because PVGIS was unavailable.",
    )


def normalize_solar_score(value: float | None) -> float:
    if value is None:
        return 55.0
    score = (float(value) - 850) / (1600 - 850) * 100
    return float(round(max(35, min(100, score)), 1))
