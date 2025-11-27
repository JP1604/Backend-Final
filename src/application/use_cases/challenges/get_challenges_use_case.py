from typing import List, Dict, Optional
from domain.entities.challenge import Challenge
from domain.entities.user import UserRole
from domain.repositories.challenge_repository import ChallengeRepository
from domain.repositories.course_repository import CourseRepository


class GetChallengesUseCase:
    def __init__(self, challenge_repository: ChallengeRepository, course_repository: Optional[CourseRepository] = None):
        self.challenge_repository = challenge_repository
        self.course_repository = course_repository

    async def execute(
        self,
        user_id: str,
        user_role: UserRole,
        course_id: Optional[str] = None,
        status: Optional[str] = None,
        difficulty: Optional[str] = None
    ) -> List[Challenge]:
        filters = {}

        # Si es estudiante, solo puede ver challenges publicados
        if user_role == UserRole.STUDENT:
            filters["status"] = "published"
            
            # Si es estudiante, solo mostrar challenges de cursos en los que está inscrito
            if self.course_repository:
                student_courses = await self.course_repository.find_by_student(user_id)
                enrolled_course_ids = [c.id for c in student_courses]
                
                # Si se especifica un course_id, verificar que el estudiante esté inscrito
                if course_id:
                    if course_id not in enrolled_course_ids:
                        return []  # No está inscrito en este curso
                else:
                    # Si no se especifica course_id, solo mostrar challenges de cursos inscritos
                    # Necesitamos filtrar por course_id en los challenges asignados
                    # Esto se hace mejor en el repositorio o aquí
                    pass

        if course_id:
            filters["course_id"] = course_id

        if status:
            filters["status"] = status

        if difficulty:
            filters["difficulty"] = difficulty

        challenges = await self.challenge_repository.find_all(filters)
        
        # Si es estudiante y no hay course_id específico, filtrar por cursos inscritos
        if user_role == UserRole.STUDENT and not course_id and self.course_repository:
            student_courses = await self.course_repository.find_by_student(user_id)
            enrolled_course_ids = [c.id for c in student_courses]
            
            # Solo incluir challenges que pertenezcan a cursos en los que está inscrito
            filtered_challenges = []
            for challenge in challenges:
                if challenge.course_id and challenge.course_id in enrolled_course_ids:
                    filtered_challenges.append(challenge)
            challenges = filtered_challenges

        # Filtrar challenges que el usuario puede ver
        filtered = [
            challenge for challenge in challenges
            if challenge.can_be_viewed_by(user_role)
        ]
        
        return filtered
