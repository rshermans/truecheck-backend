from fastapi import APIRouter, HTTPException, Depends
from sqlmodel import Session, select, func
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from pydantic import BaseModel

from models.database import User, AnalysisResult, Classroom
from routes.auth import verify_token
from database import get_session
import uuid

router = APIRouter(prefix="/api/professor", tags=["professor"])

class ClassroomCreate(BaseModel):
    name: str
    school: str
    description: Optional[str] = None
    theme_color: str = "blue"

@router.post("/classes")
async def create_classroom(
    data: ClassroomCreate,
    token_data: dict = Depends(verify_token),
    session: Session = Depends(get_session)
):
    """Create a new real Classroom entity"""
    user = session.get(User, token_data["user_id"])
    if not user or user.role not in ["professor", "admin"]:
        raise HTTPException(status_code=403, detail="Acesso negado")
    
    # Generate unique invite code
    code = str(uuid.uuid4())[:6].upper()
    while session.exec(select(Classroom).where(Classroom.invite_code == code)).first():
        code = str(uuid.uuid4())[:6].upper()
        
    classroom = Classroom(
        name=data.name,
        school=data.school,
        description=data.description,
        theme_color=data.theme_color,
        invite_code=code,
        professor_id=user.id
    )
    session.add(classroom)
    session.commit()
    session.refresh(classroom)
    return classroom

@router.delete("/classes/{class_id}")
async def delete_classroom(
    class_id: int,
    token_data: dict = Depends(verify_token),
    session: Session = Depends(get_session)
):
    """Delete a classroom entity"""
    user = session.get(User, token_data["user_id"])
    classroom = session.get(Classroom, class_id)
    if not classroom:
         raise HTTPException(status_code=404, detail="Turma não encontrada")
         
    if classroom.professor_id != user.id and user.role != "admin":
         raise HTTPException(status_code=403, detail="Não tem permissão")
         
    # Review: Should we delete students or just unassign?
    # Unassign for safety
    for student in classroom.students:
        student.classroom_id = None
        session.add(student)
        
    session.delete(classroom)
    session.commit()
    return {"message": "Turma eliminada"}


@router.get("/my-classes")
async def get_my_classes(
    token_data: dict = Depends(verify_token),
    session: Session = Depends(get_session)
):
    """Get classes managed by the professor (Hybrid: Legacy + Real Entities)"""
    # Verify user is professor or admin
    user = session.get(User, token_data["user_id"])
    if not user or user.role not in ["professor", "admin"]:
        raise HTTPException(status_code=403, detail="Acesso negado. Apenas professores podem acessar.")
    
    # 1. Legacy Classes (grouped from users without classroom_id)
    statement = (
        select(User.school, User.class_name, func.count(User.id).label("student_count"))
        .where(User.role == "user")
        .where(User.class_name.isnot(None))
        .where(User.classroom_id.is_(None)) # Only users not in a real classroom
        .group_by(User.school, User.class_name)
    )
    
    legacy_results = session.exec(statement).all()
    
    classes = []
    
    # 2. Active Classrooms (Real entities)
    active_classrooms = session.exec(
        select(Classroom).where(Classroom.professor_id == user.id)
    ).all()
    
    for c in active_classrooms:
        # Count students manually or optmize with subquery
        count = len(c.students)
        classes.append({
            "id": c.id, # Real ID (int)
            "school": c.school,
            "class_name": c.name,
            "description": c.description,
            "invite_code": c.invite_code,
            "theme_color": c.theme_color,
            "student_count": count,
            "is_legacy": False
        })
    
    # Add legacy
    for school, class_name, student_count in legacy_results:
        classes.append({
            "school": school or "Sem escola",
            "class_name": class_name,
            "student_count": student_count,
            "id": f"legacy_{school}_{class_name}",  # String ID
            "is_legacy": True,
            "theme_color": "gray"
        })
    
    return {"classes": classes}

@router.get("/class/{school}/{class_name}/students")
async def get_class_students(
    school: str,
    class_name: str,
    token_data: dict = Depends(verify_token),
    session: Session = Depends(get_session)
):
    """Get students from a specific class"""
    # Verify user is professor or admin
    user = session.get(User, token_data["user_id"])
    if not user or user.role not in ["professor", "admin"]:
        raise HTTPException(status_code=403, detail="Acesso negado. Apenas professores podem acessar.")
    
    # Get students
    statement = (
        select(User)
        .where(User.role == "user")
        .where(User.school == school)
        .where(User.class_name == class_name)
    )
    
    students = session.exec(statement).all()
    
    # Get analysis count for each student
    students_data = []
    for student in students:
        analysis_count = session.exec(
            select(func.count(AnalysisResult.id))
            .where(AnalysisResult.user_id == student.id)
        ).one()
        
        students_data.append({
            "id": student.id,
            "username": student.username,
            "email": student.email,
            "created_at": student.created_at.isoformat(),
            "analysis_count": analysis_count,
            "is_active": student.is_active
        })
    
    return {"students": students_data}

@router.get("/class/{school}/{class_name}/stats")
async def get_class_statistics(
    school: str,
    class_name: str,
    token_data: dict = Depends(verify_token),
    session: Session = Depends(get_session)
):
    """Get statistics for a specific class"""
    # Verify user is professor or admin
    user = session.get(User, token_data["user_id"])
    if not user or user.role not in ["professor", "admin"]:
        raise HTTPException(status_code=403, detail="Acesso negado. Apenas professores podem acessar.")
    
    # Get students from this class
    students = session.exec(
        select(User)
        .where(User.role == "user")
        .where(User.school == school)
        .where(User.class_name == class_name)
    ).all()
    
    student_ids = [s.id for s in students]
    
    if not student_ids:
        return {
            "total_students": 0,
            "total_analyses": 0,
            "average_ai_score": 0,
            "average_user_score": 0,
            "average_discrepancy": 0,
            "recent_activity": [],
            "verdict_distribution": {},
            "activity_timeline": []
        }
    
    # Get all analyses from these students
    analyses = session.exec(
        select(AnalysisResult)
        .where(AnalysisResult.user_id.in_(student_ids))
    ).all()
    
    # Calculate statistics
    total_analyses = len(analyses)
    avg_ai_score = sum(a.ai_score for a in analyses) / total_analyses if total_analyses > 0 else 0
    avg_user_score = sum(a.user_score for a in analyses) / total_analyses if total_analyses > 0 else 0
    avg_discrepancy = sum(a.discrepancy for a in analyses) / total_analyses if total_analyses > 0 else 0
    
    # Verdict distribution
    verdict_counts = {}
    for analysis in analyses:
        verdict_counts[analysis.verdict] = verdict_counts.get(analysis.verdict, 0) + 1
    
    # Recent activity (last 10 analyses)
    recent = sorted(analyses, key=lambda x: x.timestamp, reverse=True)[:10]
    recent_activity = []
    for analysis in recent:
        student = next((s for s in students if s.id == analysis.user_id), None)
        recent_activity.append({
            "id": analysis.id,
            "student_name": student.username if student else "Desconhecido",
            "content_preview": analysis.content[:100] + "..." if len(analysis.content) > 100 else analysis.content,
            "verdict": analysis.verdict,
            "ai_score": analysis.ai_score,
            "timestamp": analysis.timestamp.isoformat()
        })
    
    # Activity timeline (last 30 days)
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    timeline_analyses = [a for a in analyses if a.timestamp >= thirty_days_ago]
    
    # Group by date
    activity_by_date = {}
    for analysis in timeline_analyses:
        date_key = analysis.timestamp.date().isoformat()
        activity_by_date[date_key] = activity_by_date.get(date_key, 0) + 1
    
    activity_timeline = [
        {"date": date, "count": count}
        for date, count in sorted(activity_by_date.items())
    ]
    
    return {
        "total_students": len(students),
        "total_analyses": total_analyses,
        "average_ai_score": round(avg_ai_score, 1),
        "average_user_score": round(avg_user_score, 1),
        "average_discrepancy": round(avg_discrepancy, 1),
        "recent_activity": recent_activity,
        "verdict_distribution": verdict_counts,
        "activity_timeline": activity_timeline
    }

@router.get("/student/{student_id}/details")
async def get_student_details(
    student_id: int,
    token_data: dict = Depends(verify_token),
    session: Session = Depends(get_session)
):
    """Get detailed information about a specific student"""
    # Verify user is professor or admin
    user = session.get(User, token_data["user_id"])
    if not user or user.role not in ["professor", "admin"]:
        raise HTTPException(status_code=403, detail="Acesso negado. Apenas professores podem acessar.")
    
    # Get student
    student = session.get(User, student_id)
    if not student or student.role != "user":
        raise HTTPException(status_code=404, detail="Aluno não encontrado")
    
    # Get student's analyses
    analyses = session.exec(
        select(AnalysisResult)
        .where(AnalysisResult.user_id == student_id)
        .order_by(AnalysisResult.timestamp.desc())
    ).all()
    
    # Calculate statistics
    total_analyses = len(analyses)
    avg_ai_score = sum(a.ai_score for a in analyses) / total_analyses if total_analyses > 0 else 0
    avg_user_score = sum(a.user_score for a in analyses) / total_analyses if total_analyses > 0 else 0
    avg_discrepancy = sum(a.discrepancy for a in analyses) / total_analyses if total_analyses > 0 else 0
    
    # Verdict distribution
    verdict_counts = {}
    for analysis in analyses:
        verdict_counts[analysis.verdict] = verdict_counts.get(analysis.verdict, 0) + 1
    
    # Recent analyses
    recent_analyses = []
    for analysis in analyses[:20]:  # Last 20
        recent_analyses.append({
            "id": analysis.id,
            "content_preview": analysis.content[:100] + "..." if len(analysis.content) > 100 else analysis.content,
            "verdict": analysis.verdict,
            "ai_score": analysis.ai_score,
            "user_score": analysis.user_score,
            "discrepancy": analysis.discrepancy,
            "timestamp": analysis.timestamp.isoformat()
        })
    
    return {
        "student": {
            "id": student.id,
            "username": student.username,
            "email": student.email,
            "school": student.school,
            "class_name": student.class_name,
            "created_at": student.created_at.isoformat(),
            "is_active": student.is_active
        },
        "statistics": {
            "total_analyses": total_analyses,
            "average_ai_score": round(avg_ai_score, 1),
            "average_user_score": round(avg_user_score, 1),
            "average_discrepancy": round(avg_discrepancy, 1),
            "verdict_distribution": verdict_counts
        },
        "recent_analyses": recent_analyses
    }

@router.delete("/students/{student_id}")
async def delete_student(
    student_id: int,
    token_data: dict = Depends(verify_token),
    session: Session = Depends(get_session)
):
    """Delete a student from the system"""
    # Verify user is professor or admin
    user = session.get(User, token_data["user_id"])
    if not user or user.role not in ["professor", "admin"]:
        raise HTTPException(status_code=403, detail="Acesso negado. Apenas professores podem eliminar alunos.")
    
    # Get student
    student = session.get(User, student_id)
    if not student:
        raise HTTPException(status_code=404, detail="Aluno não encontrado")
    
    if student.role != "user":
        raise HTTPException(status_code=400, detail="Apenas utilizadores do tipo 'user' podem ser eliminados")
    
    # Delete student's analyses first (cascade)
    from models.database import AnalysisResult
    analyses = session.exec(select(AnalysisResult).where(AnalysisResult.user_id == student_id)).all()
    for analysis in analyses:
        session.delete(analysis)
    
    # Delete student
    session.delete(student)
    session.commit()
    
    return {"message": "Aluno eliminado com sucesso"}


class StudentCreate(BaseModel):
    username: str
    password: str
    email: Optional[str] = None
    school: str
    class_name: str
    is_active: bool = True

@router.post("/students")
async def create_student(
    student_data: StudentCreate,
    token_data: dict = Depends(verify_token),
    session: Session = Depends(get_session)
):
    """Create a new student in a specific class"""
    # Verify user is professor or admin
    user = session.get(User, token_data["user_id"])
    if not user or user.role not in ["professor", "admin"]:
        raise HTTPException(status_code=403, detail="Acesso negado. Apenas professores podem acessar.")
    
    from passlib.context import CryptContext
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    
    # Check if username already exists
    existing = session.exec(select(User).where(User.username == student_data.username)).first()
    if existing:
        raise HTTPException(status_code=400, detail="Username já existe")
    
    password_hash = pwd_context.hash(student_data.password)
    new_user = User(
        username=student_data.username,
        password_hash=password_hash,
        email=student_data.email,
        role="user",
        school=student_data.school,
        class_name=student_data.class_name,
        is_active=student_data.is_active
    )
    session.add(new_user)
    session.commit()
    session.refresh(new_user)
    return new_user

