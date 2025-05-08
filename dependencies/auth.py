import jwt
from fastapi import Depends, Header, HTTPException
from sqlmodel import Session, select
from typing import Optional
from db.db import get_session
from models.User import User

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

async def get_current_user(
    user_id: str = Depends(get_current_user_id),
    session: Session = Depends(get_session)
) -> User:
    """Get user record from database using the ID from the token"""
    user = session.exec(select(User).where(User.id == user_id)).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user