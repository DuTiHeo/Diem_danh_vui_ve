from fastapi import APIRouter, Request
import os
import socket

router = APIRouter()

def get_server_lan_ip(request: Request | None = None) -> str:
    # 1. If request came from a client with Host header, prioritize that host!
    if request:
        host_header = request.headers.get("x-forwarded-host") or request.headers.get("host") or ""
        host_only = host_header.split(":")[0].strip()
        if host_only and host_only not in ["localhost", "127.0.0.1", "backend"]:
            return host_only

    # 2. Prioritize environment variable if explicitly set
    configured_ip = os.getenv("SERVER_LAN_IP")
    if configured_ip and configured_ip.strip() and configured_ip.strip() not in ["localhost", "127.0.0.1"]:
        return configured_ip.strip()

    # 3. Try socket route lookup
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.settimeout(0.2)
        s.connect(("8.8.8.8", 80))
        detected_ip = s.getsockname()[0]
        s.close()
        # If in docker bridge (172.19.x), fallback
        if not (detected_ip.startswith("172.19.") or detected_ip.startswith("172.17.") or detected_ip.startswith("127.")):
            return detected_ip
    except Exception:
        pass

    return "172.18.57.85"

@router.get("/network-info")
async def get_network_info(request: Request):
    lan_ip = get_server_lan_ip(request)
    client_ip = request.client.host if request.client else "unknown"
    return {
        "lan_ip": lan_ip,
        "frontend_port": 3000,
        "backend_port": 8000,
        "client_ip": client_ip,
        "checkin_base_url": f"http://{lan_ip}:3000"
    }
