# import json
# from .request import Request
# from .response import Response
# from .dictionary import CaseInsensitiveDict

# class HttpAdapter:
#     __attrs__ = [
#         "ip",
#         "port",
#         "conn", 
#         "connaddr",
#         "routes",
#         "request",
#         "response"
#     ]

#     def __init__(self, ip, port, conn, connaddr, routes):
#         self.ip = ip
#         self.port = port
#         self.conn = conn
#         self.connaddr = connaddr
#         self.routes = routes
#         self.request = Request()
#         self.response = Response()
        
#     ########################################### Main function #################################
#     def handle_client(self, conn, addr, routes):
#         self.conn = conn        
#         self.connaddr = addr
#         req = self.request
#         resp = self.response

#         # Read headers (until \r\n\r\n), then read body according to Content-Length
#         data = b""
#         # initial read
#         chunk = conn.recv(4096)
#         if not chunk:
#             conn.close()
#             return
#         data += chunk
#         # wait until end of headers
#         while b"\r\n\r\n" not in data:
#             chunk = conn.recv(4096)
#             if not chunk:
#                 break
#             data += chunk

#         header_part, sep, body_part = data.partition(b"\r\n\r\n")
#         headers_text = header_part.decode("utf-8", errors="replace")

#         # parse Content-Length if any
#         content_length = 0
#         for line in headers_text.splitlines():
#             if line.lower().startswith("content-length:"):
#                 try:
#                     content_length = int(line.split(":", 1)[1].strip())
#                 except:
#                     content_length = 0
#                 break

#         # body_part may already contain some (or all) of the body; read remaining
#         body_bytes = body_part
#         remaining = content_length - len(body_bytes)
#         while remaining > 0:
#             chunk = conn.recv(4096)
#             if not chunk:
#                 break
#             body_bytes += chunk
#             remaining = content_length - len(body_bytes)

#         # build full message for Request.prepare (headers + body as text)
#         try:
#             full_msg = headers_text + "\r\n\r\n" + body_bytes.decode("utf-8", errors="replace")
#         except:
#             full_msg = headers_text + "\r\n\r\n"

#         # give Request the raw body bytes too
#         req.body = body_bytes
#         req.prepare(full_msg, routes)
#         req.prepare(full_msg, routes)
        
#         # Authorized?
#         if req.path == '/index.html':
#             if not (req.cookies and req.cookies.get('auth') == 'true'):
#                 response = resp.build_unauthorized()
#                 conn.sendall(response)
#                 conn.close()
#                 return
        
#         # --- Handle POST /login (Task 1 Cookie Session) when no custom route ---
#         if req.method == "POST" and req.path == "/login" and not req.hook:
#             body_str = req.body.decode("utf-8", errors="replace") if isinstance(req.body, (bytes, bytearray)) else str(req.body)
#             print(f"[Login] Received body: {body_str}")

#             if "username=admin" in body_str and "password=password" in body_str:
#                 # Gửi cookie và trả trang index.html
#                 with open("www/index.html", "r", encoding="utf-8") as f:
#                     content = f.read()
#                 header = (
#                     "HTTP/1.1 200 OK\r\n"
#                     "Content-Type: text/html\r\n"
#                     "Set-Cookie: auth=true\r\n"
#                     "Content-Length: {}\r\n"
#                     "\r\n"
#                 ).format(len(content.encode("utf-8")))
#                 conn.sendall((header + content).encode("utf-8"))
#             else:
#                 # Sai tài khoản/mật khẩu
#                 response = resp.build_unauthorized()
#                 conn.sendall(response)

#             conn.close()
#             return
#         if req.hook:
#             print("[HttpAdapter] hook in route-path METHOD {} PATH {}".format(req.hook._route_path,req.hook._route_methods))
#             hook_headers = getattr(req, "headers", {}) or {}
#             hook_body = req.body.decode("utf-8", errors="replace") if isinstance(req.body, (bytes, bytearray)) else (req.body or "")
#             hook_result = req.hook(headers=hook_headers, body=hook_body)

#             status_code = 200
#             body_obj = hook_result

#             if isinstance(hook_result, tuple) and len(hook_result) == 2:
#                 body_obj, status_code = hook_result

#             # Support legacy LOGIN_SUCCESS/FAILED for cookie task
#             if hook_result == "LOGIN_SUCCESS":
#                 resp.headers['Set-Cookie'] = 'auth=true'
#                 resp.status_code = 200 
#                 resp.reason = "OK"
#             elif hook_result == "LOGIN_FAILED":
#                 response = resp.build_unauthorized() 
#                 conn.sendall(response)
#                 conn.close()
#                 return
#             else:
#                 if isinstance(body_obj, dict):
#                     payload = json.dumps(body_obj).encode("utf-8")
#                     content_type = "application/json"
#                 elif isinstance(body_obj, bytes):
#                     payload = body_obj
#                     content_type = "application/octet-stream"
#                 else:
#                     payload = str(body_obj).encode("utf-8")
#                     content_type = "text/plain"

#                 reasons = {200: "OK", 400: "Bad Request", 401: "Unauthorized", 404: "Not Found"}
#                 reason = reasons.get(status_code, "OK" if status_code < 400 else "ERROR")
#                 header = (
#                     f"HTTP/1.1 {status_code} {reason}\r\n"
#                     f"Content-Type: {content_type}\r\n"
#                     f"Content-Length: {len(payload)}\r\n"
#                     "\r\n"
#                 )
#                 conn.sendall(header.encode("utf-8") + payload)
#                 conn.close()
#                 return
#         if not hasattr(resp, 'status_code') or resp.status_code is None:
#             resp.status_code = 200
#         if not hasattr(resp, 'reason') or resp.reason is None:
#             resp.reason = "OK"
#         response = resp.build_response(req)
#         conn.sendall(response)
#         conn.close()

#     @property
#     def extract_cookies(self, req, resp):
#         """
#         Build cookies from the :class:`Request <Request>` headers.

#         :param req:(Request) The :class:`Request <Request>` object.
#         :param resp: (Response) The res:class:`Response <Response>` object.
#         :rtype: cookies - A dictionary of cookie key-value pairs.
#         """
#         cookies = {}
#         for header in headers:
#             if header.startswith("Cookie:"):
#                 cookie_str = header.split(":", 1)[1].strip()
#                 for pair in cookie_str.split(";"):
#                     key, value = pair.strip().split("=")
#                     cookies[key] = value
#         return cookies

#     def build_response(self, req, resp):
#         """Builds a :class:`Response <Response>` object 

#         :param req: The :class:`Request <Request>` used to generate the response.
#         :param resp: The  response object.
#         :rtype: Response
#         """
#         response = Response()

#         # Set encoding.
#         response.encoding = get_encoding_from_headers(response.headers)
#         response.raw = resp
#         response.reason = response.raw.reason

#         if isinstance(req.url, bytes):
#             response.url = req.url.decode("utf-8")
#         else:
#             response.url = req.url

#         # Add new cookies from the server.
#         response.cookies = extract_cookies(req)

#         # Give the Response some context.
#         response.request = req
#         response.connection = self

#         return response

#     # def get_connection(self, url, proxies=None):
#         # """Returns a url connection for the given URL. 

#         # :param url: The URL to connect to.
#         # :param proxies: (optional) A Requests-style dictionary of proxies used on this request.
#         # :rtype: int
#         # """

#         # proxy = select_proxy(url, proxies)

#         # if proxy:
#             # proxy = prepend_scheme_if_needed(proxy, "http")
#             # proxy_url = parse_url(proxy)
#             # if not proxy_url.host:
#                 # raise InvalidProxyURL(
#                     # "Please check proxy URL. It is malformed "
#                     # "and could be missing the host."
#                 # )
#             # proxy_manager = self.proxy_manager_for(proxy)
#             # conn = proxy_manager.connection_from_url(url)
#         # else:
#             # # Only scheme should be lower case
#             # parsed = urlparse(url)
#             # url = parsed.geturl()
#             # conn = self.poolmanager.connection_from_url(url)

#         # return conn


#     def add_headers(self, request):
#         """
#         Add headers to the request.

#         This method is intended to be overridden by subclasses to inject
#         custom headers. It does nothing by default.

        
#         :param request: :class:`Request <Request>` to add headers to.
#         """
#         pass

#     def build_proxy_headers(self, proxy):
#         """Returns a dictionary of the headers to add to any request sent
#         through a proxy. 

#         :class:`HttpAdapter <HttpAdapter>`.

#         :param proxy: The url of the proxy being used for this request.
#         :rtype: dict
#         """
#         headers = {}
#         #
#         # TODO: build your authentication here
#         #       username, password =...
#         # we provide dummy auth here
#         #
#         username, password = ("user1", "password")

#         if username:
#             headers["Proxy-Authorization"] = (username, password)

#         return headers















#khong nho la gi

# import json
# from .request import Request
# from .response import Response
# from .dictionary import CaseInsensitiveDict

# class HttpAdapter:
#     __attrs__ = [
#         "ip", "port", "conn", "connaddr", "routes", "request", "response"
#     ]

#     def __init__(self, ip, port, conn, connaddr, routes):
#         self.ip = ip
#         self.port = port
#         self.conn = conn
#         self.connaddr = connaddr
#         self.routes = routes
#         self.request = Request()
#         self.response = Response()
        
#     def handle_client(self, conn, addr, routes):
#         self.conn = conn        
#         self.connaddr = addr
#         req = self.request
#         resp = self.response

#         # --- PHẦN 1: ĐỌC DỮ LIỆU TỪ SOCKET (Của nhmkct1 - Task 2.1 rất kỹ phần này) ---
#         try:
#             # Đọc chunk đầu tiên
#             data = b""
#             chunk = conn.recv(4096)
#             if not chunk:
#                 conn.close()
#                 return
#             data += chunk
            
#             # Đọc tiếp cho đến khi hết header (\r\n\r\n)
#             while b"\r\n\r\n" not in data:
#                 chunk = conn.recv(4096)
#                 if not chunk: break
#                 data += chunk

#             header_part, sep, body_part = data.partition(b"\r\n\r\n")
#             headers_text = header_part.decode("utf-8", errors="replace")

#             # Parse Content-Length để đọc nốt body nếu thiếu
#             content_length = 0
#             for line in headers_text.splitlines():
#                 if line.lower().startswith("content-length:"):
#                     try:
#                         content_length = int(line.split(":", 1)[1].strip())
#                     except: pass
#                     break

#             body_bytes = body_part
#             remaining = content_length - len(body_bytes)
#             while remaining > 0:
#                 chunk = conn.recv(4096)
#                 if not chunk: break
#                 body_bytes += chunk
#                 remaining = content_length - len(body_bytes)

#             # Build full message string cho Request.prepare
#             try:
#                 full_msg = headers_text + "\r\n\r\n" + body_bytes.decode("utf-8", errors="replace")
#             except:
#                 full_msg = headers_text + "\r\n\r\n"

#             # Đưa body dạng bytes vào request (quan trọng cho upload file/ảnh nếu có)
#             req.body = body_bytes.decode("utf-8", errors="replace") if isinstance(body_bytes, bytes) else body_bytes
            
#             # Prepare Request (Phân tích method, path, headers)
#             req.prepare(full_msg, routes)
            
#             # --- PHẦN 2: XỬ LÝ AUTHENTICATION (Task 2.1) ---
#             # Kiểm tra Cookie cho index.html
#             if req.path == '/index.html' or req.path == '/':
#                 # Logic lấy cookie từ request
#                 cookies = self.extract_cookies(req)
#                 if cookies.get('auth') != 'true':
#                     # Chưa đăng nhập -> Chặn
#                     # (Nhưng trong start_sampleapp.py ta đã có redirect rồi, nên ở đây có thể bỏ qua hoặc giữ lại tùy ý)
#                     pass 

#             # --- PHẦN 3: GỌI HÀM XỬ LÝ (HOOK) ---
#             if req.hook:
#                 print(f"[HttpAdapter] Calling Hook: {req.hook.__name__}")
                
#                 # Gọi hàm xử lý (login, submit-info, send-peer...)
#                 # Truyền headers và body vào
#                 hook_result = req.hook(headers=req.headers, body=req.body)
                
#                 # --- PHẦN 4: XỬ LÝ KẾT QUẢ TRẢ VỀ (GỘP LOGIC CỦA CẢ 2) ---
                
#                 # Case A: Task 2.1 trả về tuple (body, status)
#                 status_code = 200
#                 if isinstance(hook_result, tuple) and len(hook_result) == 2:
#                     hook_result, status_code = hook_result
#                     resp.status_code = status_code

#                 # Case B: Task 2.2 trả về Dictionary (JSON)
#                 if isinstance(hook_result, dict):
#                     # Đây là cái Web Chat cần!
#                     if "status" in hook_result and "body" in hook_result:
#                         # Dạng đầy đủ: {status: "200 OK", body: "...", Content-Type: "..."}
#                         # (Dùng cho đọc file static)
#                         resp.status_code = int(hook_result.get("status", "200").split()[0])
#                         resp.headers["Content-Type"] = hook_result.get("Content-Type", "text/plain")
                        
#                         body_content = hook_result["body"]
#                         if isinstance(body_content, str):
#                             resp._content = body_content.encode('utf-8')
#                         else:
#                             resp._content = body_content # Đã là bytes (ảnh)
#                     else:
#                         # Dạng API JSON thuần: {status: "ok", peers: [...]}
#                         resp.set_json(hook_result)

#                 # Case C: Trả về String (HTML/Text)
#                 elif isinstance(hook_result, str):
#                     resp.set_html(hook_result)

#                 # Case D: Legacy code (LOGIN_SUCCESS/FAILED)
#                 elif hook_result == "LOGIN_SUCCESS":
#                     resp.headers['Set-Cookie'] = 'auth=true'
#                     resp.set_json({"status": "ok", "cookie": "auth=true"})
#                 elif hook_result == "LOGIN_FAILED":
#                     resp.set_404() # Hoặc 401

#                 # Cuối cùng: Xây dựng phản hồi và gửi đi
#                 final_response = resp.build_dynamic()
#                 conn.sendall(final_response)
                
#             else:
#                 # Không tìm thấy route -> 404
#                 # Hoặc dùng logic build_response cũ để đọc file tĩnh nếu cần
#                 resp.status_code = 404
#                 resp.set_html("<h1>404 Not Found (No Route)</h1>")
#                 conn.sendall(resp.build_dynamic())

#         except Exception as e:
#             print(f"[HttpAdapter] Error: {e}")
#         finally:
#             conn.close()

#     def extract_cookies(self, req):
#         """Lấy cookie từ header"""
#         cookies = {}
#         if not req or not req.headers: return cookies
        
#         cookie_header = req.headers.get("Cookie") or req.headers.get("cookie")
#         if cookie_header:
#             parts = cookie_header.split(';')
#             for part in parts:
#                 if '=' in part:
#                     k, v = part.strip().split('=', 1)
#                     cookies[k] = v
#         return cookies


















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
        
    ########################################### Main function #################################
    # def handle_client(self, conn, addr, routes):
    #     """
    #     Handle an incoming client connection.
    #     Combines logic from Task 2.1 (Robust Parsing & Auth) and Task 2.2 (API Hooks).
    #     """
    #     self.conn = conn        
    #     self.connaddr = addr
    #     req = self.request
    #     resp = self.response

    #     # ---------------------------------------------------------
    #     # 1. ROBUST REQUEST PARSING (From Task 2.1)
    #     # ---------------------------------------------------------
    #     data = b""
    #     # initial read
    #     chunk = conn.recv(4096)
    #     if not chunk:
    #         conn.close()
    #         return
    #     data += chunk
    #     # wait until end of headers
    #     while b"\r\n\r\n" not in data:
    #         chunk = conn.recv(4096)
    #         if not chunk:
    #             break
    #         data += chunk

    #     header_part, sep, body_part = data.partition(b"\r\n\r\n")
    #     headers_text = header_part.decode("utf-8", errors="replace")

    #     # parse Content-Length if any
    #     content_length = 0
    #     for line in headers_text.splitlines():
    #         if line.lower().startswith("content-length:"):
    #             try:
    #                 content_length = int(line.split(":", 1)[1].strip())
    #             except:
    #                 content_length = 0
    #             break

    #     # body_part may already contain some (or all) of the body; read remaining
    #     body_bytes = body_part
    #     remaining = content_length - len(body_bytes)
    #     while remaining > 0:
    #         chunk = conn.recv(4096)
    #         if not chunk:
    #             break
    #         body_bytes += chunk
    #         remaining = content_length - len(body_bytes)

    #     # build full message for Request.prepare
    #     try:
    #         full_msg = headers_text + "\r\n\r\n" + body_bytes.decode("utf-8", errors="replace")
    #     except:
    #         full_msg = headers_text + "\r\n\r\n"

    #     # Give Request the raw body bytes and prepare
    #     req.body = body_bytes
    #     req.prepare(full_msg, routes)
        
    #     # ---------------------------------------------------------
    #     # 2. SECURITY & AUTH (From Task 2.1)
    #     # ---------------------------------------------------------
    #     # Protected resources check
    #     if req.path == '/index.html':
    #         # Check for auth=true cookie
    #         if not (req.cookies and req.cookies.get('auth') == 'true'):
    #             response = resp.build_unauthorized()
    #             conn.sendall(response)
    #             conn.close()
    #             return
        
    #     # Handle manual POST /login (Cookie Session Task)
    #     # This is fallback if no route hook is defined for /login
    #     if req.method == "POST" and req.path == "/login" and not req.hook:
    #         body_str = req.body.decode("utf-8", errors="replace") if isinstance(req.body, (bytes, bytearray)) else str(req.body)
    #         print(f"[Login] Received body: {body_str}")

    #         if "username=admin" in body_str and "password=password" in body_str:
    #             with open("www/index.html", "r", encoding="utf-8") as f:
    #                 content = f.read()
    #             header = (
    #                 "HTTP/1.1 200 OK\r\n"
    #                 "Content-Type: text/html\r\n"
    #                 "Set-Cookie: auth=true\r\n"
    #                 "Content-Length: {}\r\n"
    #                 "\r\n"
    #             ).format(len(content.encode("utf-8")))
    #             conn.sendall((header + content).encode("utf-8"))
    #         else:
    #             response = resp.build_unauthorized()
    #             conn.sendall(response)
    #         conn.close()
    #         return

    #     # ---------------------------------------------------------
    #     # 3. API & HOOKS (Combined Task 2.1 & 2.2)
    #     # ---------------------------------------------------------
    #     if req.hook:
    #         print("[HttpAdapter] hook in route-path METHOD {} PATH {}".format(req.hook._route_path, req.hook._route_methods))
            
    #         # Prepare arguments for the hook
    #         hook_headers = getattr(req, "headers", {}) or {}
    #         hook_body = req.body.decode("utf-8", errors="replace") if isinstance(req.body, (bytes, bytearray)) else (req.body or "")
            
    #         # Execute the hook (User App Logic)
    #         hook_result = req.hook(headers=hook_headers, body=hook_body)

    #         status_code = 200
    #         body_obj = hook_result

    #         # If hook returns tuple (body, status_code)
    #         if isinstance(hook_result, tuple) and len(hook_result) == 2:
    #             body_obj, status_code = hook_result

    #         # Handle specific return types
    #         if hook_result == "LOGIN_SUCCESS":
    #             resp.headers['Set-Cookie'] = 'auth=true; Path=/'
    #             resp.status_code = 200 
    #             resp.reason = "OK"
    #             # Fall through to build_response or standard return
    #             # For simplicity, we can return empty JSON or simple text
    #             body_obj = {"status": "Login Successful"}

    #         elif hook_result == "LOGIN_FAILED":
    #             response = resp.build_unauthorized() 
    #             conn.sendall(response)
    #             conn.close()
    #             return

    #         # Construct Response based on Data Type (JSON support for Task 2.2)
    #         if isinstance(body_obj, dict):
    #             payload = json.dumps(body_obj).encode("utf-8")
    #             content_type = "application/json"
    #         elif isinstance(body_obj, bytes):
    #             payload = body_obj
    #             content_type = "application/octet-stream"
    #         else:
    #             # String or HTML
    #             payload = str(body_obj).encode("utf-8")
    #             # Detect if it looks like HTML
    #             if str(body_obj).strip().startswith("<"):
    #                 content_type = "text/html"
    #             else:
    #                 content_type = "text/plain"

    #         reasons = {200: "OK", 400: "Bad Request", 401: "Unauthorized", 404: "Not Found"}
    #         reason = reasons.get(status_code, "OK" if status_code < 400 else "ERROR")
            
    #         header = (
    #             f"HTTP/1.1 {status_code} {reason}\r\n"
    #             f"Content-Type: {content_type}\r\n"
    #             f"Content-Length: {len(payload)}\r\n"
    #             "\r\n"
    #         )
    #         conn.sendall(header.encode("utf-8") + payload)
    #         conn.close()
    #         return

    #     # ---------------------------------------------------------
    #     # 4. STATIC FILES (Default Behavior)
    #     # ---------------------------------------------------------
    #     if not hasattr(resp, 'status_code') or resp.status_code is None:
    #         resp.status_code = 200
    #     if not hasattr(resp, 'reason') or resp.reason is None:
    #         resp.reason = "OK"
            
    #     response = resp.build_response(req)
    #     conn.sendall(response)
    #     conn.close()
    
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