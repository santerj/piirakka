import json

import requests

"""
try:

    python somafm.py | python -m json.tool

for ready formatting
"""

URL = "https://somafm.com/channels.json"
main = []
resp = requests.get(URL)
for channel in resp.json()['channels']:
    main.append(dict({
        "name": f"SomaFM - { channel['title'] }",
        "url": channel['playlists'][0]['url']
    }))
print(json.dumps(main))
