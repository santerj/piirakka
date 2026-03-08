"""Pytest configuration and shared fixtures."""
from __future__ import annotations

import os
import tempfile
from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from piirakka.model.base import Base


@pytest.fixture
def temp_db():
    """Create a temporary SQLite database for testing."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        db_path = tmp.name

    engine = create_engine(f"sqlite:///{db_path}", echo=False)
    Base.metadata.create_all(engine)

    yield engine

    # Cleanup
    os.unlink(db_path)


@pytest.fixture
def db_session(temp_db):
    """Provide a database session for testing."""
    SessionLocal = sessionmaker(bind=temp_db)
    session = SessionLocal()

    yield session

    session.close()


@pytest.fixture
def mock_player():
    """Create a mocked Player instance to avoid spawning MPV."""
    with patch("piirakka.model.player.subprocess.Popen"):
        with patch("piirakka.model.player.Player._init_mpv", return_value=MagicMock()):
            # Mock callback to capture events
            callback = MagicMock()

            from piirakka.model.player import Player

            player = Player(
                mpv=False,  # Disabled MPV spawning
                ipc_socket="/tmp/test_mpv.sock",
                database=":memory:",
                callback=callback,
            )

            yield player


@pytest.fixture
def mpv_ipc_mock(monkeypatch):
    """Mock MPV IPC socket communication."""

    def mock_ipc_command(self, cmd: str):
        """Mock IPC command responses."""
        import json

        cmd_dict = json.loads(cmd.strip())
        command = cmd_dict.get("command", [])[0]

        # Mock common MPV responses
        responses = {
            "get_property": {"error": "success", "data": None},
            "set_property": {"error": "success"},
            "loadfile": {"error": "success"},
        }

        return responses.get(command, {"error": "success"})

    from piirakka.model.player import Player

    monkeypatch.setattr(Player, "_ipc_command", mock_ipc_command)
