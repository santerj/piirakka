from pydantic import BaseModel

class PlayerContext(BaseModel):
    # this class is used to hydrate the frontend with server-sent events.
    # it contains everyhting required to populate the frontend with real time data.
    volume: int
