from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel
import os
import socket

router = APIRouter()

class UpdateNetworkInfoRequest(BaseModel):
    lan_ip: str

def is_docker_or_loopback(ip: str) -> bool:
    if not ip or ip in ["localhost", "127.0.0.1", "0.0.0.0", "backend"]:
        return True
    parts = ip.split(".")
    if len(parts) == 4 and parts[0] == "172":
        try:
            second = int(parts[1])
            # 172.16.0.0 - 172.31.255.255 is Docker bridge default network
            if 16 <= second <= 31:
                return True
        except ValueError:
            pass
    return False

def get_server_lan_ip(request: Request | None = None) -> str:
    # 1. Live read from .env files on disk (both root .env and frontend .env.local)
    for env_path in [
        "/app/.env",
        ".env",
        "../.env",
        "../../.env",
        "/app/.env.local",
        "frontend/.env.local",
        "../frontend/.env.local",
    ]:
        if os.path.exists(env_path):
            try:
                with open(env_path, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if line.startswith("SERVER_LAN_IP=") or line.startswith("NEXT_PUBLIC_LAN_IP="):
                            val = line.split("=", 1)[1].strip().strip('"').strip("'")
                            if val and not is_docker_or_loopback(val):
                                return val
            except Exception:
                pass

    # 2. If request came from a client with Host header, prioritize that host!
    if request:
        host_header = request.headers.get("x-forwarded-host") or request.headers.get("host") or ""
        host_only = host_header.split(":")[0].strip()
        if host_only and not is_docker_or_loopback(host_only):
            return host_only

    # 3. Environment variable fallback
    configured_ip = os.getenv("SERVER_LAN_IP") or os.getenv("NEXT_PUBLIC_LAN_IP")
    if configured_ip and not is_docker_or_loopback(configured_ip.strip()):
        return configured_ip.strip()

    # 4. Check socket route
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.settimeout(0.2)
        s.connect(("8.8.8.8", 80))
        detected_ip = s.getsockname()[0]
        s.close()
        if not is_docker_or_loopback(detected_ip):
            return detected_ip
    except Exception:
        pass

    return "192.168.1.131"

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

@router.post("/network-info")
async def update_network_info(req: UpdateNetworkInfoRequest):
    new_ip = req.lan_ip.strip()
    if not new_ip:
        raise HTTPException(status_code=400, detail="Địa chỉ IP không được để trống")

    os.environ["SERVER_LAN_IP"] = new_ip
    os.environ["NEXT_PUBLIC_LAN_IP"] = new_ip

    # Persist to all accessible .env and .env.local files
    target_files = [
        "/app/.env",
        ".env",
        "../.env",
        "../../.env",
        "/app/.env.local",
        "frontend/.env.local",
        "../frontend/.env.local",
    ]
    persisted = []
    for env_path in target_files:
        if os.path.exists(env_path):
            try:
                with open(env_path, "r", encoding="utf-8") as f:
                    content = f.read()

                lines = content.splitlines()
                updated_lines = []
                found_server_ip = False
                found_next_ip = False

                for line in lines:
                    if line.startswith("SERVER_LAN_IP="):
                        updated_lines.append(f"SERVER_LAN_IP={new_ip}")
                        found_server_ip = True
                    elif line.startswith("NEXT_PUBLIC_LAN_IP="):
                        updated_lines.append(f"NEXT_PUBLIC_LAN_IP={new_ip}")
                        found_next_ip = True
                    else:
                        updated_lines.append(line)

                if not found_server_ip and ("frontend" not in env_path and ".local" not in env_path):
                    updated_lines.append(f"SERVER_LAN_IP={new_ip}")
                if not found_next_ip:
                    updated_lines.append(f"NEXT_PUBLIC_LAN_IP={new_ip}")

                with open(env_path, "w", encoding="utf-8") as f:
                    f.write("\n".join(updated_lines) + "\n")
                persisted.append(env_path)
            except Exception:
                pass

    return {
        "success": True,
        "lan_ip": new_ip,
        "persisted_to": persisted,
        "message": f"Đã cập nhật IP mạng thành {new_ip}"
    }
