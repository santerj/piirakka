from pydantic import BaseModel
from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.dialects.postgresql import UUID
import uuid
from datetime import datetime

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
            added_on=self.added_on
        )

class StationPydantic(BaseModel):
    # pydantic representation of Station
    station_id: str
    name: str
    url: str
    added_on: datetime

    def to_sqlalchemy(self):
        # TODO:
        pass
