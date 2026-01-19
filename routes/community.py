from fastapi import APIRouter, HTTPException, Depends, status
from sqlmodel import Session, select
from typing import List
from pydantic import BaseModel

from database import get_session
from models.database import InboxMessage, User
from routes.auth import verify_token

router = APIRouter(prefix="/api/community", tags=["community"])

class MessageCreate(BaseModel):
    subject: str
    message: str
    email: str  # Allow anonymous/guest emails too if needed, or pre-fill from user

@router.post("/contact")
async def send_message(
    msg_data: MessageCreate,
    user: dict = Depends(verify_token),
    session: Session = Depends(get_session)
):
    """Send a message to the community inbox"""
    # Get user details
    db_user = session.get(User, user["user_id"])
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
        
    message = InboxMessage(
        sender_id=db_user.id,
        sender_name=db_user.username,
        email=msg_data.email or db_user.email,
        subject=msg_data.subject,
        message=msg_data.message
    )
    session.add(message)
    session.commit()
    return {"message": "Mensagem enviada com sucesso"}
