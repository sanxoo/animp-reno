import urllib.parse
import requests

baseurl = "http://localhost:1031"

data = {
    "systemName": "test",
    "list": [
        {"seq": "1", "ip": "nwjwBUmlUV5beFPs4vpglw==", "port": 22, "id": "eKElmohFMBO2ZAKP0BdoWA==", "pw": "l3m97J5oznP3KApRaC8iGw==", "prompt": "$ "},
        {"seq": "2", "ip": "nwjwBUmlUV5beFPs4vpglw==", "port": 22, "id": "eKElmohFMBO2ZAKP0BdoWA==", "pw": "l3m97J5oznP3KApRaC8iGw==", "prompt": "$ "},
    ],
}
res = requests.post(urllib.parse.urljoin(baseurl, f"api/test/connecting"), json=data)
print(res.status_code)
print(res.text)

