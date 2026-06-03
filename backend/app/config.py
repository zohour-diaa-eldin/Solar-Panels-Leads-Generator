from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "Solar Lead AI"
    environment: str = "development"
    database_url: str = Field(
        default="postgresql+psycopg2://postgres:postgres@db:5432/solar_leads",
        validation_alias="DATABASE_URL",
    )
    google_solar_api_key: str | None = Field(default=None, validation_alias="GOOGLE_SOLAR_API_KEY")
    overpass_url: str = Field(default="https://overpass-api.de/api/interpreter", validation_alias="OVERPASS_URL")
    overpass_fallback_urls: str = Field(
        default="https://overpass.osm.ch/api/interpreter,https://overpass.kumi.systems/api/interpreter",
        validation_alias="OVERPASS_FALLBACK_URLS",
    )
    overpass_timeout_seconds: int = Field(default=25, validation_alias="OVERPASS_TIMEOUT_SECONDS")
    osm_map_api_url: str = Field(default="https://api.openstreetmap.org/api/0.6/map", validation_alias="OSM_MAP_API_URL")
    pvgis_url: str = Field(default="https://re.jrc.ec.europa.eu/api/v5_3/PVcalc", validation_alias="PVGIS_URL")
    open_meteo_archive_url: str = Field(
        default="https://archive-api.open-meteo.com/v1/archive",
        validation_alias="OPEN_METEO_ARCHIVE_URL",
    )
    external_api_timeout_seconds: int = Field(default=18, validation_alias="EXTERNAL_API_TIMEOUT_SECONDS")
    france_weather_year: int | None = Field(default=None, validation_alias="FRANCE_WEATHER_YEAR")
    default_analysis_limit: int = Field(default=220, validation_alias="DEFAULT_ANALYSIS_LIMIT")
    allowed_origins: str = Field(
        default="http://localhost:5173,http://127.0.0.1:5173",
        validation_alias="ALLOWED_ORIGINS",
    )
    demo_project_name: str = Field(default="Cairo Solar Leads Demo", validation_alias="DEMO_PROJECT_NAME")

    @property
    def cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.allowed_origins.split(",") if origin.strip()]

    @property
    def overpass_urls(self) -> list[str]:
        urls = [self.overpass_url]
        urls.extend(url.strip() for url in self.overpass_fallback_urls.split(",") if url.strip())
        deduped: list[str] = []
        for url in urls:
            if url not in deduped:
                deduped.append(url)
        return deduped


@lru_cache
def get_settings() -> Settings:
    return Settings()
