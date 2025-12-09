import argparse
import socket
import threading
import json
import time
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
        # connection mapping: (ip,port) -> socket
        self.connections = {}
        self.lock = threading.Lock()
        self.running = False

        # channels: channel_name -> set((ip,port))
        self.channels = {}
        self.unread = {}

    # ----- tracker interactions -----
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

    def add_self_to_channel(self, channel_name):
        """Call /add-list to announce membership and receive channel peer list."""
        status, resp = http_post_json(
            self.tracker,
            '/add-list',
            {'channel': channel_name, 'peer': {'name': self.name, 'ip': self.ip, 'port': self.port}},
            timeout=5
        )
        if status != 200 or not isinstance(resp, dict):
            print(f"[peer] join_channel: tracker returned {status} resp={resp}")
            return set()
        peers = resp.get('peers', [])
        result = set()
        for p in peers:
            try:
                result.add((p['ip'], int(p['port'])))
            except Exception:
                continue
        # remove self
        result.discard((self.ip, self.port))
        return result

    # ----- channel operations -----
    def join_channel(self, channel_name):
        with self.lock:
            if channel_name in self.channels:
                print(f"[peer] already joined channel '{channel_name}'")
                return
            self.channels[channel_name] = set()
            self.unread[channel_name] = 0

        peers = self.add_self_to_channel(channel_name)
        with self.lock:
            self.channels[channel_name].update(peers)

        # connect to peers in the channel
        for ip, port in list(peers):
            if (ip, port) == (self.ip, self.port):
                continue
            self.connect_to_peer(ip, port)

        print(f"[peer] Joined channel '{channel_name}' peers={self.channels[channel_name]}")

    # ----- networking: server accept / recv -----
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
                conn.settimeout(3)
                print(f"[peer] Accepted connection from {addr}")
                threading.Thread(target=self._handle_incoming_conn, args=(conn,), daemon=True).start()
            except Exception as e:
                # print and continue
                print('[peer] accept error', e)

    def _handle_incoming_conn(self, conn):
        """Handle a newly accepted socket. The peer is expected to send a HELLO message
        immediately that tells us its listening ip/port. After that we continue reading
        newline-delimited JSON messages.
        """
        buf = b''
        remote_key = None
        try:
            # receive until we get a newline
            while True:
                try:
                    chunk = conn.recv(4096)
                except socket.timeout:
                    # keep waiting for initial hello for a little while
                    continue
                if not chunk:
                    return
                buf += chunk
                if b'\n' in buf:
                    line, buf = buf.split(b'\n', 1)
                    try:
                        msg = json.loads(line.decode('utf-8'))
                    except Exception:
                        # initial message malformed; ignore
                        return
                    # Expect a hello message:
                    if msg.get('type') == 'hello' and 'ip' in msg and 'port' in msg:
                        try:
                            remote_key = (msg['ip'], int(msg['port']))
                        except Exception:
                            return
                        with self.lock:
                            # store connection mapped to remote_key
                            self.connections[remote_key] = conn
                        # after hello, process any buffered remainder (buf)
                        if buf:
                            # push remainder back to processing loop
                            pass
                        break
                    else:
                        # If first message isn't hello, try to infer remote ip/port
                        addr = None
                        try:
                            addr = conn.getpeername()
                        except Exception:
                            addr = None
                        if addr:
                            remote_key = (addr[0], None)
                            # we cannot know remote listening port, so we do not map by listening-port key
                            # We'll still process messages but cannot send targeted channel messages unless a matching connection exists
                        # Process this first message as normal
                        self._handle_incoming_message(msg, conn)
                        break
            # Now enter normal receive loop processing newline-delimited JSON
            while True:
                try:
                    if b'\n' in buf:
                        line, buf = buf.split(b'\n', 1)
                        try:
                            msg = json.loads(line.decode('utf-8'))
                        except Exception:
                            continue
                        self._handle_incoming_message(msg, conn)
                        continue
                    chunk = conn.recv(4096)
                    if not chunk:
                        break
                    buf += chunk
                except socket.timeout:
                    continue
                except Exception:
                    break
        finally:
            try:
                conn.close()
            except Exception:
                pass
            if remote_key:
                with self.lock:
                    # remove mapping only if same object
                    existing = self.connections.get(remote_key)
                    if existing is conn:
                        self.connections.pop(remote_key, None)
            print(f"[peer] Connection closed {remote_key or 'unknown'}")

    def _handle_incoming_message(self, msg, conn_or_key):
        # msg is a dict
        t = msg.get('type')
        if t == 'chat':
            channel = msg.get('channel', 'default')
            sender = msg.get('sender', 'unknown')
            text = msg.get('msg', '')
            print(f"[chat][{channel}] {sender}: {text}")
            self.notify_incoming(channel)
        else:
            # ignore other message types for now
            pass

    # ----- outgoing connection + recv thread -----
    def connect_to_peer(self, ip, port, retries=3, delay=0.6):
        key = (ip, int(port))
        with self.lock:
            if key in self.connections:
                return True
        for attempt in range(retries):
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.settimeout(3)
                s.connect((ip, int(port)))
                s.settimeout(None)
                # store connection
                with self.lock:
                    self.connections[key] = s
                # send hello so receiving side can map socket to (ip,port)
                hello = {'type': 'hello', 'name': self.name, 'ip': self.ip, 'port': self.port}
                s.sendall((json.dumps(hello) + '\n').encode('utf-8'))
                # start recv loop in background
                threading.Thread(target=self._recv_loop, args=(s, key), daemon=True).start()
                print(f"[peer] Connected to peer {ip}:{port}")
                return True
            except Exception as e:
                print(f"[peer] connect_to_peer {ip}:{port} attempt {attempt+1} failed: {e}")
                try:
                    s.close()
                except Exception:
                    pass
                time.sleep(delay)
        return False

    def _recv_loop(self, s, key):
        s.settimeout(1)
        buf = b''
        try:
            while True:
                try:
                    chunk = s.recv(4096)
                except socket.timeout:
                    continue
                if not chunk:
                    break
                buf += chunk
                while b'\n' in buf:
                    line, buf = buf.split(b'\n', 1)
                    try:
                        msg = json.loads(line.decode('utf-8'))
                    except Exception:
                        continue
                    # handle message
                    self._handle_incoming_message(msg, key)
        except Exception as e:
            # print('[peer] recv loop error', e)
            pass
        finally:
            with self.lock:
                try:
                    existing = self.connections.get(key)
                    if existing is s:
                        self.connections.pop(key, None)
                except Exception:
                    pass
            try:
                s.close()
            except Exception:
                pass
            print('[peer] remote closed', key)

    # ----- sending -----
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
                self.connections.pop(k, None)

    def broadcast_channel(self, channel, text):
        with self.lock:
            peers = set(self.channels.get(channel, set()))
            conns = dict(self.connections)

        msg = {'type': 'chat', 'sender': self.name, 'channel': channel, 'msg': text}
        raw = (json.dumps(msg) + '\n').encode('utf-8')

        for peer in peers:
            s = conns.get(peer)
            if s:
                try:
                    s.sendall(raw)
                except Exception as e:
                    print('[peer] send error channel', peer, e)

    # ----- background refresh -----
    def refresh_peers_loop(self, interval=3):
        def loop():
            while self.running:
                try:
                    # optional: ensure we're connected to global peers so broadcasts (no-channel) reach others
                    peer_list = self.get_peer_list()
                    for p in peer_list:
                        try:
                            k = (p['ip'], int(p['port']))
                        except Exception:
                            continue
                        if k == (self.ip, self.port):
                            continue
                        with self.lock:
                            already = k in self.connections
                        if not already:
                            # connect in background
                            threading.Thread(target=self.connect_to_peer, args=(k[0], k[1]), daemon=True).start()

                    # sync channels: for each channel we joined, ask tracker for peer list
                    with self.lock:
                        channels = list(self.channels.keys())
                    for ch in channels:
                        peers = self.add_self_to_channel(ch)
                        with self.lock:
                            self.channels[ch] = peers
                        # connect to channel peers
                        for ip, port in list(peers):
                            with self.lock:
                                if (ip, port) not in self.connections and (ip, port) != (self.ip, self.port):
                                    threading.Thread(target=self.connect_to_peer, args=(ip, port), daemon=True).start()

                except Exception as e:
                    print('[peer] refresh error', e)
                time.sleep(interval)
        threading.Thread(target=loop, daemon=True).start()

    # ----- helpers / CLI -----
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
        print("Commands:\n  /join <channel>\n  /channel <channel> <msg>\n  /list\n  /quit\n  (plain text -> broadcast)")
        while True:
            try:
                line = input()
            except EOFError:
                break
            if not line:
                continue
            if line.startswith('/join '):
                channel = line.split(' ', 1)[1].strip()
                self.join_channel(channel)
                continue
            if line.startswith('/channel '):
                parts = line.split(' ', 2)
                if len(parts) < 3:
                    print('Usage: /channel <channel> <msg>')
                    continue
                channel, msg = parts[1], parts[2]
                if channel not in self.channels:
                    print(f"Not joined in channel '{channel}'. Use /join {channel} first.")
                    continue
                self.broadcast_channel(channel, msg)
                self.mark_read(channel)
                continue
            if line.strip() == '/list':
                entries = self.list_channels()
                print('Channels summary:')
                for ch, n_peers, unread, peers in entries:
                    print(f"  {ch} | peers={n_peers} | unread={unread}")
                    if n_peers:
                        print('    peers:', peers)
                with self.lock:
                    print('Connections:', list(self.connections.keys()))
                continue
            if line.strip() == '/quit':
                break
            # plain broadcast to all connections
            self.broadcast(line.strip())
        self.shutdown()

    def shutdown(self):
        print('[peer] shutting down...')
        self.running = False
        try:
            if self.server:
                self.server.close()
        except Exception:
            pass
        with self.lock:
            for s in list(self.connections.values()):
                try:
                    s.close()
                except Exception:
                    pass
            self.connections.clear()

    def list_channels(self):
        with self.lock:
            lines = []
            for ch, peers in self.channels.items():
                unread = self.unread.get(ch, 0)
                lines.append((ch, len(peers), unread, list(peers)))
            return lines

    def notify_incoming(self, channel):
        with self.lock:
            self.unread[channel] = self.unread.get(channel, 0) + 1
        print(f"[notify][{channel}] New message (unread={self.unread[channel]})")

    def mark_read(self, channel):
        with self.lock:
            self.unread[channel] = 0


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--ip', default='127.0.0.1')
    parser.add_argument('--port', type=int, required=True)
    parser.add_argument('--tracker', default='http://127.0.0.1:8000')
    parser.add_argument('--name', default=None)
    args = parser.parse_args()

    name = args.name or f"peer-{args.port}"
    node = PeerNode(name, args.ip, args.port, args.tracker)

    # start server first
    node.start_server()

    # register to tracker before joining channels
    for i in range(3):
        try:
            ok = node.register_to_tracker()
            if ok:
                break
        except Exception as e:
            print('[peer] register error', e)
        time.sleep(1)

    # background refresh
    node.refresh_peers_loop()

    # connect to any known peers (optional)
    node.connect_to_all()

    # join default channel after register
    node.join_channel('general')

    try:
        node.interactive_loop()
    except KeyboardInterrupt:
        node.shutdown()


if __name__ == '__main__':
    main()
