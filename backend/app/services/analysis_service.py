from __future__ import annotations

from sqlalchemy import delete
from sqlalchemy.orm import Session

from app.config import Settings
from app.models import Building, Project
from app.schemas.project import AnalyzeBboxResponse, Bbox
from app.services.geometry import centroid_lat_lon, shape_to_wkb_element
from app.services.overpass_service import OverpassService
from app.services.panel_detection_provider import MockPanelDetectionProvider
from app.services.scoring import score_building
from app.services.solar_provider import get_solar_provider
from app.services.france_region_provider import is_france_coordinate
from app.services.weather_provider import WeatherMetrics, WeatherProvider


class AnalysisService:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.overpass_service = OverpassService(settings)
        self.solar_provider = get_solar_provider(settings)
        self.panel_detection_provider = MockPanelDetectionProvider()
        self.weather_provider = WeatherProvider(settings)

    async def analyze_bbox(self, db: Session, project: Project, bbox: Bbox, limit: int) -> AnalyzeBboxResponse:
        project.status = "analyzing"
        project.bbox = bbox.model_dump()
        db.add(project)
        db.commit()

        candidates, source = await self.overpass_service.fetch_buildings(bbox, limit)

        db.execute(delete(Building).where(Building.project_id == project.id))
        analyzed_count = 0
        weather_cache: dict[tuple[float, float], WeatherMetrics] = {}

        for candidate in candidates[:limit]:
            latitude, longitude = centroid_lat_lon(candidate.geometry)
            solar = await self.solar_provider.get_building_potential(latitude, longitude, candidate.area_m2)
            weather = None
            if is_france_coordinate(latitude, longitude):
                weather_key = (round(latitude, 1), round(longitude, 1))
                if weather_key not in weather_cache:
                    weather_cache[weather_key] = await self.weather_provider.get_temperature_metrics(latitude, longitude)
                weather = weather_cache[weather_key]
            panel_detection = await self.panel_detection_provider.detect_existing_panels(
                candidate.osm_id,
                latitude,
                longitude,
                candidate.area_m2,
            )
            score = score_building(
                area_m2=candidate.area_m2,
                building_type=candidate.building_type,
                solar=solar,
                panel_detection=panel_detection,
                latitude=latitude,
                longitude=longitude,
                weather=weather,
            )
            db.add(
                Building(
                    project_id=project.id,
                    osm_id=candidate.osm_id,
                    geometry=shape_to_wkb_element(candidate.geometry),
                    area_m2=float(round(candidate.area_m2, 1)),
                    building_type=candidate.building_type,
                    address=candidate.address,
                    source=candidate.source,
                    lead_score=score.lead_score,
                    opportunity_level=score.opportunity_level,
                    estimated_solar_potential=float(solar.potential_score),
                    usable_roof_area_m2=score.usable_roof_area_m2,
                    has_existing_panels=panel_detection.has_existing_panels,
                    panel_confidence=panel_detection.confidence,
                    type_priority_score=score.type_priority_score,
                    accessibility_score=score.accessibility_score,
                    scoring_explanation=score.scoring_explanation,
                    recommended_action=score.recommended_action,
                )
            )
            analyzed_count += 1

        project.status = "ready"
        db.add(project)
        db.commit()
        return AnalyzeBboxResponse(
            project_id=project.id,
            fetched_count=len(candidates),
            analyzed_count=analyzed_count,
            source=source,
            message=f"Analyzed {analyzed_count} buildings from {source}.",
        )
