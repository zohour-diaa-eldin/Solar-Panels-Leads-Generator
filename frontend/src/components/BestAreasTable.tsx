import { ArrowUpRight, ThermometerSun } from "lucide-react";
import type { FranceAreaRank } from "../types";

interface BestAreasTableProps {
  areas: FranceAreaRank[];
  selectedId: string | null;
  isLoading: boolean;
  onSelect: (area: FranceAreaRank) => void;
  onAnalyze: (area: FranceAreaRank) => void;
}

const formatter = new Intl.NumberFormat("en-US", { maximumFractionDigits: 1 });

export default function BestAreasTable({ areas, selectedId, isLoading, onSelect, onAnalyze }: BestAreasTableProps) {
  return (
    <section className="areas-section">
      <div className="section-heading">
        <div>
          <h2>Best Sales Areas</h2>
          <p>France screening ranked by PVGIS solar, temperature fit, and commercial roof proxies</p>
        </div>
        <span className="data-pill">{isLoading ? "Ranking..." : `${areas.length} areas`}</span>
      </div>

      <div className="areas-grid">
        {areas.length === 0 ? (
          <div className="area-empty">
            <ThermometerSun size={24} aria-hidden="true" />
            <p>Run France ranking to compare real solar and temperature signals.</p>
          </div>
        ) : (
          areas.map((area, index) => (
            <article
              className={selectedId === area.id ? "area-card selected" : "area-card"}
              key={area.id}
              onClick={() => onSelect(area)}
            >
              <div className="area-card-top">
                <span className="rank-number">{index + 1}</span>
                <div>
                  <h3>{area.name}</h3>
                  <p>{area.region}</p>
                </div>
                <strong>{formatter.format(area.overall_score)}</strong>
              </div>
              <div className="area-metrics">
                <span>PV {area.estimated_pv_output_kwh_kwp ? formatter.format(area.estimated_pv_output_kwh_kwp) : "-"} kWh/kWp</span>
                <span>Solar {formatter.format(area.solar_score)}</span>
                <span>Heat risk {formatter.format(area.heat_risk_score)}</span>
                <span>Summer {area.summer_max_temp_c ? `${formatter.format(area.summer_max_temp_c)} C` : "-"}</span>
              </div>
              <p className="area-action">{area.recommended_action}</p>
              <button
                type="button"
                className="area-analyze"
                onClick={(event) => {
                  event.stopPropagation();
                  onAnalyze(area);
                }}
              >
                <ArrowUpRight size={15} aria-hidden="true" />
                Analyze Buildings
              </button>
            </article>
          ))
        )}
      </div>
    </section>
  );
}
