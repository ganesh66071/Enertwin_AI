"""Campus SQLAlchemy model."""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Campus(Base):
    __tablename__ = "campuses"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    location: Mapped[str] = mapped_column(String(512), nullable=False, default="")
    campus_type: Mapped[str] = mapped_column(String(128), nullable=False, default="General")
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    energy_records = relationship("EnergyRecord", back_populates="campus", cascade="all, delete-orphan")
    analyses = relationship("AnalysisResult", back_populates="campus", cascade="all, delete-orphan")
