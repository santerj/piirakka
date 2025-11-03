import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel
from sqlalchemy import Column, DateTime, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Session

from piirakka.model.base import Base


class Station(Base):
    __tablename__ = 'stations'
    station_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    url = Column(String, nullable=False)
    added_on = Column(DateTime, default=datetime.utcnow)
    listen_time = Column(Integer, default=0, nullable=False)

    def to_pydantic(self):
        return StationPydantic(
            station_id=str(self.station_id),
            name=self.name,
            url=self.url,
            added_on=self.added_on,
            listen_time=self.listen_time
        )
    
def create_station(session: Session, name: str, url: str) -> Station:
    station = Station(name=name, url=url)
    session.add(station)
    session.commit()
    session.refresh(station)
    return station

def delete_station(session: Session, station_id: uuid.UUID) -> bool:
    station = session.get(Station, station_id)
    if station:
        session.delete(station)
        session.commit()
        return True
    return False

def get_station(session: Session, station_id: uuid.UUID) -> Optional[Station]:
    return session.get(Station, station_id)

def list_stations(session: Session) -> list[Station]:
    return session.query(Station).all()

class StationPydantic(BaseModel):
    # pydantic representation of Station
    station_id: str
    name: str
    url: str
    added_on: datetime
    listen_time: int

    def to_sqlalchemy(self):
        return Station(
            station_id=self.station_id,
            name=self.name,
            url=self.url,
            added_on=self.added_on,
            listen_time=self.listen_time
        )
