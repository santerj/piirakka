import json
import logging
import os
import socket
import subprocess
import threading
import time
from random import choice

from piirakka.model.device import AudioDevice
from piirakka.model.event import BroadcastEvent, EventType
from piirakka.model.player_state import PlayerState
from piirakka.model.station import Station, StationPydantic

VOLUME_INIT = 50
VOLUME_MAX = 130

logger = logging.getLogger(__name__)


class Player:
    def __init__(self, mpv, ipc_socket, database, callback) -> None:
        self.use_mpv = mpv
        self.ipc_socket = ipc_socket
        self.database = database
        self.callback = callback
        self._ipc_connection: socket.socket | None = None
        self._ipc_buffer = b""
        self._ipc_request_id = 0
        self._ipc_lock = threading.Lock()
        if self.use_mpv:
            self.proc = self._init_mpv()  # mpv process

        self.volume = self.get_volume()
        self.volume_before_mute = self.volume or VOLUME_INIT
        self.playing = self.get_status()
        self.stations: list[StationPydantic] = []
        self.current_station: StationPydantic = None
        # initial station set by context

    def __del__(self) -> None:
        self.close()

    def close(self) -> None:
        connection = getattr(self, "_ipc_connection", None)
        if connection is not None:
            connection.close()
            self._ipc_connection = None
        if getattr(self, "use_mpv", False) and hasattr(self, "proc"):
            self.proc.terminate()
        ipc_socket = getattr(self, "ipc_socket", None)
        if getattr(self, "use_mpv", False) and ipc_socket and os.path.exists(ipc_socket):
            os.remove(self.ipc_socket)

    def _connect_ipc(self) -> socket.socket:
        if self._ipc_connection is None:
            connection = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            connection.settimeout(10)
            connection.connect(self.ipc_socket)
            self._ipc_connection = connection
        return self._ipc_connection

    def _close_ipc_connection(self) -> None:
        if self._ipc_connection is not None:
            self._ipc_connection.close()
            self._ipc_connection = None
        self._ipc_buffer = b""

    def _next_request_id(self) -> int:
        self._ipc_request_id += 1
        return self._ipc_request_id

    def _ipc_command(self, command: list) -> dict:
        with self._ipc_lock:
            request_id = self._next_request_id()
            request = {"command": command, "request_id": request_id}
            connection = self._connect_ipc()
            try:
                connection.sendall(self._dumps(request).encode())
                while True:
                    newline_index = self._ipc_buffer.find(b"\n")
                    if newline_index == -1:
                        data = connection.recv(4096)
                        if not data:
                            raise ConnectionError("mpv IPC connection closed")
                        self._ipc_buffer += data
                        continue

                    raw_response = self._ipc_buffer[:newline_index]
                    self._ipc_buffer = self._ipc_buffer[newline_index + 1 :]
                    if not raw_response:
                        continue
                    response = json.loads(raw_response)
                    if response.get("request_id") == request_id:
                        return response
            except Exception as e:
                self._close_ipc_connection()
                logger.error(e, exc_info=True)
                raise

    def _mpv_command(self, *arguments) -> dict:
        return self._ipc_command(list(arguments))

    def get_player_state(self) -> PlayerState:
        # for creation of callback events - sent into websocket
        return PlayerState(
            playback_status=self.get_status(),
            volume=self.get_volume(),
            current_station_name=self.current_station.name,
            track_title=self.current_track(),
        )

    def _init_mpv(self):
        cmd = [
            "mpv",
            "--idle",
            "--input-ipc-server=" + self.ipc_socket,
            "--volume=" + str(VOLUME_INIT),
            "--volume-max=" + str(VOLUME_MAX),  # TODO: source from config file
            "--cache=yes",
            "--cache-secs=" + str(15),
            "--really-quiet",
        ]
        proc = subprocess.Popen(cmd)
        time.sleep(4)  # wait for mpv to start
        return proc

    @staticmethod
    def _ipc_success(resp: dict) -> bool:
        if resp and "error" in resp.keys():
            return resp["error"] == "success"
        else:
            return False

    def _dumps(self, cmd: dict) -> str:
        return json.dumps(cmd) + "\n"

    def get_status(self) -> bool:
        # true: playing
        # false: paused
        resp = self._mpv_command("get_property", "pause")
        if self._ipc_success(resp):
            return not resp.get("data") if resp else False

    def get_volume(self) -> int:
        resp = self._mpv_command("get_property", "volume")
        if self._ipc_success(resp):
            return round(resp.get("data"))

    def set_volume(self, vol: int) -> bool:
        if not 0 <= vol <= VOLUME_MAX:
            return False
        if vol > 0:
            self.volume_before_mute = vol
        resp = self._mpv_command("set_property", "volume", str(vol))
        if self._ipc_success(resp):
            self.volume = vol
        self.callback(
            # send rendered html directly over websocket to subscribers
            BroadcastEvent(event_type=EventType.PLAYER_BAR_UPDATED, content=self.get_player_state().render())
        )
        return self._ipc_success(resp)

    def toggle_mute(self) -> bool:
        current_volume = self.get_volume()
        if current_volume:
            self.volume_before_mute = current_volume
            return self.set_volume(0)
        return self.set_volume(self.volume_before_mute)

    def get_bitrate(self) -> int:
        resp = self._mpv_command("get_property", "audio-bitrate")
        if self._ipc_success(resp):
            return int(resp.get("data"))

    def get_codec(self) -> str:
        resp = self._mpv_command("get_property", "audio-codec-name")
        if self._ipc_success(resp):
            return resp.get("data")

    def get_device(self) -> str:
        # currently used audio device
        resp = self._mpv_command("get_property", "audio-device")
        if self._ipc_success(resp):
            return resp.get("data")

    def ao_reload(self) -> str:
        resp = self._mpv_command("ao-reload")
        if self._ipc_success(resp):
            return resp.get("error")

    async def set_device(self, device: str) -> str:
        """Try to give bluetooth/pipewire some time to negotiate before switching output device.

        - Pause audio
        - Set device
        - Reload AO
        - Sleep
        - Unpause

        """
        self._mpv_command("set_property", "pause", True)
        resp = self._mpv_command("set_property", "audio-device", device)
        self.ao_reload()  # reload immediately after setting device
        time.sleep(1)
        self._mpv_command("set_property", "pause", False)
        if self._ipc_success(resp):
            return resp.get("error")

    def list_devices(self) -> list[AudioDevice]:
        # all available audio devices
        resp = self._mpv_command("get_property", "audio-device-list")
        if self._ipc_success(resp):
            devices = []
            for dev in resp["data"]:
                devices.append(AudioDevice(name=dev["name"], description=dev["description"]))
            return devices

    def update_stations(self, stations: list[StationPydantic]) -> None:
        # TODO: verify if is uuid4 or str
        current_station_id = None
        if self.current_station:
            current_station_id = self.current_station.station_id

        self.stations = stations

        if current_station_id:
            matching_station = next((s for s in stations if s.station_id == current_station_id), None)
            if matching_station:
                # keep currently playing station
                self.current_station = matching_station

    def get_stations(self) -> list[Station]:
        return self.stations

    def play_station_with_id(self, station_id: str):
        # TODO: verify if is uuid4 or str
        matching_station = next((s for s in self.stations if s.station_id == station_id))
        if matching_station:
            self._set_station(url=matching_station.url)
            self.current_station = matching_station

    def _set_station(self, url: str):
        # TODO: rework to accept StationPydantic
        resp = self._mpv_command("loadfile", url, "replace")
        self.playing = True
        return bool(resp)

    def play(self) -> bool:
        resp = self._mpv_command("set_property", "pause", False)
        self.playing = True
        self.callback(
            # send rendered html directly over websocket to subscribers
            BroadcastEvent(event_type=EventType.PLAYER_BAR_UPDATED, content=self.get_player_state().render())
        )
        return bool(resp)

    def pause(self) -> bool:
        resp = self._mpv_command("set_property", "pause", True)
        self.playing = False
        self.callback(
            # send rendered html directly over websocket to subscribers
            BroadcastEvent(event_type=EventType.PLAYER_BAR_UPDATED, content=self.get_player_state().render())
        )
        return bool(resp)

    def toggle(self) -> bool:
        if self.playing:
            return self.pause()
        else:
            return self.play()

    def current_track(self) -> str | None:
        # TODO: don't assume stream is Icecast
        # TODO: check if equivalent fields exist for shoutcast, hls, dash
        # other interesting fields
        # genre: resp["data"]["icy-genre"]
        # desc: resp["data"]["icy-name"]
        resp = self._mpv_command("get_property", "metadata")
        if self._ipc_success(resp):
            try:
                return resp["data"]["icy-title"]
            except KeyError:
                pass
        return None

    def shuffle(self) -> None:
        if len(self.stations) < 2:
            return
        current_id = self.current_station.station_id
        choices = [s for s in self.stations if s.station_id != current_id]
        random_station = choice(choices)
        self.play_station_with_id(random_station.station_id)
        # TODO: add small wait to have a better chance of actually broadcasting an update here
        self.callback(
            # send rendered html directly over websocket to subscribers
            BroadcastEvent(event_type=EventType.PLAYER_BAR_UPDATED, content=self.get_player_state().render())
        )
