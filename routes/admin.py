from fastapi import APIRouter, HTTPException, Depends, status
from sqlmodel import Session, select, func
from typing import List, Optional
from datetime import datetime, timedelta
from pydantic import BaseModel

from database import get_session
from models.database import User, Material, Challenge, AnalysisResult, InboxMessage
from routes.auth import verify_token

router = APIRouter(prefix="/api/admin", tags=["admin"])

def verify_admin(user: dict = Depends(verify_token)):
    """Dependency to verify if user is admin"""
    if user["role"] != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso restrito a administradores"
        )
    return user

def verify_staff(user: dict = Depends(verify_token)):
    """Dependency to verify if user is admin or professor"""
    if user["role"] not in ["admin", "professor"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso restrito a staff"
        )
    return user

# --- Dashboard Stats ---
@router.get("/stats")
async def get_dashboard_stats(
    user: dict = Depends(verify_admin),
    session: Session = Depends(get_session)
):
    """Get system statistics for admin dashboard"""
    total_users = session.exec(select(func.count(User.id))).first()
    total_analyses = session.exec(select(func.count(AnalysisResult.id))).first()
    total_materials = session.exec(select(func.count(Material.id))).first()
    total_challenges = session.exec(select(func.count(Challenge.id))).first()
    
    # Ensure we get the integer value (handle potential tuple/row return)
    # If it's a tuple/row, take the first element. If it's already int (unlikely with exec), use it.
    total_users = total_users if isinstance(total_users, int) else total_users[0]
    total_analyses = total_analyses if isinstance(total_analyses, int) else total_analyses[0]
    total_materials = total_materials if isinstance(total_materials, int) else total_materials[0]
    total_challenges = total_challenges if isinstance(total_challenges, int) else total_challenges[0]
    
    recent_users_objs = session.exec(select(User).order_by(User.created_at.desc()).limit(5)).all()
    recent_users = [
        {
            "id": u.id,
            "username": u.username,
            "email": u.email,
            "role": u.role,
            "created_at": u.created_at
        }
        for u in recent_users_objs
    ]
    
    return {
        "counts": {
            "users": total_users,
            "analyses": total_analyses,
            "materials": total_materials,
            "challenges": total_challenges
        },
        "recent_users": recent_users
    }

# --- Analytics ---
@router.get("/analytics/trends")
async def get_trends(
    user: dict = Depends(verify_admin),
    session: Session = Depends(get_session)
):
    """Get analysis trends for the last 30 days"""
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    query = select(AnalysisResult.id, AnalysisResult.timestamp).where(AnalysisResult.timestamp >= thirty_days_ago)
    results = session.exec(query).all()
    trends: dict[str, int] = {}
    for result in results:
        date_str = result.timestamp.strftime('%Y-%m-%d')
        trends[date_str] = trends.get(date_str, 0) + 1
    final_trends = []
    for i in range(30):
        date = (thirty_days_ago + timedelta(days=i)).strftime('%Y-%m-%d')
        final_trends.append({"date": date, "count": trends.get(date, 0)})
    return final_trends

@router.get("/analytics/scores")
async def get_score_distribution(
    user: dict = Depends(verify_admin),
    session: Session = Depends(get_session)
):
    """Get distribution of AI scores"""
    results = session.exec(select(AnalysisResult.id, AnalysisResult.ai_score)).all()
    distribution = {"0-20": 0, "21-40": 0, "41-60": 0, "61-80": 0, "81-100": 0}
    for result in results:
        score = result.ai_score
        if score <= 20:
            distribution["0-20"] += 1
        elif score <= 40:
            distribution["21-40"] += 1
        elif score <= 60:
            distribution["41-60"] += 1
        elif score <= 80:
            distribution["61-80"] += 1
        else:
            distribution["81-100"] += 1
    return [{"range": k, "count": v} for k, v in distribution.items()]

@router.get("/analytics/activity")
async def get_user_activity(
    user: dict = Depends(verify_admin),
    session: Session = Depends(get_session)
):
    """Get top active users"""
    results = session.exec(select(AnalysisResult.id, AnalysisResult.student_name, AnalysisResult.user_id)).all()
    user_counts: dict[str, int] = {}
    for result in results:
        name = result.student_name or "Anônimo"
        if result.user_id:
            user_obj = session.get(User, result.user_id)
            if user_obj:
                name = user_obj.username
        user_counts[name] = user_counts.get(name, 0) + 1
    sorted_users = sorted(user_counts.items(), key=lambda x: x[1], reverse=True)[:5]
    return [{"username": name, "count": count} for name, count in sorted_users]

# --- User Management (CRUD) ---
class UserCreate(BaseModel):
    username: str
    password: str
    email: Optional[str] = None
    role: str = "user"
    is_active: bool = True
    school: Optional[str] = None
    class_name: Optional[str] = None

class UserUpdate(BaseModel):
    email: Optional[str] = None
    role: Optional[str] = None
    is_active: Optional[bool] = None
    school: Optional[str] = None
    class_name: Optional[str] = None

@router.get("/users")
async def list_users(
    user: dict = Depends(verify_admin),
    session: Session = Depends(get_session)
):
    """List all users"""
    users = session.exec(select(User)).all()
    return users

@router.post("/users")
async def create_user(
    user_data: UserCreate,
    user: dict = Depends(verify_admin),
    session: Session = Depends(get_session)
):
    """Create a new user (admin only)"""
    from passlib.context import CryptContext
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    
    # Check if username already exists
    existing = session.exec(select(User).where(User.username == user_data.username)).first()
    if existing:
        raise HTTPException(status_code=400, detail="Username já existe")
    
    password_hash = pwd_context.hash(user_data.password)
    new_user = User(
        username=user_data.username,
        password_hash=password_hash,
        email=user_data.email,
        role=user_data.role,
        is_active=user_data.is_active,
        school=user_data.school,
        class_name=user_data.class_name
    )
    session.add(new_user)
    session.commit()
    session.refresh(new_user)
    return new_user

@router.put("/users/{user_id}")
async def update_user(
    user_id: int,
    updates: UserUpdate,
    user: dict = Depends(verify_admin),
    session: Session = Depends(get_session)
):
    """Update user details"""
    db_user = session.get(User, user_id)
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    if updates.email is not None:
        db_user.email = updates.email
    if updates.role is not None:
        db_user.role = updates.role
    if updates.is_active is not None:
        db_user.is_active = updates.is_active
    if updates.school is not None:
        db_user.school = updates.school
    if updates.class_name is not None:
        db_user.class_name = updates.class_name
        
    session.add(db_user)
    session.commit()
    session.refresh(db_user)
    return db_user

@router.delete("/users/{user_id}")
async def delete_user(
    user_id: int,
    user: dict = Depends(verify_admin),
    session: Session = Depends(get_session)
):
    """Delete a user"""
    db_user = session.get(User, user_id)
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    session.delete(db_user)
    session.commit()
    return {"message": "User deleted"}

# --- Material Management ---
class MaterialCreate(BaseModel):
    title: str
    type: str
    url: str
    file_size: Optional[str] = None
    description: Optional[str] = None

@router.post("/materials")
async def create_material(
    material_data: MaterialCreate,
    user: dict = Depends(verify_staff),
    session: Session = Depends(get_session)
):
    """Create new educational material"""
    material = Material(
        **material_data.dict(),
        user_id=user["user_id"]
    )
    session.add(material)
    session.commit()
    session.refresh(material)
    return material

@router.get("/materials")
async def list_materials(
    session: Session = Depends(get_session)
):
    """List all materials (public)"""
    materials = session.exec(select(Material).order_by(Material.created_at.desc())).all()
    return materials

@router.put("/materials/{material_id}")
async def update_material(
    material_id: int,
    material_data: MaterialCreate,
    user: dict = Depends(verify_staff),
    session: Session = Depends(get_session)
):
    """Update an existing material"""
    material = session.get(Material, material_id)
    if not material:
        raise HTTPException(status_code=404, detail="Material não encontrado")
    
    # Update fields
    material.title = material_data.title
    material.type = material_data.type
    material.url = material_data.url
    material.description = material_data.description
    if material_data.file_size:
        material.file_size = material_data.file_size
    
    session.add(material)
    session.commit()
    session.refresh(material)
    return material

@router.delete("/materials/{material_id}")
async def delete_material(
    material_id: int,
    user: dict = Depends(verify_staff),
    session: Session = Depends(get_session)
):
    """Delete a material"""
    material = session.get(Material, material_id)
    if not material:
        raise HTTPException(status_code=404, detail="Material não encontrado")
    
    session.delete(material)
    session.commit()
    return {"message": "Material eliminado com sucesso"}

# --- Challenge Management ---
class ChallengeCreate(BaseModel):
    title: str
    description: str
    points: int = 10

@router.post("/challenges")
async def create_challenge(
    challenge_data: ChallengeCreate,
    user: dict = Depends(verify_admin),
    session: Session = Depends(get_session)
):
    """Create new gamification challenge"""
    challenge = Challenge(**challenge_data.dict())
    session.add(challenge)
    session.commit()
    session.refresh(challenge)
    return challenge

@router.get("/challenges")
async def list_challenges(
    session: Session = Depends(get_session)
):
    challenges = session.exec(select(Challenge).where(Challenge.is_active == True)).all()
    return challenges

# --- Inbox Management ---
@router.get("/inbox")
async def get_inbox_messages(
    user: dict = Depends(verify_admin),
    session: Session = Depends(get_session)
):
    """Get all community messages"""
    messages = session.exec(select(InboxMessage).order_by(InboxMessage.created_at.desc())).all()
    return messages

@router.put("/inbox/{message_id}/read")
async def mark_message_read(
    message_id: int,
    user: dict = Depends(verify_admin),
    session: Session = Depends(get_session)
):
    """Mark message as read"""
    message = session.get(InboxMessage, message_id)
    if not message:
        raise HTTPException(status_code=404, detail="Message not found")
    message.is_read = True
    session.add(message)
    session.commit()
    return {"message": "Marked as read"}
