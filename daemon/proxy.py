import socket
import threading
from .response import *
from .httpadapter import HttpAdapter
from .dictionary import CaseInsensitiveDict

# Biến toàn cục để theo dõi lượt Round-Robin cho từng hostname
# Ví dụ: { 'app2.local': 1 }
RR_COUNTERS = {}
RR_LOCK = threading.Lock()

def forward_request(host, port, request):
    """
    Forwards an HTTP request to a backend server and retrieves the response.
    """
    backend = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        backend.connect((host, port))
        # Gửi request gốc đi
        backend.sendall(request.encode() if isinstance(request, str) else request)
        
        # Nhận response từ backend
        response = b""
        while True:
            chunk = backend.recv(4096)
            if not chunk:
                break
            response += chunk
        backend.close()
        return response
    except socket.error as e:
        print(f"[Proxy] Connection error to backend {host}:{port} - {e}")
        return (
            "HTTP/1.1 502 Bad Gateway\r\n"
            "Content-Type: text/plain\r\n"
            "Content-Length: 15\r\n"
            "Connection: close\r\n"
            "\r\n"
            "502 Bad Gateway"
        ).encode('utf-8')


def resolve_routing_policy(hostname, routes):
    """
    Handles routing policy (Round-Robin) to return the matching backend.
    """
    # Lấy thông tin từ routes (được parse từ start_proxy.py)
    # Mặc định trả về None nếu không tìm thấy host
    config = routes.get(hostname)
    
    if not config:
        print(f"[Proxy] Hostname '{hostname}' not found in routes.")
        return '127.0.0.1', 9000 # Dummy fallback

    proxy_map, policy = config
    proxy_host = '127.0.0.1'
    proxy_port = '9000'

    # Trường hợp 1: Có nhiều backend (List) -> Áp dụng Round Robin
    if isinstance(proxy_map, list) and len(proxy_map) > 0:
        if policy == 'round-robin':
            with RR_LOCK:
                # Lấy index hiện tại, mặc định là 0
                current_idx = RR_COUNTERS.get(hostname, 0)
                
                # Chọn backend dựa trên index
                selected = proxy_map[current_idx % len(proxy_map)]
                
                # Tăng index cho lần sau
                RR_COUNTERS[hostname] = (current_idx + 1) % len(proxy_map)
                
            print(f"[Proxy] Round-Robin selected: {selected} for {hostname}")
            parts = selected.split(":", 1)
            proxy_host = parts[0]
            proxy_port = parts[1] if len(parts) > 1 else 80
        else:
            # Nếu không phải round-robin, mặc định lấy cái đầu tiên
            selected = proxy_map[0]
            parts = selected.split(":", 1)
            proxy_host = parts[0]
            proxy_port = parts[1] if len(parts) > 1 else 80

    # Trường hợp 2: Chỉ có 1 backend (String)
    elif isinstance(proxy_map, str):
        parts = proxy_map.split(":", 1)
        proxy_host = parts[0]
        proxy_port = parts[1] if len(parts) > 1 else 80

    return proxy_host, proxy_port

def handle_client(ip, port, conn, addr, routes):
    """
    Handles an individual client connection.
    """
    try:
        # Đọc request từ client
        request_data = conn.recv(4096)
        if not request_data:
            conn.close()
            return

        request_text = request_data.decode('utf-8', errors='replace')
        
        # Extract hostname từ Header
        hostname = None
        for line in request_text.splitlines():
            if line.lower().startswith('host:'):
                raw_host = line.split(':', 1)[1].strip()
                # --- FIX LỖI: Tách bỏ port nếu có (vd: app2.local:8080 -> app2.local) ---
                if ':' in raw_host:
                    hostname = raw_host.split(':')[0]
                else:
                    hostname = raw_host
                break
        
        if not hostname:
            print(f"[Proxy] No Host header found from {addr}")
            conn.close()
            return

        print(f"[Proxy] Request for {hostname} from {addr}")

        # Resolve Destination
        resolved_host, resolved_port = resolve_routing_policy(hostname, routes)
        
        try:
            resolved_port = int(resolved_port)
        except ValueError:
            resolved_port = 80

        # Forward request
        if resolved_host:
            # print(f"[Proxy] Forwarding to {resolved_host}:{resolved_port}")
            response = forward_request(resolved_host, resolved_port, request_data)        
        else:
            response = b"HTTP/1.1 404 Not Found\r\n\r\nHost not mapped"

        conn.sendall(response)
        
    except Exception as e:
        print(f"[Proxy] Error handling client: {e}")
    finally:
        conn.close()

def run_proxy(ip, port, routes):
    proxy = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    proxy.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    try:
        proxy.bind((ip, port))
        proxy.listen(50)
        print("[Proxy] Listening on IP {} port {}".format(ip, port))
        
        while True:
            conn, addr = proxy.accept()
            # --- ĐÃ SỬA: THÊM MULTI-THREADING ---
            client_thread = threading.Thread(
                target=handle_client,
                args=(ip, port, conn, addr, routes)
            )
            client_thread.daemon = True
            client_thread.start()
            
    except socket.error as e:
      print("Socket error: {}".format(e))
    except KeyboardInterrupt:
        print("\n[Proxy] Shutting down...")
        proxy.close()

def create_proxy(ip, port, routes):
    run_proxy(ip, port, routes)