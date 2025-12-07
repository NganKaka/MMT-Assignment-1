"""chatapp.py - simple tracker webapp using provided WeApRous framework

Routes provided:
- PUT /login  (not used heavily, stub)
- POST /submit-info  (register a peer)  body: JSON {name, ip, port}
- GET  /get-list    (return list of peers) -> JSON list
- POST /clear-list  (clear registry) -- for testing
"""

from daemon.weaprous import WeApRous
import json
import threading
import requests
import http.client
import os

app = WeApRous()
CHANNELS = {}
MESSAGES = {}
PEERS = []

lock = threading.Lock()

# helper
def _peer_key(p):
    return f"{p.get('ip')}:{int(p.get('port'))}"

def _safe_json_load(s):
    try:
        return json.loads(s) if s else {}
    except Exception:
        return {}


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

# ----- Peer APIs -----

#Login
@app.route('/login', methods=['PUT'])
def login(headers='guest', body='anonymous'):
    # Not implementing auth here; stub to satisfy assignment API
    # return {'status': 'ok'}
    return json.dumps({"status":"ok"})

# Register
# @app.route('/register', methods=['POST'])
# def register(headers='', body=''):
#     # data = json.loads(body)
#     # if data not in PEERS:
#     #     PEERS.append(data)
#     # return json.dumps({"status":"ok"})
#     try:
#         data = json.loads(body)
#         ip = data.get("ip")
#         port = data.get("port")
#         name = data.get("name")

#         # Giả sử bạn có danh sách toàn cục PEERS
#         global PEERS
#         PEERS.append({"ip": ip, "port": port, "name": name})

#         return json.dumps({"status": "success", "peer": data})
#     except Exception as e:
#         return json.dumps({"status": "error", "message": str(e)})

#Ping
@app.route('/ping', methods=['GET'])
def ping(headers='', body=''):
    return json.dumps({"status":"ok"})

#Sync
# @app.route('/sync', methods=['GET'])
# def sync(headers='', body=''):
#     external = json.loads(body)
#     merge_peers(PEERS, external)
#     return json.dumps(PEERS)

# def merge_peers(local_peers, incoming_peers):
#     # Chỉ thêm peer mới, tránh duplicate
#     existing = {(p["ip"], p["port"]) for p in local_peers}

#     for peer in incoming_peers:
#         key = (peer["ip"], peer["port"])
#         if key not in existing:
#             local_peers.append(peer)
#             existing.add(key)


@app.route('/submit-info', methods=['POST'])
def submit_info(headers='', body=''):
    # body expected JSON string or dict
    # try:
    #     if isinstance(body, str) and body:
    #         data = json._safe_json_load(body)
    #     elif isinstance(body, dict):
    #         data = body
    #     else:
    #         data = {}
    # except Exception:
    #     data = {}
    data = _safe_json_load(body)
    name = data.get('name') or f"peer-{len(PEERS)+1}"
    ip = data.get('ip')
    port = int(data.get('port', 0))
    if not ip or not port:
        return json.dumps({'status': 'error', 'reason': 'ip/port required'})

    # dedupe
    with lock:
        for p in PEERS:
            if p['ip'] == ip and int(p['port']) == int(port):
                p['name'] = name
                break
        else:
            PEERS.append({'name': name, 'ip': ip, 'port': port})

    return json.dumps({'status': 'ok', 'peers': PEERS})

@app.route('/get-list', methods=['GET'])
def get_list(headers='', body=''):
    # return list of peers as JSON
    with lock:
        return json.dumps(PEERS)
    # return json.dumps(CHANNELS)
    # return {
    #     "status": "200 OK",
    #     "Content-Type": "application/json",
    #     "body": PEERS
    # }
    # return PEERS

@app.route('/clear-list', methods=['POST'])
def clear_list(headers='', body=''):
    with lock:
        PEERS.clear()
        CHANNELS.clear()
        MESSAGES.clear()
    return json.dumps({'status': 'ok'})


# ----- Channel APIs -----

@app.route('/add-list', methods=['POST'])
def add_list(headers='', body=''):
    try:
        # if isinstance(body, str) and body:
        #     data = json.loads(body)
        # else:
        #     return {"status": "error", "message": "Missing body"}
        data = _safe_json_load(body)
        channel = data.get('channel')
        peer = data.get('peer')

        if not channel or not peer:
            return {"status": "error", "message": "Channel or peer missing"}

        with lock:
            CHANNELS.setdefault(channel, [])
            # if channel not in CHANNELS:
            #     CHANNELS[channel] = []

            # deduplicate peer
            existing = {(p['ip'], p['port']) for p in CHANNELS[channel]}
            # key = (peer['ip'], peer['port'])
            key = (peer.get('ip'), int(peer.get('port')))
            if key not in existing:
                CHANNELS[channel].append({"name": peer.get('name'), "ip": peer.get('ip'), "port": int(peer.get('port'))})
            
            global_found = False
            for p in PEERS:
                if p['ip'] == peer.get('ip') and int(p['port']) == int(peer.get('port')):
                    global_found = True
                    # p['name'] = peer.get('name', p['name'])
                    break
            if not global_found:
                PEERS.append({"name": peer.get('name'), "ip": peer.get('ip'), "port": int(peer.get('port'))})

            peers_snapshot = CHANNELS[channel].copy()    
        return json.dumps({"status":"ok", "channel": channel, "peers": peers_snapshot})
            
            
            # PEERS.append(peer)  # also add to global PEERS

        # return {"status": "ok", "channel": channel, "peers": CHANNELS[channel]}
    except Exception as e:
        return {"status": "error", "message": str(e)}
    # try:
    #     data = json.loads(body)
    #     channel = data.get('channel')
    #     peer = data.get('peer')
    #     if not channel or not peer:
    #         return {"status": "error", "reason": "channel and peer required"}
    #     CHANNELS.setdefault(channel, [])
    #     # Avoid duplicate peers
    #     if peer not in CHANNELS[channel]:
    #         CHANNELS[channel].append(peer)
    #     return {"status": "ok", "channel": channel, "peers": CHANNELS[channel]}
    # except Exception as e:
    #     return {"status": "error", "message": str(e)}


@app.route('/get-channels', methods=['GET'])
def get_channels(headers='', body=''):
    with lock:
        summary = {c: {'peers': CHANNELS.get(c, []), 'messages': len(MESSAGES.get(c, []))} for c in CHANNELS}
    return json.dumps(summary)


@app.route('/channels', methods=['GET'])
def list_channels(headers='', body=''):
    with lock:
        return json.dumps(list(CHANNELS.keys()))
    
@app.route('/get-messages', methods=['GET'])
def get_messages(headers='', body=''):
    # headers contains Query encoded as JSON string by WeApRous in earlier code
    try:
        h = json.loads(headers)
        query = h.get("Query","")
    except Exception:
        query = ""
    # query like "channel=general"
    channel = query.replace("channel=", "")
    with lock:
        return json.dumps(MESSAGES.get(channel, []))

# @app.route('/connect-peer', methods=['POST'])
# def connect_peer(headers='', body=''):
#     # Stub: tracker can optionally trigger peers to connect
#     # return {"status": "ok"}
#     """
#     Request server to initiate or confirm connection to a peer.
#     Body expected: {"peer": {"name":..., "ip":..., "port":...}}
#     """
#     try:
#         data = json.loads(body)
#         peer = data.get('peer')
#         if not peer or not all(k in peer for k in ('ip','port','name')):
#             return json.dumps({"status":"error","message":"Invalid peer info"})
#         # Check if peer is already in registry
#         for p in PEERS:
#             if p['ip'] == peer['ip'] and int(p['port']) == int(peer['port']):
#                 return json.dumps({"status":"ok","message":"Already registered", "peer": p})
#         PEERS.append(peer)
#         return json.dumps({"status":"ok","peer": peer})
#     except Exception as e:
#         return json.dumps({"status":"error","message": str(e)})


@app.route('/broadcast-peer', methods=['POST'])
def broadcast_peer(headers='', body=''):
    """
    Broadcast a message to all peers in a channel.
    Body expected: {"channel":"channel_name","msg":"text"}
    """
    try:
        # if isinstance(body, str) and body:
        #     data = json.loads(body)
        # else:
        #     return {"status": "error", "message": "Missing body"}
        data = _safe_json_load(body)
        channel = data.get('channel')
        msg = data.get('msg')
        sender = data.get('sender', 'tracker')

        if not channel or msg is None:
            return json.dumps({"status":"error","message":"channel and msg required"})

        with lock:
            if channel not in CHANNELS:
                return {"status": "error", "message": "Channel not found"}

            # add message to channel messages (you may want a separate messages dict)
            # if channel not in MESSAGES:
            #     MESSAGES[channel] = []
            MESSAGES.setdefault(channel, [])

            entry = {"sender": sender, "msg": msg} 
            MESSAGES[channel].append(entry)

            for peer in list(CHANNELS[channel]):
                try:
                    conn = http.client.HTTPConnection(peer['ip'], peer['port'], timeout=1)
                    # payload = json.dumps({"peer": peer, "msg": msg, "sender": sender, "channel": channel})
                    
                    payload = json.dumps({
                        "sender": sender,
                        "msg": msg,
                        "channel": channel
                    })
                    conn.request("POST", "/send-peer", body=payload, headers={"Content-Type":"application/json"})
                    resp = conn.getresponse()
                    resp.read()
                    conn.close()
                except Exception as e:
                    # best-effort; just print warning
                    print(f"[Warning] cannot push to {peer['name']}@{peer['ip']}:{peer['port']} - {e}")
            
            
            
            # MESSAGES[channel].append(msg)

            # for peer in CHANNELS[channel]:
            #     try:
            #         requests.post(
            #             f"http://{peer['ip']}:{peer['port']}/send-peer",
            #             json={"peer": peer, "msg": msg},
            #             timeout=1
            #         )
            #     except Exception as e:
            #         print(f"[Warning] Cannot push to {peer['name']}@{peer['ip']}:{peer['port']} - {e}")
        # if "messages" not in CHANNELS[channel]:
        #     CHANNELS[channel].append({"messages": []})

        # CHANNELS[channel][-1]["messages"].append(msg)  # simple append

        # optionally send to all peers via P2P (your peer_network handles that)
        return json.dumps({"status": "ok", "channel": channel, "msg": msg})

    except Exception as e:
        return {"status": "error", "message": str(e)}
    # try:
    #     data = json.loads(body)
    #     channel = data.get("channel")
    #     msg = data.get("msg")
    #     if not channel or msg is None:
    #         return json.dumps({"status":"error","message":"Missing channel or msg"})
    #     # Ensure channel exists
    #     if channel not in CHANNELS:
    #         return json.dumps({"status":"error","message":"Channel not found"})
    #     # Broadcast logic: here just log/update channel peers
    #     for peer in CHANNELS[channel]:
    #         print(f"[broadcast to {peer['name']}@{peer['ip']}:{peer['port']}] {msg}")
    #     return json.dumps({"status":"ok","channel": channel,"msg": msg})
    # except Exception as e:
    #     return json.dumps({"status":"error","message": str(e)})
    # try:
    #     data = json.loads(body)
    #     msg = data.get('msg')
    #     channel = data.get('channel')
    #     if not msg or not channel:
    #         return {"status": "error", "reason": "msg and channel required"}
    #     # Normally would notify peers in channel (logic handled by peer nodes)
    #     return {"status": "ok", "channel": channel, "msg": msg}
    # except Exception as e:
    #     return {"status": "error", "message": str(e)}


@app.route('/send-peer', methods=['POST'])
def send_peer(headers='', body=''):
    """
    Send a message to a specific peer.
    Body expected: {"peer": {"name":..., "ip":..., "port":...}, "msg":"text"}
    """
    try:
        data = _safe_json_load(body)
        peer = data.get("peer")
        msg = data.get("msg")
        sender = data.get("sender", None)
        channel = data.get("channel", None)

        print(f"[tracker] send-peer received for {peer} from sender {sender} ch={channel} msg={msg}")

        # if not peer or msg is None:
        #     return json.dumps({"status":"error","message":"Missing peer or msg"})
        # print(f"[send to {peer['name']}@{peer['ip']}:{peer['port']}] {msg}")
        return json.dumps({"status":"ok"})
    except Exception as e:
        return json.dumps({"status":"error","message": str(e)})
    # try:
    #     data = json.loads(body)
    #     msg = data.get('msg')
    #     peer = data.get('peer')
    #     if not msg or not peer:
    #         return {"status": "error", "reason": "msg and peer required"}
    #     # Normally would send directly to a specific peer
    #     return {"status": "ok", "peer": peer, "msg": msg}
    # except Exception as e:
    #     return {"status": "error", "message": str(e)}

# @app.route('/get-messages', methods=['GET'])
# def get_messages(headers='', body=''):
#     query = json.loads(headers).get("Query", "")
#     channel = query.replace("channel=", "")
#     with lock:
#         return json.dumps(MESSAGES.get(channel, []))



if __name__ == '__main__':
    import argparse, os
    parser = argparse.ArgumentParser()
    parser.add_argument('--ip', default='127.0.0.1')
    parser.add_argument('--port', type=int, default=8000)
    args = parser.parse_args()
    app.prepare_address(args.ip, args.port)
    app.run()
