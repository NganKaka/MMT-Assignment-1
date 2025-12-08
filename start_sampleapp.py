import argparse
import json
import socket
import threading
from collections import defaultdict
from typing import Dict, Tuple

from daemon.weaprous import WeApRous

PORT = 8000
app = WeApRous()

# --- DATABASE ---
# _peers: { "username": {"ip": "...", "port": "...", "channels": ["General", "Game"]} }
_peers: Dict[str, Dict] = {}

# _channels: { "General": ["user1"], "Game": ["user1", "user2"] }
_channels: Dict[str, list] = {"General": []} 

# _inbox: { "username": [msg1, msg2] }
_inbox: Dict[str, list] = defaultdict(list)

_lock = threading.Lock()

def _parse_body(body):
    if isinstance(body, dict): return body
    if not body: return {}
    try: return json.loads(body)
    except: return {}

# --- API ROUTES ---

@app.route("/login", methods=["POST"])
def login(headers="guest", body="anonymous"):
    data = _parse_body(body)
    username = data.get("username") or data.get("peer_id")
    password = data.get("password")
    ip = data.get("ip") or "127.0.0.1"
    port = data.get("port")

    print(f"[Auth] Login: user={username}")

    if password == "password":
        with _lock:
            # Lưu thông tin user
            _peers[username] = {
                "name": username, 
                "ip": ip, 
                "port": port,
                "channels": ["General"] # Mặc định ai cũng có General
            }
            # Thêm vào kênh General
            if username not in _channels["General"]:
                _channels["General"].append(username)

        # Nếu là admin -> Trả về text để set cookie (Task 1)
        if username == "admin":
            return "LOGIN_SUCCESS"
        
        # Nếu là peer -> Trả về JSON (Task 2)
        return {"status": "ok", "peer_id": username}
    
    return {"status": "error", "message": "Invalid credentials"}, 401

@app.route("/get-list", methods=["POST", "GET"])
def get_list(headers, body):
    """Lấy danh sách người dùng online"""
    with _lock:
        peer_list = list(_peers.values())
    return {"status": "ok", "peers": peer_list}

@app.route("/get-channels", methods=["POST"])
def get_channels(headers, body):
    """Lấy danh sách kênh (Admin thấy hết, User chỉ thấy kênh đã join)"""
    data = _parse_body(body)
    peer_id = data.get("peer_id")
    
    with _lock:
        if peer_id == "admin":
            # Admin thấy tất cả kênh
            channels = list(_channels.keys())
        else:
            # User thấy kênh mình đã join (được lưu trong _peers)
            user_info = _peers.get(peer_id, {})
            channels = user_info.get("channels", ["General"])
            
    return {"status": "ok", "channels": channels}

@app.route("/add-list", methods=["POST"])
def add_list(headers, body):
    """Tạo hoặc tham gia kênh"""
    data = _parse_body(body)
    channel = data.get("channel")
    username = data.get("username")

    if not channel or not username:
        return {"status": "error", "message": "Missing info"}, 400

    with _lock:
        # 1. Tạo kênh nếu chưa có
        if channel not in _channels:
            _channels[channel] = []
        
        # 2. Thêm user vào danh sách thành viên kênh
        if username not in _channels[channel]:
            _channels[channel].append(username)
            
        # 3. Cập nhật danh sách kênh của user
        if username in _peers:
            if channel not in _peers[username]["channels"]:
                _peers[username]["channels"].append(channel)

    print(f"[Channel] {username} joined {channel}")
    return {"status": "ok", "channel": channel}

@app.route("/send-peer", methods=["POST"])
def send_peer(headers, body):
    """Gửi tin nhắn riêng"""
    data = _parse_body(body)
    target = data.get("target")
    sender = data.get("sender")
    msg = data.get("msg") or data.get("message")

    if not target or not msg: return {"status": "error"}, 400
    if target == sender: return {"status": "error", "message": "Self"}, 403

    # Xử lý /kick (Admin)
    if msg.startswith("/kick") and sender == "admin":
        user_to_kick = msg.split(" ")[1]
        with _lock:
            if user_to_kick in _peers:
                del _peers[user_to_kick]
                # Xóa khỏi các kênh
                for ch in _channels:
                    if user_to_kick in _channels[ch]:
                        _channels[ch].remove(user_to_kick)
        return {"status": "ok", "message": f"Kicked {user_to_kick}"}

    # Lưu tin nhắn direct
    with _lock:
        if target in _peers:
            _inbox[target].append({
                "sender": sender,
                "msg": msg,
                "type": "direct",
                "timestamp": "now"
            })
            print(f"[Direct] {sender} -> {target}: {msg}")
            return {"status": "ok"}
        else:
            return {"status": "error", "message": "Offline"}, 404

@app.route("/broadcast-peer", methods=["POST"])
def broadcast_peer(headers, body):
    """Gửi tin nhắn vào Kênh"""
    data = _parse_body(body)
    channel = data.get("channel")
    msg = data.get("msg") or data.get("message")
    sender = data.get("sender")

    if not channel or not msg: return {"status": "error"}, 400

    with _lock:
        # Lấy danh sách thành viên trong kênh đó
        members = _channels.get(channel, [])
        if not members: return {"status": "error", "message": "Channel empty/not found"}, 404

        for member in members:
            if member != sender and member in _peers:
                _inbox[member].append({
                    "sender": channel, # Hiển thị tên kênh là người gửi
                    "real_sender": sender, # Người thực gửi
                    "msg": f"{sender}: {msg}",
                    "type": "channel"
                })
        print(f"[Channel {channel}] {sender}: {msg}")

    return {"status": "ok"}

@app.route("/get-messages", methods=["POST"])
def get_messages(headers, body):
    data = _parse_body(body)
    peer_id = data.get("peer_id")
    messages = []
    if peer_id:
        with _lock:
            if peer_id in _inbox:
                messages = _inbox[peer_id][:]
                _inbox[peer_id] = []
    
    formatted = [{"sender": m["sender"], "message": m["msg"]} for m in messages]
    return {"status": "ok", "messages": formatted}

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--server-ip", default="0.0.0.0")
    parser.add_argument("--server-port", type=int, default=PORT)
    args = parser.parse_args()
    app.prepare_address(args.server_ip, args.server_port)
    app.run()