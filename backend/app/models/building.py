import uuid
from datetime import datetime

from geoalchemy2 import Geometry
from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Index, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class Building(Base):
    __tablename__ = "buildings"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    osm_id: Mapped[str | None] = mapped_column(String(80), nullable=True, index=True)
    geometry = mapped_column(Geometry(geometry_type="GEOMETRY", srid=4326, spatial_index=True), nullable=False)
    area_m2: Mapped[float] = mapped_column(Float, nullable=False)
    building_type: Mapped[str] = mapped_column(String(80), default="unknown", nullable=False)
    address: Mapped[str | None] = mapped_column(Text, nullable=True)
    source: Mapped[str] = mapped_column(String(80), default="openstreetmap", nullable=False)

    lead_score: Mapped[float] = mapped_column(Float, default=0, nullable=False)
    opportunity_level: Mapped[str] = mapped_column(String(20), default="low", nullable=False)
    estimated_solar_potential: Mapped[float] = mapped_column(Float, default=0, nullable=False)
    usable_roof_area_m2: Mapped[float] = mapped_column(Float, default=0, nullable=False)
    has_existing_panels: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    panel_confidence: Mapped[float] = mapped_column(Float, default=0, nullable=False)
    type_priority_score: Mapped[float] = mapped_column(Float, default=0, nullable=False)
    accessibility_score: Mapped[float] = mapped_column(Float, default=0, nullable=False)
    scoring_explanation: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    recommended_action: Mapped[str] = mapped_column(Text, default="", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    project = relationship("Project", back_populates="buildings")


Index("ix_buildings_project_score", Building.project_id, Building.lead_score.desc())
