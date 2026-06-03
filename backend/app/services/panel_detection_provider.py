from __future__ import annotations

import hashlib
from dataclasses import dataclass


@dataclass
class PanelDetection:
    has_existing_panels: bool
    confidence: float
    provider: str


class PanelDetectionProvider:
    async def detect_existing_panels(
        self,
        building_id: str | None,
        latitude: float,
        longitude: float,
        roof_area_m2: float,
    ) -> PanelDetection:
        raise NotImplementedError


class MockPanelDetectionProvider(PanelDetectionProvider):
    async def detect_existing_panels(
        self,
        building_id: str | None,
        latitude: float,
        longitude: float,
        roof_area_m2: float,
    ) -> PanelDetection:
        latitude = float(latitude)
        longitude = float(longitude)
        roof_area_m2 = float(roof_area_m2)
        # TODO: Replace with satellite tile retrieval plus YOLO/segmentation inference.
        # TODO: Cache tile chips and model outputs by provider, bbox, zoom, and model version.
        key = f"{building_id}:{latitude:.5f}:{longitude:.5f}:{roof_area_m2:.1f}"
        digest = hashlib.sha256(key.encode("utf-8")).hexdigest()
        bucket = int(digest[:4], 16) % 100
        has_panels = bucket < 14 and roof_area_m2 > 80
        confidence = 0.72 + (bucket % 20) / 100
        return PanelDetection(has_existing_panels=has_panels, confidence=float(round(min(confidence, 0.94), 2)), provider="mock")
