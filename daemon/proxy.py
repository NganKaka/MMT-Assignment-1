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
daemon.proxy
~~~~~~~~~~~~~~~~~

This module implements a simple proxy server using Python's socket and threading libraries.
It routes incoming HTTP requests to backend services based on hostname mappings and returns
the corresponding responses to clients.

Requirement:
-----------------
- socket: provides socket networking interface.
- threading: enables concurrent client handling via threads.
- response: customized :class: `Response <Response>` utilities.
- httpadapter: :class: `HttpAdapter <HttpAdapter >` adapter for HTTP request processing.
- dictionary: :class: `CaseInsensitiveDict <CaseInsensitiveDict>` for managing headers and cookies.

"""
import socket
import threading
import time
from .response import *
from .httpadapter import HttpAdapter
from .dictionary import CaseInsensitiveDict

#: Default fallback when no route matched
DEFAULT_BACKEND = ('127.0.0.1', 9000)

#: A dictionary mapping hostnames to backend IP and port tuples.
#: Used to determine routing targets for incoming requests.
PROXY_PASS = {
    "192.168.56.103:8080": ('192.168.56.103', 9000),
    "app1.local": ('192.168.56.103', 9001),
    "app2.local": ('192.168.56.103', 9002),
}


def forward_request(host, port, request):
    """
    Forwards an HTTP request to a backend server and retrieves the response.

    :params host (str): IP address of the backend server.
    :params port (int): port number of the backend server.
    :params request (str): incoming HTTP request.

    :rtype bytes: Raw HTTP response from the backend server. If the connection
                  fails, returns a 404 Not Found response.
    """

    backend = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    backend.settimeout(timeout=5)

    try:
        backend.connect((host, port))

        if isinstance(request_bytes, str):
            request_bytes = request_bytes.encode('utf-8')

        backend.sendall(request.encode())
        
        response = b""
        while True:
            try:
                chunk = backend.recv(4096)
            except socket.timeout:
                print("Socket timeout when receiving data from backend {}:{}".format(host, port))
                break
            if not chunk:
                break
            response += chunk
        return response
    except socket.error as e:
        print("[Proxy][forward_request] Socket error: {}".format(e))
        return (
            "HTTP/1.1 502 Bad Gateway\r\n"
            "Content-Type: text/plain\r\n"
            "Content-Length: 11\r\n"
            "Connection: close\r\n"
            "\r\n"
            "Bad Gateway"
        ).encode('utf-8')
    #   print("Socket error: {}".format(e))
    #   return (
    #         "HTTP/1.1 404 Not Found\r\n"
    #         "Content-Type: text/plain\r\n"
    #         "Content-Length: 13\r\n"
    #         "Connection: close\r\n"
    #         "\r\n"
    #         "404 Not Found"
    #     ).encode('utf-8')
    finally:
        backend.close()


def resolve_routing_policy(hostname, routes):
    """
    Handles an routing policy to return the matching proxy_pass.
    It determines the target backend to forward the request to.

    :params host (str): IP address of the request target server.
    :params port (int): port number of the request target server.
    :params routes (dict): dictionary mapping hostnames and location.
    """

    # print(hostname)
    # proxy_map, policy = routes.get(hostname,('127.0.0.1:9000','round-robin'))
    # print(proxy_map)
    # print(policy)

    # proxy_host = ''
    # proxy_port = '9000'
    # if isinstance(proxy_map, list):
    #     if len(proxy_map) == 0:
    #         print("[Proxy] Emtpy resolved routing of hostname {}".format(hostname))
    #         print("Empty proxy_map result")
    #         # TODO: implement the error handling for non mapped host
    #         #       the policy is design by team, but it can be 
    #         #       basic default host in your self-defined system
    #         # Use a dummy host to raise an invalid connection
    #         proxy_host = '127.0.0.1'
    #         proxy_port = '9000'
    #     elif len(value) == 1:
    #         proxy_host, proxy_port = proxy_map[0].split(":", 2)
    #     #elif: # apply the policy handling 
    #     #   proxy_map
    #     #   policy
    #     else:
    #         # Out-of-handle mapped host
    #         proxy_host = '127.0.0.1'
    #         proxy_port = '9000'
    # else:
    #     print("[Proxy] resolve route of hostname {} is a singulair to".format(hostname))
    #     proxy_host, proxy_port = proxy_map.split(":", 2)

    # return proxy_host, proxy_port
    # default when hostname not found
    entry = routes.get(hostname, None)

    # If routes stored as mapping to a pair (proxy_map, policy) -> normalize
    if isinstance(entry, tuple) and len(entry) == 2 and isinstance(entry[1], str):
        proxy_map = entry[0]
        policy = entry[1]
    else:
        proxy_map = entry
        policy = None

    # If entry is direct (host,port) tuple as values like ('127.0.0.1', 9000)
    if isinstance(proxy_map, tuple) and len(proxy_map) == 2 and isinstance(proxy_map[1], int):
        return str(proxy_map[0]), str(proxy_map[1])

    # If proxy_map is a string like "ip:port"
    if isinstance(proxy_map, str):
        if ":" in proxy_map:
            host, port = proxy_map.split(":", 1)
            return host, port
        else:
            # assume default port
            return proxy_map, str(DEFAULT_BACKEND[1])

    # If proxy_map is a list, try to use first entry
    if isinstance(proxy_map, list):
        if len(proxy_map) == 0:
            print("[Proxy] Empty proxy_map for hostname {}".format(hostname))
            return str(DEFAULT_BACKEND[0]), str(DEFAULT_BACKEND[1])
        first = proxy_map[0]
        if isinstance(first, str) and ":" in first:
            host, port = first.split(":", 1)
            return host, port
        elif isinstance(first, tuple) and len(first) == 2:
            return str(first[0]), str(first[1])
        else:
            return str(DEFAULT_BACKEND[0]), str(DEFAULT_BACKEND[1])

    # If entry is a tuple like ('127.0.0.1', 9000)
    if isinstance(entry, tuple) and len(entry) == 2:
        return str(entry[0]), str(entry[1])

    # fallback to default backend
    print("[Proxy] No valid route entry for hostname {}, using default {}".format(hostname, DEFAULT_BACKEND))
    return str(DEFAULT_BACKEND[0]), str(DEFAULT_BACKEND[1])

def _recv_all_headers(conn, initial=b''):
    """
    Read from socket until header section (double CRLF) is complete.
    Returns header_bytes and remaining bytes after the header (may include body bytes).
    """
    data = bytearray(initial)
    conn.settimeout(2.0)
    while True:
        if b"\r\n\r\n" in data:
            header_end = data.index(b"\r\n\r\n") + 4
            return bytes(data[:header_end]), bytes(data[header_end:])
        try:
            chunk = conn.recv(4096)
        except socket.timeout:
            # timeouts are acceptable if we've got something
            if data:
                if b"\r\n\r\n" in data:
                    header_end = data.index(b"\r\n\r\n") + 4
                    return bytes(data[:header_end]), bytes(data[header_end:])
                else:
                    # incomplete headers -> return what we have
                    return bytes(data), b''
            else:
                return b'', b''
        if not chunk:
            return bytes(data), b''
        data.extend(chunk)


def _parse_content_length(headers_bytes):
    """
    Parse Content-Length from header bytes, return integer or 0.
    """
    try:
        headers_text = headers_bytes.decode('iso-8859-1')
    except Exception:
        headers_text = headers_bytes.decode('utf-8', errors='ignore')
    for line in headers_text.splitlines():
        if line.lower().startswith('content-length:'):
            try:
                return int(line.split(':', 1)[1].strip())
            except Exception:
                return 0
    return 0


def _extract_host_from_request_line(request_line):
    """
    For proxy-style requests, request line can contain absolute URI:
      GET http://example.com:8080/path HTTP/1.1
    This helper extracts host[:port] if present.
    """
    parts = request_line.split()
    if len(parts) < 2:
        return None
    target = parts[1]
    if target.startswith("http://") or target.startswith("https://"):
        # strip scheme
        try:
            without_scheme = target.split("://", 1)[1]
            hostport = without_scheme.split("/", 1)[0]
            return hostport
        except Exception:
            return None
    return None

def handle_client(ip, port, conn, addr, routes):
    """
    Handles an individual client connection by parsing the request,
    determining the target backend, and forwarding the request.

    The handler extracts the Host header from the request to
    matches the hostname against known routes. In the matching
    condition,it forwards the request to the appropriate backend.

    The handler sends the backend response back to the client or
    returns 404 if the hostname is unreachable or is not recognized.

    :params ip (str): IP address of the proxy server.
    :params port (int): port number of the proxy server.
    :params conn (socket.socket): client connection socket.
    :params addr (tuple): client address (IP, port).
    :params routes (dict): dictionary mapping hostnames and location.
    """

    # request = conn.recv(1024).decode()

    # # Extract hostname
    # for line in request.splitlines():
    #     if line.lower().startswith('host:'):
    #         hostname = line.split(':', 1)[1].strip()

    # print("[Proxy] {} at Host: {}".format(addr, hostname))

    # # Resolve the matching destination in routes and need conver port
    # # to integer value
    # resolved_host, resolved_port = resolve_routing_policy(hostname, routes)
    # try:
    #     resolved_port = int(resolved_port)
    # except ValueError:
    #     print("Not a valid integer")

    # if resolved_host:
    #     print("[Proxy] Host name {} is forwarded to {}:{}".format(hostname,resolved_host, resolved_port))
    #     response = forward_request(resolved_host, resolved_port, request)        
    # else:
    #     response = (
    #         "HTTP/1.1 404 Not Found\r\n"
    #         "Content-Type: text/plain\r\n"
    #         "Content-Length: 13\r\n"
    #         "Connection: close\r\n"
    #         "\r\n"
    #         "404 Not Found"
    #     ).encode('utf-8')
    # conn.sendall(response)
    # conn.close()
    try:
        # receive headers first (may also return some body bytes)
        headers_bytes, remaining = _recv_all_headers(conn)
        if not headers_bytes:
            print("[Proxy] Empty request from {}".format(addr))
            conn.close()
            return

        # parse Host header from headers; fallback to absolute URI in request line
        try:
            headers_text = headers_bytes.decode('iso-8859-1')
        except Exception:
            headers_text = headers_bytes.decode('utf-8', errors='ignore')

        hostname = None
        request_lines = headers_text.splitlines()
        if len(request_lines) > 0:
            # attempt to parse host from request-line absolute URL
            req_line = request_lines[0]
            host_from_line = _extract_host_from_request_line(req_line)
            if host_from_line:
                hostname = host_from_line

        for line in request_lines:
            if line.lower().startswith('host:'):
                hostname = line.split(':', 1)[1].strip()
                break

        if not hostname:
            # no Host header, use default
            hostname = "{}:{}".format(ip, port)

        # determine if we need to read body
        content_length = _parse_content_length(headers_bytes)
        body = remaining
        to_read = content_length - len(body)
        while to_read > 0:
            chunk = conn.recv(min(4096, to_read))
            if not chunk:
                break
            body += chunk
            to_read -= len(chunk)

        raw_request = headers_bytes + body

        print("[Proxy] {} -> Host: {}".format(addr, hostname))

        # Resolve backend
        resolved_host, resolved_port = resolve_routing_policy(hostname, routes)
        try:
            resolved_port_int = int(resolved_port)
        except Exception:
            print("[Proxy] Resolved port not integer: {} (using default)".format(resolved_port))
            resolved_port_int = DEFAULT_BACKEND[1]

        if resolved_host:
            print("[Proxy] Forwarding {} to {}:{}".format(hostname, resolved_host, resolved_port_int))
            response = forward_request(resolved_host, resolved_port_int, raw_request)
        else:
            response = (
                "HTTP/1.1 404 Not Found\r\n"
                "Content-Type: text/plain\r\n"
                "Content-Length: 13\r\n"
                "Connection: close\r\n"
                "\r\n"
                "404 Not Found"
            ).encode('utf-8')

        # send back to client
        try:
            conn.sendall(response)
        except socket.error as e:
            print("[Proxy] Error sending response to {}: {}".format(addr, e))

    except Exception as e:
        print("[Proxy] Exception handling client {}: {}".format(addr, e))
        try:
            conn.sendall((
                "HTTP/1.1 500 Internal Server Error\r\n"
                "Content-Type: text/plain\r\n"
                "Content-Length: 21\r\n"
                "Connection: close\r\n"
                "\r\n"
                "Internal Server Error"
            ).encode('utf-8'))
        except Exception:
            pass
    finally:
        try:
            conn.close()
        except Exception:
            pass

def run_proxy(ip, port, routes):
    """
    Starts the proxy server and listens for incoming connections. 

    The process dinds the proxy server to the specified IP and port.
    In each incomping connection, it accepts the connections and
    spawns a new thread for each client using `handle_client`.
 

    :params ip (str): IP address to bind the proxy server.
    :params port (int): port number to listen on.
    :params routes (dict): dictionary mapping hostnames and location.

    """

    proxy = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    proxy.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    try:
        proxy.bind((ip, port))
        proxy.listen(50)
        print("[Proxy] Listening on IP {} port {}".format(ip,port))
        while True:
            try:
                conn, addr = proxy.accept()
            #
            #  TODO: implement the step of the client incomping connection
            #        using multi-thread programming with the
            #        provided handle_client routine
            #
            except KeyboardInterrupt:
                print("[Proxy] KeyboardInterrupt, shutting down")
                break
            except socket.error as e:
                print("[Proxy] Accept error: {}".format(e))
                continue

            # spawn a thread to handle client
            t = threading.Thread(target=handle_client, args=(ip, port, conn, addr, routes))
            t.daemon = True
            t.start()
    except socket.error as e:
      print("Socket error: {}".format(e))
    finally:
        try:
            proxy.close()
        except Exception:
            pass

def create_proxy(ip, port, routes):
    """
    Entry point for launching the proxy server.

    :params ip (str): IP address to bind the proxy server.
    :params port (int): port number to listen on.
    :params routes (dict): dictionary mapping hostnames and location.
    """

    run_proxy(ip, port, routes)
