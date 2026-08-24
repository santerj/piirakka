import logging
import os
import pickle
import tempfile
from pathlib import Path

logger = logging.getLogger(__name__)


def load_state(path: str) -> dict:
    logger.info("Loading persisted state from %s", path)
    try:
        with open(path, "rb") as state_file:
            state = pickle.load(state_file)
            if not isinstance(state, dict):
                logger.warning("Persisted state at %s is not a dictionary", path)
                return {}
            tracks = state.get("track_history", [])
            logger.info(
                "Loaded persisted state: %d tracks, audio device=%s, bluetooth device=%s",
                len(tracks) if isinstance(tracks, list) else 0,
                state.get("audio_device_name") or "none",
                state.get("bluetooth_device_name") or "none",
            )
            return state
    except FileNotFoundError:
        logger.info("No persisted state found at %s", path)
        return {}
    except (OSError, pickle.PickleError, EOFError, ValueError, TypeError, AttributeError, ImportError):
        logger.warning("Unable to load persisted state from %s", path, exc_info=True)
        return {}


def save_state(path: str, state: dict) -> None:
    tracks = state.get("track_history", [])
    logger.info(
        "Saving persisted state to %s: %d tracks, audio device=%s, bluetooth device=%s",
        path,
        len(tracks) if isinstance(tracks, list) else 0,
        state.get("audio_device_name") or "none",
        state.get("bluetooth_device_name") or "none",
    )
    temporary_path = None
    try:
        state_path = Path(path)
        state_path.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(dir=state_path.parent, delete=False) as state_file:
            temporary_path = state_file.name
            pickle.dump(state, state_file)
        os.replace(temporary_path, state_path)
        logger.info("Persisted state saved to %s", path)
    except (OSError, pickle.PickleError, TypeError):
        logger.warning("Unable to save persisted state to %s", path, exc_info=True)
        if temporary_path:
            try:
                os.unlink(temporary_path)
            except OSError:
                pass
