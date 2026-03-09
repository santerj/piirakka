import logging
from collections import deque
from typing import Optional

from piirakka.model.recent_track import RecentTrack

logger = logging.getLogger(__name__)


class TrackHistoryManager:

    def __init__(self, max_length: int = 50):
        self.history: deque[RecentTrack] = deque(maxlen=max_length)
        self.max_length = max_length

    def add_track(self, track: RecentTrack) -> None:
        self.history.appendleft(track)
        logger.debug(f"Track added to history: {track.title}. History size: {len(self.history)}")

    def get_history(self) -> list[RecentTrack]:
        return list(self.history)

    def most_recent(self) -> Optional[RecentTrack]:
        return self.history[0] if self.history else None

    def __len__(self) -> int:
        return len(self.history)

    def __bool__(self) -> bool:
        # True if history is not empty
        return bool(self.history)
