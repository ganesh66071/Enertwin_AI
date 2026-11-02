"""Energy record SQLAlchemy model."""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class EnergyRecord(Base):
    __tablename__ = "energy_records"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=lambda: str(uuid.uuid4()))
    campus_id: Mapped[str] = mapped_column(String(64), ForeignKey("campuses.id", ondelete="CASCADE"), nullable=False, index=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    building_name: Mapped[str] = mapped_column(String(255), nullable=False)
    floor: Mapped[str | None] = mapped_column(String(64), nullable=True)
    zone: Mapped[str | None] = mapped_column(String(128), nullable=True)

    energy_consumption_kwh: Mapped[float] = mapped_column(Float, nullable=False)
    hvac_energy_kwh: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    lighting_energy_kwh: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    equipment_energy_kwh: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)

    peak_demand_kw: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)

    occupancy_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    occupancy_percent: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)

    indoor_temperature_c: Mapped[float] = mapped_column(Float, nullable=False, default=24.0)
    outdoor_temperature_c: Mapped[float] = mapped_column(Float, nullable=False, default=28.0)
    humidity_percent: Mapped[float] = mapped_column(Float, nullable=False, default=55.0)

    hvac_runtime_hours: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    hvac_setpoint_c: Mapped[float] = mapped_column(Float, nullable=False, default=24.0)

    equipment_runtime_hours: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)

    electricity_tariff: Mapped[float] = mapped_column(Float, nullable=False, default=8.2)
    co2_emission_kg: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)

    data_source: Mapped[str] = mapped_column(String(32), nullable=False, default="dataset")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    campus = relationship("Campus", back_populates="energy_records")
