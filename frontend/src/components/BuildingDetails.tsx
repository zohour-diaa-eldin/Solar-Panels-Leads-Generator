import { BadgeCheck, CircleAlert, Gauge, PanelsTopLeft } from "lucide-react";
import type { BuildingFeature } from "../types";

interface BuildingDetailsProps {
  building: BuildingFeature | null;
}

const formatter = new Intl.NumberFormat("en-US", { maximumFractionDigits: 1 });

const componentLabels: Record<string, string> = {
  estimated_solar_potential: "Solar potential",
  usable_roof_area: "Usable roof area",
  no_existing_solar_panels: "No existing panels",
  building_type_priority: "Building priority",
  accessibility_proximity: "Accessibility",
  temperature_fit: "Temperature fit"
};

export default function BuildingDetails({ building }: BuildingDetailsProps) {
  if (!building) {
    return (
      <aside className="details-panel empty-state">
        <PanelsTopLeft size={26} aria-hidden="true" />
        <h2>Building Details</h2>
        <p>Select a scored polygon to inspect the lead profile.</p>
      </aside>
    );
  }

  const props = building.properties;
  const components = props.scoring_explanation.components;
  const solarProvider = props.scoring_explanation.solar_provider;
  const temperatureAdjustment = props.scoring_explanation.adjustments?.temperature_adjustment_points;
  const environment = props.scoring_explanation.environment as
    | {
        average_annual_temp_c?: number | null;
        summer_max_temp_c?: number | null;
        heat_risk_score?: number | null;
        temperature_fit_score?: number | null;
      }
    | undefined;

  return (
    <aside className="details-panel">
      <div className="details-header">
        <div>
          <span className={`pill ${props.opportunity_level}`}>{props.opportunity_level}</span>
          <h2>{props.address ?? `OSM ${props.osm_id ?? props.id.slice(0, 8)}`}</h2>
        </div>
        <div className="score-badge">
          <Gauge size={18} aria-hidden="true" />
          <strong>{formatter.format(props.lead_score)}</strong>
        </div>
      </div>

      <div className="detail-metrics">
        <Metric label="Roof area" value={`${formatter.format(props.usable_roof_area_m2)} m2`} />
        <Metric label="Building type" value={props.building_type} />
        <Metric label="Solar potential" value={`${formatter.format(props.estimated_solar_potential)}/100`} />
        {solarProvider?.provider && (
          <Metric
            label="Solar data"
            value={`${formatProviderName(solarProvider.provider)} · ${formatProviderName(
              solarProvider.data_quality ?? "estimated"
            )}`}
          />
        )}
        {solarProvider?.annual_kwh !== undefined && solarProvider.annual_kwh !== null && (
          <Metric label="Annual PV output" value={`${formatter.format(solarProvider.annual_kwh)} kWh`} />
        )}
        {solarProvider?.max_panel_count !== undefined && solarProvider.max_panel_count !== null && (
          <Metric label="Panel capacity" value={`${solarProvider.max_panel_count} panels`} />
        )}
        <Metric
          label="Existing panels"
          value={props.has_existing_panels ? "Detected" : "Not detected"}
          tone={props.has_existing_panels ? "warning" : "positive"}
        />
        {environment?.summer_max_temp_c !== undefined && environment.summer_max_temp_c !== null && (
          <Metric label="Summer max" value={`${formatter.format(environment.summer_max_temp_c)} C`} />
        )}
        {environment?.heat_risk_score !== undefined && environment.heat_risk_score !== null && (
          <Metric label="Heat risk" value={`${formatter.format(environment.heat_risk_score)}/100`} />
        )}
        {temperatureAdjustment !== undefined && temperatureAdjustment !== 0 && (
          <Metric label="Temp adjustment" value={`${temperatureAdjustment > 0 ? "+" : ""}${formatter.format(temperatureAdjustment)} pts`} />
        )}
      </div>

      <section className="explanation-block">
        <h3>AI Lead Score</h3>
        {Object.entries(components).map(([key, value]) => (
          <div className="score-row" key={key}>
            <span>{componentLabels[key] ?? key}</span>
            <div className="score-track" aria-hidden="true">
              <div style={{ width: `${Math.min(100, Math.max(0, value))}%` }} />
            </div>
            <strong>{formatter.format(value)}</strong>
          </div>
        ))}
      </section>

      <section className="action-block">
        {props.has_existing_panels ? <CircleAlert size={20} aria-hidden="true" /> : <BadgeCheck size={20} aria-hidden="true" />}
        <p>{props.recommended_action}</p>
      </section>
    </aside>
  );
}

function Metric({ label, value, tone }: { label: string; value: string; tone?: "warning" | "positive" }) {
  return (
    <div className={`metric ${tone ?? ""}`}>
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}

function formatProviderName(value: string) {
  return value
    .split("_")
    .filter(Boolean)
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(" ");
}
