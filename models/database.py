from typing import Optional, Dict, Any, List
from sqlmodel import Field, SQLModel, JSON, Relationship
from datetime import datetime
import json

class User(SQLModel, table=True):
    """User authentication model"""
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(unique=True, index=True)
    password_hash: str
    email: Optional[str] = Field(default=None)
    role: str = Field(default="user")  # admin, professor, user
    school: Optional[str] = Field(default=None)
    class_name: Optional[str] = Field(default=None)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    is_active: bool = Field(default=True)
    
    # Gamification fields
    xp: int = Field(default=0)  # Experience points
    level: int = Field(default=1)  # Current level
    
    
    # Relationships
    analysis_results: List["AnalysisResult"] = Relationship(back_populates="user")
    materials: List["Material"] = Relationship(back_populates="author")

class Material(SQLModel, table=True):
    """Educational materials and resources"""
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str
    type: str  # pdf, image, video, link
    url: str
    description: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    file_size: Optional[str] = None
    
    # Author
    user_id: Optional[int] = Field(default=None, foreign_key="user.id")
    author: Optional[User] = Relationship(back_populates="materials")

class Challenge(SQLModel, table=True):
    """Gamification challenges"""
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str
    description: str
    points: int = 10
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)

class AnalysisResult(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    content: str = Field(index=True)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    # Scores
    ai_score: int
    user_score: int
    discrepancy: int
    
    # User Info (backward compatibility)
    student_name: Optional[str] = Field(default="Anônimo")
    
    # New: Foreign key to User
    user_id: Optional[int] = Field(default=None, foreign_key="user.id")
    user: Optional[User] = Relationship(back_populates="analysis_results")
    
    # Verdicts
    verdict: str
    discrepancy_level: str
    
    # Full Data (stored as JSON string for flexibility)
    full_json_data: str = Field(default="{}")
    
    # Sources (stored as JSON string)
    sources_data: str = Field(default="[]")

    @property
    def sources(self) -> List[Dict[str, Any]]:
        return json.loads(self.sources_data)
    
    @sources.setter
    def sources(self, value: List[Dict[str, Any]]):
        self.sources_data = json.dumps(value)

    @property
    def details(self) -> Dict[str, Any]:
        return json.loads(self.full_json_data)
    
    @details.setter
    def details(self, value: Dict[str, Any]):
        self.full_json_data = json.dumps(value)

class InboxMessage(SQLModel, table=True):
    """Community inbox messages (Service Learning)"""
    id: Optional[int] = Field(default=None, primary_key=True)
    sender_id: Optional[int] = Field(default=None, foreign_key="user.id")
    sender_name: str
    email: str
    subject: str
    message: str
    is_read: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Optional relationship
    sender: Optional[User] = Relationship()

class News(SQLModel, table=True):
    """Fact-checked news articles"""
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str
    summary: str
    url: str
    image_url: Optional[str] = None
    published_at: datetime = Field(default_factory=datetime.utcnow)
    source: str
    verdict: str  # Verdadeiro, Falso, Parcial
    language: str = "pt"
    category: str = "Geral"
    tags: str = Field(default="[]")  # JSON string of tags
    
    @property
    def tags_list(self) -> List[str]:
        return json.loads(self.tags)
    
    @tags_list.setter
    def tags_list(self, value: List[str]):
        self.tags = json.dumps(value)
