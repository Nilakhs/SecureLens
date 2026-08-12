from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.database.connection import Base


class Remediation(Base):
    __tablename__ = "remediations"

    id = Column(Integer, primary_key=True, index=True)
    finding_id = Column(Integer, ForeignKey("findings.id", ondelete="CASCADE"), nullable=False)
    model = Column(String, nullable=False)
    original_code = Column(Text, nullable=False)
    fixed_code = Column(Text, nullable=False)
    explanation = Column(Text, nullable=False)
    diff = Column(Text, nullable=False)
    syntax_valid = Column(Boolean, default=True, nullable=False)
    verification_status = Column(String, default="UNVERIFIED", nullable=False)  # UNVERIFIED | VERIFIED | FAILED
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    finding = relationship("Finding", back_populates="remediations")
