from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import Building
from app.schemas.building import BuildingFeature
from app.services.serializers import building_to_feature

router = APIRouter(prefix="/api/buildings", tags=["buildings"])


@router.get("/{building_id}", response_model=BuildingFeature)
def get_building(building_id: UUID, db: Session = Depends(get_db)) -> BuildingFeature:
    building = db.get(Building, building_id)
    if not building:
        raise HTTPException(status_code=404, detail="Building not found")
    return building_to_feature(building)
