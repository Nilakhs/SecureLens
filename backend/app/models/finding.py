from sqlalchemy import Column, Integer, String, Text, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app.database.connection import Base


class Finding(Base):
    __tablename__ = "findings"

    id = Column(Integer, primary_key=True, index=True)
    scan_id = Column(Integer, ForeignKey("scans.id", ondelete="CASCADE"), nullable=False)
    scanner = Column(String, nullable=False)  # semgrep, bandit
    rule_id = Column(String, nullable=False)
    category = Column(String, nullable=False)
    severity = Column(String, nullable=False)
    priority = Column(String, nullable=False)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    file = Column(String, nullable=False)
    line = Column(Integer, nullable=False)
    cwe = Column(JSON, default=list, nullable=False)
    owasp = Column(JSON, default=list, nullable=False)

    # Relationships
    scan = relationship("Scan", back_populates="findings")
    explanations = relationship("AIExplanation", back_populates="finding", cascade="all, delete-orphan")
    remediations = relationship("Remediation", back_populates="finding", cascade="all, delete-orphan")
