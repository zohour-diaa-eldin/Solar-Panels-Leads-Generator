from fastapi import APIRouter, Depends

from app.config import Settings, get_settings
from app.schemas.france import FranceRankAreasRequest, FranceRankAreasResponse
from app.services.france_ranking import FranceRankingService

router = APIRouter(prefix="/api/france", tags=["france"])


@router.post("/rank-areas", response_model=FranceRankAreasResponse)
async def rank_france_areas(
    payload: FranceRankAreasRequest,
    settings: Settings = Depends(get_settings),
) -> FranceRankAreasResponse:
    service = FranceRankingService(settings)
    return await service.rank_areas(
        limit=payload.limit,
        include_weather=payload.include_weather,
        include_pvgis=payload.include_pvgis,
    )
