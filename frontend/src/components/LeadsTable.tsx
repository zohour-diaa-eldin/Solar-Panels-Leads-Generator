import { ArrowUpRight } from "lucide-react";
import type { ProjectSummary } from "../types";

interface LeadsTableProps {
  summary: ProjectSummary | null;
  selectedId: string | null;
  onSelect: (buildingId: string) => void;
}

const formatter = new Intl.NumberFormat("en-US", { maximumFractionDigits: 1 });

export default function LeadsTable({ summary, selectedId, onSelect }: LeadsTableProps) {
  const leads = summary?.top_leads ?? [];

  return (
    <section className="leads-section">
      <div className="section-heading">
        <div>
          <h2>Top 20 Leads</h2>
          <p>Ranked by weighted opportunity score</p>
        </div>
      </div>
      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Lead</th>
              <th>Type</th>
              <th>Score</th>
              <th>Roof</th>
              <th>Potential</th>
              <th>Action</th>
            </tr>
          </thead>
          <tbody>
            {leads.length === 0 ? (
              <tr>
                <td colSpan={6} className="empty-cell">
                  No leads analyzed yet.
                </td>
              </tr>
            ) : (
              leads.map((lead, index) => (
                <tr
                  key={lead.id}
                  className={selectedId === lead.id ? "selected" : ""}
                  onClick={() => onSelect(lead.id)}
                  tabIndex={0}
                  onKeyDown={(event) => {
                    if (event.key === "Enter") onSelect(lead.id);
                  }}
                >
                  <td>
                    <button type="button" className="row-button" aria-label={`Open lead ${index + 1}`}>
                      <ArrowUpRight size={15} aria-hidden="true" />
                    </button>
                    <span>{lead.address ?? `Lead ${index + 1}`}</span>
                  </td>
                  <td>{lead.building_type}</td>
                  <td>
                    <span className={`score-chip ${lead.opportunity_level}`}>{formatter.format(lead.lead_score)}</span>
                  </td>
                  <td>{formatter.format(lead.usable_roof_area_m2)} m2</td>
                  <td>{formatter.format(lead.estimated_solar_potential)}/100</td>
                  <td>{lead.recommended_action}</td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </section>
  );
}
