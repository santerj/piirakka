import json
import random

from dataclasses import dataclass, asdict

import mpv


@dataclass
class Station:
    name: str
    url: str


class Player:
    def __init__(self):
        self._mpv = mpv.MPV()
        self._stations = []
        self._stationLoader()
        self._currentStation = random.choice(self._stations)
        self._playing = False

    def getStation(self):
        return asdict(self._currentStation)

    def setStation(self, station):
        self._currentStation = station

    def changeStation(self):
        new = random.choice(self._stations)
        if new == self._currentStation:
            self.changeStation()
        else:
            self.setStation(new)
            self.play()

    def play(self) -> None:
        self._mpv.play(self._currentStation.url)
        self._playing = True

    def stop(self) -> None:
        self._mpv.stop()
        self._playing = False

    def status(self) -> str:
        if self._playing:
            return 'playing'
        else:
            return 'paused'
        
    def _stationLoader(self):
        with open("stations.json", "r") as f:
            for station in json.load(f):
                self._stations.append(
                    Station(name=station['name'],
                            url=station['url']
                    )
                )
