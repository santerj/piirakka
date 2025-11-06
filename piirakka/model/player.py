import json
import os
import socket
import subprocess
import time
from random import choice

from piirakka.model.event import PlayerBarUpdateEvent
from piirakka.model.player_state import PlayerState
from piirakka.model.station import Station, StationPydantic

VOLUME_INIT = 50
VOLUME_MAX = 130


class Player:
    def __init__(self, mpv, ipc_socket, database, callback) -> None:
        self.use_mpv = mpv
        self.ipc_socket = ipc_socket
        self.database = database
        self.callback = callback
        if self.use_mpv:
            self.proc = self._init_mpv()  # mpv process

        self.volume = self.get_volume()
        self.playing = self.get_status()
        self.stations: list[StationPydantic] = []
        self.current_station: StationPydantic = None
        # initial station set by context

    def __del__(self) -> None:
        if self.use_mpv and hasattr(self, "proc"):
            self.proc.terminate()
            os.remove(self.ipc_socket)

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

    def _ipc_command(self, cmd: str) -> dict:
        try:
            # Create a Unix domain socket
            with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as sock:
                # Connect to the MPV IPC socket
                sock.connect(self.ipc_socket)

                # Send the command
                sock.sendall(cmd.encode())

                # Receive the response
                response = sock.recv(4096).decode()
                sock.close()
                return json.loads(response)

        except Exception as e:
            print(f"Error: {e}")
            return None

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
        cmd = {"command": ["get_property", "pause"]}
        cmd = self._dumps(cmd)
        resp = self._ipc_command(cmd)
        if self._ipc_success(resp):
            return not resp["data"] if resp else False

    def get_volume(self) -> int:
        cmd = {"command": ["get_property", "volume"]}
        cmd = self._dumps(cmd)
        resp = self._ipc_command(cmd)
        if self._ipc_success(resp):
            return round(resp["data"])

    def set_volume(self, vol: int) -> bool:
        if not 0 <= vol <= VOLUME_MAX:
            return False
        cmd = {"command": ["set_property", "volume", str(vol)]}
        cmd = self._dumps(cmd)
        resp = self._ipc_command(cmd)
        self.callback(
            PlayerBarUpdateEvent(content=self.get_player_state())
        )  # signal to controller to re-render control bar
        return self._ipc_success(resp)

    def get_bitrate(self) -> int:
        cmd = {"command": ["get_property", "audio-bitrate"]}
        cmd = self._dumps(cmd)
        resp = self._ipc_command(cmd)
        if self._ipc_success(resp):
            return int(resp["data"])

    def get_codec(self) -> str:
        cmd = {"command": ["get_property", "audio-codec-name"]}
        cmd = self._dumps(cmd)
        resp = self._ipc_command(cmd)
        if self._ipc_success(resp):
            return resp["data"]

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
        cmd = {"command": ["loadfile", f"{url}", "replace"]}
        cmd = self._dumps(cmd)
        resp = self._ipc_command(cmd)
        self.playing = True
        return True if resp else False

    def play(self) -> bool:
        cmd = {"command": ["set_property", "pause", False]}
        cmd = self._dumps(cmd)
        resp = self._ipc_command(cmd)
        self.playing = True
        self.callback(
            PlayerBarUpdateEvent(content=self.get_player_state())
        )  # signal to controller to re-render control bar
        return True if resp else False

    def pause(self) -> bool:
        cmd = {"command": ["set_property", "pause", True]}
        cmd = self._dumps(cmd)
        resp = self._ipc_command(cmd)
        self.playing = False
        self.callback(
            PlayerBarUpdateEvent(content=self.get_player_state())
        )  # signal to controller to re-render control bar
        return True if resp else False

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
        cmd = {"command": ["get_property", "metadata"]}
        cmd = self._dumps(cmd)
        resp = self._ipc_command(cmd)
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
            PlayerBarUpdateEvent(content=self.get_player_state())
        )  # signal to controller to re-render control bar
