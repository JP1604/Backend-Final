from typing import Dict, Any
from domain.entities.user import User
from domain.repositories.user_repository import UserRepository


class LoginUseCase:
    def __init__(self, user_repository: UserRepository, password_service, jwt_service):
        self.user_repository = user_repository
        self.password_service = password_service
        self.jwt_service = jwt_service

    async def execute(self, email: str, password: str) -> Dict[str, Any]:
        # Buscar usuario por email
        user = await self.user_repository.find_by_email(email)
        
        if not user:
            raise ValueError("Invalid credentials")

        # Verificar contraseña usando bcrypt
        is_password_correct = await self.password_service.verify_password(
            password, 
            user.password
        )
        if not is_password_correct:
            raise ValueError("Invalid credentials")

        # Generar token JWT
        access_token = self.jwt_service.create_access_token(
            data={"sub": user.id, "email": user.email, "role": user.role}
        )

        return {
            "user": {
                "id": user.id,
                "email": user.email,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "role": user.role
            },
            "access_token": access_token,
            "token_type": "bearer"
        }
