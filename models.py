from sqlalchemy import Column, Integer, String, Float, DateTime
from datetime import datetime
from database import Base

class ComplaintModel(Base):
    __tablename__ = "complaints"

    id = Column(Integer, primary_key=True, index=True)
    description = Column(String, nullable=False)
    category = Column(String, index=True)
    issue = Column(String, index=True)
    severity = Column(String, index=True)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    priority_score = Column(Integer, default=0)
    status = Column(String, default="Pending")
    created_at = Column(DateTime, default=datetime.utcnow)