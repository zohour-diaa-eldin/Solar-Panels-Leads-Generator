from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import date

import httpx

from app.config import Settings

logger = logging.getLogger(__name__)


@dataclass
class WeatherMetrics:
    average_annual_temp_c: float | None
    summer_max_temp_c: float | None
    heat_risk_score: float
    temperature_fit_score: float
    provider: str
    data_quality: str
    notes: str


class WeatherProvider:
    def __init__(self, settings: Settings):
        self.settings = settings

    async def get_temperature_metrics(self, latitude: float, longitude: float) -> WeatherMetrics:
        year = self.settings.france_weather_year or (date.today().year - 1)
        params = {
            "latitude": float(latitude),
            "longitude": float(longitude),
            "start_date": f"{year}-01-01",
            "end_date": f"{year}-12-31",
            "daily": "temperature_2m_mean,temperature_2m_max",
            "timezone": "Europe/Paris",
        }
        try:
            async with httpx.AsyncClient(timeout=self.settings.external_api_timeout_seconds) as client:
                response = await client.get(self.settings.open_meteo_archive_url, params=params)
                response.raise_for_status()
                payload = response.json()
            return parse_open_meteo_response(payload, year)
        except Exception as exc:  # noqa: BLE001 - ranking should degrade gracefully for demos.
            logger.warning("Open-Meteo lookup failed for %.4f, %.4f: %s", latitude, longitude, exc)
            return fallback_weather_metrics(latitude)


def parse_open_meteo_response(payload: dict, year: int) -> WeatherMetrics:
    daily = payload.get("daily") or {}
    dates = daily.get("time") or []
    mean_values = [float(value) for value in daily.get("temperature_2m_mean") or [] if value is not None]
    max_values = daily.get("temperature_2m_max") or []
    summer_max_values = [
        float(value)
        for sample_date, value in zip(dates, max_values)
        if value is not None and sample_date[5:7] in {"06", "07", "08"}
    ]

    average_temp = sum(mean_values) / len(mean_values) if mean_values else None
    summer_max = max(summer_max_values) if summer_max_values else None
    heat_risk = heat_risk_score(summer_max)

    return WeatherMetrics(
        average_annual_temp_c=round(average_temp, 1) if average_temp is not None else None,
        summer_max_temp_c=round(summer_max, 1) if summer_max is not None else None,
        heat_risk_score=heat_risk,
        temperature_fit_score=temperature_fit_score(heat_risk),
        provider="open_meteo_archive",
        data_quality="live",
        notes=f"Open-Meteo archive daily temperatures for {year}.",
    )


def fallback_weather_metrics(latitude: float) -> WeatherMetrics:
    lat = float(latitude)
    average_temp = 16.5 - max(0, lat - 43.5) * 0.9
    summer_max = 36.0 - max(0, lat - 43.5) * 1.2
    heat_risk = heat_risk_score(summer_max)
    return WeatherMetrics(
        average_annual_temp_c=round(average_temp, 1),
        summer_max_temp_c=round(summer_max, 1),
        heat_risk_score=heat_risk,
        temperature_fit_score=temperature_fit_score(heat_risk),
        provider="weather_fallback",
        data_quality="estimated_fallback",
        notes="Fallback temperature estimate derived from France latitude band because weather API was unavailable.",
    )


def heat_risk_score(summer_max_temp_c: float | None) -> float:
    if summer_max_temp_c is None:
        return 35.0
    score = (float(summer_max_temp_c) - 28) / (42 - 28) * 100
    return float(round(max(0, min(100, score)), 1))


def temperature_fit_score(heat_risk: float) -> float:
    return float(round(max(45, 100 - float(heat_risk) * 0.38), 1))
