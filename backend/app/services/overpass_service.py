from __future__ import annotations

import logging
import xml.etree.ElementTree as ET

import httpx

from app.config import Settings
from app.schemas.project import Bbox
from app.services.demo_data import BuildingCandidate, generate_sample_buildings
from app.services.geometry import area_m2, polygon_from_lon_lat_pairs

logger = logging.getLogger(__name__)


class OverpassService:
    def __init__(self, settings: Settings):
        self.settings = settings

    async def fetch_buildings(self, bbox: Bbox, limit: int) -> tuple[list[BuildingCandidate], str]:
        try:
            buildings = await self._fetch_from_overpass(bbox, limit)
            if buildings:
                return buildings[:limit], "openstreetmap"
            logger.info("Overpass returned no buildings; trying OSM Map API")
        except Exception as exc:  # noqa: BLE001 - API fallback should keep demo alive.
            logger.warning("Overpass fetch failed; trying OSM Map API: %s", exc)

        try:
            buildings = await self._fetch_from_osm_map_api(bbox, limit)
            if buildings:
                return buildings[:limit], "openstreetmap"
            logger.info("OSM Map API returned no buildings; using sample fallback data")
        except Exception as exc:  # noqa: BLE001 - sample fallback should keep demo alive.
            logger.warning("OSM Map API fetch failed; using sample fallback data: %s", exc)

        return generate_sample_buildings(bbox, limit=limit), "sample_fallback"

    async def _fetch_from_overpass(self, bbox: Bbox, limit: int) -> list[BuildingCandidate]:
        query = f"""
        [out:json][timeout:{self.settings.overpass_timeout_seconds}];
        (
          way["building"]({bbox.south},{bbox.west},{bbox.north},{bbox.east});
        );
        out geom {limit};
        """
        last_error: Exception | None = None
        for url in self.settings.overpass_urls:
            try:
                async with httpx.AsyncClient(timeout=self.settings.overpass_timeout_seconds + 10) as client:
                    response = await client.get(url, params={"data": query})
                    response.raise_for_status()
                    payload = response.json()
                return parse_overpass_buildings(payload)
            except Exception as exc:  # noqa: BLE001 - try next mirror before falling back to sample data.
                last_error = exc
                logger.warning("Overpass mirror failed (%s): %s", url, exc)
        if last_error:
            raise last_error
        return []

    async def _fetch_from_osm_map_api(self, bbox: Bbox, limit: int) -> list[BuildingCandidate]:
        collected: list[BuildingCandidate] = []
        seen_osm_ids: set[str] = set()
        async with httpx.AsyncClient(timeout=self.settings.overpass_timeout_seconds + 20) as client:
            for tile in sample_bboxes(bbox):
                params = {
                    "bbox": f"{tile.west},{tile.south},{tile.east},{tile.north}",
                }
                response = await client.get(self.settings.osm_map_api_url, params=params)
                response.raise_for_status()
                for candidate in parse_osm_map_xml(response.content):
                    if candidate.osm_id and candidate.osm_id in seen_osm_ids:
                        continue
                    if candidate.osm_id:
                        seen_osm_ids.add(candidate.osm_id)
                    collected.append(candidate)
                    if len(collected) >= limit:
                        return collected
        return collected


def parse_overpass_buildings(payload: dict) -> list[BuildingCandidate]:
    candidates: list[BuildingCandidate] = []
    for element in payload.get("elements", []):
        geometry_points = element.get("geometry") or []
        polygon = polygon_from_lon_lat_pairs((point["lon"], point["lat"]) for point in geometry_points)
        if polygon is None:
            continue

        measured_area = area_m2(polygon)
        if measured_area < 25:
            continue

        tags = element.get("tags", {})
        candidates.append(
            BuildingCandidate(
                osm_id=str(element.get("id")) if element.get("id") is not None else None,
                geometry=polygon,
                area_m2=measured_area,
                building_type=normalize_building_type(tags.get("building")),
                address=format_address(tags),
                source="openstreetmap",
            )
        )
    return candidates


def parse_osm_map_xml(content: bytes) -> list[BuildingCandidate]:
    root = ET.fromstring(content)
    nodes: dict[str, tuple[float, float]] = {}
    for node in root.findall("node"):
        node_id = node.attrib.get("id")
        lat = node.attrib.get("lat")
        lon = node.attrib.get("lon")
        if node_id and lat and lon:
            nodes[node_id] = (float(lon), float(lat))

    candidates: list[BuildingCandidate] = []
    for way in root.findall("way"):
        tags = {tag.attrib.get("k"): tag.attrib.get("v") for tag in way.findall("tag") if tag.attrib.get("k")}
        if "building" not in tags:
            continue
        coords = [nodes[nd.attrib["ref"]] for nd in way.findall("nd") if nd.attrib.get("ref") in nodes]
        polygon = polygon_from_lon_lat_pairs(coords)
        if polygon is None:
            continue
        measured_area = area_m2(polygon)
        if measured_area < 25:
            continue
        osm_id = way.attrib.get("id")
        candidates.append(
            BuildingCandidate(
                osm_id=f"osm-way-{osm_id}" if osm_id else None,
                geometry=polygon,
                area_m2=measured_area,
                building_type=normalize_building_type(tags.get("building")),
                address=format_address(tags),
                source="openstreetmap_map_api",
            )
        )
    return candidates


def sample_bboxes(bbox: Bbox, cell_size: float = 0.01, max_tiles: int = 9) -> list[Bbox]:
    lat_span = bbox.north - bbox.south
    lon_span = bbox.east - bbox.west
    if lat_span <= cell_size and lon_span <= cell_size:
        return [bbox]

    center_lat = (bbox.south + bbox.north) / 2
    center_lon = (bbox.west + bbox.east) / 2
    offsets = [
        (0, 0),
        (0, 1),
        (0, -1),
        (1, 0),
        (-1, 0),
        (1, 1),
        (1, -1),
        (-1, 1),
        (-1, -1),
    ]
    tiles: list[Bbox] = []
    half = cell_size / 2
    for lat_offset, lon_offset in offsets[:max_tiles]:
        lat = center_lat + lat_offset * cell_size
        lon = center_lon + lon_offset * cell_size
        south = max(bbox.south, lat - half)
        north = min(bbox.north, lat + half)
        west = max(bbox.west, lon - half)
        east = min(bbox.east, lon + half)
        if north > south and east > west:
            tiles.append(Bbox(south=south, west=west, north=north, east=east))
    return tiles


def normalize_building_type(value: str | None) -> str:
    if not value or value in {"yes", "true"}:
        return "unknown"
    normalized = value.lower().strip().replace("_", " ")
    aliases = {
        "apartments": "apartment",
        "commercial": "commercial",
        "retail": "commercial",
        "industrial": "industrial",
        "warehouse": "warehouse",
        "school": "school",
        "university": "school",
        "hospital": "hospital",
        "residential": "residential",
        "house": "residential",
        "detached": "residential",
    }
    return aliases.get(normalized, normalized)


def format_address(tags: dict) -> str | None:
    parts = [
        tags.get("addr:housenumber"),
        tags.get("addr:street"),
        tags.get("addr:suburb"),
        tags.get("addr:city"),
    ]
    address = ", ".join(part for part in parts if part)
    return address or None
