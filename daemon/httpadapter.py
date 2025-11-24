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
    def handle_client(self, conn, addr, routes):
        self.conn = conn        
        self.connaddr = addr
        req = self.request
        resp = self.response

        # Read headers (until \r\n\r\n), then read body according to Content-Length
        data = b""
        # initial read
        chunk = conn.recv(4096)
        if not chunk:
            conn.close()
            return
        data += chunk
        # wait until end of headers
        while b"\r\n\r\n" not in data:
            chunk = conn.recv(4096)
            if not chunk:
                break
            data += chunk

        header_part, sep, body_part = data.partition(b"\r\n\r\n")
        headers_text = header_part.decode("utf-8", errors="replace")

        # parse Content-Length if any
        content_length = 0
        for line in headers_text.splitlines():
            if line.lower().startswith("content-length:"):
                try:
                    content_length = int(line.split(":", 1)[1].strip())
                except:
                    content_length = 0
                break

        # body_part may already contain some (or all) of the body; read remaining
        body_bytes = body_part
        remaining = content_length - len(body_bytes)
        while remaining > 0:
            chunk = conn.recv(4096)
            if not chunk:
                break
            body_bytes += chunk
            remaining = content_length - len(body_bytes)

        # build full message for Request.prepare (headers + body as text)
        try:
            full_msg = headers_text + "\r\n\r\n" + body_bytes.decode("utf-8", errors="replace")
        except:
            full_msg = headers_text + "\r\n\r\n"

        # give Request the raw body bytes too
        req.body = body_bytes
        req.prepare(full_msg, routes)
        req.prepare(full_msg, routes)
        
        # Authorized?
        if req.path == '/index.html':
            if not (req.cookies and req.cookies.get('auth') == 'true'):
                response = resp.build_unauthorized()
                conn.sendall(response)
                conn.close()
                return
        
        # --- Handle POST /login (Task 1 Cookie Session) ---
        if req.method == "POST" and req.path == "/login":
            body_str = req.body.decode("utf-8", errors="replace") if isinstance(req.body, (bytes, bytearray)) else str(req.body)
            print(f"[Login] Received body: {body_str}")

            if "username=admin" in body_str and "password=password" in body_str:
                # Gửi cookie và trả trang index.html
                with open("www/index.html", "r", encoding="utf-8") as f:
                    content = f.read()
                header = (
                    "HTTP/1.1 200 OK\r\n"
                    "Content-Type: text/html\r\n"
                    "Set-Cookie: auth=true\r\n"
                    "Content-Length: {}\r\n"
                    "\r\n"
                ).format(len(content.encode("utf-8")))
                conn.sendall((header + content).encode("utf-8"))
            else:
                # Sai tài khoản/mật khẩu
                response = resp.build_unauthorized()
                conn.sendall(response)

            conn.close()
            return
        
        if req.hook:
            print("[HttpAdapter] hook in route-path METHOD {} PATH {}".format(req.hook._route_path,req.hook._route_methods))
            #
            # TODO: handle for App hook here
            #
            #login_result = req.hook(headers="bksysnet", body="get in touch")
            # Pass real parsed headers/body to app hook
            hook_headers = getattr(req, "headers", {}) or {}
            hook_body = req.body.decode("utf-8", errors="replace") if isinstance(req.body, (bytes, bytearray)) else (req.body or "")
            login_result = req.hook(headers=hook_headers, body=hook_body)
            if login_result == "LOGIN_SUCCESS":
                resp.headers['Set-Cookie'] = 'auth=true'
                resp.status_code = 200 
                resp.reason = "OK"
                
            elif login_result == "LOGIN_FAILED":
                response = resp.build_unauthorized() 
                conn.sendall(response)
                conn.close()
                return
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

        :param req:(Request) The :class:`Request <Request>` object.
        :param resp: (Response) The res:class:`Response <Response>` object.
        :rtype: cookies - A dictionary of cookie key-value pairs.
        """
        cookies = {}
        for header in headers:
            if header.startswith("Cookie:"):
                cookie_str = header.split(":", 1)[1].strip()
                for pair in cookie_str.split(";"):
                    key, value = pair.strip().split("=")
                    cookies[key] = value
        return cookies

    def build_response(self, req, resp):
        """Builds a :class:`Response <Response>` object 

        :param req: The :class:`Request <Request>` used to generate the response.
        :param resp: The  response object.
        :rtype: Response
        """
        response = Response()

        # Set encoding.
        response.encoding = get_encoding_from_headers(response.headers)
        response.raw = resp
        response.reason = response.raw.reason

        if isinstance(req.url, bytes):
            response.url = req.url.decode("utf-8")
        else:
            response.url = req.url

        # Add new cookies from the server.
        response.cookies = extract_cookies(req)

        # Give the Response some context.
        response.request = req
        response.connection = self

        return response

    # def get_connection(self, url, proxies=None):
        # """Returns a url connection for the given URL. 

        # :param url: The URL to connect to.
        # :param proxies: (optional) A Requests-style dictionary of proxies used on this request.
        # :rtype: int
        # """

        # proxy = select_proxy(url, proxies)

        # if proxy:
            # proxy = prepend_scheme_if_needed(proxy, "http")
            # proxy_url = parse_url(proxy)
            # if not proxy_url.host:
                # raise InvalidProxyURL(
                    # "Please check proxy URL. It is malformed "
                    # "and could be missing the host."
                # )
            # proxy_manager = self.proxy_manager_for(proxy)
            # conn = proxy_manager.connection_from_url(url)
        # else:
            # # Only scheme should be lower case
            # parsed = urlparse(url)
            # url = parsed.geturl()
            # conn = self.poolmanager.connection_from_url(url)

        # return conn


    def add_headers(self, request):
        """
        Add headers to the request.

        This method is intended to be overridden by subclasses to inject
        custom headers. It does nothing by default.

        
        :param request: :class:`Request <Request>` to add headers to.
        """
        pass

    def build_proxy_headers(self, proxy):
        """Returns a dictionary of the headers to add to any request sent
        through a proxy. 

        :class:`HttpAdapter <HttpAdapter>`.

        :param proxy: The url of the proxy being used for this request.
        :rtype: dict
        """
        headers = {}
        #
        # TODO: build your authentication here
        #       username, password =...
        # we provide dummy auth here
        #
        username, password = ("user1", "password")

        if username:
            headers["Proxy-Authorization"] = (username, password)

        return headers