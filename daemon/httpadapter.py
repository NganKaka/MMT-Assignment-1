
#demo 

import json
from .request import Request
from .response import Response
from .dictionary import CaseInsensitiveDict

class HttpAdapter:
    __attrs__ = [
        "ip",
        "port",
        "conn", 
        "connaddr",
        "routes",
        "request",
        "response"
    ]

    def __init__(self, ip, port, conn, connaddr, routes):
        self.ip = ip
        self.port = port
        self.conn = conn
        self.connaddr = connaddr
        self.routes = routes
        self.request = Request()
        self.response = Response()
    
    def handle_client(self, conn, addr, routes):
        self.conn = conn        
        self.connaddr = addr
        req = self.request
        resp = self.response

        # --- 1. ĐỌC REQUEST (Giữ nguyên logic cũ) ---
        data = b""
        chunk = conn.recv(4096)
        if not chunk:
            conn.close()
            return
        data += chunk
        while b"\r\n\r\n" not in data:
            chunk = conn.recv(4096)
            if not chunk: break
            data += chunk

        header_part, sep, body_part = data.partition(b"\r\n\r\n")
        headers_text = header_part.decode("utf-8", errors="replace")

        content_length = 0
        for line in headers_text.splitlines():
            if line.lower().startswith("content-length:"):
                try:
                    content_length = int(line.split(":", 1)[1].strip())
                except: pass
                break

        body_bytes = body_part
        remaining = content_length - len(body_bytes)
        while remaining > 0:
            chunk = conn.recv(4096)
            if not chunk: break
            body_bytes += chunk
            remaining = content_length - len(body_bytes)

        try:
            full_msg = headers_text + "\r\n\r\n" + body_bytes.decode("utf-8", errors="replace")
        except:
            full_msg = headers_text + "\r\n\r\n"

        req.body = body_bytes
        req.prepare(full_msg, routes)
        
        # --- 2. SECURITY CHECK (Kiểm tra Auth cho index.html) ---
        if req.path == '/index.html':
            # Debug: In ra cookie nhận được để kiểm tra
            print(f"[Security] Checking cookie for /index.html. Cookies: {req.cookies}")
            if not (req.cookies and req.cookies.get('auth') == 'true'):
                response = resp.build_unauthorized()
                conn.sendall(response)
                conn.close()
                return
        
        # --- 3. XỬ LÝ HOOK (Login / Chat API) ---
        if req.hook:
            print("[HttpAdapter] hook in route-path METHOD {} PATH {}".format(req.hook._route_path, req.hook._route_methods))
            
            hook_headers = getattr(req, "headers", {}) or {}
            hook_body = req.body.decode("utf-8", errors="replace") if isinstance(req.body, (bytes, bytearray)) else (req.body or "")
            
            # Gọi hàm xử lý (login, send_peer...)
            hook_result = req.hook(headers=hook_headers, body=hook_body)

            status_code = 200
            body_obj = hook_result

            if isinstance(hook_result, tuple) and len(hook_result) == 2:
                body_obj, status_code = hook_result

            # --- QUAN TRỌNG: XỬ LÝ COOKIE ---
            if hook_result == "LOGIN_SUCCESS":
                # Set cookie với Path=/ để có hiệu lực toàn trang
                resp.headers['Set-Cookie'] = 'auth=true; Path=/'
                resp.status_code = 200 
                resp.reason = "OK"
                body_obj = {"status": "Login Successful", "role": "admin"}

            # Chuẩn bị nội dung trả về
            if isinstance(body_obj, dict):
                payload = json.dumps(body_obj).encode("utf-8")
                content_type = "application/json"
            elif isinstance(body_obj, bytes):
                payload = body_obj
                content_type = "application/octet-stream"
            else:
                payload = str(body_obj).encode("utf-8")
                content_type = "text/html" if str(body_obj).strip().startswith("<") else "text/plain"

            reasons = {200: "OK", 400: "Bad Request", 401: "Unauthorized", 403: "Forbidden", 404: "Not Found"}
            reason = reasons.get(status_code, "OK")
            
            # --- SỬA LỖI: TẠO HEADER ĐẦY ĐỦ (BAO GỒM COOKIE) ---
            header_lines = [
                f"HTTP/1.1 {status_code} {reason}",
                f"Content-Type: {content_type}",
                f"Content-Length: {len(payload)}"
            ]
            
            # Chèn thêm các header phụ (như Set-Cookie) từ resp.headers
            for key, value in resp.headers.items():
                header_lines.append(f"{key}: {value}")
            
            # Kết thúc header bằng dòng trống
            header_str = "\r\n".join(header_lines) + "\r\n\r\n"
            
            conn.sendall(header_str.encode("utf-8") + payload)
            conn.close()
            return

        # --- 4. STATIC FILES ---
        if not hasattr(resp, 'status_code') or resp.status_code is None:
            resp.status_code = 200
        if not hasattr(resp, 'reason') or resp.reason is None:
            resp.reason = "OK"
            
        response = resp.build_response(req)
        conn.sendall(response)
        conn.close()

    @property
    def extract_cookies(self, req, resp):
        """
        Build cookies from the :class:`Request <Request>` headers.
        (Fixed using Task 2.2 implementation which is correct)
        """
        cookies = {}
        # Uses req.headers which is a CaseInsensitiveDict or dict
        if hasattr(req, 'headers') and req.headers:
            for header, value in req.headers.items():
                if header.lower() == "cookie":
                    # value format: "key=val; key2=val2"
                    for pair in value.split(";"):
                        if "=" in pair:
                            k, v = pair.strip().split("=", 1)
                            cookies[k] = v
        return cookies

    def build_response(self, req, resp):
        """Builds a :class:`Response <Response>` object"""
        response = Response()

        # Set encoding (Simplification: Default to utf-8 if helper not found)
        # response.encoding = get_encoding_from_headers(response.headers)
        response.encoding = 'utf-8'
        
        response.raw = resp
        response.reason = response.raw.reason

        if isinstance(req.url, bytes):
            response.url = req.url.decode("utf-8")
        else:
            response.url = req.url

        # Add new cookies from the server.
        # Note: calling self.extract_cookies because it is a property/method of Adapter
        # But wait, extract_cookies is usually to READ cookies from request.
        # response.cookies should store Set-Cookie.
        # For this assignment, we just map request cookies to response context if needed.
        response.cookies = self.extract_cookies(req, resp)

        # Give the Response some context.
        response.request = req
        response.connection = self

        return response

    def add_headers(self, request):
        pass

    def build_proxy_headers(self, proxy):
        headers = {}
        username, password = ("user1", "password")
        if username:
            headers["Proxy-Authorization"] = (username, password)
        return headers