"""Dependency injection for FastAPI endpoints."""

import os
from fastapi import Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from jose import JWTError, jwt

from db.database import SessionLocal
from db.models import User, Student

API_SECRET_KEY = os.environ.get("API_SECRET_KEY")
if not API_SECRET_KEY:
    raise RuntimeError(
        "API_SECRET_KEY environment variable is required. "
        "Set it before starting the application."
    )
ALGORITHM = "HS256"


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _decode_token(request: Request) -> dict:
    token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="يرجى تسجيل الدخول أولًا",
        )
    try:
        payload = jwt.decode(token, API_SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="انتهت جلسة الدخول أو أصبحت غير صالحة، سجّل الدخول مرة أخرى",
        )
    return payload


def get_current_user(request: Request, db: Session = Depends(get_db)) -> User:
    """Resolve the authenticated supervisor from the legacy researcher role."""
    payload = _decode_token(request)
    role = payload.get("role")
    if role != "researcher":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="هذه الصفحة متاحة للمشرف فقط",
        )
    try:
        user_id = int(payload.get("sub"))
    except (TypeError, ValueError):
        raise HTTPException(status_code=401, detail="جلسة الدخول غير صالحة")
    user = db.query(User).filter(User.id == user_id).first()
    if user is None or not user.is_active or user.role != "researcher":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="حساب المشرف غير متاح، سجّل الدخول مرة أخرى",
        )
    return user


def get_current_student(request: Request, db: Session = Depends(get_db)) -> Student:
    payload = _decode_token(request)
    role = payload.get("role")
    if role != "student":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="هذه الصفحة متاحة للطالب فقط",
        )
    try:
        student_id = int(payload.get("sub"))
    except (TypeError, ValueError):
        raise HTTPException(status_code=401, detail="جلسة الدخول غير صالحة")
    student = db.query(Student).filter(Student.id == student_id).first()
    if student is None or not student.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="حساب الطالب غير متاح، تواصل مع المشرف",
        )
    return student


get_current_researcher = get_current_user


def get_any_authenticated(request: Request, db: Session = Depends(get_db)):
    payload = _decode_token(request)
    role = payload.get("role")
    try:
        entity_id = int(payload.get("sub"))
    except (TypeError, ValueError):
        raise HTTPException(status_code=401, detail="جلسة الدخول غير صالحة")
    if role == "researcher":
        entity = db.query(User).filter(User.id == entity_id, User.is_active.is_(True)).first()
    elif role == "student":
        entity = db.query(Student).filter(Student.id == entity_id, Student.is_active.is_(True)).first()
    else:
        raise HTTPException(status_code=403, detail="نوع الحساب غير معروف")
    if entity is None:
        raise HTTPException(status_code=401, detail="الحساب غير موجود أو غير نشط")
    return role, entity
