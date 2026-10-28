from fastapi import APIRouter, Request
import os
import socket

router = APIRouter()

def get_server_lan_ip() -> str:
    # 1. Prioritize environment variable
    configured_ip = os.getenv("SERVER_LAN_IP")
    if configured_ip and configured_ip.strip():
        return configured_ip.strip()

    # 2. Try socket route lookup
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.settimeout(0.2)
        s.connect(("8.8.8.8", 80))
        detected_ip = s.getsockname()[0]
        s.close()
        # If in docker bridge (172.x), fallback to host LAN IP
        if detected_ip.startswith("172.") or detected_ip.startswith("127."):
            return "192.168.1.131"
        return detected_ip
    except Exception:
        return "192.168.1.131"

@router.get("/network-info")
async def get_network_info(request: Request):
    lan_ip = get_server_lan_ip()
    client_ip = request.client.host if request.client else "unknown"
    return {
        "lan_ip": lan_ip,
        "frontend_port": 3000,
        "backend_port": 8000,
        "client_ip": client_ip,
        "checkin_base_url": f"http://{lan_ip}:3000"
    }
