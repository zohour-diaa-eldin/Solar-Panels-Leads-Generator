from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.config import Settings, get_settings
from app.db import get_db
from app.models import Building, Project
from app.schemas.building import BuildingFeatureCollection
from app.schemas.project import AnalyzeBboxRequest, AnalyzeBboxResponse, ProjectCreate, ProjectRead, ProjectSummary
from app.services.analysis_service import AnalysisService
from app.services.demo_data import CAIRO_DEMO_BBOX
from app.services.serializers import building_to_feature, building_to_summary_lead

router = APIRouter(prefix="/api/projects", tags=["projects"])


@router.post("", response_model=ProjectRead, status_code=201)
def create_project(payload: ProjectCreate, db: Session = Depends(get_db)) -> Project:
    project = Project(name=payload.name, city=payload.city, bbox=payload.bbox.model_dump() if payload.bbox else None)
    db.add(project)
    db.commit()
    db.refresh(project)
    return project


@router.get("/demo", response_model=ProjectRead)
def get_demo_project(
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> Project:
    project = db.execute(select(Project).where(Project.name == settings.demo_project_name)).scalar_one_or_none()
    if project:
        return project
    project = Project(name=settings.demo_project_name, city="Cairo, Egypt", bbox=CAIRO_DEMO_BBOX.model_dump())
    db.add(project)
    db.commit()
    db.refresh(project)
    return project


@router.get("/{project_id}", response_model=ProjectRead)
def get_project(project_id: UUID, db: Session = Depends(get_db)) -> Project:
    project = db.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


@router.post("/{project_id}/analyze-bbox", response_model=AnalyzeBboxResponse)
async def analyze_bbox(
    project_id: UUID,
    payload: AnalyzeBboxRequest,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> AnalyzeBboxResponse:
    project = db.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    service = AnalysisService(settings)
    return await service.analyze_bbox(db, project, payload.bbox, payload.limit)


@router.get("/{project_id}/buildings", response_model=BuildingFeatureCollection)
def get_project_buildings(project_id: UUID, db: Session = Depends(get_db)) -> BuildingFeatureCollection:
    if not db.get(Project, project_id):
        raise HTTPException(status_code=404, detail="Project not found")
    buildings = db.execute(
        select(Building).where(Building.project_id == project_id).order_by(Building.lead_score.desc())
    ).scalars()
    return BuildingFeatureCollection(features=[building_to_feature(building) for building in buildings])


@router.get("/{project_id}/summary", response_model=ProjectSummary)
def get_project_summary(project_id: UUID, db: Session = Depends(get_db)) -> ProjectSummary:
    if not db.get(Project, project_id):
        raise HTTPException(status_code=404, detail="Project not found")

    counts = db.execute(
        select(Building.opportunity_level, func.count(Building.id))
        .where(Building.project_id == project_id)
        .group_by(Building.opportunity_level)
    ).all()
    count_map = {level: count for level, count in counts}
    roof_area = db.execute(
        select(func.coalesce(func.sum(Building.usable_roof_area_m2), 0)).where(Building.project_id == project_id)
    ).scalar_one()
    top_leads = db.execute(
        select(Building)
        .where(Building.project_id == project_id)
        .order_by(Building.lead_score.desc())
        .limit(20)
    ).scalars()

    total = sum(count_map.values())
    return ProjectSummary(
        project_id=project_id,
        total_buildings=total,
        high_opportunity_count=count_map.get("high", 0),
        medium_opportunity_count=count_map.get("medium", 0),
        low_opportunity_count=count_map.get("low", 0),
        estimated_total_roof_area_m2=round(float(roof_area), 1),
        top_leads=[building_to_summary_lead(building) for building in top_leads],
    )
