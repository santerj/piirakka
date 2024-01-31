import random

from flask import Flask, render_template, request

from utils.player import Player


app = Flask(__name__)
player = Player()
player.set_station("https://api.somafm.com/indiepop.pls")

@app.route('/')
def index():
    return render_template("index.html")

@app.route('/api/radio/play', methods=['POST'])
def play():
    if player.play():
        return 'success', 200
    else:
        return 'error', 500

@app.route('/api/radio/pause', methods=['POST'])
def pause():
    if player.pause():
        return 'success', 200
    else:
        return 'error', 500
    
@app.route('/api/radio/toggle', methods=['POST'])
def toggle():
    if player.toggle():
        return 'success', 200
    else:
        return 'error', 500

@app.route('/api/volume', methods=['PUT'])
def set_volume():
    data = request.get_json()
    if "level" not in data:
        return 'error', 400
    elif not 0 <= data["level"] <= 130:
        return 'error', 400

    resp = player.set_volume(data["level"])
    if resp:
        return 'success', 200
    else:
        return 'error', 500

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8000)
