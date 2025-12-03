"""peer_network.py

Simple peer-to-peer node logic for the assignment.
Usage (example):
  python apps/peer_network.py --ip 127.0.0.1 --port 10001 --tracker http://127.0.0.1:8000 --name peer1

Behavior:
- Registers itself with tracker (POST /submit-info)
- Requests peer list from tracker (GET /get-list)
- Starts a TCP server to accept connections from peers
- Connects to peers from tracker list (avoids connecting to self)
- Provides interactive terminal input to send broadcast messages
- Received messages are printed to console

Message format (JSON, newline-delimited):
  { "type": "chat", "sender": "<name>", "msg": "<text>" }

Notes:
- This is a lightweight reference implementation to demonstrate P2P chat logic.
- The tracker is the webapp provided in apps/chatapp.py (runs on port 8000 by default).
"""

import argparse
import socket
import threading
import json
import time
import sys
from urllib.parse import urlparse

import http.client

def http_post_json(url, path, data, timeout=5):
    p = urlparse(url)
    conn = http.client.HTTPConnection(p.hostname, p.port or 80, timeout=timeout)
    body = json.dumps(data)
    headers = {'Content-Type': 'application/json'}
    conn.request('POST', path, body=body, headers=headers)
    resp = conn.getresponse()
    content = resp.read().decode('utf-8')
    try:
        return resp.status, json.loads(content) if content else None
    except Exception:
        return resp.status, content

def http_get_json(url, path, timeout=5):
    p = urlparse(url)
    conn = http.client.HTTPConnection(p.hostname, p.port or 80, timeout=timeout)
    conn.request('GET', path)
    resp = conn.getresponse()
    content = resp.read().decode('utf-8')
    try:
        return resp.status, json.loads(content) if content else None
    except Exception:
        return resp.status, content

class PeerNode:
    def __init__(self, name, ip, port, tracker_url):
        self.name = name
        self.ip = ip
        self.port = int(port)
        self.tracker = tracker_url.rstrip('/')
        self.server = None
        self.connections = {}  # (ip,port) -> socket
        self.lock = threading.Lock()
        self.running = False

    def register_to_tracker(self):
        data = {'name': self.name, 'ip': self.ip, 'port': self.port}
        status, resp = http_post_json(self.tracker, '/submit-info', data)
        print(f"[tracker] register status={status} resp={resp}")
        return status == 200

    def get_peer_list(self):
        status, resp = http_get_json(self.tracker, '/get-list')
        if status == 200 and isinstance(resp, list):
            return resp
        return []

    def start_server(self):
        print('[peer] starting server...')
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server.bind((self.ip, self.port))
        self.server.listen(5)
        self.running = True
        threading.Thread(target=self._accept_loop, daemon=True).start()
        print(f"[peer] Listening on {self.ip}:{self.port}")

    def _accept_loop(self):
        while self.running:
            try:
                conn, addr = self.server.accept()
                print(f"[peer] Accepted connection from {addr}")
                threading.Thread(target=self._handle_conn, args=(conn, addr), daemon=True).start()
            except Exception as e:
                print('[peer] accept error', e)

    def _handle_conn(self, conn, addr):
        with conn:
            buf = b''
            while True:
                try:
                    data = conn.recv(4096)
                    if not data:
                        break
                    buf += data
                    # simple newline-delimited JSON messages
                    while b'\n' in buf:
                        line, buf = buf.split(b'\n', 1)
                        try:
                            msg = json.loads(line.decode('utf-8'))
                            self.on_message(msg, addr)
                        except Exception as e:
                            print('[peer] parse error', e)
                except Exception as e:
                    print('[peer] connection error', e)
                    break
        print(f"[peer] Connection closed {addr}")

    def on_message(self, msg, addr):
        # handle incoming message
        t = msg.get('type')
        if t == 'chat':
            sender = msg.get('sender', str(addr))
            text = msg.get('msg', '')
            print(f"[chat] {sender}: {text}")
        else:
            print('[peer] unknown msg', msg)

    def connect_to_peer(self, ip, port, retries=5, delay=1):
        key = (ip, int(port))
        if key in self.connections:
            return True
        # try:
        #     s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        #     s.settimeout(5)
        #     s.connect((ip, int(port)))
        #     s.settimeout(None)
        #     with self.lock:
        #         self.connections[key] = s
        #     # start a receiver thread for this connection
        #     threading.Thread(target=self._recv_loop, args=(s, key), daemon=True).start()
        #     print(f"[peer] Connected to peer {ip}:{port}")
        #     return True
        # except Exception as e:
        #     print(f"[peer] connect_to_peer {ip}:{port} failed: {e}")
        #     return False
        for attempt in range(retries):
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.settimeout(5)
                s.connect((ip, int(port)))
                s.settimeout(None)
                with self.lock:
                    self.connections[key] = s
                threading.Thread(target=self._recv_loop, args=(s, key), daemon=True).start()
                print(f"[peer] Connected to peer {ip}:{port}")
                return True
            except Exception as e:
                print(f"[peer] connect_to_peer {ip}:{port} attempt {attempt+1} failed: {e}")
                time.sleep(delay)
        return False

    def _recv_loop(self, s, key):
        # reading messages sent back from this socket
        try:
            buf = b''
            while True:
                data = s.recv(4096)
                if not data:
                    break
                buf += data
                while b'\n' in buf:
                    line, buf = buf.split(b'\n', 1)
                    try:
                        msg = json.loads(line.decode('utf-8'))
                        self.on_message(msg, key)
                    except Exception as e:
                        print('[peer] parse recv error', e)
        except Exception as e:
            print('[peer] recv loop error', e)
        finally:
            print('[peer] remote closed', key)
            with self.lock:
                try:
                    del self.connections[key]
                except KeyError:
                    pass

    def broadcast(self, text):
        msg = {'type': 'chat', 'sender': self.name, 'msg': text}
        raw = (json.dumps(msg) + '\n').encode('utf-8')
        dead = []
        with self.lock:
            for k, s in list(self.connections.items()):
                try:
                    s.sendall(raw)
                except Exception as e:
                    print('[peer] send error to', k, e)
                    dead.append(k)
            for k in dead:
                try:
                    del self.connections[k]
                except KeyError:
                    pass

    def connect_to_all(self):
        peer_list = self.get_peer_list()
        for p in peer_list:
            try:
                if p.get('ip') == self.ip and int(p.get('port')) == self.port:
                    continue
                self.connect_to_peer(p.get('ip'), p.get('port'))
            except Exception:
                pass

    def interactive_loop(self):
        print('Type messages to broadcast to all connected peers. Type /list to show peers. /quit to exit.')
        while True:
            try:
                line = input()
            except EOFError:
                break
            if not line:
                continue
            if line.strip() == '/quit':
                break
            if line.strip() == '/list':
                with self.lock:
                    print('Connections:', list(self.connections.keys()))
                continue
            # broadcast
            self.broadcast(line.strip())
        self.shutdown()

    def shutdown(self):
        print('[peer] shutting down...')
        self.running = False
        try:
            if self.server:
                self.server.close()
        except:
            pass
        with self.lock:
            for s in list(self.connections.values()):
                try:
                    s.close()
                except:
                    pass
            self.connections.clear()

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--ip', default='127.0.0.1')
    parser.add_argument('--port', type=int, required=True)
    parser.add_argument('--tracker', default='http://127.0.0.1:8000')
    parser.add_argument('--name', default=None)
    args = parser.parse_args()
    name = args.name or f"peer-{args.port}"
    node = PeerNode(name, args.ip, args.port, args.tracker)
    node.start_server()
    # register to tracker
    registered = False
    for i in range(3):
        try:
            registered = node.register_to_tracker()
            if registered:
                break
        except Exception as e:
            print('[peer] register error', e)
        time.sleep(1)
    # get peers and connect
    print(f'[peer] fetching peer list...' + node.get_peer_list().__str__())
    # time.sleep(1)
    for _ in range(5):  # thử 5 lần, mỗi lần cách nhau 1 giây
        peers = node.get_peer_list()
        if any(p.get('ip') != node.ip or int(p.get('port')) != node.port for p in peers):
            break
        time.sleep(1)
    node.connect_to_all()
    # periodically refresh peer list and connect
    def refresh_loop():
        while node.running:
            try:
                time.sleep(3)
                node.connect_to_all()
            except Exception as e:
                print('[peer] refresh error', e)
    threading.Thread(target=refresh_loop, daemon=True).start()
    # interactive console
    try:
        node.interactive_loop()
    except KeyboardInterrupt:
        node.shutdown()

if __name__ == '__main__':
    main()