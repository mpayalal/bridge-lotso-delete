import jwt
from fastapi import Header, HTTPException
from typing import Optional


async def get_current_user_id(authorization: Optional[str] = Header(None)) -> str:
    """Extract user_id from JWT token in Authorization header"""
    print(f"Authorization Header: {authorization}")
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid token")
    
    token = authorization.split(" ")[1]
    decoded = jwt.decode(token, options={"verify_signature": False})
    
    user_id = decoded.get("user_id") or decoded.get("sub")
    
    if not user_id:
        raise HTTPException(status_code=401, detail="User ID not found in token")
    
    return user_id
