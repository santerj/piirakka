import time

from functools import wraps

from flask import Flask, request, jsonify, render_template

from utils.player import Player


player = Player()
app = Flask(__name__, static_folder='static')

@app.route('/')
def index():
    return app.send_static_file('index.html')

@app.route('/favicon.ico')
def favicon():
    return app.send_static_file('favicon.ico')

@app.route('/index.html')
# temporarily here until templating is finished
def index2():
    return render_template('index.html', reload_token=player.hash, stations=player.stations)

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
def stations():
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

@app.route('/api/radio/station/<int:id>', methods=['PUT'])
@require_token
def set_station(id: int):
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
    app.run()
    #app.run(host='0.0.0.0', port=8000)     # werkzeug
