import { useEffect, useMemo, useState } from "react";
import type { Feature, FeatureCollection, Geometry } from "geojson";
import L, { type LatLngBoundsExpression, type LatLngExpression, type LeafletMouseEvent, type PathOptions } from "leaflet";
import { GeoJSON, MapContainer, Rectangle, TileLayer, Tooltip, useMap, useMapEvents } from "react-leaflet";
import type { Bbox, BuildingFeature, BuildingFeatureCollection, FranceAreaRank, MapLayerMode } from "../types";

interface MapViewProps {
  bbox: Bbox;
  buildings: BuildingFeatureCollection | null;
  selectedId: string | null;
  drawEnabled: boolean;
  franceAreas: FranceAreaRank[];
  selectedAreaId: string | null;
  layerMode: MapLayerMode;
  onBboxChange: (bbox: Bbox) => void;
  onSelectBuilding: (feature: BuildingFeature) => void;
  onSelectArea: (area: FranceAreaRank) => void;
}

const colorByLevel = {
  high: "#22a06b",
  medium: "#f2b84b",
  low: "#e65f5c"
};

export default function MapView({
  bbox,
  buildings,
  selectedId,
  drawEnabled,
  franceAreas,
  selectedAreaId,
  layerMode,
  onBboxChange,
  onSelectBuilding,
  onSelectArea
}: MapViewProps) {
  const mapBounds = useMemo(() => boundsFromBbox(bbox), [bbox]);
  const features = buildings?.features ?? [];
  const geoJsonKey = `${features.map((feature) => feature.properties.id).join("-")}-${selectedId ?? "none"}`;

  return (
    <div className="map-shell">
      <MapContainer bounds={mapBounds} scrollWheelZoom className="map">
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
        <FitToBounds bbox={bbox} features={features} franceAreas={franceAreas} />
        <DrawBbox enabled={drawEnabled} bbox={bbox} onBboxChange={onBboxChange} />
        <Rectangle bounds={mapBounds} pathOptions={{ color: "#3674b5", weight: 2, dashArray: "6 6", fillOpacity: 0.04 }} />
        {franceAreas.map((area) => (
          <AreaRectangle
            area={area}
            key={area.id}
            layerMode={layerMode}
            selected={area.id === selectedAreaId}
            onSelectArea={onSelectArea}
          />
        ))}
        {features.length > 0 && (
          <GeoJSON
            key={geoJsonKey}
            data={{ type: "FeatureCollection", features } as FeatureCollection}
            style={(feature) => styleFeature(feature as Feature<Geometry, BuildingFeature["properties"]>, selectedId)}
            onEachFeature={(feature, layer) => {
              const typedFeature = feature as BuildingFeature;
              layer.on({
                click: () => onSelectBuilding(typedFeature)
              });
              layer.bindTooltip(
                `<strong>Score ${typedFeature.properties.lead_score}</strong><br>${typedFeature.properties.building_type}`,
                { sticky: true }
              );
            }}
          />
        )}
      </MapContainer>
      <div className="map-legend">
        {layerMode === "temperature" ? (
          <>
            <LegendItem color="#2f80ed" label="Cooler" />
            <LegendItem color="#f2b84b" label="Warm" />
            <LegendItem color="#e65f5c" label="Heat Risk" />
          </>
        ) : layerMode === "solar" ? (
          <>
            <LegendItem color="#8bc34a" label="Moderate" />
            <LegendItem color="#22a06b" label="Strong" />
            <LegendItem color="#0b6b4f" label="Excellent" />
          </>
        ) : (
          <>
            <LegendItem color={colorByLevel.high} label="High" />
            <LegendItem color={colorByLevel.medium} label="Medium" />
            <LegendItem color={colorByLevel.low} label="Low" />
          </>
        )}
      </div>
    </div>
  );
}

function FitToBounds({ bbox, features, franceAreas }: { bbox: Bbox; features: BuildingFeature[]; franceAreas: FranceAreaRank[] }) {
  const map = useMap();

  useEffect(() => {
    if (features.length > 0) {
      const bounds = L.geoJSON({ type: "FeatureCollection", features } as FeatureCollection).getBounds();
      if (bounds.isValid()) {
        map.fitBounds(bounds.pad(0.16), { animate: true });
        return;
      }
    }
    if (franceAreas.length > 0 && features.length === 0) {
      const corners: LatLngExpression[] = franceAreas.flatMap((area) => [
        [area.bbox.south, area.bbox.west] as [number, number],
        [area.bbox.north, area.bbox.east] as [number, number]
      ]);
      const bounds = L.latLngBounds(corners);
      if (bounds.isValid()) {
        map.fitBounds(bounds.pad(0.08), { animate: true });
        return;
      }
    }
    map.fitBounds(boundsFromBbox(bbox), { animate: true });
  }, [bbox, features, franceAreas, map]);

  return null;
}

function AreaRectangle({
  area,
  layerMode,
  selected,
  onSelectArea
}: {
  area: FranceAreaRank;
  layerMode: MapLayerMode;
  selected: boolean;
  onSelectArea: (area: FranceAreaRank) => void;
}) {
  const color = areaColor(area, layerMode);
  return (
    <Rectangle
      bounds={boundsFromBbox(area.bbox)}
      pathOptions={{
        color: selected ? "#101828" : color,
        weight: selected ? 3 : 1.8,
        fillColor: color,
        fillOpacity: selected ? 0.28 : 0.16
      }}
      eventHandlers={{
        click: () => onSelectArea(area)
      }}
    >
      <Tooltip sticky>
        <strong>{area.name}</strong>
        <br />
        Overall {area.overall_score} | Solar {area.solar_score}
        <br />
        Heat risk {area.heat_risk_score}
      </Tooltip>
    </Rectangle>
  );
}

function DrawBbox({ enabled, bbox, onBboxChange }: { enabled: boolean; bbox: Bbox; onBboxChange: (bbox: Bbox) => void }) {
  const [start, setStart] = useState<L.LatLng | null>(null);
  const [preview, setPreview] = useState<LatLngBoundsExpression | null>(null);

  useEffect(() => {
    if (!enabled) {
      setStart(null);
      setPreview(null);
    }
  }, [enabled]);

  useMapEvents({
    click(event: LeafletMouseEvent) {
      if (!enabled) return;
      if (!start) {
        setStart(event.latlng);
        return;
      }

      const next = bboxFromCorners(start.lat, start.lng, event.latlng.lat, event.latlng.lng);
      onBboxChange(next);
      setStart(null);
      setPreview(null);
    },
    mousemove(event: LeafletMouseEvent) {
      if (!enabled || !start) return;
      setPreview([
        [start.lat, start.lng],
        [event.latlng.lat, event.latlng.lng]
      ]);
    }
  });

  return preview ? <Rectangle bounds={preview} pathOptions={{ color: "#1f8a70", weight: 2, fillOpacity: 0.08 }} /> : null;
}

function styleFeature(feature: Feature<Geometry, BuildingFeature["properties"]>, selectedId: string | null): PathOptions {
  const level = feature.properties?.opportunity_level ?? "low";
  const selected = feature.properties?.id === selectedId;
  return {
    color: selected ? "#101828" : colorByLevel[level],
    weight: selected ? 3 : 1.6,
    fillColor: colorByLevel[level],
    fillOpacity: selected ? 0.74 : 0.52
  };
}

function boundsFromBbox(bbox: Bbox): LatLngBoundsExpression {
  return [
    [bbox.south, bbox.west],
    [bbox.north, bbox.east]
  ];
}

function bboxFromCorners(latA: number, lonA: number, latB: number, lonB: number): Bbox {
  return {
    south: Math.min(latA, latB),
    west: Math.min(lonA, lonB),
    north: Math.max(latA, latB),
    east: Math.max(lonA, lonB)
  };
}

function areaColor(area: FranceAreaRank, layerMode: MapLayerMode) {
  if (layerMode === "temperature") {
    if (area.heat_risk_score >= 70) return "#e65f5c";
    if (area.heat_risk_score >= 38) return "#f2b84b";
    return "#2f80ed";
  }
  const score = layerMode === "solar" ? area.solar_score : area.overall_score;
  if (score >= 85) return "#0b6b4f";
  if (score >= 70) return "#22a06b";
  if (score >= 55) return "#8bc34a";
  return "#f2b84b";
}

function LegendItem({ color, label }: { color: string; label: string }) {
  return (
    <span>
      <i style={{ backgroundColor: color }} />
      {label}
    </span>
  );
}
