import subprocess
import socket
import json
import time

SOCKET = '/tmp/piirakka.sock'

class Player:
    def __init__(self) -> None:
        self.socket = SOCKET
        self.proc = self._init_mpv()    # mpv process
        # possible statuses:
        # paused, playing, waiting
        self.status = "paused"

    def __del__(self) -> None:
        self.proc.terminate()

    def _init_mpv(self):
        cmd = ['mpv', '--idle', '--input-ipc-server=' + self.socket]
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

    def _dumps(self, cmd: dict) -> str:
        return json.dumps(cmd) + '\n'

    def set_station(self, url: str):
        cmd = {
            "command": [
                "loadfile",
                f"{url}",
                "replace"
            ]
        }
        print(cmd)
        cmd = self._dumps(cmd)
        resp = self._ipc_command(cmd)

    def play(self) -> bool:
        if self.status == 'paused':
            cmd = {
                "command": [
                    "set_property",
                    "pause", False
                ]
            }
            cmd = self._dumps(cmd)
            resp = self._ipc_command(cmd)
            self.status = 'playing'
            return True
        else:
            return False

    def pause(self) -> bool:
        if self.status == 'playing':
            cmd = {
                "command": [
                    "set_property",
                    "pause", True
                ]
            }
            cmd = self._dumps(cmd)
            resp = self._ipc_command(cmd)
            self.status = 'paused'
            return True
        else:
            return False

    def toggle(self) -> bool:
        if self.status == 'playing':
            return self.pause()
        elif self.status == 'paused':
            return self.play()
        else:
            return False

    def set_volume(self, vol: int) -> bool:
        if not 0 <= vol <= 100:
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
        return False if resp is None else True

    def icy_title(self) -> str | None:
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
            return resp["data"]["icy-title"]
        except KeyError:
            return None
