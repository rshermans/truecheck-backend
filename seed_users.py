"""
Seed script to create initial users with different roles.
Run: python seed_users.py
"""
from sqlmodel import Session, select
from passlib.context import CryptContext
from database import engine, create_db_and_tables
from models.database import User

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Users to seed
SEED_USERS = [
    {
        "username": "rshermans",
        "email": "rshermans@email.com",
        "password": "TRUEcheck@2025",
        "role": "admin"
    },
    {
        "username": "professor_demo",
        "email": "professor@truecheck.edu",
        "password": "Professor@2025",
        "role": "professor"
    },
    {
        "username": "aluno_demo",
        "email": "aluno@truecheck.edu",
        "password": "Aluno@2025",
        "role": "user",
        "school": "Escola Secundária de Lisboa",
        "class_name": "12º A"
    },
    {
        "username": "maria_silva",
        "email": "maria.silva@escola.pt",
        "password": "Aluno@2025",
        "role": "user",
        "school": "Escola Secundária de Lisboa",
        "class_name": "12º A"
    },
    {
        "username": "joao_santos",
        "email": "joao.santos@escola.pt",
        "password": "Aluno@2025",
        "role": "user",
        "school": "Escola Secundária de Lisboa",
        "class_name": "12º A"
    },
    {
        "username": "ana_costa",
        "email": "ana.costa@escola.pt",
        "password": "Aluno@2025",
        "role": "user",
        "school": "Escola Secundária de Lisboa",
        "class_name": "11º B"
    },
    {
        "username": "pedro_alves",
        "email": "pedro.alves@escola.pt",
        "password": "Aluno@2025",
        "role": "user",
        "school": "Escola Secundária de Lisboa",
        "class_name": "11º B"
    }
]

def seed_users():
    """Create or update seed users"""
    # Ensure tables exist
    create_db_and_tables()
    
    with Session(engine) as session:
        for user_data in SEED_USERS:
            # Check if user exists
            existing = session.exec(
                select(User).where(User.username == user_data["username"])
            ).first()
            
            if existing:
                # Update existing user
                existing.email = user_data["email"]
                existing.password_hash = pwd_context.hash(user_data["password"])
                existing.role = user_data["role"]
                existing.is_active = True
                existing.school = user_data.get("school")
                existing.class_name = user_data.get("class_name")
                print(f"✅ Updated user: {user_data['username']} ({user_data['role']})")
            else:
                # Create new user
                user = User(
                    username=user_data["username"],
                    email=user_data["email"],
                    password_hash=pwd_context.hash(user_data["password"]),
                    role=user_data["role"],
                    is_active=True,
                    school=user_data.get("school"),
                    class_name=user_data.get("class_name")
                )
                session.add(user)
                print(f"✅ Created user: {user_data['username']} ({user_data['role']})")
            
            session.commit()
    
    print("\n🎉 Seed complete! Users available:")
    for user in SEED_USERS:
        print(f"   - {user['username']} ({user['role']})")

if __name__ == "__main__":
    seed_users()
