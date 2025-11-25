from typing import Dict, Any
from datetime import datetime
import uuid
from domain.entities.user import User, UserRole
from domain.repositories.user_repository import UserRepository


class CreateUserUseCase:
    def __init__(self, user_repository: UserRepository, password_service):
        self.user_repository = user_repository
        self.password_service = password_service

    async def execute(
        self,
        email: str,
        password: str,
        first_name: str,
        last_name: str,
        role: UserRole = UserRole.STUDENT
    ) -> Dict[str, Any]:
        # Validar datos de entrada
        self._validate_input(email, password, first_name, last_name)
        
        # Verificar si el email ya existe
        existing_user = await self.user_repository.find_by_email(email)
        if existing_user:
            raise ValueError("Email already registered")

        # Hash de la contraseña
        hashed_password = self.password_service.hash_password(password)

        # Crear entidad de usuario
        user = User(
            id=str(uuid.uuid4()),
            email=email,
            password=hashed_password,
            first_name=first_name,
            last_name=last_name,
            role=role,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )

        # Guardar en la base de datos
        saved_user = await self.user_repository.save(user)

        return {
            "id": saved_user.id,
            "email": saved_user.email,
            "first_name": saved_user.first_name,
            "last_name": saved_user.last_name,
            "role": saved_user.role
        }
    
    def _validate_input(self, email: str, password: str, first_name: str, last_name: str):
        """Validate user input data"""
        # Email validation
        if not email or not email.strip():
            raise ValueError("Email is required")
        if "@" not in email or "." not in email:
            raise ValueError("Invalid email format")
        
        # Password validation
        if not password or len(password) < 6:
            raise ValueError("Password must be at least 6 characters long")
        
        # Name validation
        if not first_name or not first_name.strip():
            raise ValueError("First name is required")
        if not last_name or not last_name.strip():
            raise ValueError("Last name is required")

