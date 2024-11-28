from pydantic import BaseModel
from sqlalchemy import Column, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.dialects.postgresql import UUID
import uuid
from datetime import datetime

Base = declarative_base()

class Station(Base):
    __tablename__ = 'stations'
    station_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    url = Column(String, nullable=False)
    added_on = Column(DateTime, default=datetime.utcnow)

class StationPydantic(BaseModel):
    # pydantic representation of Station
    # TODO: construct from instance of Station
    station_id: str
    name: str
    url: str
    added_on: str  # TODO: datetime
