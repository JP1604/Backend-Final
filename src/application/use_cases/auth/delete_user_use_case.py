from domain.repositories.user_repository import UserRepository
from domain.entities.user import UserRole


class DeleteUserUseCase:
    def __init__(self, user_repository: UserRepository):
        self.user_repository = user_repository

    async def execute(
        self, 
        user_id: str,
        current_user_id: str,
        current_user_role: UserRole
    ) -> bool:
        # Solo admins pueden eliminar usuarios
        if current_user_role != UserRole.ADMIN:
            raise ValueError("Only administrators can delete users")

        # Verificar que el usuario existe
        user = await self.user_repository.find_by_id(user_id)
        if not user:
            raise ValueError("User not found")

        # No permitir auto-eliminación
        if user_id == current_user_id:
            raise ValueError("You cannot delete your own account")

        # Prevenir eliminación del último admin
        if user.role == UserRole.ADMIN:
            all_users = await self.user_repository.find_all()
            admin_count = sum(1 for u in all_users if u.role == UserRole.ADMIN)
            if admin_count <= 1:
                raise ValueError("Cannot delete the last administrator account")

        # Eliminar usuario
        await self.user_repository.delete(user_id)
        return True

