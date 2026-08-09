import ipaddress
import re
import uuid
from datetime import datetime
from urllib.parse import urlparse

import validators
from pydantic import BaseModel
from sqlalchemy import Column, DateTime, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Session

from piirakka.model.base import Base

MIN_STATION_NAME_LENGTH = 1
MAX_STATION_NAME_LENGTH = 100


def validate_station_name(name: str) -> bool:
    if not isinstance(name, str):
        return False

    normalized_name = name.strip()
    if len(normalized_name) < MIN_STATION_NAME_LENGTH or len(normalized_name) > MAX_STATION_NAME_LENGTH:
        return False

    if re.search(r"[<>]", normalized_name):
        return False

    if re.search(r"(?i)<\s*script", normalized_name):
        return False

    return True


def validate_station_url(url: str) -> bool:
    if not isinstance(url, str):
        return False

    normalized_url = url.strip()
    if not normalized_url:
        return False

    parsed = urlparse(normalized_url)
    scheme = parsed.scheme.lower()

    def host_is_valid(hostname: str | None) -> bool:
        if hostname is None:
            return False
        if hostname == "localhost":
            return True
        try:
            ipaddress.ip_address(hostname)
            return True
        except ValueError:
            return False

    if scheme in {"http", "https"}:
        if not parsed.netloc:
            return False

        hostname = parsed.hostname
        if host_is_valid(hostname):
            return True

        return bool(validators.domain(hostname or ""))

    if "://" in normalized_url:
        return False

    parsed_no_scheme = urlparse("//" + normalized_url)
    if not parsed_no_scheme.netloc:
        return False

    hostname = parsed_no_scheme.hostname
    return host_is_valid(hostname)


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
    station = Station(name=name.strip(), url=url.strip(), sort_order=sort_order)
    session.add(station)
    session.commit()
    session.refresh(station)
    return station


def update_station(session: Session, station_id: str, name: str | None, url: str | None) -> Station | None:
    station = session.get(Station, uuid.UUID(station_id))
    if station:
        if name is not None:
            station.name = name
        if url is not None:
            station.url = url
        session.commit()
        session.refresh(station)
        return station
    return None


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


def get_station(session: Session, station_id: str) -> Station | None:
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
