from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.database.connection import Base


class AIExplanation(Base):
    __tablename__ = "ai_explanations"

    id = Column(Integer, primary_key=True, index=True)
    finding_id = Column(Integer, ForeignKey("findings.id", ondelete="CASCADE"), nullable=False)
    model = Column(String, nullable=False)
    summary = Column(Text, nullable=False)
    why_it_matters = Column(Text, nullable=False)
    potential_impact = Column(Text, nullable=False)
    recommended_fix = Column(Text, nullable=False)
    best_practice = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    finding = relationship("Finding", back_populates="explanations")
