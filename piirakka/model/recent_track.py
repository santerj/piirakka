from pydantic import BaseModel


class RecentTrack(BaseModel):
    title: str
    station: str
    timestamp: str
