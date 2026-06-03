import { Building2, Factory, MapPinned, Ruler } from "lucide-react";
import type { ProjectSummary } from "../types";

interface SummaryCardsProps {
  summary: ProjectSummary | null;
}

const numberFormat = new Intl.NumberFormat("en-US", { maximumFractionDigits: 0 });

export default function SummaryCards({ summary }: SummaryCardsProps) {
  const cards = [
    {
      label: "Buildings Analyzed",
      value: summary ? numberFormat.format(summary.total_buildings) : "0",
      icon: Building2,
      tone: "blue"
    },
    {
      label: "High Opportunity",
      value: summary ? numberFormat.format(summary.high_opportunity_count) : "0",
      icon: Factory,
      tone: "green"
    },
    {
      label: "Medium Opportunity",
      value: summary ? numberFormat.format(summary.medium_opportunity_count) : "0",
      icon: MapPinned,
      tone: "amber"
    },
    {
      label: "Usable Roof Area",
      value: summary ? `${numberFormat.format(summary.estimated_total_roof_area_m2)} m2` : "0 m2",
      icon: Ruler,
      tone: "coral"
    }
  ];

  return (
    <section className="summary-grid" aria-label="Analysis summary">
      {cards.map((card) => {
        const Icon = card.icon;
        return (
          <article className="summary-card" key={card.label}>
            <div className={`summary-icon ${card.tone}`}>
              <Icon size={20} aria-hidden="true" />
            </div>
            <div>
              <p>{card.label}</p>
              <strong>{card.value}</strong>
            </div>
          </article>
        );
      })}
    </section>
  );
}
