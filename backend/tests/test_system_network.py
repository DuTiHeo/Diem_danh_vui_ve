import pytest
from httpx import AsyncClient, ASGITransport
from main import app
import os

@pytest.mark.asyncio
async def test_get_and_update_network_info():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # 1. Get network info
        res = await ac.get("/api/v1/system/network-info")
        assert res.status_code == 200
        data = res.json()
        assert "lan_ip" in data
        assert "checkin_base_url" in data

        # 2. Update network info
        test_ip = "192.168.1.131"
        res2 = await ac.post("/api/v1/system/network-info", json={"lan_ip": test_ip})
        assert res2.status_code == 200
        data2 = res2.json()
        assert data2["success"] is True
        assert data2["lan_ip"] == test_ip

        # 3. Verify get returns updated IP
        res3 = await ac.get("/api/v1/system/network-info")
        assert res3.status_code == 200
        data3 = res3.json()
        assert data3["lan_ip"] == test_ip
