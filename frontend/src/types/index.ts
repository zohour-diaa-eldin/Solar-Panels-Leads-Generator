import type { Geometry } from "geojson";

export type OpportunityLevel = "high" | "medium" | "low";

export interface Bbox {
  south: number;
  west: number;
  north: number;
  east: number;
}

export interface Project {
  id: string;
  name: string;
  city: string | null;
  status: string;
  bbox: Bbox | null;
  created_at: string;
  updated_at: string;
}

export interface ProjectCreateInput {
  name: string;
  city?: string | null;
  bbox?: Bbox | null;
}

export interface ScoringExplanation {
  weights: Record<string, number>;
  components: Record<string, number>;
  provider_notes: Record<string, string>;
  environment?: Record<string, unknown>;
}

export interface BuildingProperties {
  id: string;
  project_id: string;
  osm_id: string | null;
  area_m2: number;
  usable_roof_area_m2: number;
  building_type: string;
  address: string | null;
  source: string;
  lead_score: number;
  opportunity_level: OpportunityLevel;
  estimated_solar_potential: number;
  has_existing_panels: boolean;
  panel_confidence: number;
  type_priority_score: number;
  accessibility_score: number;
  scoring_explanation: ScoringExplanation;
  recommended_action: string;
}

export interface BuildingFeature {
  type: "Feature";
  geometry: Geometry;
  properties: BuildingProperties;
}

export interface BuildingFeatureCollection {
  type: "FeatureCollection";
  features: BuildingFeature[];
}

export interface SummaryLead {
  id: string;
  osm_id: string | null;
  address: string | null;
  building_type: string;
  area_m2: number;
  usable_roof_area_m2: number;
  lead_score: number;
  opportunity_level: OpportunityLevel;
  estimated_solar_potential: number;
  recommended_action: string;
}

export interface ProjectSummary {
  project_id: string;
  total_buildings: number;
  high_opportunity_count: number;
  medium_opportunity_count: number;
  low_opportunity_count: number;
  estimated_total_roof_area_m2: number;
  top_leads: SummaryLead[];
}

export interface AnalyzeResponse {
  project_id: string;
  fetched_count: number;
  analyzed_count: number;
  source: string;
  message: string;
}

export type MapLayerMode = "leads" | "solar" | "temperature";

export interface FranceAreaRank {
  id: string;
  name: string;
  region: string;
  department: string;
  segment: string;
  latitude: number;
  longitude: number;
  bbox: Bbox;
  overall_score: number;
  solar_score: number;
  temperature_fit_score: number;
  commercial_priority_score: number;
  roof_area_proxy_score: number;
  accessibility_score: number;
  annual_irradiation_kwh_m2: number | null;
  estimated_pv_output_kwh_kwp: number | null;
  average_annual_temp_c: number | null;
  summer_max_temp_c: number | null;
  heat_risk_score: number;
  recommended_action: string;
  rationale: string[];
  data_sources: string[];
  data_quality: string;
}

export interface FranceRankAreasResponse {
  country: "France";
  analysis_level: string;
  areas: FranceAreaRank[];
  source_notes: string[];
}
