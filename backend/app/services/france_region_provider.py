from __future__ import annotations

from dataclasses import dataclass

from app.schemas.project import Bbox


@dataclass(frozen=True)
class FranceSalesArea:
    id: str
    name: str
    region: str
    department: str
    segment: str
    latitude: float
    longitude: float
    bbox: Bbox
    commercial_priority_score: float
    roof_area_proxy_score: float
    accessibility_score: float


class FranceRegionProvider:
    def list_sales_areas(self) -> list[FranceSalesArea]:
        return FRANCE_SALES_AREAS


def is_france_coordinate(latitude: float, longitude: float) -> bool:
    return 41.0 <= float(latitude) <= 51.8 and -5.6 <= float(longitude) <= 9.8


FRANCE_SALES_AREAS = [
    FranceSalesArea(
        id="marseille-aix",
        name="Marseille-Aix Industrial Corridor",
        region="Provence-Alpes-Cote d'Azur",
        department="Bouches-du-Rhone",
        segment="industrial_logistics_commercial",
        latitude=43.42,
        longitude=5.37,
        bbox=Bbox(south=43.25, west=5.20, north=43.55, east=5.55),
        commercial_priority_score=96,
        roof_area_proxy_score=94,
        accessibility_score=92,
    ),
    FranceSalesArea(
        id="montpellier-nimes",
        name="Montpellier-Nimes Commercial Belt",
        region="Occitanie",
        department="Herault / Gard",
        segment="commercial_industrial_public_buildings",
        latitude=43.72,
        longitude=4.12,
        bbox=Bbox(south=43.50, west=3.65, north=43.95, east=4.55),
        commercial_priority_score=92,
        roof_area_proxy_score=88,
        accessibility_score=90,
    ),
    FranceSalesArea(
        id="perpignan",
        name="Perpignan Logistics and Retail Area",
        region="Occitanie",
        department="Pyrenees-Orientales",
        segment="logistics_retail_commercial",
        latitude=42.70,
        longitude=2.90,
        bbox=Bbox(south=42.60, west=2.75, north=42.82, east=3.05),
        commercial_priority_score=78,
        roof_area_proxy_score=79,
        accessibility_score=80,
    ),
    FranceSalesArea(
        id="avignon-orange",
        name="Avignon-Orange Rhone Solar Belt",
        region="Provence-Alpes-Cote d'Azur",
        department="Vaucluse",
        segment="industrial_agriculture_commercial",
        latitude=43.95,
        longitude=4.81,
        bbox=Bbox(south=43.78, west=4.62, north=44.18, east=5.05),
        commercial_priority_score=82,
        roof_area_proxy_score=86,
        accessibility_score=84,
    ),
    FranceSalesArea(
        id="toulon",
        name="Toulon-La Seyne Commercial Rooftops",
        region="Provence-Alpes-Cote d'Azur",
        department="Var",
        segment="commercial_public_buildings",
        latitude=43.12,
        longitude=5.93,
        bbox=Bbox(south=43.04, west=5.78, north=43.20, east=6.10),
        commercial_priority_score=80,
        roof_area_proxy_score=77,
        accessibility_score=82,
    ),
    FranceSalesArea(
        id="nice-sophia",
        name="Nice-Cannes-Sophia Antipolis",
        region="Provence-Alpes-Cote d'Azur",
        department="Alpes-Maritimes",
        segment="commercial_technology_public_buildings",
        latitude=43.65,
        longitude=7.05,
        bbox=Bbox(south=43.55, west=6.85, north=43.78, east=7.35),
        commercial_priority_score=86,
        roof_area_proxy_score=75,
        accessibility_score=85,
    ),
    FranceSalesArea(
        id="toulouse",
        name="Toulouse Aerospace and Industrial Belt",
        region="Occitanie",
        department="Haute-Garonne",
        segment="aerospace_industrial_logistics",
        latitude=43.60,
        longitude=1.43,
        bbox=Bbox(south=43.45, west=1.25, north=43.75, east=1.65),
        commercial_priority_score=94,
        roof_area_proxy_score=92,
        accessibility_score=91,
    ),
    FranceSalesArea(
        id="bordeaux-merignac",
        name="Bordeaux-Merignac Business Parks",
        region="Nouvelle-Aquitaine",
        department="Gironde",
        segment="commercial_airport_logistics",
        latitude=44.84,
        longitude=-0.63,
        bbox=Bbox(south=44.75, west=-0.75, north=44.95, east=-0.45),
        commercial_priority_score=90,
        roof_area_proxy_score=88,
        accessibility_score=88,
    ),
    FranceSalesArea(
        id="la-rochelle",
        name="La Rochelle Coastal Commercial Zone",
        region="Nouvelle-Aquitaine",
        department="Charente-Maritime",
        segment="commercial_port_logistics",
        latitude=46.16,
        longitude=-1.15,
        bbox=Bbox(south=46.10, west=-1.25, north=46.25, east=-1.05),
        commercial_priority_score=72,
        roof_area_proxy_score=74,
        accessibility_score=76,
    ),
    FranceSalesArea(
        id="lyon-east",
        name="Lyon East Industrial Belt",
        region="Auvergne-Rhone-Alpes",
        department="Rhone / Isere",
        segment="industrial_logistics_commercial",
        latitude=45.73,
        longitude=4.96,
        bbox=Bbox(south=45.60, west=4.78, north=45.86, east=5.10),
        commercial_priority_score=98,
        roof_area_proxy_score=96,
        accessibility_score=94,
    ),
    FranceSalesArea(
        id="valence",
        name="Valence Rhone Valley Rooftops",
        region="Auvergne-Rhone-Alpes",
        department="Drome",
        segment="industrial_logistics_commercial",
        latitude=44.93,
        longitude=4.89,
        bbox=Bbox(south=44.85, west=4.78, north=45.05, east=5.05),
        commercial_priority_score=79,
        roof_area_proxy_score=82,
        accessibility_score=83,
    ),
    FranceSalesArea(
        id="grenoble",
        name="Grenoble Business and Public Buildings",
        region="Auvergne-Rhone-Alpes",
        department="Isere",
        segment="commercial_technology_public_buildings",
        latitude=45.18,
        longitude=5.72,
        bbox=Bbox(south=45.10, west=5.60, north=45.25, east=5.85),
        commercial_priority_score=82,
        roof_area_proxy_score=76,
        accessibility_score=81,
    ),
    FranceSalesArea(
        id="nantes-saint-nazaire",
        name="Nantes-Saint-Nazaire Industrial Axis",
        region="Pays de la Loire",
        department="Loire-Atlantique",
        segment="industrial_port_logistics",
        latitude=47.22,
        longitude=-1.58,
        bbox=Bbox(south=47.15, west=-1.75, north=47.35, east=-1.40),
        commercial_priority_score=88,
        roof_area_proxy_score=91,
        accessibility_score=87,
    ),
    FranceSalesArea(
        id="paris-saclay",
        name="Paris-Saclay and Essonne Business Parks",
        region="Ile-de-France",
        department="Essonne",
        segment="technology_commercial_public_buildings",
        latitude=48.73,
        longitude=2.20,
        bbox=Bbox(south=48.65, west=2.05, north=48.85, east=2.35),
        commercial_priority_score=96,
        roof_area_proxy_score=90,
        accessibility_score=96,
    ),
    FranceSalesArea(
        id="lille",
        name="Lille Metropole Logistics Rooftops",
        region="Hauts-de-France",
        department="Nord",
        segment="logistics_industrial_commercial",
        latitude=50.63,
        longitude=3.06,
        bbox=Bbox(south=50.52, west=2.95, north=50.75, east=3.20),
        commercial_priority_score=91,
        roof_area_proxy_score=89,
        accessibility_score=90,
    ),
    FranceSalesArea(
        id="strasbourg",
        name="Strasbourg Port and Industrial Area",
        region="Grand Est",
        department="Bas-Rhin",
        segment="industrial_port_logistics",
        latitude=48.58,
        longitude=7.75,
        bbox=Bbox(south=48.50, west=7.65, north=48.67, east=7.85),
        commercial_priority_score=84,
        roof_area_proxy_score=83,
        accessibility_score=86,
    ),
]
