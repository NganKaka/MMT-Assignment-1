import json
import socket
import argparse
from daemon.weaprous import WeApRous

PORT = 8000 
app = WeApRous()

@app.route('/login', methods=['POST'])
def login(headers="guest", body="anonymous"):
    creds = {}
    try:
        pairs = body.split('&')
        for pair in pairs:
            key, value = pair.split('=', 1)
            creds[key] = value
    except Exception:
        pass 
        
    username = creds.get('username')
    password = creds.get('password')

    if username == 'admin' and password == 'password':
        print("[SampleApp] Login SUCCESS for user: {}".format(username))
        return "LOGIN_SUCCESS"
    else:
        print("[SampleApp] Login FAILED for user: {}".format(username))
        return "LOGIN_FAILED"

@app.route('/hello', methods=['PUT'])
def hello(headers, body):
    print("[SampleApp] ['PUT'] Hello in {} to {}".format(headers, body))

if __name__ == "__main__":
    # Ví dụ: python start_sampleapp.py --server-port 8001
    parser = argparse.ArgumentParser(prog='Backend', description='', epilog='Beckend daemon')
    parser.add_argument('--server-ip', default='0.0.0.0')
    parser.add_argument('--server-port', type=int, default=PORT)
 
    args = parser.parse_args()
    ip = args.server_ip
    port = args.server_port

    app.prepare_address(ip, port)
    app.run()