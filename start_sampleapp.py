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


@app.route('/login', methods=['POST'])
def login(headers, body):
    """
    Xử lý đăng nhập.
    Trả về chuỗi đặc biệt "LOGIN_SUCCESS" hoặc "LOGIN_FAILED" 
    để httpadapter.py nhận diện và set cookie.
    """
    try:
        # 1. Parse dữ liệu từ body (Client gửi lên dạng JSON)
        # Body có thể là bytes hoặc string tùy vào quá trình đọc
        if isinstance(body, bytes):
            body_str = body.decode("utf-8")
        else:
            body_str = str(body)

        # Parse JSON
        data = json.loads(body_str) if body_str else {}
        
        username = data.get("username")
        password = data.get("password")

        # 2. Kiểm tra thông tin (Hardcode: admin/password)
        if username == "admin" and password == "password":
            # QUAN TRỌNG: Phải trả về đúng chuỗi này để khớp với logic trong httpadapter.py
            return "LOGIN_SUCCESS"
        else:
            return "LOGIN_FAILED"

    except Exception as e:
        print(f"[Login Error] {e}")
        return "LOGIN_FAILED"


@app.route("/", methods=["GET"])
def index(headers="", body=""):
    """
    Trang chủ (Protected).
    Chỉ hiển thị nếu request có cookie auth=true (Task 1B).
    """
    # 1. Lấy Cookie từ headers
    # headers thường là dict (CaseInsensitiveDict), ta lấy chuỗi Cookie ra
    cookie_header = headers.get("Cookie", "") if isinstance(headers, dict) else ""
    
    # 2. Kiểm tra auth=true có trong chuỗi cookie không
    if "auth=true" not in cookie_header:
        # Nếu chưa đăng nhập -> Trả về lỗi 401 Unauthorized
        return "<h1>401 Unauthorized - Please Login First</h1>", 401

    # 3. Nếu đã có cookie -> Đọc và trả về file index.html như cũ
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

    print("DEBUG PEERS:", PEERS)
    print("DEBUG CHANNELS:", CHANNELS)
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
    print("RAW BODY:", body)
    """
    body = {
        "channel": "Game",
        "peer": {"name":"Hung", "ip":"127.0.0.1", "port":9001}
    }
    """
    data = _safe_json(body)
    channel = data.get("channel")
    print("CHANNEL:", channel)
    peer = data.get("peer")
    print("PEER:", peer)

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

@app.route('/broadcast-peer', methods=['POST'])
def broadcast_peer(headers, body):
    print("RAW BODY:", body)

    try:
        data = _safe_json(body)

        channel = data.get('channel')
        msg = data.get('msg')
        sender = data.get('sender', 'tracker')

        print("CHANNEL:", channel)
        print("MSG:", msg)
        print("SENDER:", sender)

        if not channel or msg is None:
            return json.dumps({"status": "error", "message": "channel and msg required"})

        with lock:
            # 🔥 Tự tạo channel nếu chưa có
            if channel not in CHANNELS:
                print(f"[INFO] Creating new channel: {channel}")
                CHANNELS[channel] = []

            # 🔥 Lưu tin nhắn vào channel chung
            MESSAGES.setdefault(channel, [])
            entry = {"sender": sender, "msg": msg}
            MESSAGES[channel].append(entry)

            print(f"[INFO] Message appended to channel '{channel}':", entry)

        print("DEBUG CHANNELS:", CHANNELS)
        print("DEBUG MESSAGES:", MESSAGES)
        # Trả lại kết quả
        return json.dumps({
            "status": "ok",
            "channel": channel,
            "msg": msg,
            "sender": sender
        })

    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)})


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
    print("RAW BODY:", body)
    data = _safe_json(body)
    print("PARSED DATA:", data)
    sender = data.get("sender")
    print("SENDER:", sender)
    target = data.get("target")
    print("TARGET:", target)
    msg = data.get("msg")
    print("MSG:", msg)

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
