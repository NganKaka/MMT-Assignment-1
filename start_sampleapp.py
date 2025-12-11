# # import argparse
# # import json
# # import socket
# # import threading
# # from collections import defaultdict
# # from typing import Dict, Tuple

# # from daemon.weaprous import WeApRous

# # PORT = 8000
# # app = WeApRous()

# # # --- DATABASE ---
# # # _peers: { "username": {"ip": "...", "port": "...", "channels": ["General", "Game"]} }
# # _peers: Dict[str, Dict] = {}

# # # _channels: { "General": ["user1"], "Game": ["user1", "user2"] }
# # _channels: Dict[str, list] = {"General": []} 

# # # _inbox: { "username": [msg1, msg2] }
# # _inbox: Dict[str, list] = defaultdict(list)

# # _lock = threading.Lock()

# # def _parse_body(body):
# #     if isinstance(body, dict): return body
# #     if not body: return {}
# #     try: return json.loads(body)
# #     except: return {}

# # # --- API ROUTES ---

# # @app.route("/login", methods=["POST"])
# # def login(headers="guest", body="anonymous"):
# #     data = _parse_body(body)
# #     username = data.get("username") or data.get("peer_id")
# #     password = data.get("password")
# #     ip = data.get("ip") or "127.0.0.1"
# #     port = data.get("port")

# #     print(f"[Auth] Login: user={username}")

# #     if password == "password":
# #         with _lock:
# #             # Lưu thông tin user
# #             _peers[username] = {
# #                 "name": username, 
# #                 "ip": ip, 
# #                 "port": port,
# #                 "channels": ["General"] # Mặc định ai cũng có General
# #             }
# #             # Thêm vào kênh General
# #             if username not in _channels["General"]:
# #                 _channels["General"].append(username)

# #         # Nếu là admin -> Trả về text để set cookie (Task 1)
# #         if username == "admin":
# #             return "LOGIN_SUCCESS"
        
# #         # Nếu là peer -> Trả về JSON (Task 2)
# #         return {"status": "ok", "peer_id": username}
    
# #     return {"status": "error", "message": "Invalid credentials"}, 401

# # @app.route("/get-list", methods=["POST", "GET"])
# # def get_list(headers, body):
# #     """Lấy danh sách người dùng online"""
# #     with _lock:
# #         peer_list = list(_peers.values())
# #     return {"status": "ok", "peers": peer_list}

# # @app.route("/get-channels", methods=["POST"])
# # def get_channels(headers, body):
# #     """Lấy danh sách kênh (Admin thấy hết, User chỉ thấy kênh đã join)"""
# #     data = _parse_body(body)
# #     peer_id = data.get("peer_id")
    
# #     with _lock:
# #         if peer_id == "admin":
# #             # Admin thấy tất cả kênh
# #             channels = list(_channels.keys())
# #         else:
# #             # User thấy kênh mình đã join (được lưu trong _peers)
# #             user_info = _peers.get(peer_id, {})
# #             channels = user_info.get("channels", ["General"])
            
# #     return {"status": "ok", "channels": channels}

# # @app.route("/add-list", methods=["POST"])
# # def add_list(headers, body):
# #     """Tạo hoặc tham gia kênh"""
# #     data = _parse_body(body)
# #     channel = data.get("channel")
# #     username = data.get("username")

# #     if not channel or not username:
# #         return {"status": "error", "message": "Missing info"}, 400

# #     with _lock:
# #         # 1. Tạo kênh nếu chưa có
# #         if channel not in _channels:
# #             _channels[channel] = []
        
# #         # 2. Thêm user vào danh sách thành viên kênh
# #         if username not in _channels[channel]:
# #             _channels[channel].append(username)
            
# #         # 3. Cập nhật danh sách kênh của user
# #         if username in _peers:
# #             if channel not in _peers[username]["channels"]:
# #                 _peers[username]["channels"].append(channel)

# #     print(f"[Channel] {username} joined {channel}")
# #     return {"status": "ok", "channel": channel}

# # @app.route("/send-peer", methods=["POST"])
# # def send_peer(headers, body):
# #     """Gửi tin nhắn riêng"""
# #     data = _parse_body(body)
# #     target = data.get("target")
# #     sender = data.get("sender")
# #     msg = data.get("msg") or data.get("message")

# #     if not target or not msg: return {"status": "error"}, 400
# #     if target == sender: return {"status": "error", "message": "Self"}, 403

# #     # Xử lý /kick (Admin)
# #     if msg.startswith("/kick") and sender == "admin":
# #         user_to_kick = msg.split(" ")[1]
# #         with _lock:
# #             if user_to_kick in _peers:
# #                 del _peers[user_to_kick]
# #                 # Xóa khỏi các kênh
# #                 for ch in _channels:
# #                     if user_to_kick in _channels[ch]:
# #                         _channels[ch].remove(user_to_kick)
# #         return {"status": "ok", "message": f"Kicked {user_to_kick}"}

# #     # Lưu tin nhắn direct
# #     with _lock:
# #         if target in _peers:
# #             _inbox[target].append({
# #                 "sender": sender,
# #                 "msg": msg,
# #                 "type": "direct",
# #                 "timestamp": "now"
# #             })
# #             print(f"[Direct] {sender} -> {target}: {msg}")
# #             return {"status": "ok"}
# #         else:
# #             return {"status": "error", "message": "Offline"}, 404

# # @app.route("/broadcast-peer", methods=["POST"])
# # def broadcast_peer(headers, body):
# #     """Gửi tin nhắn vào Kênh"""
# #     data = _parse_body(body)
# #     channel = data.get("channel")
# #     msg = data.get("msg") or data.get("message")
# #     sender = data.get("sender")

# #     if not channel or not msg: return {"status": "error"}, 400

# #     with _lock:
# #         # Lấy danh sách thành viên trong kênh đó
# #         members = _channels.get(channel, [])
# #         if not members: return {"status": "error", "message": "Channel empty/not found"}, 404

# #         for member in members:
# #             if member != sender and member in _peers:
# #                 _inbox[member].append({
# #                     "sender": channel, # Hiển thị tên kênh là người gửi
# #                     "real_sender": sender, # Người thực gửi
# #                     "msg": f"{sender}: {msg}",
# #                     "type": "channel"
# #                 })
# #         print(f"[Channel {channel}] {sender}: {msg}")

# #     return {"status": "ok"}

# # @app.route("/get-messages", methods=["POST"])
# # def get_messages(headers, body):
# #     data = _parse_body(body)
# #     peer_id = data.get("peer_id")
# #     messages = []
# #     if peer_id:
# #         with _lock:
# #             if peer_id in _inbox:
# #                 messages = _inbox[peer_id][:]
# #                 _inbox[peer_id] = []
    
# #     formatted = [{"sender": m["sender"], "message": m["msg"]} for m in messages]
# #     return {"status": "ok", "messages": formatted}

# # if __name__ == "__main__":
# #     parser = argparse.ArgumentParser()
# #     parser.add_argument("--server-ip", default="0.0.0.0")
# #     parser.add_argument("--server-port", type=int, default=PORT)
# #     args = parser.parse_args()
# #     app.prepare_address(args.server_ip, args.server_port)
# #     app.run()


# import argparse
# import json
# import threading
# from daemon.weaprous import WeApRous
# import os
# import http.client

# app = WeApRous()

# # ========== DATABASE ==========
# PEERS = []              # [{name, ip, port}]
# CHANNELS = {}           # {channel: [ {name,ip,port}, ... ]}
# MESSAGES = {}           # {channel: [ {sender,msg}, ... ]}
# lock = threading.Lock()


# def _safe_json(body):
#     try:
#         if isinstance(body, dict):
#             return body
#         if body:
#             return json.loads(body)
#     except:
#         pass
#     return {}


# # ========== STATIC FILE ==========
# @app.route("/", methods=["GET"])
# def index(headers="", body=""):
#     try:
#         with open("./www/index.html", "r", encoding="utf-8") as f:
#             return {
#                 "status": "200 OK",
#                 "Content-Type": "text/html",
#                 "body": f.read()
#             }
#     except:
#         return {
#             "status": "404 Not Found",
#             "Content-Type": "text/html",
#             "body": "<h1>index.html not found</h1>"
#         }


# # @app.route("/staticfile", methods=["GET"])
# # def static_files(headers="", body=""):
# #     query = json.loads(headers).get("Query", "")
# #     file = query.replace("file=", "")
# #     path = f"./staticfile/{file}"
# #     if not os.path.exists(path):
# #         return f"File not found: {file}"
# #     with open(path, "r", encoding="utf-8") as f:
# #         return f.read()

# # @app.route("/staticfile", methods=["GET"])
# # def static_files(headers="", body=""):
# #     file = ""
# #     if isinstance(headers, dict):
# #         file = headers.get("Query", "").replace("file=", "")

# #     path = f"./static/{file}"

# #     if not os.path.exists(path):
# #         return f"File not found: {file}"

# #     with open(path, "r", encoding="utf-8") as f:
# #         return f.read()

# @app.route("/staticfile", methods=["GET"])
# def static_files(headers="", body=""):
#     import json, os, urllib.parse

#     query = json.loads(headers).get("Query", "")
#     file = query.replace("file=", "")

#     # FIX: bỏ query string nếu có
#     file = file.split("?")[0]

#     path = os.path.join("./static", file)

#     print("[DEBUG static] Resolving:", path)

#     if not os.path.exists(path):
#         return f"File not found: {file}"

#     with open(path, "r", encoding="utf-8") as f:
#         return f.read()



# # ========== TRACKER API ==========

# @app.route("/ping", methods=["GET"])
# def ping(headers="", body=""):
#     return json.dumps({"status": "ok"})


# # @app.route("/submit-info", methods=["POST"])
# # def submit_info(headers="", body=""):
# #     data = _safe_json(body)
# #     name = data.get("name")
# #     ip = data.get("ip")
# #     port = data.get("port")

# #     if not ip or not port:
# #         return json.dumps({"status": "error", "message": "ip/port required"})

# #     with lock:
# #         # update or insert
# #         for p in PEERS:
# #             if p["ip"] == ip and int(p["port"]) == int(port):
# #                 p["name"] = name
# #                 return json.dumps({"status": "ok", "peers": PEERS})

# #         PEERS.append({"name": name, "ip": ip, "port": int(port)})

# #     return json.dumps({"status": "ok", "peers": PEERS})

# @app.route("/submit-info", methods=["POST"])
# def submit_info(headers="", body=""):
#     data = _safe_json(body)
#     name = data.get("name")
#     ip = data.get("ip")
#     port = data.get("port")

#     if not ip or not port:
#         return json.dumps({"status": "error", "message": "ip/port required"})

#     with lock:
#         # update or insert
#         for p in PEERS:
#             if p["ip"] == ip and int(p["port"]) == int(port):
#                 p["name"] = name
#                 break
#         else:
#             # peer mới
#             PEERS.append({"name": name, "ip": ip, "port": int(port)})

#         # TỰ ĐỘNG ADD vào channel mặc định
#         CHANNELS.setdefault("global", [])

#         key = (ip, int(port))
#         exists = [(p["ip"], p["port"]) for p in CHANNELS["global"]]
#         if key not in exists:
#             CHANNELS["global"].append({
#                 "name": name,
#                 "ip": ip,
#                 "port": int(port)
#             })

#     return json.dumps({"status": "ok", "peers": PEERS})


# @app.route("/get-list", methods=["GET"])
# def get_list(headers="", body=""):
#     with lock:
#         return json.dumps(PEERS)


# @app.route("/add-list", methods=["POST"])
# def add_list(headers="", body=""):
#     data = _safe_json(body)
#     channel = data.get("channel")
#     peer = data.get("peer")

#     if not channel or not peer:
#         return json.dumps({"status": "error", "message": "Channel or peer missing"})

#     with lock:
#         CHANNELS.setdefault(channel, [])

#         key = (peer["ip"], int(peer["port"]))
#         existing = {(p["ip"], int(p["port"])) for p in CHANNELS[channel]}

#         if key not in existing:
#             CHANNELS[channel].append({
#                 "name": peer["name"],
#                 "ip": peer["ip"],
#                 "port": int(peer["port"])
#             })

#         # add to global peer list if missing
#         for p in PEERS:
#             if p["ip"] == peer["ip"] and int(p["port"]) == int(peer["port"]):
#                 break
#         else:
#             PEERS.append(peer)

#         snapshot = CHANNELS[channel].copy()

#     return json.dumps({"status": "ok", "channel": channel, "peers": snapshot})


# # @app.route("/get-channels", methods=["GET"])
# # def get_channels(headers="", body=""):
# #     with lock:
# #         out = {
# #             c: {"peers": CHANNELS[c], "messages": len(MESSAGES.get(c, []))}
# #             for c in CHANNELS
# #         }
# #     return json.dumps(out)

# # @app.route('/get-channels', methods=['GET'])
# # def get_channels(headers='', body=''):
# #     query = ""
# #     if isinstance(headers, dict):
# #         query = headers.get("Query", "")
# #     # else:
# #     #     query = ""

# #     with lock:
# #         summary = {
# #             c: {
# #                 'peers': CHANNELS.get(c, []), 
# #                 'messages': len(MESSAGES.get(c, []))
# #             } 
# #             for c in CHANNELS
# #         }
# #     return json.dumps(summary)

# # @app.route('/get-channels', methods=['GET'])
# # def get_channels(headers='', body=''):
# #     peer = ""
# #     if isinstance(headers, dict):
# #         q = headers.get("Query", "")
# #         if q.startswith("peer_id="):
# #             peer = q.replace("peer_id=", "")

# #     with lock:
# #         # Lấy danh sách channel mà user nằm trong đó
# #         summary = {
# #             c: {
# #                 'peers': CHANNELS[c],
# #                 'messages': len(MESSAGES.get(c, []))
# #             }
# #             for c in CHANNELS
# #             if any(p["name"] == peer for p in CHANNELS[c])
# #         }

# #     return json.dumps(summary)

# @app.route('/get-channels', methods=['GET'])
# def get_channels(headers='', body=''):
#     path = headers.get("Path", "")
#     if "?" in path:
#         path, query_string = path.split("?", 1)
#     else:
#         query_string = ""

#     peer = ""
#     if query_string.startswith("peer_id="):
#         peer = query_string.replace("peer_id=", "")

#     with lock:
#         summary = {
#             c: {
#                 'peers': CHANNELS[c],
#                 'messages': len(MESSAGES.get(c, []))
#             }
#             for c in CHANNELS
#             if any(p["name"] == peer for p in CHANNELS[c])
#         }

#     return json.dumps(summary)



# # @app.route("/get-messages", methods=["GET"])
# # def get_messages(headers="", body=""):
# #     h = json.loads(headers)
# #     channel = h.get("Query", "").replace("channel=", "")
# #     with lock:
# #         return json.dumps(MESSAGES.get(channel, []))

# # @app.route('/get-messages', methods=['GET'])
# # def get_messages(headers='', body=''):
# #     # headers contains Query encoded as JSON string by WeApRous in earlier code
# #     # try:
# #     #     h = json.loads(headers)
# #     #     query = h.get("Query","")
# #     # except Exception:
# #     #     query = ""
# #     # query like "channel=general"
# #     query = ""
# #     if isinstance(headers, dict):
# #         query = headers.get("Query", "")
# #     else:
# #         query = ""
# #     channel = query.replace("channel=", "")
# #     with lock:
# #         return json.dumps(MESSAGES.get(channel, []))

# @app.route('/get-messages', methods=['GET'])
# def get_messages(headers='', body=''):
#     path = headers.get("Path", "")
#     if "?" in path:
#         path, query_string = path.split("?", 1)
#     else:
#         query_string = ""

#     peer = ""
#     if isinstance(headers, dict):
#         q = headers.get("Query", "")
#         if q.startswith("peer_id="):
#             peer = q.replace("peer_id=", "")

#     out = {}

#     with lock:
#         for ch, arr in MESSAGES.items():
#             if peer in ch.split("__"):
#                 out[ch] = arr

#     return json.dumps(out)


# @app.route("/broadcast-peer", methods=["POST"])
# def broadcast_peer(headers="", body=""):
#     data = _safe_json(body)
#     channel = data.get("channel")
#     msg = data.get("msg")
#     sender = data.get("sender", "tracker")

#     if not channel or msg is None:
#         return json.dumps({"status": "error", "message": "channel and msg required"})

#     with lock:
#         if channel not in CHANNELS:
#             return json.dumps({"status": "error", "message": "channel not found"})

#         MESSAGES.setdefault(channel, [])
#         MESSAGES[channel].append({"sender": sender, "msg": msg})

#         for peer in CHANNELS[channel]:
#             try:
#                 conn = http.client.HTTPConnection(peer["ip"], peer["port"], timeout=1)
#                 payload = json.dumps({
#                     "sender": sender,
#                     "msg": msg,
#                     "channel": channel
#                 })
#                 conn.request("POST", "/send-peer", body=payload,
#                              headers={"Content-Type": "application/json"})
#                 conn.getresponse().read()
#                 conn.close()
#             except Exception as e:
#                 print("[Warning] cannot push to peer:", peer, e)

#     return json.dumps({"status": "ok"})


# # @app.route("/send-peer", methods=["POST"])
# # def send_peer(headers="", body=""):
# #     data = _safe_json(body)
# #     print("[tracker] send-peer:", data)
# #     return json.dumps({"status": "ok"})

# @app.route('/send-peer', methods=['POST'])
# def send_peer(headers='', body=''):
#     print("[tracker] send-peer:", body)
#     data = _safe_json(body)
#     sender = data.get('sender', '')
#     msg = data.get('msg', '')
#     target = data.get('target', '')

#     if not sender or not target:
#         return json.dumps({"status": "error", "message": "invalid sender/target"})

#     # tạo channel 1-1, ví dụ Hung__An
#     channel = "__".join(sorted([sender, target]))

#     with lock:
#         MESSAGES.setdefault(channel, [])
#         MESSAGES[channel].append({
#             "from": sender,
#             "to": target,
#             "message": msg
#         })

#     return json.dumps({"status": "ok"})



# @app.route("/clear-list", methods=["POST"])
# def clear_list(headers="", body=""):
#     with lock:
#         PEERS.clear()
#         CHANNELS.clear()
#         MESSAGES.clear()
#     return json.dumps({"status": "ok"})


# # ========== START ==========
# if __name__ == "__main__":
#     parser = argparse.ArgumentParser()
#     parser.add_argument("--ip", default="127.0.0.1")
#     parser.add_argument("--port", type=int, default=8000)
#     args = parser.parse_args()

#     app.prepare_address(args.ip, args.port)
#     app.run()



import argparse
import json
import threading
from daemon.weaprous import WeApRous
import os
import http.client

# -----------------------------------------------------
#  INIT
# -----------------------------------------------------

app = WeApRous()

PEERS = []              # [{name, ip, port}]
CHANNELS = {}           # {channel_name: [peer,...]}
MESSAGES = {}           # {channel: [msgObj,...]}
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

lock = threading.Lock()


# -----------------------------------------------------
#  HELPER
# -----------------------------------------------------

def _safe_json(body):
    try:
        if isinstance(body, dict):
            return body
        if body:
            return json.loads(body)
    except:
        pass
    return {}

def _peer_key(p):
    return f"{p['ip']}:{p['port']}"


# -----------------------------------------------------
#  STATIC FILE
# -----------------------------------------------------

@app.route("/", methods=["GET"])
def index(headers="", body=""):
    try:
        with open("./www/index.html", "r", encoding="utf-8") as f:
            return {
                "status": "200 OK",
                "Content-Type": "text/html",
                "body": f.read()
            }
    except:
        return {
            "status": "404 Not Found",
            "Content-Type": "text/html",
            "body": "<h1>index.html not found</h1>"
        }


# @app.route("/staticfile", methods=["GET"])
# def static_files(headers="", body=""):
#     # headers = {"Query": "file=js/chatui.js"}
#     # query = ""
#     # if isinstance(headers, dict):
#     #     query = headers.get("Query", "")

#     # file = query.replace("file=", "").split("?")[0]
#     # path = os.path.join("./static", file)

#     # print("[STATIC] load:", path)

#     # if not os.path.exists(path):
#     #     return f"File not found: {file}"

#     # with open(path, "r", encoding="utf-8") as f:
#     #     return f.read()
#     import json, os
    
#     query = json.loads(headers).get("Query", "")
#     file = query.replace("file=", "")
#     path = f"./static/{file}"

#     if not os.path.exists(path):
#         return f"File not found: {file}"

#     with open(path, "r", encoding="utf-8") as f:
#         return f.read()

# @app.route("/staticfile", methods=["GET"])
# def static_files(headers="", body=""):
#     query = ""
#     if isinstance(headers, dict):
#         query = headers.get("Query", "")

#     params = dict(x.split("=",1) for x in query.split("&") if "=" in x)
#     filename = params.get("file")

#     if not filename:
#         return "File not specified", 400

#     file_path = os.path.join(BASE_DIR, "static", filename)

#     print(f"[Response] DEBUG: Looking for file at -> {file_path}")

#     if os.path.exists(file_path):
#         with open(file_path, "rb") as f:
#             return f.read()
#     else:
#         print(f"[Response] Error: File not found at {file_path}")
#         return "File not found", 404

# @app.route("/staticfile", methods=["GET"])
# def static_files(headers="", body=""):
#     query = ""
#     if isinstance(headers, dict):
#         query = headers.get("Query", "")

#     params = dict(x.split("=", 1) for x in query.split("&") if "=" in x and x)
#     filename = params.get("file")

#     if not filename:
#         return "File not specified", 400

#     file_path = os.path.join(BASE_DIR, "static", filename)
#     print(f"[Response] DEBUG: Looking for file at -> {file_path}")

#     if not os.path.exists(file_path):
#         print(f"[Response] Error: File not found at {file_path}")
#         return "File not found", 404

#     # Xác định content type
#     ext = filename.split(".")[-1].lower()
#     content_type = {
#         "css": "text/css",
#         "js": "application/javascript",
#         "html": "text/html"
#     }.get(ext, "text/plain")

#     with open(file_path, "r", encoding="utf-8") as f:
#         content = f.read()

#     # Trả về trực tiếp nội dung, với header Content-Type
#     return content, 200, {"Content-Type": content_type}

# @app.route("/staticfile", methods=["GET"])
# def static_files(headers="", body=""):
#     import os

#     query = ""
#     if isinstance(headers, dict):
#         query = headers.get("Query", "")

#     params = dict(x.split("=", 1) for x in query.split("&") if "=" in x and x)
#     filename = params.get("file")

#     if not filename:
#         return "File not specified", 400

#     file_path = os.path.join(BASE_DIR, "static", filename)
#     print(f"[Response] DEBUG: Looking for file at -> {file_path}")

#     if not os.path.exists(file_path):
#         print(f"[Response] Error: File not found at {file_path}")
#         return "File not found", 404

#     # Xác định content type
#     ext = filename.split(".")[-1].lower()
#     content_type = {
#         "css": "text/css",
#         "js": "application/javascript",
#         "html": "text/html"
#     }.get(ext, "text/plain")

#     # đọc file
#     with open(file_path, "rb") as f:
#         content = f.read()  # đọc binary

#     # Trả về raw content cùng Content-Type, không JSON
#     return content, 200, {"Content-Type": content_type}

# @app.route("/staticfile", methods=["GET"])
# def static_files(headers="", body=""):
#     import os

#     query = ""
#     if isinstance(headers, dict):
#         query = headers.get("Query", "")

#     params = dict(x.split("=", 1) for x in query.split("&") if "=" in x and x)
#     filename = params.get("file")

#     if not filename:
#         return "File not specified", 400

#     file_path = os.path.join(BASE_DIR, "static", filename)
#     print(f"[Response] DEBUG: Looking for file at -> {file_path}")

#     if not os.path.exists(file_path):
#         print(f"[Response] Error: File not found at {file_path}")
#         return "File not found", 404

#     # Xác định content type
#     ext = filename.split(".")[-1].lower()
#     content_type = {
#         "css": "text/css",
#         "js": "application/javascript",
#         "html": "text/html"
#     }.get(ext, "text/plain")

#     # đọc file binary
#     with open(file_path, "rb") as f:
#         content = f.read()

#     # Trả về trực tiếp raw content, không bọc JSON
#     return content, 200, {"Content-Type": content_type}

# @app.route("/staticfile", methods=["GET"])
# def static_files(headers="", body=""):
#     import os

#     query = ""
#     if isinstance(headers, dict):
#         query = headers.get("Query", "")

#     params = dict(x.split("=", 1) for x in query.split("&") if "=" in x and x)
#     filename = params.get("file")

#     if not filename:
#         return "File not specified", 400

#     file_path = os.path.join(BASE_DIR, "static", filename)
#     print(f"[Response] DEBUG: Looking for file at -> {file_path}")

#     if not os.path.exists(file_path):
#         print(f"[Response] Error: File not found at {file_path}")
#         return "File not found", 404

#     ext = filename.split(".")[-1].lower()
#     content_type = {
#         "css": "text/css",
#         "js": "application/javascript",
#         "html": "text/html"
#     }.get(ext, "text/plain")

#     # đọc raw bytes
#     with open(file_path, "rb") as f:
#         content = f.read()

#     # trả trực tiếp nội dung, không json.dumps
#     return content, 200, {"Content-Type": content_type}

@app.route("/staticfile", methods=["GET"])
def static_files(headers="", body=""):
    query = headers.get("Query", "") if isinstance(headers, dict) else ""
    params = dict(x.split("=", 1) for x in query.split("&") if "=" in x and x)
    filename = params.get("file")

    if not filename:
        return "File not specified", 400

    file_path = os.path.join(BASE_DIR, "static", filename)
    if not os.path.exists(file_path):
        return "File not found", 404

    ext = filename.split(".")[-1].lower()
    content_type = {
        "css": "text/css",
        "js": "application/javascript",
        "html": "text/html"
    }.get(ext, "text/plain")

    # Mở file text, trả str
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Trả thẳng content + header, không json.dumps
    return content, 200, {"Content-Type": content_type}




# -----------------------------------------------------
#  BASIC TRACKER API
# -----------------------------------------------------

@app.route("/ping", methods=["GET"])
def ping(headers="", body=""):
    return json.dumps({"status": "ok"})


@app.route("/submit-info", methods=["POST"])
def submit_info(headers="", body=""):
    """
    Peer gửi thông tin để đăng ký với tracker:
    {
        "name": "Hung",
        "ip": "127.0.0.1",
        "port": 9001
    }
    """
    data = _safe_json(body)
    name = data.get("name")
    ip = data.get("ip")
    port = data.get("port")

    if not ip or not port:
        return json.dumps({"status": "error", "message": "ip/port required"})

    with lock:
        # cập nhật nếu có
        for p in PEERS:
            if p["ip"] == ip and int(p["port"]) == int(port):
                p["name"] = name
                break
        else:
            PEERS.append({"name": name, "ip": ip, "port": int(port)})

        # auto join global
        CHANNELS.setdefault("global", [])
        exists = {(p["ip"], p["port"]) for p in CHANNELS["global"]}
        if (ip, int(port)) not in exists:
            CHANNELS["global"].append({
                "name": name,
                "ip": ip,
                "port": int(port)
            })

    return json.dumps({"status": "ok", "peers": PEERS})


@app.route("/get-list", methods=["GET"])
def get_list(headers="", body=""):
    with lock:
        return json.dumps(PEERS)


@app.route("/clear-list", methods=["POST"])
def clear_list(headers="", body=""):
    with lock:
        PEERS.clear()
        CHANNELS.clear()
        MESSAGES.clear()
    return json.dumps({"status": "ok"})


# -----------------------------------------------------
#  CHANNEL JOIN
# -----------------------------------------------------

@app.route("/add-list", methods=["POST"])
def add_list(headers="", body=""):
    """
    body = {
        "channel": "Game",
        "peer": {"name":"Hung", "ip":"127.0.0.1", "port":9001}
    }
    """
    data = _safe_json(body)
    channel = data.get("channel")
    peer = data.get("peer")

    if not channel or not peer:
        return json.dumps({"status": "error", "message": "Channel or peer missing"})

    with lock:
        CHANNELS.setdefault(channel, [])

        # avoid duplicate
        key = (peer["ip"], int(peer["port"]))
        exists = {(p["ip"], p["port"]) for p in CHANNELS[channel]}

        if key not in exists:
            CHANNELS[channel].append({
                "name": peer["name"],
                "ip": peer["ip"],
                "port": int(peer["port"])
            })

        # ensure global PEERS list has this peer
        for p in PEERS:
            if p["ip"] == peer["ip"] and int(p["port"]) == int(peer["port"]):
                break
        else:
            PEERS.append(peer)

        snapshot = CHANNELS[channel].copy()

    return json.dumps({"status": "ok", "channel": channel, "peers": snapshot})


# -----------------------------------------------------
#  GET CHANNEL LIST
# -----------------------------------------------------

# @app.route("/get-channels", methods=["GET"])
# def get_channels(headers="", body=""):
#     """
#     Trả về:
#     {
#         "global": {peers:[], messages:x},
#         "Game": { ... }
#     }
#     """
#     with lock:
#         out = {
#             c: {
#                 "peers": CHANNELS[c],
#                 "messages": len(MESSAGES.get(c, []))
#             }
#             for c in CHANNELS
#         }
#     return json.dumps(out)
@app.route("/get-channels", methods=["GET"])
def get_channels(headers="", body=""):
    path = headers.get("Path", "") if isinstance(headers, dict) else ""
    query_string = ""
    if "?" in path:
        _, query_string = path.split("?", 1)

    peer_id = None
    params = dict(x.split("=",1) for x in query_string.split("&") if "=" in x)
    peer_id = params.get("peer_id")

    with lock:
        summary = {}
        if peer_id:
            # chỉ channel peer này đã join
            for ch, peers in CHANNELS.items():
                if any(p["name"] == peer_id for p in peers):
                    summary[ch] = {
                        "peers": peers,
                        "messages": len(MESSAGES.get(ch, []))
                    }
        else:
            # admin hoặc tổng quan
            summary = {
                ch: {
                    "peers": peers,
                    "messages": len(MESSAGES.get(ch, []))
                }
                for ch, peers in CHANNELS.items()
            }

    return json.dumps(summary)



# -----------------------------------------------------
#  GET MESSAGES
# -----------------------------------------------------

# @app.route("/get-messages", methods=["GET"])
# def get_messages(headers="", body=""):
#     """
#     Query: channel=global
#     """
#     query = ""
#     if isinstance(headers, dict):
#         query = headers.get("Query", "")

#     channel = query.replace("channel=", "")

#     with lock:
#         return json.dumps(MESSAGES.get(channel, []))
@app.route("/get-messages", methods=["GET"])
def get_messages(headers="", body=""):
    query = ""
    if isinstance(headers, dict):
        query = headers.get("Query", "")

    # hỗ trợ 2 loại query:
    #  /get-messages?peer_id=An
    #  /get-messages?channel=global
    params = dict(x.split("=",1) for x in query.split("&") if "=" in x)

    peer_id = params.get("peer_id")
    channel = params.get("channel")

    out = []

    with lock:
        # 1) Nếu query channel → trả tin nhắn của channel
        if channel:
            msgs = MESSAGES.get(channel, [])
            for m in msgs:
                out.append({
                    "sender": m.get("sender", m.get("from")),
                    "message": m.get("msg", m.get("message")),
                    "channel": channel
                })
            return json.dumps({"messages": out})

        # 2) Nếu query peer_id → gom tất cả DM liên quan
        if peer_id:
            for ch, msgs in MESSAGES.items():
                # direct-channel như "An__Hung"
                if "__" in ch and peer_id in ch.split("__"):
                    for m in msgs:
                        sender = m.get("from")
                        receiver = m.get("to")
                        if receiver == peer_id or sender == peer_id:
                            out.append({
                                "sender": sender,
                                "message": m["message"],
                                "channel": ch
                            })

            return json.dumps({"messages": out})

    return json.dumps({"messages": []})



# -----------------------------------------------------
#  BROADCAST MESSAGE
# -----------------------------------------------------

@app.route("/broadcast-peer", methods=["POST"])
def broadcast_peer(headers="", body=""):
    """
    body = {
        "channel": "global",
        "msg": "hello",
        "sender": "Hung"
    }
    """
    data = _safe_json(body)
    channel = data.get("channel")
    msg = data.get("msg")
    sender = data.get("sender", "tracker")

    if not channel or msg is None:
        return json.dumps({"status": "error", "message": "channel and msg required"})

    with lock:
        if channel not in CHANNELS:
            return json.dumps({"status": "error", "message": "channel not found"})

        MESSAGES.setdefault(channel, [])
        MESSAGES[channel].append({"sender": sender, "msg": msg})

        for peer in CHANNELS[channel]:
            try:
                conn = http.client.HTTPConnection(peer["ip"], peer["port"], timeout=1)
                payload = json.dumps({
                    "channel": channel,
                    "sender": sender,
                    "msg": msg
                })
                conn.request("POST", "/receive-channel", body=payload,
                             headers={"Content-Type": "application/json"})
                conn.getresponse().read()
                conn.close()
            except Exception as e:
                print("[Warning] cannot push to peer:", peer, e)

    return json.dumps({"status": "ok"})

@app.route("/receive-channel", methods=["POST"])
def receive_channel(headers="", body=""):
    data = _safe_json(body)
    channel = data.get("channel")
    sender = data.get("sender")
    msg = data.get("msg")

    if not channel or msg is None:
        return json.dumps({"status": "error", "message": "invalid data"})

    with lock:
        MESSAGES.setdefault(channel, [])
        MESSAGES[channel].append({"sender": sender, "msg": msg})

    print(f"[Channel {channel}] {sender}: {msg}")
    return json.dumps({"status": "ok"})



# -----------------------------------------------------
#  DIRECT MESSAGE
# -----------------------------------------------------

@app.route("/send-peer", methods=["POST"])
def send_peer(headers="", body=""):
    """
    body = { sender:"Hung", target:"An", msg:"hi" }
    Tracker sẽ tạo channel 1-1: Hung__An
    """
    data = _safe_json(body)
    sender = data.get("sender")
    target = data.get("target")
    msg = data.get("msg")

    if not sender or not target:
        return json.dumps({"status": "error", "message": "invalid sender/target"})

    ch = "__".join(sorted([sender, target]))

    with lock:
        MESSAGES.setdefault(ch, [])
        MESSAGES[ch].append({
            "from": sender,
            "to": target,
            "message": msg
        })

    return json.dumps({"status": "ok"})


# -----------------------------------------------------
#  START
# -----------------------------------------------------

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--ip", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    a = parser.parse_args()

    app.prepare_address(a.ip, a.port)
    app.run()
