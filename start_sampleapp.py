# import argparse
# import json
# import socket
# import threading
# from collections import defaultdict
# from typing import Dict, Tuple

# from daemon.weaprous import WeApRous

# PORT = 8000
# app = WeApRous()

# # In-memory state for peers and channels. Thread-safe because backend spawns threads.
# _peers: Dict[str, Dict[str, str]] = {}
# _channels: Dict[str, set] = defaultdict(set)
# _inbox: Dict[str, list] = defaultdict(list) 
# _lock = threading.Lock()


# def _parse_body(body: str) -> Dict[str, str]:
#     """
#     Parse a body that might be URL-encoded form (`a=1&b=2`) or JSON.
#     """
#     if not body:
#         return {}
#     try:
#         return json.loads(body)
#     except Exception:
#         pass

#     parsed: Dict[str, str] = {}
#     for pair in body.split("&"):
#         if not pair or "=" not in pair:
#             continue
#         key, value = pair.split("=", 1)
#         parsed[key] = value
#     return parsed


# def _require_peer(body_map: Dict[str, str]) -> Tuple[bool, str]:
#     peer_id = body_map.get("peer_id")
#     if not peer_id:
#         return False, "peer_id missing"
#     return True, peer_id

# @app.route("/login", methods=["POST"])
# def login(headers="guest", body="anonymous"):
#     """
#     Xử lý đăng nhập Hybrid (Sửa lỗi nhận diện Admin)
#     """
#     data = _parse_body(body or "")
    
#     # Lấy tên đăng nhập (dù frontend gửi là 'username' hay 'peer_id')
#     current_user = data.get("username") or data.get("peer_id")
#     password = data.get("password")

#     print(f"[Auth] Debug: Input user='{current_user}', pass='{password}'")

#     # --- LOGIC CHO TASK 1 (ADMIN) ---
#     # Nếu tên là admin và pass đúng -> Kích hoạt Task 1
#     if current_user == "admin" and password == "password":
#         print("[Auth] Admin login detected -> Task 1 Cookie Mode")
#         # Trả về tín hiệu để HttpAdapter set cookie
#         return "LOGIN_SUCCESS"

#     # --- LOGIC CHO TASK 2 (CHAT) ---
#     if not current_user:
#         return {"status": "error", "message": "Missing username/peer_id"}, 400

#     if password == "password":
#         ip = data.get("ip") or headers.get("host", "unknown")
#         port = data.get("port", "")
#         with _lock:
#             _peers[current_user] = {"ip": ip, "port": port, "channels": set()}
            
#         print(f"[Auth] Peer login: {current_user} -> Task 2 Chat Mode")
#         return {"status": "ok", "peer_id": current_user}, 200
    
#     print(f"[Auth] Login failed for {current_user}")
#     return {"status": "error", "message": "Invalid credentials"}, 401


# @app.route("/add-list", methods=["POST"])
# def add_list(headers="guest", body="anonymous"):
#     """
#     Add a peer to a channel membership list.
#     """
#     data = _parse_body(body or "")
#     ok, peer_id = _require_peer(data)
#     if not ok:
#         return {"status": "error", "message": peer_id}, 400

#     channel = data.get("channel")
#     if not channel:
#         return {"status": "error", "message": "channel missing"}, 400

#     with _lock:
#         if peer_id not in _peers:
#             return {"status": "error", "message": "peer not authenticated"}, 401
#         _channels[channel].add(peer_id)
#         _peers[peer_id].setdefault("channels", set()).add(channel)
#         members = list(_channels[channel])

#     print(f"[SampleApp] Peer {peer_id} joined channel {channel}")
#     return {"status": "ok", "channel": channel, "members": members}, 200


# @app.route("/connect-peer", methods=["POST", "GET"])
# def connect_peer(headers="guest", body="anonymous"):
#     """
#     Optional trigger to fetch peers for a caller to connect to.
#     """
#     data = _parse_body(body or "")
#     ok, peer_id = _require_peer(data)
#     if not ok:
#         return {"status": "error", "message": peer_id}, 400

#     with _lock:
#         if peer_id not in _peers:
#             return {"status": "error", "message": "peer not authenticated"}, 401
#         peers = [
#             {"peer_id": pid, "ip": info.get("ip"), "port": info.get("port")}
#             for pid, info in _peers.items()
#             if pid != peer_id
#         ]

#     return {"status": "ok", "peers": peers}, 200


# @app.route("/broadcast-peer", methods=["POST"])
# def broadcast_peer(headers="guest", body="anonymous"):
#     """
#     Broadcast a message to all members of a channel.
#     """
#     data = _parse_body(body or "")
#     ok, peer_id = _require_peer(data)
#     if not ok:
#         return {"status": "error", "message": peer_id}, 400
    
#     # --- START ACCESS CONTROL ---
#     # Kiểm tra xem người gửi có phải là admin không
#     if peer_id != "admin":
#         print(f"[AccessControl] Denied broadcast request from {peer_id}")
#         return {
#             "status": "error", 
#             "message": "Access Denied: Only 'admin' can broadcast."
#         }, 403 
#     # --- END ACCESS CONTROL ---
    
#     channel = data.get("channel")
#     message = data.get("message", "")
#     if not channel:
#         return {"status": "error", "message": "channel missing"}, 400

#     with _lock:
#         if peer_id not in _peers:
#             return {"status": "error", "message": "peer not authenticated"}, 401
#         targets = list(_channels.get(channel, []))

#     print(f"[SampleApp] Broadcast from {peer_id} -> channel {channel}: {message}")
#     return {
#         "status": "ok",
#         "channel": channel,
#         "targets": targets,
#         "message": message,
#     }, 200

# @app.route("/send-peer", methods=["POST"])
# def send_peer(headers="guest", body="anonymous"):
#     """
#     Send a direct message to a specific peer.
#     """
#     data = _parse_body(body or "")
#     ok, peer_id = _require_peer(data)
#     if not ok:
#         return {"status": "error", "message": peer_id}, 400

#     target = data.get("target")
#     message = data.get("message", "")
#     if not target:
#         return {"status": "error", "message": "target missing"}, 400

#     # ================= ACCESS CONTROL LOGIC =================
    
#     # TRƯỜNG HỢP 1: Xử lý lệnh đặc biệt "/kick" (Chỉ Admin mới được dùng)
#     if message.startswith("/kick"):
#         # Authorization Check: Bạn là ai?
#         if peer_id != "admin":
#             print(f"[AccessControl] User {peer_id} tried to use admin command.")
#             return {
#                 "status": "error", 
#                 "message": "⛔ ACCESS DENIED: Only 'admin' can use /kick command."
#             }, 403 # Forbidden
        
#         # Nếu là admin -> Thực thi lệnh
#         target_to_kick = message.split(" ")[1] if len(message.split(" ")) > 1 else target
        
#         with _lock:
#             if target_to_kick in _peers:
#                 del _peers[target_to_kick] # Xóa user khỏi danh sách
#                 print(f"[Admin] User {target_to_kick} was kicked by Admin.")
                
#                 # Gửi thông báo lại cho Admin
#                 return {
#                     "status": "ok", 
#                     "to": target, 
#                     "message": f"SYSTEM: User {target_to_kick} has been kicked out."
#                 }, 200
#             else:
#                  return {"status": "error", "message": "User not found to kick"}, 404

#     # ================= END ACCESS CONTROL =================
    
#     with _lock:
#         if peer_id not in _peers:
#             return {"status": "error", "message": "peer not authenticated"}, 401
        
#         # Kiểm tra target có tồn tại không (Optional, tùy logic)
#         # if target not in _peers:
#         #    return {"status": "error", "message": "target not found"}, 404

#         # LƯU TIN NHẮN VÀO HỘP THƯ CỦA TARGET
#         msg_obj = {
#             "sender": peer_id,
#             "message": message,
#             "timestamp": "now" # Bạn có thể thêm datetime thực tế nếu muốn
#         }
#         _inbox[target].append(msg_obj)

#     print(f"[SampleApp] Direct message {peer_id} -> {target}: {message}")
#     return {"status": "ok", "to": target, "message": message}, 200


# # THÊM API MỚI ĐỂ NHẬN TIN NHẮN
# @app.route("/get-messages", methods=["POST"])
# def get_messages(headers="guest", body="anonymous"):
#     """
#     Fetch pending messages for the authenticated peer.
#     """
#     data = _parse_body(body or "")
#     ok, peer_id = _require_peer(data)
#     if not ok:
#         return {"status": "error", "message": peer_id}, 400
    
#     messages = []
#     with _lock:
#         if peer_id in _inbox and _inbox[peer_id]:
#             # Lấy tất cả tin nhắn và xóa khỏi hàng đợi (cơ chế Popping)
#             messages = _inbox[peer_id][:] 
#             _inbox[peer_id] = [] # Xóa tin đã đọc
            
#     return {"status": "ok", "messages": messages}, 200


# @app.route("/hello", methods=["PUT"])
# def hello(headers, body):
#     print(f"[SampleApp] ['PUT'] Hello in {headers} to {body}")


# if __name__ == "__main__":
#     parser = argparse.ArgumentParser(
#         prog="Backend", description="", epilog="Beckend daemon"
#     )
#     parser.add_argument("--server-ip", default="0.0.0.0")
#     parser.add_argument("--server-port", type=int, default=PORT)

#     args = parser.parse_args()
#     ip = args.server_ip
#     port = args.server_port

#     app.prepare_address(ip, port)
#     app.run()










# import argparse
# import json
# import socket
# import threading
# from collections import defaultdict
# from typing import Dict, Tuple

# from daemon.weaprous import WeApRous

# PORT = 8000
# app = WeApRous()

# # --- DATABASE GIẢ LẬP (Lưu trên RAM) ---
# # _peers: { "username": {"ip": "...", "port": "...", "channels": [...]} }
# _peers: Dict[str, Dict] = {}

# # _channels: { "channel_name": ["user1", "user2"] }
# _channels: Dict[str, list] = defaultdict(list)

# # _inbox: { "username": [ {msg1}, {msg2} ] } -> Lưu tin nhắn chờ nhận
# _inbox: Dict[str, list] = defaultdict(list)

# # _channel_messages: { "channel_name": [ {msg1}, {msg2} ] } -> Lưu lịch sử tin nhắn kênh (Optional)
# _channel_messages: Dict[str, list] = defaultdict(list)

# _lock = threading.Lock()

# # --- HELPER FUNCTIONS ---
# def _parse_body(body):
#     """An toàn parse body thành dict, chấp nhận cả chuỗi JSON hoặc dict sẵn"""
#     if isinstance(body, dict): return body
#     if not body: return {}
#     try:
#         return json.loads(body)
#     except:
#         return {}

# # --- API ROUTES ---

# @app.route("/login", methods=["POST"])
# def login(headers="guest", body="anonymous"):
#     """
#     Hybrid Login:
#     - Admin: Trả về LOGIN_SUCCESS (Cookie)
#     - Peer: Trả về JSON ok
#     """
#     data = _parse_body(body)
#     username = data.get("username") or data.get("peer_id")
#     password = data.get("password")
#     ip = data.get("ip") or "127.0.0.1"
#     port = data.get("port")

#     print(f"[Auth] Login request: user={username} pass={password} ip={ip} port={port}")

#     # 1. Logic Admin (Task 1)
#     if username == "admin" and password == "password":
#         return "LOGIN_SUCCESS"

#     # 2. Logic Peer (Task 2)
#     if username and password == "password":
#         with _lock:
#             # Lưu/Cập nhật thông tin Peer
#             _peers[username] = {
#                 "name": username,
#                 "ip": ip, 
#                 "port": port, 
#                 "channels": []
#             }
#         return {"status": "ok", "peer_id": username}
    
#     return {"status": "error", "message": "Invalid credentials"}, 401

# # --- API CHO PEER (GET LIST) ---
# @app.route("/get-list", methods=["GET"])
# def get_list(headers, body):
#     """Trả về danh sách người dùng đang online"""
#     with _lock:
#         # Chuyển dict _peers thành list để trả về
#         peer_list = []
#         for name, info in _peers.items():
#             peer_list.append(info)
#     return peer_list

# # --- API CHO CHANNEL ---
# @app.route("/channels", methods=["GET"])
# def list_channels(headers, body):
#     """Trả về danh sách tên các kênh hiện có"""
#     with _lock:
#         return list(_channels.keys())

# @app.route("/add-list", methods=["POST"])
# def add_list(headers, body):
#     """
#     User tham gia vào một kênh (Join Channel)
#     Input: { "channel": "tên_kênh", "peer": { "name": "..." } }
#     """
#     data = _parse_body(body)
#     channel_name = data.get("channel")
#     peer_info = data.get("peer") # dict {name, ip, port}

#     if not channel_name or not peer_info:
#         return {"status": "error", "message": "Missing channel or peer info"}, 400

#     username = peer_info.get("name")

#     with _lock:
#         # 1. Thêm user vào danh sách thành viên của kênh
#         if username not in _channels[channel_name]:
#             _channels[channel_name].append(username)
        
#         # 2. Cập nhật thông tin kênh vào hồ sơ user
#         if username in _peers:
#             if channel_name not in _peers[username].get("channels", []):
#                 _peers[username]["channels"].append(channel_name)

#     print(f"[Channel] User {username} joined channel {channel_name}")
#     return {"status": "ok", "channel": channel_name}

# # --- API GỬI TIN NHẮN (DIRECT) ---
# @app.route("/send-peer", methods=["POST"])
# def send_peer(headers, body):
#     """Gửi tin nhắn riêng (Direct)"""
#     data = _parse_body(body)
    
#     # Client JS gửi lên: peer (target name), msg, sender
#     # Lưu ý: Client của bạn gửi target nằm trong biến "peer": {name: "..."} hoặc "target": "..."
#     # Ta xử lý linh hoạt:
#     target_name = data.get("target")
#     if not target_name and isinstance(data.get("peer"), dict):
#         target_name = data.get("peer").get("name")
    
#     sender = data.get("sender")
#     msg = data.get("msg") or data.get("message")

#     if not target_name or not msg:
#         return {"status": "error", "message": "Missing target or msg"}, 400

#     # ACCESS CONTROL: Chặn gửi cho chính mình
#     if target_name == sender:
#         return {"status": "error", "message": "Cannot send to yourself"}, 403

#     # ACCESS CONTROL: Admin Command (/kick)
#     if msg.startswith("/kick") and sender != "admin":
#         return {"status": "error", "message": "Access Denied"}, 403
    
#     if msg.startswith("/kick") and sender == "admin":
#         user_to_kick = msg.split(" ")[1]
#         with _lock:
#             if user_to_kick in _peers:
#                 del _peers[user_to_kick]
#         return {"status": "ok", "message": f"Kicked {user_to_kick}"}

#     # LƯU TIN NHẮN VÀO INBOX CỦA NGƯỜI NHẬN
#     with _lock:
#         if target_name in _peers:
#             _inbox[target_name].append({
#                 "sender": sender,
#                 "msg": msg,
#                 "type": "direct",
#                 "timestamp": "now"
#             })
#             print(f"[Direct] {sender} -> {target_name}: {msg}")
#             return {"status": "ok"}
#         else:
#             return {"status": "error", "message": "User not found"}, 404

# # --- API GỬI TIN NHẮN (BROADCAST / CHANNEL) ---
# @app.route("/broadcast-peer", methods=["POST"])
# def broadcast_peer(headers, body):
#     """Gửi tin nhắn vào Kênh (Channel)"""
#     data = _parse_body(body)
#     channel = data.get("channel")
#     msg = data.get("msg") or data.get("message")
#     sender = data.get("sender")

#     if not channel or not msg:
#         return {"status": "error", "message": "Missing info"}, 400

#     with _lock:
#         # Lấy danh sách thành viên trong kênh
#         members = _channels.get(channel, [])
        
#         # Gửi tin nhắn cho TẤT CẢ thành viên (trừ người gửi)
#         for member in members:
#             if member != sender and member in _peers:
#                 _inbox[member].append({
#                     "sender": channel, # Người gửi hiển thị là Tên Kênh
#                     "real_sender": sender, # Người thực gửi
#                     "msg": f"{sender}: {msg}", # Format tin nhắn: "Hung: hello"
#                     "type": "channel"
#                 })
        
#         print(f"[Channel] {sender} -> {channel}: {msg}")

#     return {"status": "ok"}

# # --- API NHẬN TIN NHẮN (POLLING) ---
# @app.route("/get-messages", methods=["GET"])
# def get_messages(headers, body):
#     """
#     Client polling để lấy tin mới.
#     Cách lấy username: Client JS (WeApRous) gửi query trong Header hoặc Body.
#     Với GET request, ta check Header 'Query' (do WeApRous client cũ) 
#     HOẶC đơn giản nhất: Sửa JS để gửi request POST kèm peer_id.
    
#     TUY NHIÊN: Để khớp với script.js hiện tại (dùng GET), ta sẽ hack nhẹ:
#     Lấy tin nhắn dựa vào tham số query trong header (nếu có)
#     Hoặc giả định client gửi đúng.
    
#     FIX: Tốt nhất là script.js nên gọi POST /get-messages-post
#     Nhưng ở đây tôi sẽ xử lý cả 2 trường hợp.
#     """
#     # Xử lý Header custom của WeApRous (nếu có)
#     # Ví dụ Header: Query: channel=Hung
#     user_to_check = None
#     try:
#         # Thử parse header Query nếu client gửi lên
#         if isinstance(headers, dict):
#             q = headers.get("Query", "") # "channel=Hung"
#             if "channel=" in q:
#                 user_to_check = q.split("=")[1]
#     except: pass

#     # Nếu không có trong header, ta trả về rỗng (Client JS sẽ cần sửa lại gửi POST tốt hơn)
#     # Nhưng đợi đã, script.js của bạn đang gọi: 
#     # fetch('/get-messages', { headers: { 'Query': `channel=${currentTarget}` } })
#     # Vấn đề là: get-messages này dùng để lấy tin INBOX của CURRENT USER,
#     # Chứ không phải lấy tin của channel.
    
#     # ==> QUYẾT ĐỊNH: Chúng ta sẽ dùng POST cho get-messages trong Script.js (đã sửa ở bước trước)
#     # Ở đây tôi define route POST cho chắc ăn.
#     return []

# @app.route("/get-messages", methods=["POST"])
# def get_messages_post(headers, body):
#     """Lấy tin nhắn từ Inbox (Dùng POST để gửi peer_id an toàn)"""
#     data = _parse_body(body)
#     peer_id = data.get("peer_id")
    
#     messages = []
#     if peer_id:
#         with _lock:
#             if peer_id in _inbox and _inbox[peer_id]:
#                 # Lấy hết tin nhắn ra và xóa khỏi hàng đợi
#                 messages = _inbox[peer_id][:]
#                 _inbox[peer_id] = []
                
#     # Format lại cho đúng chuẩn JS mong đợi
#     # JS mong đợi: { messages: [ {sender, message} ] }
#     formatted_msgs = []
#     for m in messages:
#         formatted_msgs.append({
#             "sender": m["sender"],
#             "message": m["msg"]
#         })

#     return {"status": "ok", "messages": formatted_msgs}


# # --- MAIN ---
# if __name__ == "__main__":
#     parser = argparse.ArgumentParser()
#     parser.add_argument("--server-ip", default="0.0.0.0")
#     parser.add_argument("--server-port", type=int, default=PORT)
#     args = parser.parse_args()
    
#     app.prepare_address(args.server_ip, args.server_port)
#     app.run()

























# import argparse
# import json
# import socket
# import threading
# from collections import defaultdict
# from typing import Dict, Tuple

# from daemon.weaprous import WeApRous

# PORT = 8000
# app = WeApRous()

# # --- DATABASE GIẢ LẬP ---
# _peers: Dict[str, Dict] = {}
# # Mặc định có sẵn kênh General
# _channels: Dict[str, list] = {"General": []} 
# _inbox: Dict[str, list] = defaultdict(list)
# _lock = threading.Lock()

# def _parse_body(body):
#     if isinstance(body, dict): return body
#     if not body: return {}
#     try: return json.loads(body)
#     except: return {}

# # --- API ROUTES ---

# @app.route("/login", methods=["POST"])
# def login(headers="guest", body="anonymous"):
#     data = _parse_body(body)
#     username = data.get("username") or data.get("peer_id")
#     password = data.get("password")
#     ip = data.get("ip") or "127.0.0.1"
#     port = data.get("port")

#     print(f"[Auth] Login: user={username} port={port}")

#     # Task 1: Admin
#     if username == "admin" and password == "password":
#         with _lock:
#             # THÊM DÒNG NÀY: Để Admin cũng hiện lên danh sách online
#             _peers["admin"] = {"name": "admin", "ip": ip, "port": port}
#             # Thêm vào kênh General
#             if "admin" not in _channels["General"]:
#                 _channels["General"].append("admin")
        
#         return "LOGIN_SUCCESS" # Trả về để set Cookie (Task 1)

#     # Task 2: Peer
#     if username and password == "password":
#         with _lock:
#             _peers[username] = {
#                 "name": username,
#                 "ip": ip, 
#                 "port": port
#             }
#             # Tự động thêm user vào kênh General
#             if username not in _channels["General"]:
#                 _channels["General"].append(username)
                
#         return {"status": "ok", "peer_id": username}
    
#     return {"status": "error", "message": "Invalid credentials"}, 401

# @app.route("/get-list", methods=["POST", "GET"])
# def get_list(headers, body):
#     """Trả về danh sách tất cả peer đang online"""
#     with _lock:
#         peer_list = list(_peers.values())
#     return {"status": "ok", "peers": peer_list}

# @app.route("/send-peer", methods=["POST"])
# def send_peer(headers, body):
#     """Gửi tin nhắn riêng (Direct)"""
#     data = _parse_body(body)
#     target = data.get("target") or data.get("peer", {}).get("name")
#     sender = data.get("sender")
#     msg = data.get("msg") or data.get("message")

#     if not target or not msg: return {"status": "error"}, 400

#     # Chặn gửi cho chính mình
#     if target == sender: return {"status": "error", "message": "Self-message"}, 403

#     # --- 1. XỬ LÝ LỆNH ADMIN /KICK ---
#     if msg.startswith("/kick"):
#         # Chỉ Admin được dùng
#         if sender != "admin":
#             return {"status": "error", "message": "Access Denied: Only admin can kick"}, 403
        
#         # Lấy tên người bị kick: /kick user123
#         parts = msg.split(" ")
#         if len(parts) < 2:
#             return {"status": "error", "message": "Usage: /kick <username>"}, 400
            
#         user_to_kick = parts[1]
        
#         with _lock:
#             if user_to_kick in _peers:
#                 del _peers[user_to_kick] # Xóa khỏi danh sách online
#                 # Xóa khỏi kênh General
#                 if user_to_kick in _channels["General"]:
#                     _channels["General"].remove(user_to_kick)
                    
#                 print(f"[Admin] Kicked user: {user_to_kick}")
#                 return {"status": "ok", "message": f"User {user_to_kick} has been kicked."}
#             else:
#                 return {"status": "error", "message": "User not found"}, 404
    
#     # --- 2. XỬ LÝ GỬI TIN NHẮN THƯỜNG ---
#     # (Đoạn này đã được đưa ra ngoài block if /kick)
#     with _lock:
#         if target in _peers:
#             _inbox[target].append({
#                 "sender": sender,
#                 "msg": msg,
#                 "type": "direct", # Đánh dấu là tin direct
#                 "timestamp": "now"
#             })
#             print(f"[Direct] {sender} -> {target}: {msg}")
#             return {"status": "ok"}
#         else:
#             return {"status": "error", "message": "User offline"}, 404

# @app.route("/broadcast-peer", methods=["POST"])
# def broadcast_peer(headers, body):
#     """Gửi tin nhắn vào kênh General (Broadcast)"""
#     data = _parse_body(body)
#     channel = "General" # Mặc định luôn là General
#     msg = data.get("msg") or data.get("message")
#     sender = data.get("sender")

#     if not msg: return {"status": "error"}, 400

#     with _lock:
#         # Lấy danh sách tất cả peer đang online
#         all_peers = list(_peers.keys())
        
#         for p in all_peers:
#             if p != sender:
#                 _inbox[p].append({
#                     "sender": channel, # Người gửi hiển thị là 'General'
#                     "real_sender": sender,
#                     "msg": f"{sender}: {msg}",
#                     "type": "channel"
#                 })
#         print(f"[Broadcast] {sender} -> All: {msg}")

#     return {"status": "ok"}

# @app.route("/get-messages", methods=["POST"])
# def get_messages(headers, body):
#     data = _parse_body(body)
#     peer_id = data.get("peer_id")
#     messages = []
#     if peer_id:
#         with _lock:
#             if peer_id in _inbox:
#                 messages = _inbox[peer_id][:]
#                 _inbox[peer_id] = []
    
#     # Format lại
#     formatted = [{"sender": m["sender"], "message": m["msg"]} for m in messages]
#     return {"status": "ok", "messages": formatted}

# if __name__ == "__main__":
#     parser = argparse.ArgumentParser()
#     parser.add_argument("--server-ip", default="0.0.0.0")
#     parser.add_argument("--server-port", type=int, default=PORT)
#     args = parser.parse_args()
#     app.prepare_address(args.server_ip, args.server_port)
#     app.run()
    
    


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