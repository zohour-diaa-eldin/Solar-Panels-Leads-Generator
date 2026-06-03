from app.models import Building
from app.schemas.building import BuildingFeature, BuildingRead
from app.schemas.project import SummaryLead
from app.services.geometry import db_geometry_to_geojson


def building_to_read(building: Building) -> BuildingRead:
    return BuildingRead(
        id=building.id,
        project_id=building.project_id,
        osm_id=building.osm_id,
        area_m2=round(building.area_m2, 1),
        usable_roof_area_m2=round(building.usable_roof_area_m2, 1),
        building_type=building.building_type,
        address=building.address,
        source=building.source,
        lead_score=round(building.lead_score, 1),
        opportunity_level=building.opportunity_level,
        estimated_solar_potential=round(building.estimated_solar_potential, 1),
        has_existing_panels=building.has_existing_panels,
        panel_confidence=round(building.panel_confidence, 2),
        type_priority_score=round(building.type_priority_score, 1),
        accessibility_score=round(building.accessibility_score, 1),
        scoring_explanation=building.scoring_explanation,
        recommended_action=building.recommended_action,
    )


def building_to_feature(building: Building) -> BuildingFeature:
    return BuildingFeature(geometry=db_geometry_to_geojson(building.geometry), properties=building_to_read(building))


def building_to_summary_lead(building: Building) -> SummaryLead:
    return SummaryLead(
        id=building.id,
        osm_id=building.osm_id,
        address=building.address,
        building_type=building.building_type,
        area_m2=round(building.area_m2, 1),
        usable_roof_area_m2=round(building.usable_roof_area_m2, 1),
        lead_score=round(building.lead_score, 1),
        opportunity_level=building.opportunity_level,
        estimated_solar_potential=round(building.estimated_solar_potential, 1),
        recommended_action=building.recommended_action,
    )
