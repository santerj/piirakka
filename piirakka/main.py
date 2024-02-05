from functools import wraps
from os import getenv

from flask import Flask, request, jsonify, render_template

from utils.player import Player

# init player

SPAWN_MPV = getenv("MPV", True)
SOCKET = getenv("SOCKET", "/tmp/piirakka.sock")
DATABASE = getenv("DATABASE", "./piirakka.db")

def create_app(mpv, socket, database):
    player = Player(mpv, socket, database)
    app = Flask(__name__, static_folder='static')
    app.config['player'] = player
    return app

app = create_app(SPAWN_MPV, SOCKET, DATABASE)
player = app.config['player']

if __name__ == "__main__":
    # run flask
    app.run()

def require_token(func):
    @wraps(func)
    # middleware to check for Reload-Token validity
    def wrapper(*args, **kwargs):
        header_value = request.headers.get('Reload-Token')
        #print('got header', header_value, 'actual value', player.hash)
        if header_value != player.hash:
            return jsonify({'error': 'stale Reload-Token'}), 412
        else:
            # Call the original route function if the header is correct
            return func(*args, **kwargs)

    return wrapper

# routes:

@app.route('/favicon.ico')
def favicon():
    return app.send_static_file('favicon.ico')

@app.route('/')
def index():
    return render_template('index.html', reload_token=player.hash, stations=player.stations)

@app.route('/stations')
def stations():
    return render_template('stations.html', reload_token=player.hash, stations=player.stations)

@app.route('/api/token', methods=['GET'])
def get_token():
    return jsonify({'token': str(player.hash)})

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
def get_stations():
    payload = {}
    stations = player.get_stations()
    for i, station in enumerate(stations):
        payload[str(i)] = {
            'url': station.url,
            'description': station.description
        }
    return jsonify(payload)

@app.route('/api/radio/station_id', methods=['GET'])
@require_token
def station_id():
    id = player.stations.index(player.current_station)
    return jsonify(id)

@app.route('/api/radio/station/<int:id>', methods=['PUT', 'DELETE'])
@require_token
def set_or_delete_station(id: int):
    if request.method == 'PUT':
        # playback selected station
        player.play_station_with_id(id)
        return 'success', 200
    elif request.method == 'DELETE':
        # remove selected station from db
        player.delete_station(id)
        return 'accepted', 202

@app.route('/api/radio/station', methods=['POST'])
def create_station():
    try:
        data = request.json
        url = data['url']
        desc = data['description']
        result, msg = player.add_station(url=url, description=desc)
        if result:
            return msg, 201
        else:
            return msg, 400
    except KeyError:
        return 'error', 400


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
