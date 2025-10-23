from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from ...application.dtos.auth_dto import LoginRequest, LoginResponse
from ...application.use_cases.auth.login_use_case import LoginUseCase
from ...infrastructure.repositories.user_repository_impl import UserRepositoryImpl
from ...infrastructure.services.password_service import PasswordService
from ...infrastructure.services.jwt_service import JWTService
from ...infrastructure.persistence.database import get_db

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=LoginResponse)
async def login(login_request: LoginRequest, db: Session = Depends(get_db)):
    try:
        user_repository = UserRepositoryImpl(db)
        password_service = PasswordService()
        jwt_service = JWTService()
        
        login_use_case = LoginUseCase(user_repository, password_service, jwt_service)
        
        result = await login_use_case.execute(login_request.email, login_request.password)
        return result
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )
