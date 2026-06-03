import { useCallback, useEffect, useMemo, useState } from "react";
import { Crosshair, Globe2, Loader2, MapPinned, Play, RotateCcw } from "lucide-react";
import {
  analyzeProject,
  createProject,
  getBuilding,
  getDemoProject,
  getProjectBuildings,
  getProjectSummary,
  rankFranceAreas
} from "./api/client";
import BestAreasTable from "./components/BestAreasTable";
import BuildingDetails from "./components/BuildingDetails";
import LeadsTable from "./components/LeadsTable";
import MapView from "./components/MapView";
import SummaryCards from "./components/SummaryCards";
import type {
  Bbox,
  BuildingFeature,
  BuildingFeatureCollection,
  FranceAreaRank,
  MapLayerMode,
  Project,
  ProjectSummary
} from "./types";

const CAIRO_BBOX: Bbox = { south: 30.035, west: 31.206, north: 30.068, east: 31.255 };
const FRANCE_BBOX: Bbox = { south: 41.0, west: -5.6, north: 51.8, east: 9.8 };

const AREA_PRESETS: { label: string; city: string; bbox: Bbox }[] = [
  { label: "Cairo Demo", city: "Cairo, Egypt", bbox: CAIRO_BBOX },
  { label: "New Cairo", city: "Cairo, Egypt", bbox: { south: 30.004, west: 31.428, north: 30.05, east: 31.51 } },
  { label: "Giza", city: "Giza, Egypt", bbox: { south: 29.978, west: 31.12, north: 30.026, east: 31.198 } }
];

export default function App() {
  const [country, setCountry] = useState<"france" | "egypt">("france");
  const [project, setProject] = useState<Project | null>(null);
  const [demoProject, setDemoProject] = useState<Project | null>(null);
  const [bbox, setBbox] = useState<Bbox>(FRANCE_BBOX);
  const [buildings, setBuildings] = useState<BuildingFeatureCollection | null>(null);
  const [summary, setSummary] = useState<ProjectSummary | null>(null);
  const [selectedBuilding, setSelectedBuilding] = useState<BuildingFeature | null>(null);
  const [franceAreas, setFranceAreas] = useState<FranceAreaRank[]>([]);
  const [selectedFranceArea, setSelectedFranceArea] = useState<FranceAreaRank | null>(null);
  const [layerMode, setLayerMode] = useState<MapLayerMode>("solar");
  const [drawEnabled, setDrawEnabled] = useState(false);
  const [status, setStatus] = useState("Ready");
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [isRanking, setIsRanking] = useState(false);

  const selectedId = selectedBuilding?.properties.id ?? null;

  const loadProjectData = useCallback(async (projectId: string) => {
    const [buildingData, summaryData] = await Promise.all([getProjectBuildings(projectId), getProjectSummary(projectId)]);
    setBuildings(buildingData);
    setSummary(summaryData);
    if (buildingData.features.length === 0) {
      setSelectedBuilding(null);
    }
  }, []);

  useEffect(() => {
    async function boot() {
      try {
        const demo = await getDemoProject();
        setDemoProject(demo);
        await loadFranceRanking();
      } catch (bootError) {
        setError(bootError instanceof Error ? bootError.message : "Could not load startup data");
      } finally {
        setIsLoading(false);
      }
    }
    void boot();
  }, []);

  async function loadFranceRanking() {
    setIsRanking(true);
    setError(null);
    setStatus("Ranking France sales areas with PVGIS and temperature data");
    try {
      const response = await rankFranceAreas(12);
      setFranceAreas(response.areas);
      const firstArea = response.areas[0] ?? null;
      setSelectedFranceArea(firstArea);
      setBbox(firstArea?.bbox ?? FRANCE_BBOX);
      setBuildings(null);
      setSummary(null);
      setSelectedBuilding(null);
      setProject(null);
      setLayerMode("solar");
      setStatus(`Ranked ${response.areas.length} France sales areas`);
    } catch (rankingError) {
      setError(rankingError instanceof Error ? rankingError.message : "France ranking failed");
      setStatus("France ranking failed");
    } finally {
      setIsRanking(false);
    }
  }

  async function handleAnalyze() {
    if (country === "france") {
      await handleAnalyzeFranceArea(selectedFranceArea);
      return;
    }
    if (!project) return;
    setIsAnalyzing(true);
    setError(null);
    setStatus("Analyzing buildings and scoring leads");
    setSelectedBuilding(null);

    try {
      const response = await analyzeProject(project.id, bbox);
      await loadProjectData(project.id);
      setStatus(`${response.message} Source: ${response.source}.`);
      setDrawEnabled(false);
    } catch (analysisError) {
      setError(analysisError instanceof Error ? analysisError.message : "Analysis failed");
      setStatus("Analysis failed");
    } finally {
      setIsAnalyzing(false);
    }
  }

  async function handleAnalyzeFranceArea(area: FranceAreaRank | null) {
    if (!area) {
      setError("Select a France sales area first");
      return;
    }
    setCountry("france");
    setSelectedFranceArea(area);
    setBbox(area.bbox);
    setIsAnalyzing(true);
    setError(null);
    setStatus(`Creating France project for ${area.name}`);
    setSelectedBuilding(null);

    try {
      const nextProject = await createProject({
        name: `France Leads - ${area.name}`,
        city: `${area.department}, France`,
        bbox: area.bbox
      });
      setProject(nextProject);
      setStatus(`Analyzing buildings in ${area.name}`);
      const response = await analyzeProject(nextProject.id, area.bbox, 160);
      await loadProjectData(nextProject.id);
      setStatus(`${response.message} Source: ${response.source}.`);
      setLayerMode("leads");
      setDrawEnabled(false);
    } catch (analysisError) {
      setError(analysisError instanceof Error ? analysisError.message : "France area analysis failed");
      setStatus("France area analysis failed");
    } finally {
      setIsAnalyzing(false);
    }
  }

  async function handleSelectBuilding(feature: BuildingFeature) {
    setSelectedBuilding(feature);
    try {
      const detailed = await getBuilding(feature.properties.id);
      setSelectedBuilding(detailed);
    } catch {
      setSelectedBuilding(feature);
    }
  }

  async function handleSelectLead(buildingId: string) {
    try {
      const detailed = await getBuilding(buildingId);
      setSelectedBuilding(detailed);
    } catch (selectionError) {
      setError(selectionError instanceof Error ? selectionError.message : "Could not load building");
    }
  }

  const activePreset = useMemo(
    () => AREA_PRESETS.find((preset) => sameBbox(preset.bbox, bbox))?.label ?? "Custom bbox",
    [bbox]
  );

  function handleSelectFranceArea(area: FranceAreaRank) {
    setCountry("france");
    setSelectedFranceArea(area);
    setBbox(area.bbox);
    setBuildings(null);
    setSummary(null);
    setSelectedBuilding(null);
    setProject(null);
    setLayerMode((mode) => (mode === "leads" ? "solar" : mode));
    setStatus(`Selected ${area.name}`);
  }

  async function handleCountryChange(nextCountry: "france" | "egypt") {
    setCountry(nextCountry);
    setError(null);
    setSelectedBuilding(null);
    setDrawEnabled(false);
    if (nextCountry === "france") {
      setBbox(selectedFranceArea?.bbox ?? FRANCE_BBOX);
      setBuildings(null);
      setSummary(null);
      setProject(null);
      setLayerMode("solar");
      if (franceAreas.length === 0) {
        await loadFranceRanking();
      }
      return;
    }

    const demo = demoProject ?? (await getDemoProject());
    setDemoProject(demo);
    setProject(demo);
    if (demo.bbox) setBbox(demo.bbox);
    setFranceAreas([]);
    setSelectedFranceArea(null);
    setLayerMode("leads");
    await loadProjectData(demo.id);
    setStatus("Cairo demo project loaded");
  }

  return (
    <main className="app-shell">
      <header className="topbar">
        <div>
          <span className="eyebrow">Solar Lead AI</span>
          <h1>Rooftop Opportunity Command Center</h1>
        </div>
        <div className="status-strip">
          <span className={error ? "status-dot error" : isAnalyzing ? "status-dot active" : "status-dot"} />
          <span>{error ?? status}</span>
        </div>
      </header>

      <section className="control-band">
        <div className="control-group">
          <label htmlFor="country-select">Country</label>
          <select
            id="country-select"
            value={country}
            onChange={(event) => void handleCountryChange(event.target.value as "france" | "egypt")}
          >
            <option value="france">France</option>
            <option value="egypt">Egypt Demo</option>
          </select>
        </div>

        <div className="control-group">
          <label htmlFor="area-select">Area</label>
          {country === "france" ? (
            <select
              id="area-select"
              value={selectedFranceArea?.id ?? ""}
              onChange={(event) => {
                const area = franceAreas.find((item) => item.id === event.target.value);
                if (area) handleSelectFranceArea(area);
              }}
            >
              {franceAreas.map((area) => (
                <option value={area.id} key={area.id}>
                  {area.name}
                </option>
              ))}
              {franceAreas.length === 0 && <option value="">Rank France areas</option>}
            </select>
          ) : (
            <select
              id="area-select"
              value={activePreset}
              onChange={(event) => {
                const preset = AREA_PRESETS.find((item) => item.label === event.target.value);
                if (preset) {
                  setBbox(preset.bbox);
                  setDrawEnabled(false);
                }
              }}
            >
              {AREA_PRESETS.map((preset) => (
                <option key={preset.label}>{preset.label}</option>
              ))}
              <option>Custom bbox</option>
            </select>
          )}
        </div>

        <div className="control-group">
          <label htmlFor="layer-select">Layer</label>
          <select id="layer-select" value={layerMode} onChange={(event) => setLayerMode(event.target.value as MapLayerMode)}>
            <option value="solar">Solar Potential</option>
            <option value="temperature">Temperature</option>
            <option value="leads">AI Lead Score</option>
          </select>
        </div>

        <div className="bbox-readout">
          <MapPinned size={17} aria-hidden="true" />
          <span>
            {bbox.south.toFixed(4)}, {bbox.west.toFixed(4)} to {bbox.north.toFixed(4)}, {bbox.east.toFixed(4)}
          </span>
        </div>

        <div className="control-actions">
          {country === "france" && (
            <button type="button" className="secondary-button" onClick={() => void loadFranceRanking()} disabled={isRanking || isAnalyzing}>
              {isRanking ? <Loader2 size={17} className="spin" aria-hidden="true" /> : <Globe2 size={17} aria-hidden="true" />}
              Rank France
            </button>
          )}
          <button type="button" className={drawEnabled ? "secondary-button active" : "secondary-button"} onClick={() => setDrawEnabled((value) => !value)}>
            <Crosshair size={17} aria-hidden="true" />
            Draw Bbox
          </button>
          <button
            type="button"
            className="secondary-button"
            onClick={() => {
              void handleCountryChange("egypt");
            }}
          >
            <RotateCcw size={17} aria-hidden="true" />
            Cairo Demo
          </button>
          <button type="button" className="primary-button" onClick={handleAnalyze} disabled={isAnalyzing || isLoading || isRanking}>
            {isAnalyzing ? <Loader2 size={18} className="spin" aria-hidden="true" /> : <Play size={18} aria-hidden="true" />}
            {country === "france" ? "Analyze Buildings" : "Analyze Area"}
          </button>
        </div>
      </section>

      {country === "france" && (
        <BestAreasTable
          areas={franceAreas}
          selectedId={selectedFranceArea?.id ?? null}
          isLoading={isRanking}
          onSelect={handleSelectFranceArea}
          onAnalyze={(area) => void handleAnalyzeFranceArea(area)}
        />
      )}

      <SummaryCards summary={summary} />

      <section className="workspace-grid">
        <MapView
          bbox={bbox}
          buildings={buildings}
          selectedId={selectedId}
          drawEnabled={drawEnabled}
          franceAreas={country === "france" ? franceAreas : []}
          selectedAreaId={selectedFranceArea?.id ?? null}
          layerMode={layerMode}
          onBboxChange={setBbox}
          onSelectBuilding={handleSelectBuilding}
          onSelectArea={handleSelectFranceArea}
        />
        <BuildingDetails building={selectedBuilding} />
      </section>

      <LeadsTable summary={summary} selectedId={selectedId} onSelect={handleSelectLead} />
    </main>
  );
}

function sameBbox(a: Bbox, b: Bbox) {
  return a.south === b.south && a.west === b.west && a.north === b.north && a.east === b.east;
}
