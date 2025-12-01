"""
Course Repository Implementation
Handles database operations for courses, enrollments, and challenge assignments
"""
import logging
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import select, delete

from domain.entities.course import Course, CourseStatus
from domain.repositories.course_repository import CourseRepository
from infrastructure.persistence.models import CourseModel, course_students, course_challenges

logger = logging.getLogger(__name__)


class CourseRepositoryImpl(CourseRepository):
    """SQLAlchemy implementation of CourseRepository"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def _to_entity(self, model: CourseModel) -> Course:
        """Convert database model to domain entity"""
        # Handle status conversion - status is stored as string in DB
        status_value = model.status
        if isinstance(status_value, CourseStatus):
            status_value = status_value
        elif isinstance(status_value, str):
            # If it's a string, try to convert it to the enum
            try:
                status_value = CourseStatus(status_value.lower())
            except ValueError:
                # If conversion fails, default to DRAFT
                logger.warning(f"[COURSE_STATUS_CONVERSION] Invalid status '{status_value}', defaulting to DRAFT")
                status_value = CourseStatus.DRAFT
        
        return Course(
            id=str(model.id),
            name=model.name,
            description=model.description,
            teacher_id=str(model.teacher_id),
            status=status_value,
            start_date=model.start_date,
            end_date=model.end_date,
            created_at=model.created_at,
            updated_at=model.updated_at
        )
    
    def _to_model(self, entity: Course) -> CourseModel:
        """Convert domain entity to database model"""
        # Convert enum to its string value for storage
        status_value = entity.status.value if isinstance(entity.status, CourseStatus) else entity.status
        
        return CourseModel(
            id=entity.id,
            name=entity.name,
            description=entity.description,
            teacher_id=entity.teacher_id,
            status=status_value,
            start_date=entity.start_date,
            end_date=entity.end_date,
            created_at=entity.created_at,
            updated_at=entity.updated_at
        )
    
    async def save(self, course: Course) -> Course:
        """Save a new course"""
        logger.info(f"[COURSE_SAVE] Creating course: {course.name}, teacher: {course.teacher_id}")
        
        model = self._to_model(course)
        self.db.add(model)
        self.db.commit()
        self.db.refresh(model)
        
        logger.info(f"[COURSE_CREATED] Course {model.id} created successfully")
        return self._to_entity(model)
    
    async def find_by_id(self, course_id: str) -> Optional[Course]:
        """Find a course by its ID"""
        model = self.db.query(CourseModel).filter(CourseModel.id == course_id).first()
        return self._to_entity(model) if model else None
    
    async def find_all(self) -> List[Course]:
        """Get all courses"""
        models = self.db.query(CourseModel).all()
        return [self._to_entity(model) for model in models]
    
    async def find_by_teacher(self, teacher_id: str) -> List[Course]:
        """Find all courses taught by a teacher"""
        logger.debug(f"[COURSE_QUERY] Finding courses for teacher: {teacher_id}")
        
        models = self.db.query(CourseModel).filter(
            CourseModel.teacher_id == teacher_id
        ).all()
        
        return [self._to_entity(model) for model in models]
    
    async def find_by_student(self, student_id: str) -> List[Course]:
        """Find all courses a student is enrolled in"""
        logger.debug(f"[COURSE_QUERY] Finding courses for student: {student_id}")
        
        # Join courses with course_students to find enrollments
        models = self.db.query(CourseModel).join(
            course_students,
            CourseModel.id == course_students.c.course_id
        ).filter(
            course_students.c.user_id == student_id
        ).all()
        
        return [self._to_entity(model) for model in models]
    
    async def update(self, course: Course) -> Course:
        """Update an existing course"""
        logger.info(f"[COURSE_UPDATE] Updating course: {course.id}")
        
        model = self.db.query(CourseModel).filter(CourseModel.id == course.id).first()
        if not model:
            raise ValueError(f"Course {course.id} not found")
        
        # Update fields
        model.name = course.name
        model.description = course.description
        # Convert enum to its string value for storage
        model.status = course.status.value if isinstance(course.status, CourseStatus) else course.status
        model.start_date = course.start_date
        model.end_date = course.end_date
        model.teacher_id = course.teacher_id
        
        self.db.commit()
        self.db.refresh(model)
        
        logger.info(f"[COURSE_UPDATED] Course {course.id} updated successfully")
        return self._to_entity(model)
    
    async def delete(self, course_id: str) -> None:
        """Delete a course"""
        logger.info(f"[COURSE_DELETE] Deleting course: {course_id}")
        
        # Cascade delete will handle enrollments and challenge assignments
        self.db.query(CourseModel).filter(CourseModel.id == course_id).delete()
        self.db.commit()
        
        logger.info(f"[COURSE_DELETED] Course {course_id} deleted successfully")
    
    async def enroll_student(self, course_id: str, student_id: str) -> bool:
        """Enroll a student in a course"""
        logger.info(f"[COURSE_ENROLL] Enrolling student {student_id} in course {course_id}")
        
        try:
            # Check if already enrolled
            existing = self.db.execute(
                select(course_students).where(
                    course_students.c.course_id == course_id,
                    course_students.c.user_id == student_id
                )
            ).first()
            
            if existing:
                logger.warning(f"[COURSE_ENROLL] Student {student_id} already enrolled in {course_id}")
                return False
            
            # Insert enrollment
            self.db.execute(
                course_students.insert().values(
                    course_id=course_id,
                    user_id=student_id
                )
            )
            self.db.commit()
            
            logger.info(f"[COURSE_ENROLLED] Student {student_id} enrolled in course {course_id}")
            return True
            
        except Exception as e:
            logger.error(f"[COURSE_ENROLL_ERROR] Failed to enroll student: {str(e)}")
            self.db.rollback()
            raise
    
    async def unenroll_student(self, course_id: str, student_id: str) -> bool:
        """Remove a student from a course"""
        logger.info(f"[COURSE_UNENROLL] Removing student {student_id} from course {course_id}")
        
        try:
            result = self.db.execute(
                delete(course_students).where(
                    course_students.c.course_id == course_id,
                    course_students.c.user_id == student_id
                )
            )
            self.db.commit()
            
            if result.rowcount > 0:
                logger.info(f"[COURSE_UNENROLLED] Student {student_id} removed from course {course_id}")
                return True
            else:
                logger.warning(f"[COURSE_UNENROLL] Student {student_id} was not enrolled in {course_id}")
                return False
                
        except Exception as e:
            logger.error(f"[COURSE_UNENROLL_ERROR] Failed to unenroll student: {str(e)}")
            self.db.rollback()
            raise
    
    async def get_students(self, course_id: str) -> List[str]:
        """Get all student IDs enrolled in a course"""
        try:
            from uuid import UUID
            # Convert to UUID for proper comparison
            course_uuid = UUID(course_id) if isinstance(course_id, str) else course_id
            result = self.db.execute(
                select(course_students.c.user_id).where(
                    course_students.c.course_id == course_uuid
                )
            )
            return [str(row[0]) for row in result]
        except ValueError as e:
            logger.error(f"[GET_STUDENTS_ERROR] Invalid course_id format: {course_id}, error: {str(e)}")
            return []
        except Exception as e:
            logger.error(f"[GET_STUDENTS_ERROR] Error getting students: {str(e)}", exc_info=True)
            raise
    
    async def assign_challenge(self, course_id: str, challenge_id: str, order_index: int = 0) -> bool:
        """Assign a challenge to a course"""
        logger.info(f"[COURSE_ASSIGN] Assigning challenge {challenge_id} to course {course_id}")
        
        try:
            # Check if already assigned
            existing = self.db.execute(
                select(course_challenges).where(
                    course_challenges.c.course_id == course_id,
                    course_challenges.c.challenge_id == challenge_id
                )
            ).first()
            
            if existing:
                logger.warning(f"[COURSE_ASSIGN] Challenge {challenge_id} already assigned to {course_id}")
                return False
            
            # Insert assignment
            self.db.execute(
                course_challenges.insert().values(
                    course_id=course_id,
                    challenge_id=challenge_id,
                    order_index=order_index
                )
            )
            self.db.commit()
            
            logger.info(f"[COURSE_ASSIGNED] Challenge {challenge_id} assigned to course {course_id}")
            return True
            
        except Exception as e:
            logger.error(f"[COURSE_ASSIGN_ERROR] Failed to assign challenge: {str(e)}")
            self.db.rollback()
            raise
    
    async def unassign_challenge(self, course_id: str, challenge_id: str) -> bool:
        """Remove a challenge assignment from a course"""
        logger.info(f"[COURSE_UNASSIGN] Removing challenge {challenge_id} from course {course_id}")
        
        try:
            result = self.db.execute(
                delete(course_challenges).where(
                    course_challenges.c.course_id == course_id,
                    course_challenges.c.challenge_id == challenge_id
                )
            )
            self.db.commit()
            
            if result.rowcount > 0:
                logger.info(f"[COURSE_UNASSIGNED] Challenge {challenge_id} removed from course {course_id}")
                return True
            else:
                logger.warning(f"[COURSE_UNASSIGN] Challenge {challenge_id} was not assigned to {course_id}")
                return False
                
        except Exception as e:
            logger.error(f"[COURSE_UNASSIGN_ERROR] Failed to unassign challenge: {str(e)}")
            self.db.rollback()
            raise
    
    async def get_challenges(self, course_id: str) -> List[str]:
        """Get all challenge IDs assigned to a course"""
        result = self.db.execute(
            select(course_challenges.c.challenge_id).where(
                course_challenges.c.course_id == course_id
            ).order_by(course_challenges.c.order_index)
        )
        return [str(row[0]) for row in result]

