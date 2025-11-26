"""
Controlador de autenticación.
Maneja el login y autenticación de usuarios.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from application.dtos.auth_dto import LoginRequest, LoginResponse, CreateUserRequest, UserResponse
from application.use_cases.auth.login_use_case import LoginUseCase
from application.use_cases.auth.create_user_use_case import CreateUserUseCase
from infrastructure.repositories.user_repository_impl import UserRepositoryImpl
from infrastructure.services.password_service import PasswordService
from infrastructure.services.jwt_service import JWTService
from infrastructure.persistence.database import get_db

router = APIRouter(
    prefix="/auth", 
    tags=["auth"],
    responses={401: {"description": "Credenciales inválidas"}}
)


def _build_login_use_case(db: Session) -> LoginUseCase:
    """Factory para crear el caso de uso de login con sus dependencias."""
    user_repository = UserRepositoryImpl(db)
    password_service = PasswordService()
    jwt_service = JWTService()
    
    return LoginUseCase(user_repository, password_service, jwt_service)


@router.post(
    "/login", 
    response_model=LoginResponse,
    summary="Iniciar sesión"
)
async def login(
    login_request: LoginRequest, 
    db: Session = Depends(get_db)
):
    """
    Autentica un usuario y devuelve un token JWT.
    
    - **email**: Correo electrónico del usuario
    - **password**: Contraseña del usuario
    
    Retorna un token de acceso válido por 24 horas.
    """
    try:
        use_case = _build_login_use_case(db)
        result = await use_case.execute(
            login_request.email, 
            login_request.password
        )
        return result
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"}
        )
    except Exception as e:
        print(f"Error en login: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor"
        )


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar nuevo usuario"
)
async def register(
    user_data: CreateUserRequest,
    db: Session = Depends(get_db)
):
    """
    Registra un nuevo usuario en el sistema.
    
    - **email**: Correo electrónico único del usuario
    - **password**: Contraseña (será hasheada)
    - **first_name**: Nombre del usuario
    - **last_name**: Apellido del usuario
    - **role**: Rol del usuario (por defecto: STUDENT)
    """
    try:
        user_repository = UserRepositoryImpl(db)
        password_service = PasswordService()
        
        use_case = CreateUserUseCase(user_repository, password_service)
        
        result = await use_case.execute(
            email=user_data.email,
            password=user_data.password,
            first_name=user_data.first_name,
            last_name=user_data.last_name,
            role=user_data.role
        )
        
        return result
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        print(f"Error en registro: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor"
        )
