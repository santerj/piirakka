import random

from flask import Flask, render_template, request

from utils.player import Player


app = Flask(__name__)
player = Player()

@app.route('/')
def index():
    return render_template("index.html")

@app.route('/api/radio/play', methods=['GET'])
def play():
    player.set_station("https://api.somafm.com/indiepop.pls")
    player.toggle()


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8000)
