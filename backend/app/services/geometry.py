from collections.abc import Iterable

from geoalchemy2.shape import from_shape, to_shape
from pyproj import Geod
from shapely.geometry import MultiPolygon, Point, Polygon, mapping
from shapely.geometry.base import BaseGeometry

GEOD = Geod(ellps="WGS84")


def ensure_multipolygon(geometry: BaseGeometry) -> MultiPolygon:
    if isinstance(geometry, MultiPolygon):
        return geometry
    if isinstance(geometry, Polygon):
        return MultiPolygon([geometry])
    raise ValueError(f"Expected Polygon or MultiPolygon, got {geometry.geom_type}")


def shape_to_wkb_element(geometry: BaseGeometry):
    return from_shape(geometry, srid=4326)


def db_geometry_to_geojson(geometry) -> dict:
    return mapping(to_shape(geometry))


def db_geometry_to_shape(geometry) -> BaseGeometry:
    return to_shape(geometry)


def area_m2(geometry: BaseGeometry) -> float:
    area, _ = GEOD.geometry_area_perimeter(geometry)
    return float(round(abs(area), 2))


def centroid_lat_lon(geometry: BaseGeometry) -> tuple[float, float]:
    centroid: Point = geometry.centroid
    return float(centroid.y), float(centroid.x)


def polygon_from_lon_lat_pairs(points: Iterable[tuple[float, float]]) -> Polygon | None:
    coords = list(points)
    if len(coords) < 3:
        return None
    if coords[0] != coords[-1]:
        coords.append(coords[0])
    polygon = Polygon(coords)
    if polygon.is_empty:
        return None
    if not polygon.is_valid:
        repaired = polygon.buffer(0)
        if isinstance(repaired, MultiPolygon):
            polygon = max(repaired.geoms, key=lambda geom: geom.area)
        elif isinstance(repaired, Polygon):
            polygon = repaired
        else:
            return None
    if polygon.is_empty or not polygon.is_valid or polygon.area == 0:
        return None
    return polygon
