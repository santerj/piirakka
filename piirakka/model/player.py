import subprocess
import socket
import sqlite3
import json
import time

from model.player_state import PlayerState
from model.station import Station

VOLUME_MAX = 130


class Player:
    def __init__(self, mpv, socket, database, callback) -> None:
        self.use_mpv = mpv
        self.socket = socket
        self.database = database
        self.callback = callback

        self.stations: list[Station] = []
        self.playing = True
        self.volume = 50
        self._init_db()

        if self.use_mpv:
            self.proc = self._init_mpv()    # mpv process

        self.current_station: Station = None
        self.current_station_index: int = None  # index inside self.stations

        self.update_stations()
        if len(self.stations) > 0:
            # set initial station if db is populated
            default_index = 0
            self.current_station = self.stations[default_index]
            self.current_station_index = default_index
            self.play_station_with_id(default_index)
        self.set_volume(self.volume)

    def __del__(self) -> None:
        if self.use_mpv and hasattr(self, "proc"):
            self.proc.terminate()

    def _init_mpv(self):
        cmd = [
            'mpv',
                '--idle',
                '--input-ipc-server=' + self.socket,
                '--volume-max=' + str(VOLUME_MAX),  # TODO: source from config file
                '--cache=yes', 
                '--cache-secs=' + str(15)
        ]
        proc = subprocess.Popen(cmd)
        time.sleep(4)  # wait for mpv to start
        return proc

    def _ipc_command(self, cmd: str) -> str | None:
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
                return response

        except Exception as e:
            print(f"Error: {e}")
            return None

    def _init_db(self):
        conn = sqlite3.connect(self.database)
        cursor = conn.cursor()
        cursor.execute("CREATE TABLE IF NOT EXISTS stations (url VARCHAR(255), description VARCHAR(255), source VARCHAR(10))")
        conn.commit()
        conn.close()

    def _dumps(self, cmd: dict) -> str:
        return json.dumps(cmd) + '\n'
    
    def to_player_state(self) -> PlayerState:
        return PlayerState(
            playing=self.playing,
            volume=self.volume,
            stations=self.stations,
            current_station=self.current_station,
            current_station_index=self.current_station_index
        )

    def add_station(self, url: str, description: str) -> tuple[bool, str]:
        for s in self.stations:
            if s.url == url:
                return False, "url already added"
            elif s.description == description:
                return False, "name already added"

        station = Station(url=url, description=description, source='custom')
        result, msg = station.check()
        
        if result:
            station.create(db=self.database)
            self.update_stations()
            return True, "success"
        else:
            print("error", msg)
            return False, msg

    def delete_station(self, index):
        try:
            target = self.stations[index]
        except IndexError:
            return False

        conn = sqlite3.connect(self.database)
        cursor = conn.cursor()
        cursor.execute(f"DELETE FROM stations WHERE url='{target.url}' AND description='{target.description}'")
        conn.commit()
        conn.close()

        if index == self.current_station_index:
            self.current_station = self.stations[0]  # reset channel if current one was deleted
        self.update_stations()

        return True

    def update_stations(self) -> None:
        if self.current_station:
            self.current_station_index = self.stations.index(self.current_station)
        conn = sqlite3.connect(self.database)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM stations")
        rows = cursor.fetchall()
        stations = []
        for row in rows:
            url = row[0]
            description = row[1]
            source = row[2]
            stations.append(Station(url=url, description=description, source=source))  # goes to end of array
        conn.close()
        self.stations = stations
        if self.current_station:
            # keep currently playing station info
            self.current_station = self.stations[self.current_station_index]

    def get_stations(self) -> list[Station]:
        return self.stations

    def play_station_with_id(self, id: int):
        self._set_station(url=self.stations[id].url)
        self.current_station = self.stations[id]

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
        return True if resp else False

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
        return True if resp else False

    def toggle(self) -> bool:
        if self.playing:
            return self.pause()
        else:
            return self.play()

    def set_volume(self, vol: int) -> bool:
        if not 0 <= vol <= VOLUME_MAX:
            return False
        cmd = {
            "command": [
                "set_property",
                "volume",
                vol
            ]
        }
        cmd = self._dumps(cmd)
        resp = self._ipc_command(cmd)
        if resp:
            self.volume = vol
            return True
        else:
            return False

    def now_playing(self) -> dict | None:
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
        resp = json.loads(resp)
        try:
            icy_title = resp["data"]["icy-title"] if resp["data"]["icy-title"] else None
            icy_genre = resp["data"]["icy-genre"] if resp["data"]["icy-genre"] else None
            icy_name = resp["data"]["icy-name"] if resp["data"]["icy-name"] else None
            payload = {
                'status': 'playing' if self.playing else 'paused',
                'icy_title': icy_title,
                'icy_genre': icy_genre,
                'icy_name': icy_name
            }
            return payload

        except KeyError:
            return None
