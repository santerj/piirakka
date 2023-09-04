import random

from flask import Flask, render_template, request

from utils.player import Player
from utils.title_grabber import titleGrabber


app = Flask(__name__)
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
        case "toggle":
            # TODO: same format as /api/status after action
            if player._playing:
                player.stop()
                return "", 200
            else:
                player.play()
                return "", 200
        case _:
            return "", 500
        
@app.route('/api/status')
def status():
    # TODO: json response
    return player.status(), 200

@app.route('/api/currentStation')
def currentStation():
    return player.getStation(), 200

@app.route('/api/currentSong')
def currentSong():
    # TODO: add scheduled task to Player – every 20s
    # this is a slow request
    station = player.getStation()['url']
    title = titleGrabber(station)
    return title

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8000)
