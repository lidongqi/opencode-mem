from fastapi import Security, HTTPException, status
from fastapi.security import APIKeyHeader
from typing import Optional
import os

API_KEY_NAME = "X-API-Key"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)


async def get_api_key(api_key: Optional[str] = Security(api_key_header)) -> str:
    """验证 API Key"""
    # 如果未配置 API_KEY，则不需要认证（开发模式）
    expected_api_key = os.getenv("MEM0_API_KEY")

    if not expected_api_key:
        # 开发模式：未配置 API_KEY 则跳过认证
        return "dev-mode"

    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API Key is required",
        )

    if api_key != expected_api_key:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid API Key",
        )

    return api_key
