from dataclasses import dataclass
import subprocess
import socket
import sqlite3
import json
import time

SOCKET = '/tmp/piirakka.sock'
VOLUME_MAX = 130
DATABASE = 'piirakka.db'

@dataclass
class Station:
    url: str
    description: str
    source: str

class Player:
    def __init__(self) -> None:
        self.socket = SOCKET
        self.stations = []
        self.hash = ""
        self.playing = True
        self.proc = self._init_mpv()    # mpv process
        self._init_db()
        self.update_stations()
        self.current_station = self.stations[0]
        self._set_station(self.current_station.url)
        self.play() # start playback upon startup

    def __del__(self) -> None:
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
        time.sleep(2)  # wait for mpv to start
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
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        cursor.execute("CREATE TABLE IF NOT EXISTS stations (url VARCHAR(255), description VARCHAR(255), source VARCHAR(10))")
        conn.close()

    def _dumps(self, cmd: dict) -> str:
        return json.dumps(cmd) + '\n'
    
    def update_stations(self) -> None:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM stations")
        rows = cursor.fetchall()
        stations = []
        for row in rows:
            url = row[0]
            description = row[1]
            source = row[2]
            stations.append(Station(url=url, description=description, source=source))
        conn.close()
        self.stations = stations
        self.hash = str(hash(str(self.stations)))

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
        return True if resp else False

    def now_playing(self) -> dict | None:
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
