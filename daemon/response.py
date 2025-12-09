
#
# Copyright (C) 2025 pdnguyen of HCMC University of Technology VNU-HCM.
# All rights reserved.
# This file is part of the CO3093/CO3094 course.
#
# WeApRous release
#
# The authors hereby grant to Licensee personal permission to use
# and modify the Licensed Source Code for the sole purpose of studying
# while attending the course
#

"""
daemon.response
~~~~~~~~~~~~~~~~~

This module provides a :class: `Response <Response>` object to manage and persist 
response settings (cookies, auth, proxies), and to construct HTTP responses
based on incoming requests. 

The current version supports MIME type detection, content loading and header formatting
"""
import datetime
import os
import mimetypes
import json
from datetime import timezone
from .dictionary import CaseInsensitiveDict

BASE_DIR = ""

class Response():   
    """The :class:`Response <Response>` object, which contains a
    server's response to an HTTP request.
    """

    __attrs__ = [
        "_content",
        "_header",
        "status_code",
        "method",
        "headers",
        "url",
        "history",
        "encoding",
        "reason",
        "cookies",
        "elapsed",
        "request",
        "body",
        "reason",
    ]


    def __init__(self, request=None):
        """
        Initializes a new :class:`Response <Response>` object.
        """
        self._content = b""
        self._content_consumed = False
        self._next = None

        #: Integer Code of responded HTTP Status, e.g. 404 or 200.
        self.status_code = None

        #: Case-insensitive Dictionary of Response Headers.
        self.headers = {}

        #: URL location of Response.
        self.url = None

        #: Encoding to decode with when accessing response text.
        self.encoding = None

        #: A list of :class:`Response <Response>` objects from history
        self.history = []

        #: Textual reason of responded HTTP Status, e.g. "Not Found" or "OK".
        self.reason = None

        #: A of Cookies the response headers.
        self.cookies = CaseInsensitiveDict()

        #: The amount of time elapsed between sending the request
        self.elapsed = datetime.timedelta(0)

        #: The :class:`PreparedRequest <PreparedRequest>` object
        self.request = None


    def get_mime_type(self, path):
        """
        Determines the MIME type of a file based on its path.
        """
        try:
            mime_type, _ = mimetypes.guess_type(path)
        except Exception:
            return 'application/octet-stream'
        return mime_type or 'application/octet-stream'


    def prepare_content_type(self, mime_type='text/html', path=''):
        """
        Phiên bản Robust: Ưu tiên đuôi file để định vị thư mục, 
        tránh lỗi MIME type lạ trên Windows.
        """
        # 1. Ưu tiên check đuôi file (Extension)
        path = path.lower()
        if path.endswith('.js') or path.endswith('.css') or \
           path.endswith('.png') or path.endswith('.jpg') or path.endswith('.ico'):
            # Force Content-Type nếu cần và trỏ thẳng về static
            if path.endswith('.css'): self.headers['Content-Type'] = 'text/css'
            if path.endswith('.js'): self.headers['Content-Type'] = 'application/javascript'
            return BASE_DIR + "static/"
            
        if path.endswith('.html'):
            self.headers['Content-Type'] = 'text/html'
            return BASE_DIR + "www/"

        # 2. Nếu không có đuôi rõ ràng, dùng logic MIME cũ làm fallback
        base_dir = BASE_DIR + "static/" # Mặc định an toàn
        
        main_type, sub_type = "application", "octet-stream"
        try:
            if '/' in mime_type:
                main_type, sub_type = mime_type.split('/', 1)
        except:
            pass
            
        if main_type == 'text':
            if sub_type == 'html': base_dir = BASE_DIR + "www/"
            else: base_dir = BASE_DIR + "static/"
        elif main_type == 'application':
            if sub_type == 'json': base_dir = BASE_DIR + "apps/"
            else: base_dir = BASE_DIR + "static/"
            
        return base_dir


    def build_content(self, path, base_dir):
        clean_path = path.lstrip('/')
        bd_check = base_dir.rstrip('/')
        
        if bd_check and clean_path.startswith(bd_check):
            filepath = clean_path
        else:
            filepath = os.path.join(base_dir, clean_path)
        
        # IN RA ĐƯỜNG DẪN TUYỆT ĐỐI ĐỂ DEBUG
        abs_path = os.path.abspath(filepath)
        print(f"[Response] DEBUG: Looking for file at -> {abs_path}")
        
        try:
            with open(filepath, 'rb') as f:
                content = f.read()
            return len(content), content
        except (IOError, FileNotFoundError):
            print(f"[Response] Error: File not found at {filepath}")
            return 0, b""


    def build_response_header(self, request):
        """
        Constructs the HTTP response headers.
        Combines Task 2.1 structure with Task 2.2 dynamic needs.
        """
        reqhdr = request.headers
        rsphdr = self.headers

        # Default headers
        headers = {
            "Cache-Control": "no-cache",
            "Content-Type": "{}".format(self.headers.get('Content-Type', 'text/html')),
            "Content-Length": "{}".format(len(self._content)),
            "Date": "{}".format(datetime.datetime.now(timezone.utc).strftime("%a, %d %b %Y %H:%M:%S GMT")),
            "Connection": "close",
            "Pragma": "no-cache",
        }
        
        # Inject custom headers (like Set-Cookie)
        headers.update(rsphdr)
        
        # Status Line
        # Fallback if status_code is not set
        if not self.status_code:
            self.status_code = 200
        if not self.reason:
            self.reason = "OK"
            
        status_line = "HTTP/1.1 {} {}\r\n".format(self.status_code, self.reason)

        # Build Header String
        header_lines = []
        for key, value in headers.items():
            header_lines.append("{}: {}\r\n".format(key, value))
            
        all_headers_string = "".join(header_lines)
        fmt_header = status_line + all_headers_string + "\r\n"
        
        return fmt_header.encode('utf-8')

    ########################################### Dynamic Response (Task 2.2) #################################
    # These methods are crucial for the Chat API to work
    
    def set_json(self, data):
        self.status_code = 200
        self.reason = "OK"
        body = json.dumps(data)
        self._content = body.encode('utf-8')
        self.headers["Content-Type"] = "application/json"

    def set_html(self, html):
        self.status_code = 200
        self.reason = "OK"
        self._content = html.encode('utf-8')
        self.headers["Content-Type"] = "text/html"

    def set_plain(self, text):
        self.status_code = 200
        self.reason = "OK"
        self._content = text.encode('utf-8')
        self.headers["Content-Type"] = "text/plain"

    def set_404(self):
        self.status_code = 404
        self.reason = "Not Found"
        msg = "404 Not Found"
        self._content = msg.encode('utf-8')
        self.headers["Content-Type"] = "text/plain"

    def build_dynamic(self):
        """
        Builds response for API/Hook calls (JSON, Dynamic HTML).
        """
        if not self.status_code:
             self.status_code = 200
        if not self.reason:
             self.reason = "OK"

        status_line = f"HTTP/1.1 {self.status_code} {self.reason}\r\n"

        header_lines = ""
        # Auto-calculate length
        self.headers["Content-Length"] = len(self._content)
        self.headers["Connection"] = "close"
        
        for k, v in self.headers.items():
            header_lines += f"{k}: {v}\r\n"

        return (status_line + header_lines + "\r\n").encode() + self._content

    ########################################### Error Response #################################
    def build_notfound(self):
        return (
                "HTTP/1.1 404 Not Found\r\n"
                "Content-Type: text/html\r\n"
                "Content-Length: 13\r\n"
                "Connection: close\r\n"
                "\r\n"
                "404 Not Found"
            ).encode('utf-8')
        
    def build_unauthorized(self):
        return (
                "HTTP/1.1 401 Unauthorized\r\n"
                "Content-Type: text/html\r\n"
                "Content-Length: 16\r\n"
                "Connection: close\r\n"
                "\r\n"
                "401 Unauthorized"
            ).encode('utf-8')


    ########################################### Main function (Static Files) #################################
    def build_response(self, request):
        path = request.path
        mime_type = self.get_mime_type(path)
        
        # TRUYỀN THÊM path VÀO ĐÂY
        base_dir = self.prepare_content_type(mime_type=mime_type, path=path)

        c_len, content = self.build_content(path, base_dir)
        
        if c_len == 0 and not content:
             return self.build_notfound()
             
        self._content = content
        self._header = self.build_response_header(request)
        return self._header + self._content

















