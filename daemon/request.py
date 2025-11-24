from .dictionary import CaseInsensitiveDict

class Request():

    __attrs__ = [
        "method", #GET, POST, PUT
        "url", # /index.html
        "headers", # dictionary of HTTP headers ({'host':'app1.local',...})
        "body",
        "reason",
        "cookies",
        "body",
        "routes",
        "hook",
    ]

    def __init__(self):
        #: HTTP verb to send to the server (GET, POST, PUT)
        self.method = None
        #: HTTP URL to send the request to (/index.html)
        self.url = None
        #: dictionary of HTTP headers ({'host':'app1.local',...})
        self.headers = None
        #: HTTP path (/index.html)
        self.path = None        
        # The cookies set used to create Cookie header ({'auth':'true','user':'test'})
        self.cookies = {}
        #: request body to send to the server.
        self.body = None
        #: Routes
        self.routes = {}
        #: Hook point for routed mapped-path
        self.hook = None

    def extract_request_line(self, request):
        try:
            lines = request.splitlines()
            first_line = lines[0]
            method, path, version = first_line.split()

            if path == '/':
                path = '/index.html'
        except Exception:
            return None, None
        return method, path, version
    
    def prepare_headers(self, request):
        lines = request.split('\r\n')
        headers = {}
        for line in lines[1:]:
            if ': ' in line:
                key, val = line.split(': ', 1)
                headers[key.lower()] = val
        return headers

    def prepare(self, request, routes=None):
        self.method, self.path, self.version = self.extract_request_line(request)
        print("[Request] {} path {} version {}".format(self.method, self.path, self.version))
        if not routes == {}:
            self.routes = routes
            self.hook = routes.get((self.method, self.path))
            
        self.headers = self.prepare_headers(request)
        
        ########################Cookies#########################
        cookies = self.headers.get('cookie', '') ## cookies = "auth=true==; user=test;"
        cookies_pairs = cookies.split(';')
        for cookies_pair in cookies_pairs:
            no_space_cookies_pair = cookies_pair.strip()
            if not no_space_cookies_pair:
                continue
            if '=' in no_space_cookies_pair:
                key, value = no_space_cookies_pair.split('=',1)
                self.cookies[key] = value
            else:
                self.cookies[no_space_cookies_pair] = True
        return

    def prepare_body(self, data, files, json=None):
        self.prepare_content_length(self.body)
        self.body = body
        #
        # TODO prepare the request authentication
        #
	# self.auth = ...
        return


    def prepare_content_length(self, body):
        self.headers["Content-Length"] = "0"
        #
        # TODO prepare the request authentication
        #
	# self.auth = ...
        return


    def prepare_auth(self, auth, url=""):
        #
        # TODO prepare the request authentication
        #
	# self.auth = ...
        return

    def prepare_cookies(self, cookies):
            self.headers["Cookie"] = cookies
