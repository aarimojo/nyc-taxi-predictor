from fastapi import Security, HTTPException
from fastapi.security.api_key import APIKeyHeader
from starlette.status import HTTP_403_FORBIDDEN
import os

API_KEY = os.getenv("API_KEY")
api_key_header = APIKeyHeader(name="Authorization", auto_error=False)

async def verify_api_key(api_key_header: str = Security(api_key_header)):
    if not api_key_header or api_key_header.split(' ')[1] != API_KEY:
        raise HTTPException(
            status_code=HTTP_403_FORBIDDEN, detail="Could not validate credentials"
        )
    return api_key_header