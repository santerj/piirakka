import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel
from sqlalchemy import Column, DateTime, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Session

from piirakka.model.base import Base


class Station(Base):
    __tablename__ = "stations"
    station_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    url = Column(String, nullable=False)
    added_on = Column(DateTime, default=datetime.utcnow)
    listen_time = Column(Integer, default=0, nullable=False)
    sort_order = Column(Integer, default=0, nullable=False)

    def to_pydantic(self):
        return StationPydantic(
            station_id=str(self.station_id),
            name=self.name,
            url=self.url,
            added_on=self.added_on,
            listen_time=self.listen_time,
            sort_order=self.sort_order,
        )


def create_station(session: Session, name: str, url: str, sort_order: int = 100000) -> Station:
    # magic number explanation: always set new station to bottom of list
    station = Station(name=name, url=url, sort_order=sort_order)
    session.add(station)
    session.commit()
    session.refresh(station)
    return station


def update_station(session: Session, station_id: str, name: Optional[str], url: Optional[str]) -> Optional[Station]:
    station = session.get(Station, uuid.UUID(station_id))
    if station:
        if name is not None:
            station.name = name
        if url is not None:
            station.url = url
        session.commit()
        session.refresh(station)
        return station
    return False


def delete_station(session: Session, station_id: str) -> bool:
    station = session.get(Station, uuid.UUID(station_id))
    if station:
        session.delete(station)
        session.commit()
        return True
    return False


def order_stations(session: Session, station_ids: list[str]) -> bool:
    for index, station_id in enumerate(station_ids):
        station = session.get(Station, uuid.UUID(station_id))
        if station:
            station.sort_order = index
    session.commit()
    return True


def get_station(session: Session, station_id: str) -> Optional[Station]:
    return session.get(Station, uuid.UUID(station_id))


def list_stations(session: Session) -> list[Station]:
    return session.query(Station).order_by(Station.sort_order).all()


class StationPydantic(BaseModel):
    # pydantic representation of Station
    station_id: str
    name: str
    url: str
    added_on: datetime
    listen_time: int
    sort_order: int

    def to_sqlalchemy(self):
        return Station(
            station_id=self.station_id,
            name=self.name,
            url=self.url,
            added_on=self.added_on,
            listen_time=self.listen_time,
            sort_order=self.sort_order,
        )
