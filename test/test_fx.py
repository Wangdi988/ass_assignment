import os
# from fastapi.testclient import TestClient
# from unittest.mock import AsyncMock, patch
# from app.main import app
# from app.service.fx_service import fx_rate_service
# from app.cache.redis import get_redis

os.environ["SECRET_KEY"] = "your-very-secure-secret-key-for-jwt-tokens"
os.environ["REDIS_URL"] = "redis://localhost:6379"



import pytest
from httpx import AsyncClient
from unittest.mock import AsyncMock, patch
from app.main import app

@pytest.mark.asyncio
async def test_read_fx_success():
    payload = {
        "alpha_currency_code": "USD",
        "date_time": "2025-12-09 15:01:51.300",
    }

    mock_fx_rate = AsyncMock()
    mock_fx_rate.return_value.model_dump = lambda: {
        "buy_rate": 88.75,
        "sell_rate": 91.50,
        "currency": "USD",
        "timestamp": "2025-12-09 15:01:51.300"
    }

    async def mock_get_redis():
        return None

    with patch("app.cache.redis.get_redis", mock_get_redis):
        with patch("app.service.fx_service.fx_rate_service", mock_fx_rate):
            async with AsyncClient(app=app, base_url="http://testserver") as ac:
                response = await ac.post("/api/fx/read", json=payload)

    assert response.status_code == 200
    data = response.json()
    assert data["response_code"] == "0000"
    assert data["response_data"]["currency"] == "USD"
