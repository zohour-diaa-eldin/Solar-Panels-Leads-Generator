from __future__ import annotations

import hashlib
import random
from dataclasses import dataclass

from shapely.geometry import Polygon

from app.schemas.project import Bbox
from app.services.geometry import area_m2


CAIRO_DEMO_BBOX = Bbox(south=30.035, west=31.206, north=30.068, east=31.255)


@dataclass
class BuildingCandidate:
    osm_id: str | None
    geometry: Polygon
    area_m2: float
    building_type: str
    address: str | None
    source: str


BUILDING_TYPES = [
    "commercial",
    "apartments",
    "residential",
    "warehouse",
    "school",
    "hospital",
    "industrial",
    "retail",
    "yes",
]


def generate_sample_buildings(bbox: Bbox, limit: int = 80) -> list[BuildingCandidate]:
    seed = hashlib.sha256(f"{bbox.south}:{bbox.west}:{bbox.north}:{bbox.east}".encode("utf-8")).hexdigest()
    rng = random.Random(seed)
    lat_span = bbox.north - bbox.south
    lon_span = bbox.east - bbox.west
    count = min(max(limit, 24), 140)
    candidates: list[BuildingCandidate] = []

    for index in range(count):
        lat = bbox.south + lat_span * rng.uniform(0.08, 0.92)
        lon = bbox.west + lon_span * rng.uniform(0.08, 0.92)
        width = lon_span * rng.uniform(0.006, 0.018)
        height = lat_span * rng.uniform(0.006, 0.02)
        angle_jitter = rng.uniform(-0.00008, 0.00008)
        polygon = Polygon(
            [
                (lon - width, lat - height),
                (lon + width, lat - height + angle_jitter),
                (lon + width, lat + height),
                (lon - width, lat + height - angle_jitter),
            ]
        )
        if not polygon.is_valid:
            polygon = polygon.buffer(0)
        measured_area = area_m2(polygon)
        if measured_area < 35:
            continue

        building_type = BUILDING_TYPES[index % len(BUILDING_TYPES)]
        address = f"Demo Block {100 + index}, Cairo" if index % 3 != 0 else None
        candidates.append(
            BuildingCandidate(
                osm_id=f"demo-{index + 1}",
                geometry=polygon,
                area_m2=measured_area,
                building_type=building_type,
                address=address,
                source="sample_fallback",
            )
        )

    return candidates[:limit]
