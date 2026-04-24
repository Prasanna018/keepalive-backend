import socket
from urllib.parse import urlparse

FORBIDDEN_IPS = [
    "127.0.0.1",
    "0.0.0.0",
]

def is_safe_url(url: str) -> bool:
    try:
        parsed = urlparse(url)
        hostname = parsed.hostname
        if not hostname:
            return False
        if hostname == "localhost":
            return False
        ip = socket.gethostbyname(hostname)
        if ip in FORBIDDEN_IPS or ip.startswith("10.") or ip.startswith("192.168.") or ip.startswith("172."):
             if ip.startswith("172."):
                 # Check if within 172.16.0.0 to 172.31.255.255
                 second_octet = int(ip.split(".")[1])
                 if 16 <= second_octet <= 31:
                     return False
             else:
                 return False
        return True
    except Exception:
        return False
