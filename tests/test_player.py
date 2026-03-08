"""Unit tests for player model with mocked MPV subprocess."""
from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest

from piirakka.model.event import PlayerBarUpdateEvent
from piirakka.model.player import Player
from piirakka.model.station import StationPydantic


class TestPlayerInitialization:
    """Tests for Player initialization."""

    def test_player_init_without_mpv(self):
        """Test Player initialization with MPV disabled."""
        callback = MagicMock()

        with patch("piirakka.model.player.subprocess.Popen"):
            player = Player(
                mpv=False, ipc_socket="/tmp/test.sock", database=":memory:", callback=callback
            )

            assert player.use_mpv is False
            assert player.callback == callback

    def test_player_init_with_mpv_mock(self, mock_player):
        """Test Player initialization with mocked MPV."""
        assert mock_player.use_mpv is False
        assert mock_player.ipc_socket == "/tmp/test_mpv.sock"


class TestPlayerIPCHandling:
    """Tests for IPC command handling."""

    def test_ipc_success_with_success_response(self):
        """Test _ipc_success recognizes successful responses."""
        resp = {"error": "success", "data": 50}

        assert Player._ipc_success(resp) is True

    def test_ipc_success_with_error_response(self):
        """Test _ipc_success recognizes error responses."""
        resp = {"error": "property not found"}

        assert Player._ipc_success(resp) is False

    def test_ipc_success_with_none(self):
        """Test _ipc_success handles None response."""
        assert Player._ipc_success(None) is False

    def test_ipc_success_with_malformed_response(self):
        """Test _ipc_success handles malformed responses."""
        resp = {"data": 50}  # No 'error' key

        assert Player._ipc_success(resp) is False

    @patch("piirakka.model.player.socket.socket")
    def test_ipc_command_success(self, mock_socket_class, mock_player):
        """Test successful IPC command execution."""
        mock_sock = MagicMock()
        mock_socket_class.return_value.__enter__.return_value = mock_sock

        response = {"error": "success", "data": 50}
        mock_sock.recv.return_value = json.dumps(response).encode()

        result = mock_player._ipc_command('{"command": ["get_property", "volume"]}')

        assert result == response
        mock_sock.sendall.assert_called_once()

    @patch("piirakka.model.player.socket.socket")
    def test_ipc_command_socket_error(self, mock_socket_class, mock_player):
        """Test IPC command handling socket errors gracefully."""
        mock_socket_class.return_value.__enter__.side_effect = OSError("Connection refused")

        result = mock_player._ipc_command('{"command": ["get_property", "volume"]}')

        assert result is None

    @patch("piirakka.model.player.socket.socket")
    def test_ipc_command_json_decode_error(self, mock_socket_class, mock_player):
        """Test IPC command handling invalid JSON responses."""
        mock_sock = MagicMock()
        mock_socket_class.return_value.__enter__.return_value = mock_sock
        mock_sock.recv.return_value = b"not valid json"

        result = mock_player._ipc_command('{"command": ["test"]}')

        assert result is None


class TestPlayerStateQueries:
    """Tests for player state query methods."""

    @patch.object(Player, "_ipc_command")
    def test_get_volume(self, mock_ipc, mock_player):
        """Test retrieving volume."""
        mock_ipc.return_value = {"error": "success", "data": 75}

        volume = mock_player.get_volume()

        assert volume == 75

    @patch.object(Player, "_ipc_command")
    def test_get_volume_failure(self, mock_ipc, mock_player):
        """Test get_volume returns default on failure."""
        mock_ipc.return_value = None

        volume = mock_player.get_volume()

        assert volume == 50  # VOLUME_INIT

    @patch.object(Player, "_ipc_command")
    def test_get_status_playing(self, mock_ipc, mock_player):
        """Test getting playback status (playing)."""
        mock_ipc.return_value = {"error": "success", "data": False}  # pause=False means playing

        status = mock_player.get_status()

        assert status is True

    @patch.object(Player, "_ipc_command")
    def test_get_status_paused(self, mock_ipc, mock_player):
        """Test getting playback status (paused)."""
        mock_ipc.return_value = {"error": "success", "data": True}  # pause=True means paused

        status = mock_player.get_status()

        assert status is False

    @patch.object(Player, "_ipc_command")
    def test_get_status_failure(self, mock_ipc, mock_player):
        """Test get_status returns False on failure."""
        mock_ipc.return_value = None

        status = mock_player.get_status()

        assert status is False

    @patch.object(Player, "_ipc_command")
    def test_current_track_icecast(self, mock_ipc, mock_player):
        """Test retrieving current track from Icecast stream."""
        mock_ipc.return_value = {
            "error": "success",
            "data": {"icy-title": "Artist - Song Title", "icy-name": "My Radio"},
        }

        track = mock_player.current_track()

        assert track == "Artist - Song Title"

    @patch.object(Player, "_ipc_command")
    def test_current_track_unavailable(self, mock_ipc, mock_player):
        """Test current_track returns None when metadata unavailable."""
        mock_ipc.return_value = {"error": "success", "data": {}}  # No icy-title

        track = mock_player.current_track()

        assert track is None

    @patch.object(Player, "_ipc_command")
    def test_get_bitrate(self, mock_ipc, mock_player):
        """Test retrieving audio bitrate."""
        mock_ipc.return_value = {"error": "success", "data": 128000}

        bitrate = mock_player.get_bitrate()

        assert bitrate == 128000

    @patch.object(Player, "_ipc_command")
    def test_get_bitrate_failure(self, mock_ipc, mock_player):
        """Test get_bitrate returns None on failure."""
        mock_ipc.return_value = None

        bitrate = mock_player.get_bitrate()

        assert bitrate is None


class TestPlayerStateManagement:
    """Tests for player control methods."""

    @patch.object(Player, "_ipc_command")
    def test_set_volume_valid(self, mock_ipc, mock_player):
        """Test setting volume to valid value."""
        mock_ipc.return_value = {"error": "success"}

        success = mock_player.set_volume(80)

        assert success is True

    @patch.object(Player, "_ipc_command")
    def test_set_volume_out_of_range(self, mock_ipc, mock_player):
        """Test setting volume out of valid range."""
        success = mock_player.set_volume(200)  # Above VOLUME_MAX

        assert success is False
        mock_ipc.assert_not_called()

    @patch.object(Player, "_ipc_command")
    def test_play(self, mock_ipc, mock_player):
        """Test play command."""
        mock_ipc.return_value = {"error": "success"}

        success = mock_player.play()

        assert success is True
        assert mock_player.playing is True

    @patch.object(Player, "_ipc_command")
    def test_pause(self, mock_ipc, mock_player):
        """Test pause command."""
        mock_ipc.return_value = {"error": "success"}

        success = mock_player.pause()

        assert success is True
        assert mock_player.playing is False

    @patch.object(Player, "_ipc_command")
    def test_toggle_when_playing(self, mock_ipc, mock_player):
        """Test toggle when player is playing."""
        mock_ipc.return_value = {"error": "success"}
        mock_player.playing = True

        success = mock_player.toggle()

        assert success is True

    @patch.object(Player, "_ipc_command")
    def test_toggle_when_paused(self, mock_ipc, mock_player):
        """Test toggle when player is paused."""
        mock_ipc.return_value = {"error": "success"}
        mock_player.playing = False

        success = mock_player.toggle()

        assert success is True


class TestStationManagement:
    """Tests for station-related player methods."""

    def test_update_stations(self, mock_player):
        """Test updating stations in player."""
        stations = [
            StationPydantic(
                station_id="1",
                name="Station 1",
                url="http://station1.com",
                added_on=None,
                listen_time=0,
            ),
            StationPydantic(
                station_id="2",
                name="Station 2",
                url="http://station2.com",
                added_on=None,
                listen_time=0,
            ),
        ]

        mock_player.update_stations(stations)

        assert len(mock_player.stations) == 2
        assert mock_player.stations[0].name == "Station 1"

    def test_update_stations_preserves_current(self, mock_player):
        """Test that update_stations preserves current station if still available."""
        stations1 = [
            StationPydantic(
                station_id="1",
                name="Station 1",
                url="http://station1.com",
                added_on=None,
                listen_time=0,
            ),
        ]

        mock_player.update_stations(stations1)
        mock_player.current_station = mock_player.stations[0]

        # Update with new stations that include the current one
        stations2 = [
            StationPydantic(
                station_id="1",
                name="Station 1",
                url="http://station1.com",
                added_on=None,
                listen_time=0,
            ),
            StationPydantic(
                station_id="2",
                name="Station 2",
                url="http://station2.com",
                added_on=None,
                listen_time=0,
            ),
        ]

        mock_player.update_stations(stations2)

        assert mock_player.current_station.station_id == "1"

    @patch.object(Player, "_ipc_command")
    def test_shuffle(self, mock_ipc, mock_player):
        """Test shuffle station."""
        mock_ipc.return_value = {"error": "success"}

        stations = [
            StationPydantic(
                station_id="1",
                name="Station 1",
                url="http://station1.com",
                added_on=None,
                listen_time=0,
            ),
            StationPydantic(
                station_id="2",
                name="Station 2",
                url="http://station2.com",
                added_on=None,
                listen_time=0,
            ),
        ]

        mock_player.update_stations(stations)
        mock_player.current_station = mock_player.stations[0]

        # Shuffle should pick a different station
        mock_player.shuffle()

        # Callback should have been called
        mock_player.callback.assert_called()

    def test_shuffle_insufficient_stations(self, mock_player):
        """Test shuffle with only one station does nothing."""
        stations = [
            StationPydantic(
                station_id="1",
                name="Station 1",
                url="http://station1.com",
                added_on=None,
                listen_time=0,
            ),
        ]

        mock_player.update_stations(stations)
        mock_player.current_station = mock_player.stations[0]

        mock_player.shuffle()

        # Callback should not be called with only one station
        mock_player.callback.assert_not_called()
