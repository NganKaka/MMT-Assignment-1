"""chatapp.py - simple tracker webapp using provided WeApRous framework

Routes provided:
- PUT /login  (not used heavily, stub)
- POST /submit-info  (register a peer)  body: JSON {name, ip, port}
- GET  /get-list    (return list of peers) -> JSON list
- POST /clear-list  (clear registry) -- for testing
"""

from daemon.weaprous import WeApRous
import json

app = WeApRous()

import os

# serve index.html when visiting root
@app.route("/", methods=["GET"])
def index(headers="", body=""):
    try:
        with open("./www/index.html", "r", encoding="utf-8") as f:
            html = f.read()
        return {
            "status": "200 OK",
            "Content-Type": "text/html",
            "body": html
        }
    except Exception:
        return {
            "status": "404 Not Found",
            "Content-Type": "text/html",
            "body": "<h1>index.html not found</h1>"
        }



@app.route("/static", methods=["GET"])
def static_files(headers="", body=""):
    # GET /static?file=js/chatui.js
    import json
    query = json.loads(headers).get("Query", "")
    file = query.replace("file=", "")
    path = f"./static/{file}"

    if not os.path.exists(path):
        return f"File not found: {file}"

    with open(path, "r", encoding="utf-8") as f:
        return f.read()


# in-memory peer registry
PEERS = []

def _peer_key(p):
    return f"{p.get('ip')}:{p.get('port')}"

#Login
@app.route('/login', methods=['PUT'])
def login(headers='guest', body='anonymous'):
    # Not implementing auth here; stub to satisfy assignment API
    return {'status': 'ok'}

# Register
@app.route('/register', methods=['POST'])
def register(headers='', body=''):
    # data = json.loads(body)
    # if data not in PEERS:
    #     PEERS.append(data)
    # return json.dumps({"status":"ok"})
    try:
        data = json.loads(body)
        ip = data.get("ip")
        port = data.get("port")
        name = data.get("name")

        # Giả sử bạn có danh sách toàn cục PEERS
        global PEERS
        PEERS.append({"ip": ip, "port": port, "name": name})

        return json.dumps({"status": "success", "peer": data})
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)})

#Ping
@app.route('/ping', methods=['GET'])
def ping(headers='', body=''):
    return json.dumps({"status":"ok"})

#Sync
@app.route('/sync', methods=['GET'])
def sync(headers='', body=''):
    external = json.loads(body)
    merge_peers(PEERS, external)
    return json.dumps(PEERS)

def merge_peers(local_peers, incoming_peers):
    # Chỉ thêm peer mới, tránh duplicate
    existing = {(p["ip"], p["port"]) for p in local_peers}

    for peer in incoming_peers:
        key = (peer["ip"], peer["port"])
        if key not in existing:
            local_peers.append(peer)
            existing.add(key)


@app.route('/submit-info', methods=['POST'])
def submit_info(headers='', body=''):
    # body expected JSON string or dict
    try:
        if isinstance(body, str) and body:
            data = json.loads(body)
        elif isinstance(body, dict):
            data = body
        else:
            data = {}
    except Exception:
        data = {}
    name = data.get('name') or data.get('id') or f"peer-{len(PEERS)+1}"
    ip = data.get('ip')
    port = int(data.get('port', 0))
    if not ip or not port:
        return json.dumps({'status': 'error', 'reason': 'ip/port required'})

    # dedupe
    for p in PEERS:
        if p['ip'] == ip and int(p['port']) == int(port):
            p['name'] = name
            break
    else:
        PEERS.append({'name': name, 'ip': ip, 'port': port})

    return json.dumps({'status': 'ok', 'peers': PEERS})
    # if not ip or not port:
    #     return {'status': 'error', 'reason': 'ip/port required'}
    # # dedupe
    # found = False
    # for p in PEERS:
    #     if p['ip'] == ip and int(p['port']) == int(port):
    #         p['name'] = name
    #         found = True
    #         break
    # if not found:
    #     PEERS.append({'name': name, 'ip': ip, 'port': port})
    # return {'status': 'ok', 'peers': PEERS}

@app.route('/get-list', methods=['GET'])
def get_list(headers='', body=''):
    # return list of peers as JSON
    return json.dumps(PEERS)
    # return {
    #     "status": "200 OK",
    #     "Content-Type": "application/json",
    #     "body": PEERS
    # }
    # return PEERS

@app.route('/clear-list', methods=['POST'])
def clear_list(headers='', body=''):
    PEERS.clear()
    return {'status': 'ok'}

if __name__ == '__main__':
    import argparse, os
    parser = argparse.ArgumentParser()
    parser.add_argument('--ip', default='127.0.0.1')
    parser.add_argument('--port', type=int, default=8000)
    args = parser.parse_args()
    app.prepare_address(args.ip, args.port)
    app.run()