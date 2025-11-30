from typing import Dict, Any, Optional
from datetime import datetime
from domain.entities.user import User, UserRole
from domain.repositories.user_repository import UserRepository


class UpdateUserUseCase:
    def __init__(self, user_repository: UserRepository, password_service):
        self.user_repository = user_repository
        self.password_service = password_service

    async def execute(
        self,
        user_id: str,
        current_user_id: str,
        current_user_role: UserRole,
        email: Optional[str] = None,
        password: Optional[str] = None,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        role: Optional[UserRole] = None
    ) -> Dict[str, Any]:
        # Buscar usuario por ID
        user = await self.user_repository.find_by_id(user_id)
        if not user:
            raise ValueError("User not found")

        # Validación de permisos para cambiar roles
        if role is not None and role != user.role:
            # Solo admins pueden cambiar roles
            if current_user_role != UserRole.ADMIN:
                raise ValueError("Only administrators can change user roles")
            
            # No puedes cambiar tu propio rol
            if user_id == current_user_id:
                raise ValueError("You cannot change your own role")
            
            # Prevenir demotar al último admin
            if user.role == UserRole.ADMIN and role != UserRole.ADMIN:
                all_users = await self.user_repository.find_all()
                admin_count = sum(1 for u in all_users if u.role == UserRole.ADMIN)
                if admin_count <= 1:
                    raise ValueError("Cannot demote the last administrator")
            
            user.role = role

        # Si se actualiza el email, verificar que no esté en uso
        if email and email != user.email:
            existing_user = await self.user_repository.find_by_email(email)
            if existing_user:
                raise ValueError("Email already in use")
            user.email = email

        # Si se actualiza la contraseña, hashearla
        if password:
            if len(password) < 6:
                raise ValueError("Password must be at least 6 characters long")
            user.password = self.password_service.hash_password(password)

        # Actualizar otros campos si se proporcionan
        if first_name is not None:
            if not first_name.strip():
                raise ValueError("First name cannot be empty")
            user.first_name = first_name
            
        if last_name is not None:
            if not last_name.strip():
                raise ValueError("Last name cannot be empty")
            user.last_name = last_name

        user.updated_at = datetime.utcnow()

        # Guardar cambios
        updated_user = await self.user_repository.update(user)

        return {
            "id": updated_user.id,
            "email": updated_user.email,
            "first_name": updated_user.first_name,
            "last_name": updated_user.last_name,
            "role": updated_user.role
        }

