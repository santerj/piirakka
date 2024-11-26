import subprocess
import socket
import sqlite3
import json
import time
import requests
import validators
import html

VOLUME_MAX = 130


class Station:
    def __init__(self, url: str, description: str, source: str) -> None:
        self.url = url
        self.description = description
        self.source = source

    def check(self) -> tuple[bool, str]:
        # TODO: double check these
        allowed_content_types = (
            'application/pls+xml',
            'audio/mpeg',
            'audio/x-scpls',
            'audio/aac',
            'audio/flac',
            'audio/ogg',
            'audio/vnd.wav',
            'audio/x-wav',
            'audio/x-ms-wax',
            'audio/x-pn-realaudio',
            'audio/x-pn-realaudio-plugin',
            'audio/x-realaudio',
            'audio/x-aac',
            'audio/x-ogg',
            'audio/webm',
        )
        # TODO: have to rethink the validator gates.
        # TODO: many servers have a working stream endpoint, but times out upon HEAD
        # TODO: also keep in mind server-side request forgery vuln
        try:
            # gate 1 - validate url
            validators.url(self.url)
        except validators.ValidationError:
            return False, "invalid url"

        try:
            # gates 2 + 3 - respond within timeout + have correct header
            r = requests.head(self.url, timeout=1)
            content_type = r.headers.get('content-type')
            if content_type not in allowed_content_types:
                return False, f"content-type {content_type} not allowed"
        except requests.exceptions.Timeout:
            return False, "connection timed out"
        
        if html.escape(self.url) != self.url or self.url.replace("'", "''") != self.url:
            # gate 4 - check if sanitization affects description
            return False, "invalid description"

        return True, "success"

    def create(self, db: str):
        # adds a new station to database
        conn = sqlite3.connect(db)
        cursor = conn.cursor()
        cursor.execute(f"INSERT INTO stations VALUES ('{self.url}', '{self.description}', 'custom')")
        conn.commit()
        conn.close()

class Player:
    # TODO: generate a PlayerContext from all dynamic data (volume, stations, now playing, etc...)
    # TODO: PlayerContext will hydrate browser app via SSE
    def __init__(self, mpv, socket, database, callback) -> None:
        self.use_mpv = mpv
        self.socket = socket
        self.database = database
        self.callback = callback

        self.stations = []
        self.hash = ""
        self.playing = True
        self._init_db()

        if self.use_mpv:
            self.proc = self._init_mpv()    # mpv process

        self.current_station = None
        self.update_stations()
        if len(self.stations) > 0:
            # set initial station if db is populated
            self.current_station = self.stations[0]
            self._set_station(self.current_station.url)
        self.set_volume(50)

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
        # TODO: handle error if index out of range
        # TODO: reset current station if deleted stations is currently playing
        target = self.stations[index]
        conn = sqlite3.connect(self.database)
        cursor = conn.cursor()
        cursor.execute(f"DELETE FROM stations WHERE url='{target.url}' AND description='{target.description}'")
        conn.commit()
        conn.close()
        self.update_stations()

    def update_stations(self) -> None:
        if self.current_station:
            current_station_index = self.stations.index(self.current_station)
        conn = sqlite3.connect(self.database)
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
        if self.current_station:
            # keep currently playing station info
            self.current_station = self.stations[current_station_index]
        self.hash = str(hash(str(self.stations)))  # TODO: deprecate, generate a PlayerContext instead

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
