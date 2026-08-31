import pwdlib
from fastapi.security import OAuth2PasswordBearer,OAuth2PasswordRequestForm
from pwdlib import PasswordHash
from .db import get_db
from sqlalchemy import select
from jose import jwt,JWTError
from fastapi import Depends,HTTPException,status,APIRouter
from datetime import datetime,timedelta,timezone
from sqlalchemy.orm import Session
from . import models
from .schemas import User,UserInDB,UserCreate,Token,TokenData

router = APIRouter(
    prefix="/auth",
    tags=["auth"]
)

SECRET_KEY ='ca6c98238da45319af13e03ab1a35b816a940cc89d5ace491be9cba770e8da95'
ALGORITHM = 'HS256'
ACCESS_TOKEN_EXPIRE_MINUTES=30

hashed_password=PasswordHash.recommended()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")

def verify_password(plain_password, stored_password):
    return hashed_password.verify(plain_password, stored_password)
def get_password_hash(password):
    return hashed_password.hash(password)

def get_user(db: Session, username: str):
    data=db.execute(select(models.User).where(models.User.username==username))
    result=data.scalar_one_or_none()
    if not result:
        return None
    return UserInDB(
        id=result.id,
        username=result.username,
        email=result.email,
        hashed_password=result.hashed_password,
        is_active=result.is_active,
        role=result.role
    )
def authenticate_user(db, username: str, password: str):
    user=get_user(db,username)
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user

def create_access_token(data:dict, expires_delta:timedelta or None = None):
    to_encode = data.copy()
    if expires_delta:
        expire=datetime.now(timezone.utc)+expires_delta
    else:
        expire=datetime.now(timezone.utc)+timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt=jwt.encode(to_encode,SECRET_KEY,algorithm=ALGORITHM)
    return encoded_jwt

def get_current_user(db: Session=Depends(get_db), token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload=jwt.decode(token,SECRET_KEY,algorithms=[ALGORITHM])
        username=payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception
    user=get_user(db,username=token_data.username)
    if not user:
        raise credentials_exception
    return user
async def get_current_active_user(current_user: UserInDB = Depends(get_current_user)):
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

@router.post("/register")
def register(request:UserCreate, db: Session = Depends(get_db)):
    result1=db.execute(select(models.User).where(models.User.username==request.username))
    existing_username=result1.scalar_one_or_none()
    if existing_username:
        raise HTTPException(status_code=400, detail="Username already exists")
    result2=db.execute(select(models.User).where(models.User.email==request.email))
    existing_email=result2.scalar_one_or_none()
    if existing_email:
        raise HTTPException(status_code=400, detail="Email already exists")

    new_user=models.User(
        username=request.username,
        email=request.email,
        hashed_password=get_password_hash(request.password),
        role='customer'
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return {"message": "User registered Successfully",
            "username":new_user.username}

@router.post("/token",response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(),
                                 db: Session = Depends(get_db)):
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=400,
                            detail="Incorrect username or password",
                            headers={"WWW-Authenticate": "Bearer"})
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(data={"sub":user.username,"role":user.role},expires_delta=access_token_expires)
    return {"access_token": access_token, "token_type": "bearer"}

def get_current_admin(current_user:UserInDB = Depends(get_current_active_user)):
    if not current_user.role == 'admin':
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail="You are not authorized to view this page")
    return current_user


@router.get("/my-profile")
def my_profile(current_user: UserInDB = Depends(get_current_active_user)):
    return current_user

@router.get("/admin/dashboard")
def admin_dashboard(
    current_user: UserInDB = Depends(get_current_admin)
):
    return {
        "message": "Welcome to admin dashboard"
    }







