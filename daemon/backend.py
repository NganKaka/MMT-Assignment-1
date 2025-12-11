import socket
import threading
import argparse

from .response import *
from .httpadapter import HttpAdapter
from .dictionary import CaseInsensitiveDict

def handle_client(ip, port, conn, addr, routes):
    daemon = HttpAdapter(ip, port, conn, addr, routes)
    daemon.handle_client(conn, addr, routes)

def run_backend(ip, port, routes):
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        server.bind((ip, port))
        server.listen(50)
        print("[Backend] Listening on port {}".format(port))
        if routes != {}:
            print("[Backend] route settings {}".format(routes))

        while True:
            conn, addr = server.accept()
            client_thread = threading.Thread(
                target=handle_client,
                args=(ip, port, conn, addr, routes)
            )
            client_thread.daemon = True
            client_thread.start()
    except socket.error as e:
      print("Socket error: {}".format(e))

def create_backend(ip, port, routes={}):
    run_backend(ip, port, routes)
    
    
    #done TODO