# from .dictionary import CaseInsensitiveDict

# class Request():

#     __attrs__ = [
#         "method", #GET, POST, PUT
#         "url", # /index.html
#         "headers", # dictionary of HTTP headers ({'host':'app1.local',...})
#         "body",
#         "reason",
#         "cookies",
#         "body",
#         "routes",
#         "hook",
#     ]

#     def __init__(self):
#         #: HTTP verb to send to the server (GET, POST, PUT)
#         self.method = None
#         #: HTTP URL to send the request to (/index.html)
#         self.url = None
#         #: dictionary of HTTP headers ({'host':'app1.local',...})
#         self.headers = None
#         #: HTTP path (/index.html)
#         self.path = None        
#         # The cookies set used to create Cookie header ({'auth':'true','user':'test'})
#         self.cookies = {}
#         #: request body to send to the server.
#         self.body = None
#         #: Routes
#         self.routes = {}
#         #: Hook point for routed mapped-path
#         self.hook = None

#     def extract_request_line(self, request):
#         try:
#             lines = request.splitlines()
#             first_line = lines[0]
#             method, path, version = first_line.split()

#             if path == '/':
#                 path = '/index.html'
#         except Exception:
#             return None, None
#         return method, path, version
    
#     def prepare_headers(self, request):
#         lines = request.split('\r\n')
#         headers = {}
#         for line in lines[1:]:
#             if ': ' in line:
#                 key, val = line.split(': ', 1)
#                 headers[key.lower()] = val
#         return headers

#     def prepare(self, request, routes=None):
#         self.method, self.path, self.version = self.extract_request_line(request)
#         print("[Request] {} path {} version {}".format(self.method, self.path, self.version))
#         if not routes == {}:
#             self.routes = routes
#             self.hook = routes.get((self.method, self.path))
            
#         self.headers = self.prepare_headers(request)
        
#         ########################Cookies#########################
#         cookies = self.headers.get('cookie', '') ## cookies = "auth=true==; user=test;"
#         cookies_pairs = cookies.split(';')
#         for cookies_pair in cookies_pairs:
#             no_space_cookies_pair = cookies_pair.strip()
#             if not no_space_cookies_pair:
#                 continue
#             if '=' in no_space_cookies_pair:
#                 key, value = no_space_cookies_pair.split('=',1)
#                 self.cookies[key] = value
#             else:
#                 self.cookies[no_space_cookies_pair] = True
#         return

#     def prepare_body(self, data, files, json=None):
#         self.prepare_content_length(self.body)
#         self.body = body
#         #
#         # TODO prepare the request authentication
#         #
# 	# self.auth = ...
#         return


#     def prepare_content_length(self, body):
#         self.headers["Content-Length"] = "0"
#         #
#         # TODO prepare the request authentication
#         #
# 	# self.auth = ...
#         return


#     def prepare_auth(self, auth, url=""):
#         #
#         # TODO prepare the request authentication
#         #
# 	# self.auth = ...
#         return

#     def prepare_cookies(self, cookies):
#             self.headers["Cookie"] = cookies




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
daemon.request
~~~~~~~~~~~~~~~~~

This module provides a Request object to manage and persist 
request settings (cookies, auth, proxies).
"""
from .dictionary import CaseInsensitiveDict

class Request():
    """The fully mutable "class" `Request <Request>` object,
    containing the exact bytes that will be sent to the server.

    Instances are generated from a "class" `Request <Request>` object, and
    should not be instantiated manually; doing so may produce undesirable
    effects.
    """
    __attrs__ = [
        "method",
        "url",
        "headers",
        "body",
        "reason",
        "cookies",
        "body",
        "routes",
        "hook",
    ]

    def __init__(self):
        #: HTTP verb to send to the server.
        self.method = None
        #: HTTP URL to send the request to.
        self.url = None
        #: dictionary of HTTP headers.
        self.headers = None
        #: HTTP path
        self.path = None        
        # The cookies set used to create Cookie header
        self.cookies = {}
        #: request body to send to the server.
        self.body = None
        #: Routes
        self.routes = {}
        #: Hook point for routed mapped-path
        self.hook = None

    def extract_request_line(self, request):
        """
        Parses the first line of the HTTP request.
        Uses robust checking from Task 2.2.
        """
        try:
            lines = request.splitlines()
            if not lines:
                return None, None, None

            first_line = lines[0].strip()
            parts = first_line.split()

            if len(parts) != 3:
                return None, None, None

            method, path, version = parts

            # Normalized default path
            if path == '/':
                path = '/index.html'

            return method, path, version
        except Exception:
            return None, None, None
             
    def prepare_headers(self, request):
        """Prepares the given HTTP headers."""
        lines = request.split('\r\n')
        headers = {}
        # Skip the request line (index 0)
        for line in lines[1:]:
            if ': ' in line:
                key, val = line.split(': ', 1)
                headers[key.lower()] = val
            elif ':' in line: # Handle cases with no space after colon
                key, val = line.split(':', 1)
                headers[key.lower()] = val.strip()
        return headers

    def prepare(self, request, routes=None):
        """Prepares the entire request with the given parameters."""
        
        # 1. Parse Request Line
        self.method, self.path, self.version = self.extract_request_line(request)
        print("[Request] {} path {} version {}".format(self.method, self.path, self.version))

        # 2. Setup Route Hooks (From Task 2.2)
        if routes and isinstance(routes, dict):
            self.routes = routes
            # Look up (Method, Path) in routes dictionary
            self.hook = routes.get((self.method, self.path))

        # 3. Parse Headers
        self.headers = self.prepare_headers(request)

        # 4. Parse Cookies (From Task 2.1 - Correct implementation)
        cookies_header = self.headers.get('cookie', '')
        if cookies_header:
            cookies_pairs = cookies_header.split(';')
            for cookies_pair in cookies_pairs:
                no_space_cookies_pair = cookies_pair.strip()
                if not no_space_cookies_pair:
                    continue
                if '=' in no_space_cookies_pair:
                    key, value = no_space_cookies_pair.split('=', 1)
                    self.cookies[key] = value
                else:
                    self.cookies[no_space_cookies_pair] = True

        # 5. Fallback Body Parsing
        # Note: Ideally body is set by HttpAdapter which handles Content-Length reading.
        # This is just a fallback for simple text requests if self.body wasn't set externally.
        if self.body is None:
            if "\r\n\r\n" in request:
                _, body_part = request.split("\r\n\r\n", 1)
                self.body = body_part
            else:
                self.body = ""

        return

    def prepare_body(self, data, files, json=None):
        # This method seems to be a placeholder in the assignment template
        # logic is mainly handled in prepare() or HttpAdapter
        self.prepare_content_length(self.body)
        return

    def prepare_content_length(self, body):
        if self.body:
             self.headers["Content-Length"] = str(len(self.body))
        else:
             self.headers["Content-Length"] = "0"
        return

    def prepare_auth(self, auth, url=""):
        return

    def prepare_cookies(self, cookies):
        # Helper to set cookie header for outgoing requests (if needed)
        self.headers["Cookie"] = cookies