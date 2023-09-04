import random

import mpv

from flask import Flask, render_template, request


class Player:
    def __init__(self):
        self._mpv = mpv.MPV()
        self._stations = self._getStations()
        self._currentStation = random.choice(self._stations)

        self.playing = False

    def getStation(self):
        return self._currentStation

    def setStation(self, station):
        self._currentStation = station

    def changeStation(self):
        new = random.choice(self._stations)
        if new == self._currentStation:
            self.changeStation()
        else:
            self.setStation(new)
            self.play()

    def play(self):
        self._mpv.play(self._currentStation)
        self.playing = True

    def stop(self):
        self._mpv.stop()
        self.playing = False

    @staticmethod
    def _getStations():
        with open("stations.txt", "r") as file:
            lines = file.readlines()
            return [station.strip("\n") for station in lines if station != "\n" or station.startswith("#")]




app = Flask(__name__)
#player = mpv.MPV(ytdl=False)
player = Player()

@app.route('/')
def index():
    return render_template("index.html")

@app.route('/api/radio', methods=['PUT'])
def radioControl():
    args = request.args.to_dict()
    action = args["action"]
    match action:
        case "play":
            player.play()
            return "", 200
        case "stop":
            player.stop()
            return "", 200
        case "next":
            player.changeStation()
            return "", 200
        case _:
            return "", 500
        
@app.route('/api/status')
def status():
    if player.playing:
        return "playing"
    else:
        return "paused"

@app.route('/api/station')
def station():
    return player.getStation(), 200

app.run(host='0.0.0.0', port=8000)
