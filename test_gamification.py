"""
Unit Tests for Gamification System
Tests XP calculation, level progression, and award logic
"""
import pytest
from services.gamification import calculate_level, get_xp_for_next_level, award_xp, LEVEL_THRESHOLDS
from models.database import User
from sqlmodel import Session, create_engine, SQLModel
from sqlmodel.pool import StaticPool


@pytest.fixture(name="session")
def session_fixture():
    """Create a test database session"""
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


def test_calculate_level():
    """Test level calculation based on XP"""
    assert calculate_level(0) == 1
    assert calculate_level(50) == 1
    assert calculate_level(100) == 2
    assert calculate_level(250) == 3
    assert calculate_level(500) == 4
    assert calculate_level(1000) == 5
    assert calculate_level(5000) == 10


def test_get_xp_for_next_level():
    """Test XP progress calculation"""
    # Level 1 (0-100 XP)
    current, needed = get_xp_for_next_level(50)
    assert current == 50
    assert needed == 100
    
    # Level 2 (100-250 XP)
    current, needed = get_xp_for_next_level(150)
    assert current == 50  # 150 - 100 = 50 XP into level 2
    assert needed == 150  # 250 - 100 = 150 XP needed for level 3
    
    # Max level
    current, needed = get_xp_for_next_level(5000)
    assert needed == 0  # No next level


def test_award_xp_no_level_up(session):
    """Test XP award without level up"""
    user = User(username="test_user", password_hash="hash", xp=50, level=1)
    session.add(user)
    session.commit()
    
    result = award_xp(user, 30, session)
    
    assert result["xp_earned"] == 30
    assert result["total_xp"] == 80
    assert result["old_level"] == 1
    assert result["new_level"] == 1
    assert result["level_up"] is False
    assert user.xp == 80
    assert user.level == 1


def test_award_xp_with_level_up(session):
    """Test XP award with level up"""
    user = User(username="test_user", password_hash="hash", xp=95, level=1)
    session.add(user)
    session.commit()
    
    result = award_xp(user, 10, session)
    
    assert result["xp_earned"] == 10
    assert result["total_xp"] == 105
    assert result["old_level"] == 1
    assert result["new_level"] == 2
    assert result["level_up"] is True
    assert user.xp == 105
    assert user.level == 2


def test_award_xp_multiple_levels(session):
    """Test XP award that skips multiple levels"""
    user = User(username="test_user", password_hash="hash", xp=50, level=1)
    session.add(user)
    session.commit()
    
    # Award 500 XP (should jump to level 4)
    result = award_xp(user, 500, session)
    
    assert result["total_xp"] == 550
    assert result["new_level"] == 4
    assert result["level_up"] is True


def test_level_thresholds_consistency():
    """Test that level thresholds are consistent and increasing"""
    levels = sorted(LEVEL_THRESHOLDS.keys())
    for i in range(len(levels) - 1):
        current_level = levels[i]
        next_level = levels[i + 1]
        assert LEVEL_THRESHOLDS[next_level] > LEVEL_THRESHOLDS[current_level], \
            f"Level {next_level} threshold should be greater than level {current_level}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
