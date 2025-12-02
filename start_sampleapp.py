import argparse
import json
import socket
import threading
from collections import defaultdict
from typing import Dict, Tuple

from daemon.weaprous import WeApRous

PORT = 8000
app = WeApRous()

# In-memory state for peers and channels. Thread-safe because backend spawns threads.
_peers: Dict[str, Dict[str, str]] = {}
_channels: Dict[str, set] = defaultdict(set)
_lock = threading.Lock()


def _parse_body(body: str) -> Dict[str, str]:
    """
    Parse a body that might be URL-encoded form (`a=1&b=2`) or JSON.
    """
    if not body:
        return {}
    try:
        return json.loads(body)
    except Exception:
        pass

    parsed: Dict[str, str] = {}
    for pair in body.split("&"):
        if not pair or "=" not in pair:
            continue
        key, value = pair.split("=", 1)
        parsed[key] = value
    return parsed


def _require_peer(body_map: Dict[str, str]) -> Tuple[bool, str]:
    peer_id = body_map.get("peer_id")
    if not peer_id:
        return False, "peer_id missing"
    return True, peer_id


@app.route("/login", methods=["POST"])
def login(headers="guest", body="anonymous"):
    """
    Authenticate a peer with a simple shared secret (password='password').
    """
    data = _parse_body(body or "")
    ok, peer_id = _require_peer(data)
    if not ok:
        return {"status": "error", "message": peer_id}, 400

    password = data.get("password")
    if password != "password":
        print(f"[SampleApp] Login FAILED for peer: {peer_id}")
        return {"status": "error", "message": "invalid credentials"}, 401

    ip = data.get("ip") or headers.get("host", "unknown")
    port = data.get("port", "")

    with _lock:
        _peers[peer_id] = {"ip": ip, "port": port, "channels": set()}

    print(f"[SampleApp] Login SUCCESS for peer: {peer_id}")
    return {"status": "ok", "peer_id": peer_id}, 200


@app.route("/add-list", methods=["POST"])
def add_list(headers="guest", body="anonymous"):
    """
    Add a peer to a channel membership list.
    """
    data = _parse_body(body or "")
    ok, peer_id = _require_peer(data)
    if not ok:
        return {"status": "error", "message": peer_id}, 400

    channel = data.get("channel")
    if not channel:
        return {"status": "error", "message": "channel missing"}, 400

    with _lock:
        if peer_id not in _peers:
            return {"status": "error", "message": "peer not authenticated"}, 401
        _channels[channel].add(peer_id)
        _peers[peer_id].setdefault("channels", set()).add(channel)
        members = list(_channels[channel])

    print(f"[SampleApp] Peer {peer_id} joined channel {channel}")
    return {"status": "ok", "channel": channel, "members": members}, 200


@app.route("/connect-peer", methods=["POST", "GET"])
def connect_peer(headers="guest", body="anonymous"):
    """
    Optional trigger to fetch peers for a caller to connect to.
    """
    data = _parse_body(body or "")
    ok, peer_id = _require_peer(data)
    if not ok:
        return {"status": "error", "message": peer_id}, 400

    with _lock:
        if peer_id not in _peers:
            return {"status": "error", "message": "peer not authenticated"}, 401
        peers = [
            {"peer_id": pid, "ip": info.get("ip"), "port": info.get("port")}
            for pid, info in _peers.items()
            if pid != peer_id
        ]

    return {"status": "ok", "peers": peers}, 200


@app.route("/broadcast-peer", methods=["POST"])
def broadcast_peer(headers="guest", body="anonymous"):
    """
    Broadcast a message to all members of a channel.
    """
    data = _parse_body(body or "")
    ok, peer_id = _require_peer(data)
    if not ok:
        return {"status": "error", "message": peer_id}, 400

    channel = data.get("channel")
    message = data.get("message", "")
    if not channel:
        return {"status": "error", "message": "channel missing"}, 400

    with _lock:
        if peer_id not in _peers:
            return {"status": "error", "message": "peer not authenticated"}, 401
        targets = list(_channels.get(channel, []))

    print(f"[SampleApp] Broadcast from {peer_id} -> channel {channel}: {message}")
    return {
        "status": "ok",
        "channel": channel,
        "targets": targets,
        "message": message,
    }, 200


@app.route("/send-peer", methods=["POST"])
def send_peer(headers="guest", body="anonymous"):
    """
    Send a direct message to a specific peer.
    """
    data = _parse_body(body or "")
    ok, peer_id = _require_peer(data)
    if not ok:
        return {"status": "error", "message": peer_id}, 400

    target = data.get("target")
    message = data.get("message", "")
    if not target:
        return {"status": "error", "message": "target missing"}, 400

    with _lock:
        if peer_id not in _peers:
            return {"status": "error", "message": "peer not authenticated"}, 401
        if target not in _peers:
            return {"status": "error", "message": "target not found"}, 404

    print(f"[SampleApp] Direct message {peer_id} -> {target}: {message}")
    return {"status": "ok", "to": target, "message": message}, 200


@app.route("/hello", methods=["PUT"])
def hello(headers, body):
    print(f"[SampleApp] ['PUT'] Hello in {headers} to {body}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        prog="Backend", description="", epilog="Beckend daemon"
    )
    parser.add_argument("--server-ip", default="0.0.0.0")
    parser.add_argument("--server-port", type=int, default=PORT)

    args = parser.parse_args()
    ip = args.server_ip
    port = args.server_port

    app.prepare_address(ip, port)
    app.run()
