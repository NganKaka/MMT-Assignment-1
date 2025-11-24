
import datetime
import os
import mimetypes
from .dictionary import CaseInsensitiveDict
from datetime import timezone
BASE_DIR = ""

class Response():   
    """
    :attrs status_code (int): HTTP status code (e.g., 200, 404).
    :attrs headers (dict): dictionary of response headers.
    :attrs url (str): url of the response.
    :attrsencoding (str): encoding used for decoding response content.
    :attrs history (list): list of previous Response objects (for redirects).
    :attrs reason (str): textual reason for the status code (e.g., "OK", "Not Found").
    :attrs cookies (CaseInsensitiveDict): response cookies.
    :attrs elapsed (datetime.timedelta): time taken to complete the request.
    :attrs request (PreparedRequest): the original request object.
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
        self._content = False
        self._content_consumed = False
        self._next = None

        #: Integer Code of responded HTTP Status, e.g. 404 or 200.
        self.status_code = None

        #: Case-insensitive Dictionary of Response Headers.
        #: For example, ``headers['content-type']`` will return the
        #: value of a ``'Content-Type'`` response header.
        self.headers = {}

        #: URL location of Response.
        self.url = None

        #: Encoding to decode with when accessing response text.
        self.encoding = None

        #: A list of :class:`Response <Response>` objects from
        #: the history of the Request.
        self.history = []

        #: Textual reason of responded HTTP Status, e.g. "Not Found" or "OK".
        self.reason = None

        #: A of Cookies the response headers.
        self.cookies = CaseInsensitiveDict()

        #: The amount of time elapsed between sending the request
        self.elapsed = datetime.timedelta(0)

        #: The :class:`PreparedRequest <PreparedRequest>` object to which this
        #: is a response.
        self.request = None


    def get_mime_type(self, path):
        #rtype: MIME type string (e.g., 'text/html', 'image/png').
        try:
            mime_type, _ = mimetypes.guess_type(path)
        except Exception:
            return 'application/octet-stream'
        return mime_type or 'application/octet-stream'


    def prepare_content_type(self, mime_type='text/html'):
        base_dir = ""
        main_type, sub_type = mime_type.split('/', 1)
        print("[Response] processing MIME main_type={} sub_type={}".format(main_type,sub_type))
        if main_type == 'text':
            self.headers['Content-Type']='text/{}'.format(sub_type)
            if sub_type == 'plain' or sub_type == 'css':
                base_dir = BASE_DIR+"static/"
            elif sub_type == 'html':
                base_dir = BASE_DIR+"www/"
            else:
                handle_text_other(sub_type)
        elif main_type == 'image':
            base_dir = BASE_DIR+"static/"
            self.headers['Content-Type']='image/{}'.format(sub_type)
        elif main_type == 'application': #application/javascript (.js)
            if sub_type == 'javascript':
                base_dir = BASE_DIR+"static/"
                self.headers['Content-Type']='application/javascript'
            else:
                base_dir = BASE_DIR+"apps/"
                self.headers['Content-Type']='application/{}'.format(sub_type)    
        elif main_type == 'video':
            base_dir = BASE_DIR+"static/"
            self.headers['Content-Type']='video/{}'.format(sub_type)
        else:
            raise ValueError("Invalid MEME type: main_type={} sub_type={}".format(main_type,sub_type))

        return base_dir


    def build_content(self, path, base_dir):
        #path (str) "/index.html" or "/static/images/welcome.png"
        #base_dir (str) "www/" or "static/"
        #rtype (int, byte)
        
        # If path already contains the base_dir, don't duplicate it
        clean_path = path.lstrip('/')
        
        # Check if path already starts with base_dir (e.g., "static/...")
        if base_dir and clean_path.startswith(base_dir.rstrip('/')):
            # Path already includes base_dir, use it directly
            filepath = clean_path
        else:
            # Normal case: prepend base_dir
            filepath = os.path.join(base_dir, clean_path)
        
        print("[Response] DEBUG: path='{}' base_dir='{}' filepath='{}'".format(path, base_dir, filepath))
        print("[Response] serving the object at location {}".format(filepath))
        try:
            with open(filepath, 'rb') as f: #read byte
                content = f.read()
            return len(content), content
        except (IOError, FileNotFoundError):
            print("[Response] Error: File not found at {}".format(filepath))
            return 0, b""


    def build_response_header(self, request):
        """
        :request (Request) 
        :rtypes (bytes) -  encoded HTTP response header.
        """
        reqhdr = request.headers
        rsphdr = self.headers

        headers = {
                # "Accept": "{}".format(reqhdr.get("Accept", "application/json")),
                # "Accept-Language": "{}".format(reqhdr.get("Accept-Language", "en-US,en;q=0.9")),
                # "Authorization": "{}".format(reqhdr.get("Authorization", "Basic <credentials>")),
                "Cache-Control": "no-cache",
                "Content-Type": "{}".format(self.headers['Content-Type']),
                "Content-Length": "{}".format(len(self._content)),
#                "Cookie": "{}".format(reqhdr.get("Cookie", "sessionid=xyz789")), #dummy cooki
        #
        # TODO prepare the request authentication
        #
	# self.auth = ...
                "Date": "{}".format(datetime.datetime.now(timezone.utc).strftime("%a, %d %b %Y %H:%M:%S GMT")),                "Max-Forward": "10",
                "Pragma": "no-cache",
                # "Proxy-Authorization": "Basic dXNlcjpwYXNz", 
                # "Warning": "199 Miscellaneous warning",
                # "User-Agent": "{}".format(reqhdr.get("User-Agent", "Chrome/123.0.0.0")),
                "Connection": "close",
            }
        headers.update(rsphdr)
        status_line = "HTTP/1.1 {} {}\r\n".format(self.status_code, self.reason) #HTTP/1.1 200 OK
        # Header text alignment
        header_lines = []
        for key, value in headers.items():
            header_lines.append("{}: {}\r\n".format(key, value))
        all_headers_string = "".join(header_lines)
        
        fmt_header = status_line + all_headers_string + "\r\n"
        return fmt_header.encode('utf-8')

    ########################################### Error Response #################################
    # 404 Not Found #
    def build_notfound(self):
        return (
                "HTTP/1.1 404 Not Found\r\n"
                "Accept-Ranges: bytes\r\n"
                "Content-Type: text/html\r\n"
                "Content-Length: 13\r\n"
                "Cache-Control: max-age=86000\r\n"
                "Connection: close\r\n"
                "\r\n"
                "404 Not Found"
            ).encode('utf-8')
        
    # 401 Unauthorized #
    def build_unauthorized(self):
        return (
                "HTTP/1.1 401 Unauthorized\r\n"
                "Content-Type: text/html\r\n"
                "Content-Length: 16\r\n"
                "Connection: close\r\n"
                "\r\n"
                "401 Unauthorized"
            ).encode('utf-8')


    ########################################### Main function #################################
    def build_response(self, request):
        path = request.path

        mime_type = self.get_mime_type(path)
        print("[Response] {} path {} mime_type {}".format(request.method, request.path, mime_type))

        base_dir = ""

        if path.endswith('.html') or mime_type == 'text/html':
            base_dir = self.prepare_content_type(mime_type = 'text/html')
        elif mime_type == 'text/css':
            base_dir = self.prepare_content_type(mime_type = 'text/css')
        elif mime_type == 'application/javascript':
            base_dir = self.prepare_content_type(mime_type = 'application/javascript')
        elif mime_type and mime_type.startswith('image/'):
            # Handle image files (png, jpg, ico, etc.)
            base_dir = self.prepare_content_type(mime_type = mime_type)
        else:
            return self.build_notfound()

        c_len, self._content = self.build_content(path, base_dir)
        self._header = self.build_response_header(request)
        return self._header + self._content