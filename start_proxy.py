import socket
import threading
import argparse
import re
from collections import defaultdict
from daemon import create_proxy

PROXY_PORT = 8080

def parse_virtual_hosts(config_file):
    with open(config_file, 'r') as f:
        config_text = f.read()

    # Tìm tất cả các block host "..." { ... }
    host_blocks = re.findall(r'host\s+"([^"]+)"\s*\{(.*?)\}', config_text, re.DOTALL)

    routes = {}
    
    for host, block in host_blocks:
        # Tìm tất cả proxy_pass trong block đó
        # Kết quả proxy_passes sẽ là list: ['192.168.56.103:9001', ...]
        proxy_passes = re.findall(r'proxy_pass\s+http://([^\s;]+);', block)
        
        # Tìm dist_policy
        policy_match = re.search(r'dist_policy\s+([^\s;]+)', block)
        if policy_match:
            dist_policy_map = policy_match.group(1)
        else:
            dist_policy_map = 'round-robin'
            
        # --- ĐÃ SỬA: Logic lưu trữ routes ---
        # Luôn lưu proxy_map dưới dạng LIST để dễ xử lý Round-Robin
        if proxy_passes:
            routes[host] = (proxy_passes, dist_policy_map)
        else:
            print(f"[Warning] Host {host} has no proxy_pass defined.")

    # Debug: In ra bảng định tuyến đã parse
    print("\n--- PROXY ROUTING TABLE ---")
    for key, value in routes.items():
        targets, policy = value
        print(f"Host: {key} -> Policy: {policy} -> Targets: {targets}")
    print("---------------------------\n")
    
    return routes

if __name__ == "__main__":
    parser = argparse.ArgumentParser(prog='Proxy', description='HTTP Load Balancer', epilog='Proxy daemon')
    parser.add_argument('--server-ip', default='0.0.0.0')
    parser.add_argument('--server-port', type=int, default=PROXY_PORT)
 
    args = parser.parse_args()
    ip = args.server_ip
    port = args.server_port

    # Đọc config và chạy proxy
    try:
        routes = parse_virtual_hosts("config/proxy.conf")
        create_proxy(ip, port, routes)
    except FileNotFoundError:
        print("Error: Config file 'config/proxy.conf' not found.")