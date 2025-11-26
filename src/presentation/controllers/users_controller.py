"""
Users Controller - CRUD operations for user management.
Handles user creation, updates, deletion, and listing.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from application.dtos.auth_dto import (
    CreateUserRequest, 
    UpdateUserRequest, 
    UserResponse,
    DeleteUserResponse
)
from application.use_cases.auth.create_user_use_case import CreateUserUseCase
from application.use_cases.auth.update_user_use_case import UpdateUserUseCase
from application.use_cases.auth.delete_user_use_case import DeleteUserUseCase
from infrastructure.repositories.user_repository_impl import UserRepositoryImpl
from infrastructure.services.password_service import PasswordService
from infrastructure.persistence.database import get_db
from presentation.middleware.auth_middleware import get_current_user
from domain.entities.user import User

router = APIRouter(
    prefix="/users",
    tags=["users"],
    responses={404: {"description": "User not found"}}
)


def _build_create_user_use_case(db: Session) -> CreateUserUseCase:
    """Factory for creating the CreateUser use case with dependencies."""
    user_repository = UserRepositoryImpl(db)
    password_service = PasswordService()
    return CreateUserUseCase(user_repository, password_service)


def _build_update_user_use_case(db: Session) -> UpdateUserUseCase:
    """Factory for creating the UpdateUser use case with dependencies."""
    user_repository = UserRepositoryImpl(db)
    password_service = PasswordService()
    return UpdateUserUseCase(user_repository, password_service)


def _build_delete_user_use_case(db: Session) -> DeleteUserUseCase:
    """Factory for creating the DeleteUser use case with dependencies."""
    user_repository = UserRepositoryImpl(db)
    return DeleteUserUseCase(user_repository)


@router.post(
    "/",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new user"
)
async def create_user(
    user_data: CreateUserRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Create a new user in the system.
    
    - **email**: User's email address (must be unique)
    - **password**: User's password (will be hashed)
    - **first_name**: User's first name
    - **last_name**: User's last name
    - **role**: User role (STUDENT, PROFESSOR, ADMIN) - default is STUDENT
    
    Requires authentication. Only ADMIN users can create new users.
    """
    # Verificar que el usuario actual es administrador
    if current_user.get("role") != "ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can create users"
        )
    
    try:
        use_case = _build_create_user_use_case(db)
        result = await use_case.execute(
            email=user_request.email,
            password=user_request.password,
            first_name=user_request.first_name,
            last_name=user_request.last_name,
            role=user_request.role
        )
        return result
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        print(f"Error creating user: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error creating user"
        )


@router.get(
    "/",
    response_model=List[UserResponse],
    summary="Get all users"
)
async def get_all_users(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Get a list of all users in the system.
    
    Requires authentication. Only ADMIN and PROFESSOR users can view all users.
    """
    # Verificar permisos: current_user es un dict con "id", "email", "role"
    user_role = current_user.get("role", "")
    if user_role not in ["ADMIN", "PROFESSOR"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to view all users"
        )
    
    try:
        user_repository = UserRepositoryImpl(db)
        users = await user_repository.find_all()
        
        return [
            {
                "id": user.id,
                "email": user.email,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "role": user.role
            }
            for user in users
        ]
        
    except Exception as e:
        print(f"Error getting users: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving users"
        )


@router.get(
    "/{user_id}",
    response_model=UserResponse,
    summary="Get user by ID"
)
async def get_user_by_id(
    user_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Get a specific user by their ID.
    
    - **user_id**: The ID of the user to retrieve
    
    Requires authentication. Users can view their own profile, or admins/professors can view any user.
    """
    # Los usuarios pueden ver su propio perfil, o admins/profesores pueden ver cualquiera
    user_role = current_user.get("role", "")
    if user_id != current_user.get("id") and user_role not in ["ADMIN", "PROFESSOR"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to view this user"
        )
    
    try:
        user_repository = UserRepositoryImpl(db)
        user = await user_repository.find_by_id(user_id)
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        return {
            "id": user.id,
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "role": user.role
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error getting user: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving user"
        )


@router.put(
    "/{user_id}",
    response_model=UserResponse,
    summary="Update user"
)
async def update_user(
    user_id: str,
    user_update: UpdateUserRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Update a user's information.
    
    - **user_id**: The ID of the user to update
    - **email**: New email (optional)
    - **password**: New password (optional)
    - **first_name**: New first name (optional)
    - **last_name**: New last name (optional)
    - **role**: New role (optional, admin only)
    
    Requires authentication. Users can update their own profile (except role), 
    or admins can update any user. Cannot demote the last admin.
    """
    # Basic permission check: users can update themselves, admins can update anyone
    if user_id != current_user.get("id") and current_user.get("role") != "ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to update this user"
        )
    
    try:
        use_case = _build_update_user_use_case(db)
        result = await use_case.execute(
            user_id=user_id,
            current_user_id=current_user.get("id"),
            current_user_role=current_user.get("role"),
            email=user_update.email,
            password=user_update.password,
            first_name=user_update.first_name,
            last_name=user_update.last_name,
            role=user_update.role
        )
        return result
        
    except ValueError as e:
        # Determine appropriate status code
        error_msg = str(e).lower()
        if "not found" in error_msg:
            status_code = status.HTTP_404_NOT_FOUND
        elif "only admin" in error_msg or "cannot change" in error_msg or "cannot demote" in error_msg:
            status_code = status.HTTP_403_FORBIDDEN
        else:
            status_code = status.HTTP_400_BAD_REQUEST
            
        raise HTTPException(
            status_code=status_code,
            detail=str(e)
        )
    except Exception as e:
        print(f"Error updating user: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error updating user"
        )


@router.delete(
    "/{user_id}",
    response_model=DeleteUserResponse,
    summary="Delete user"
)
async def delete_user(
    user_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Delete a user from the system.
    
    - **user_id**: The ID of the user to delete
    
    Requires authentication. Only ADMIN users can delete users.
    Users cannot delete themselves.
    Cannot delete the last admin.
    """
    try:
        use_case = _build_delete_user_use_case(db)
        await use_case.execute(
            user_id=user_id,
            current_user_id=current_user.get("id"),
            current_user_role=current_user.get("role")
        )
        
        return {
            "message": "User deleted successfully",
            "user_id": user_id
        }
        
    except ValueError as e:
        # Determine appropriate status code based on error message
        error_msg = str(e).lower()
        if "not found" in error_msg:
            status_code = status.HTTP_404_NOT_FOUND
        elif "only admin" in error_msg or "cannot delete" in error_msg:
            status_code = status.HTTP_403_FORBIDDEN
        elif "your own" in error_msg or "last admin" in error_msg:
            status_code = status.HTTP_400_BAD_REQUEST
        else:
            status_code = status.HTTP_400_BAD_REQUEST
            
        raise HTTPException(
            status_code=status_code,
            detail=str(e)
        )
    except Exception as e:
        print(f"Error deleting user: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error deleting user"
        )

