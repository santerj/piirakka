import random

from flask import Flask, render_template, request, jsonify

from utils.player import Player


app = Flask(__name__)
player = Player()

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
    
@app.route('/api/radio/stations', methods=['GET'])
def stations():
    payload = {}
    stations = player.get_stations()
    for i, station in enumerate(stations):
        payload[str(i)] = {
            'url': station.url,
            'description': station.description
        }
    payload['hash'] = player.hash
    return jsonify(payload)

@app.route('/api/radio/station_id', methods=['GET'])
def station_id():
    try:
        data = request.json
        hash_ = data['hash']
    except KeyError:
        return 'error', 400
    
    if hash_ != player.hash:
        return 'error', 428

    id = player.stations.index(player.current_station)
    return jsonify(id)

@app.route('/api/radio/station/<int:id>', methods=['PUT'])
def set_station(id: int):
    try:
        data = request.json
        hash_ = data['hash']
    except KeyError:
        return 'error', 400

    if hash_ != player.hash:
        return 'error', 428

    player.play_station_with_id(id)
    return 'success', 200

@app.route('/api/radio/station', methods=['POST'])
def create_station():
    # TODO: this
    pass
    #try:
    #    data = request.json
    #    url = data['url']
    #    desc = data['description']
    #    # TODO: sanitize input
    #    # TODO: prepare to be INSERTed!
    #except KeyError:
    #    return 'error', 400
    #
    #return

@app.route('/api/radio/now', methods=['GET'])
def now():
    return jsonify(player.now_playing())

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
