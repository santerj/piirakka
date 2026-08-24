import logging
from collections import deque

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

    def load_history(self, tracks: list[RecentTrack]) -> None:
        if not isinstance(tracks, list):
            return
        valid_tracks = [track for track in tracks if isinstance(track, RecentTrack)]
        self.history = deque(valid_tracks, maxlen=self.max_length)

    def most_recent(self) -> RecentTrack | None:
        return self.history[0] if self.history else None

    def __len__(self) -> int:
        """Amount of tracks in current history."""
        return len(self.history)

    def __bool__(self) -> bool:
        """True if history is not empty."""
        return bool(self.history)
