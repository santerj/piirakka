import random

from flask import Flask, render_template, request

from utils.player import Player


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
        case _:
            return "", 500
        
@app.route('/api/status')
def status():
    # TODO: json response
    return player.status(), 200

@app.route('/api/station')
def station():
    # TODO: rework
    return player.getStation(), 200

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8000)
