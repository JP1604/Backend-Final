from sqlalchemy import Column, String, Integer, DateTime, Text, Boolean, JSON, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.sql import func
from ..persistence.database import Base
from ...domain.entities.user import UserRole
from ...domain.entities.challenge import ChallengeDifficulty, ChallengeStatus
from ...domain.entities.submission import SubmissionStatus, ProgrammingLanguage


class UserModel(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    email = Column(String(255), unique=True, nullable=False, index=True)
    password = Column(String(255), nullable=False)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    role = Column(SQLEnum(UserRole), nullable=False, default=UserRole.STUDENT)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class ChallengeModel(Base):
    __tablename__ = "challenges"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    difficulty = Column(String(20), nullable=False)  # VARCHAR en BD, no ENUM
    tags = Column(ARRAY(String), nullable=False)
    time_limit = Column(Integer, nullable=False)
    memory_limit = Column(Integer, nullable=False)
    status = Column(String(20), nullable=False, default='draft')  # VARCHAR en BD, no ENUM
    created_by = Column(UUID(as_uuid=True), nullable=False, index=True)
    course_id = Column(UUID(as_uuid=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class SubmissionModel(Base):
    __tablename__ = "submissions"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    user_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    challenge_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    language = Column(SQLEnum(ProgrammingLanguage), nullable=False)
    code = Column(Text, nullable=False)
    status = Column(SQLEnum(SubmissionStatus), nullable=False, default=SubmissionStatus.QUEUED)
    score = Column(Integer, nullable=False, default=0)
    time_ms_total = Column(Integer, nullable=False, default=0)
    cases = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class TestCaseModel(Base):
    __tablename__ = "test_cases"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    challenge_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    input = Column(Text, nullable=False)
    expected_output = Column(Text, nullable=False)
    is_hidden = Column(Boolean, nullable=False, default=False)
    order_index = Column(Integer, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
