import subprocess
import socket
import sqlite3
import json
import time

from sqlalchemy.orm import Session, sessionmaker  ## TODO: get from main
from sqlalchemy import create_engine

from piirakka.model.player_state import PlayerState
from piirakka.model.station import Station, StationPydantic

VOLUME_INIT = 50
VOLUME_MAX = 130


class Player:
    def __init__(self, mpv, socket, database, callback) -> None:
        self.use_mpv = mpv
        self.socket = socket
        self.database = database
        self.callback = callback

        self.engine = create_engine(f"sqlite:///{self.database}", echo=True)
        self.Session = sessionmaker(bind=self.engine)
        self.session = self.Session()

        self.stations: list[StationPydantic] = []
        self.playing = True  # TODO: get from mpv

        if self.use_mpv:
            self.proc = self._init_mpv()    # mpv process

        self.current_station: StationPydantic = None
        self.volume = self.get_volume()

        self.update_stations()
        if len(self.stations) > 0:
            # set initial station if db is populated
            default_index = 0
            self.current_station = self.stations[default_index]
            self.play_station_with_id(self.current_station.station_id)

    def __del__(self) -> None:
        if self.use_mpv and hasattr(self, "proc"):
            self.proc.terminate()

    def _init_mpv(self):
        cmd = [
            'mpv',
                '--idle',
                '--input-ipc-server=' + self.socket,
                '--volume=' + str(VOLUME_INIT),
                '--volume-max=' + str(VOLUME_MAX),  # TODO: source from config file
                '--cache=yes', 
                '--cache-secs=' + str(15),
                '--really-quiet'
        ]
        proc = subprocess.Popen(cmd)
        time.sleep(4)  # wait for mpv to start
        return proc

    def _ipc_command(self, cmd: str) -> dict:
        try:
            # Create a Unix domain socket
            with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as sock:
                # Connect to the MPV IPC socket
                sock.connect(self.socket)
                
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
        return resp['error'] == 'success'
    
    def _dumps(self, cmd: dict) -> str:
        return json.dumps(cmd) + '\n'

    def to_player_state(self) -> PlayerState:
        # TODO: might be redundant
        return PlayerState(
            playing=self.playing,
            volume=self.volume,
            stations=self.stations,
            current_station=self.current_station,
            current_station_index=self.current_station_index
        )
    
    def get_status(self) -> bool:
        # true: playing
        # false: paused
        cmd = {
            "command": [
                "get_property",
                "pause"
            ]
        }
        cmd = self._dumps(cmd)
        resp = self._ipc_command(cmd)
        if self._ipc_success(resp):
            return not resp['data']

    def get_volume(self) -> int:
        cmd = {
            "command": [
                "get_property",
                "volume"
            ]
        }
        cmd = self._dumps(cmd)
        resp = self._ipc_command(cmd)
        if self._ipc_success(resp):
            return round(resp['data'])

    def set_volume(self, vol: int) -> bool:
        if not 0 <= vol <= VOLUME_MAX:
            return False
        cmd = {
            "command": [
                "set_property",
                "volume",
                str(vol)
            ]
        }
        cmd = self._dumps(cmd)
        resp = self._ipc_command(cmd)
        return self._ipc_success(resp)
        # TODO: send new value via callback

    def get_bitrate(self) -> int:
        cmd = {
            "command": [
                "get_property",
                "audio-bitrate"
            ]
        }
        cmd = self._dumps(cmd)
        resp = self._ipc_command(cmd)
        if self._ipc_success(resp):
            return int(resp['data'])
        
    def get_codec(self) -> str:
        cmd = {
            "command": [
                "get_property",
                "audio-codec-name"
            ]
        }
        cmd = self._dumps(cmd)
        resp = self._ipc_command(cmd)
        if self._ipc_success(resp):
            return resp['data']

    def update_stations(self) -> None:
        # TODO: let controller handle DB select, pass via argument here
        if s := self.current_station:
            current_station_id = s.station_id

        stations = self.session.query(Station).all()
        self.stations = [s.to_pydantic() for s in stations]

        if self.current_station and current_station_id:
            # keep currently playing station info
            matching_station = next((s for s in self.stations if s.station_id == current_station_id))
            if matching_station:
                self.current_station = matching_station

    def get_stations(self) -> list[Station]:
        return self.stations

    def play_station_with_id(self, id: str):
        matching_station = next((s for s in self.stations if s.station_id == id))
        if matching_station:
            self._set_station(url=matching_station.url)
            self.current_station = matching_station

    def _set_station(self, url: str):
        cmd = {
            "command": [
                "loadfile",
                f"{url}",
                "replace"
            ]
        }
        cmd = self._dumps(cmd)
        resp = self._ipc_command(cmd)
        self.playing = True
        # TODO: send new value via callback

    def play(self) -> bool:
        cmd = {
            "command": [
                "set_property",
                "pause", False
            ]
        }
        cmd = self._dumps(cmd)
        resp = self._ipc_command(cmd)
        self.playing = True
        #self.callback(self.to_player_state().model_dump())  # TODO: don't do this if state didn't change!
        return True if resp else False
        # TODO: send new value via callback

    def pause(self) -> bool:
        cmd = {
            "command": [
                "set_property",
                "pause", True
            ]
        }
        cmd = self._dumps(cmd)
        resp = self._ipc_command(cmd)
        self.playing = False
        #self.callback(self.to_player_state().model_dump())  # TODO: don't do this if state didn't change!
        return True if resp else False
        # TODO: send new value via callback

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
        cmd = {
            "command": [
                "get_property",
                "metadata"
            ]
        }
        cmd = self._dumps(cmd)
        resp = self._ipc_command(cmd)
        if self._ipc_success(resp):
            try:
                return resp["data"]["icy-title"]
            except KeyError:
                pass
        return None
