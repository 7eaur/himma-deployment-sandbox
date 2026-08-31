"""Protected endpoints — supervisor dashboard and student lifecycle.

The internal JWT role remains ``researcher`` for backward compatibility with
accepted stages, while all user-facing language uses the approved term
``المشرف``.
"""

import json
import secrets
from datetime import datetime, timezone

import bcrypt
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from db.models import AssessmentSession, AuditLog, Attempt, ContentItem, Student, User
from dependencies import get_db, get_current_user, get_current_student, get_any_authenticated
from journey import build_journey_summary
import schemas

router = APIRouter(tags=["Protected"])


def _hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def _verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))


def _audit(
    db: Session,
    *,
    actor_id: int,
    action: str,
    entity_type: str,
    entity_id: str,
    details: dict | None = None,
) -> None:
    db.add(AuditLog(
        actor_role="researcher",
        actor_id=actor_id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        details=json.dumps(details, ensure_ascii=False, sort_keys=True) if details else None,
    ))


@router.get("/me")
def get_me(auth=Depends(get_any_authenticated)):
    role, entity = auth
    if role == "researcher":
        return {
            "id": entity.id,
            "username": entity.username,
            "full_name": entity.username,
            "role": "researcher",
        }
    return {"id": entity.id, "full_name": entity.name, "role": "student"}


@router.get("/researcher/account", response_model=schemas.SupervisorResponse)
def get_supervisor_account(user: User = Depends(get_current_user)):
    return user


@router.patch("/researcher/account", response_model=schemas.SupervisorResponse)
def update_supervisor_account(
    body: schemas.SupervisorProfileUpdateRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    duplicate = db.query(User).filter(User.username == body.username, User.id != user.id).first()
    if duplicate:
        raise HTTPException(status_code=409, detail="اسم المستخدم مستخدم بالفعل")
    old_username = user.username
    user.username = body.username
    _audit(db, actor_id=user.id, action="supervisor.profile.update", entity_type="user", entity_id=str(user.id), details={"old_username": old_username, "new_username": body.username})
    db.commit()
    db.refresh(user)
    return user


@router.post("/researcher/account/password")
def change_supervisor_password(
    body: schemas.SupervisorPasswordChangeRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not _verify_password(body.current_password, user.password_hash):
        raise HTTPException(status_code=400, detail="كلمة المرور الحالية غير صحيحة")
    if body.current_password == body.new_password:
        raise HTTPException(status_code=400, detail="اختر كلمة مرور جديدة مختلفة عن الحالية")
    user.password_hash = _hash_password(body.new_password)
    _audit(db, actor_id=user.id, action="supervisor.password.update", entity_type="user", entity_id=str(user.id))
    db.commit()
    return {"message": "تم تغيير كلمة المرور بنجاح"}


@router.get("/researcher/supervisors", response_model=list[schemas.SupervisorResponse])
def list_supervisors(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return db.query(User).filter(User.role == "researcher").order_by(User.created_at, User.id).all()


@router.post("/researcher/supervisors", status_code=status.HTTP_201_CREATED, response_model=schemas.SupervisorResponse)
def create_supervisor(
    body: schemas.SupervisorCreateRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if db.query(User).filter(User.username == body.username).first():
        raise HTTPException(status_code=409, detail="اسم المستخدم مستخدم بالفعل")
    created = User(username=body.username, password_hash=_hash_password(body.password), role="researcher", is_active=True)
    db.add(created)
    try:
        db.flush()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="تعذر إنشاء المشرف بهذا الاسم")
    _audit(db, actor_id=user.id, action="supervisor.create", entity_type="user", entity_id=str(created.id), details={"username": created.username})
    db.commit()
    db.refresh(created)
    return created


def _completed_session(db: Session, student_id: int, session_type: str) -> bool:
    return db.query(AssessmentSession.id).filter(
        AssessmentSession.student_id == student_id,
        AssessmentSession.session_type == session_type,
        AssessmentSession.status == "completed",
    ).first() is not None


def _core_progress(db: Session, student_id: int) -> tuple[int, bool]:
    session = db.query(AssessmentSession).filter(
        AssessmentSession.student_id == student_id,
        AssessmentSession.session_type == "core",
    ).order_by(AssessmentSession.id.desc()).first()
    if not session:
        return 0, False
    completed = db.query(Attempt.id).join(ContentItem, ContentItem.id == Attempt.item_id).filter(
        Attempt.session_id == session.id,
        Attempt.status == "completed",
        ContentItem.kind == "core_activity",
        ContentItem.level_id == session.assigned_level,
    ).count()
    return completed, session.status == "completed" and completed >= 10


def _student_payload(db: Session, student: Student) -> dict:
    pretest_completed = _completed_session(db, student.id, "pretest")
    posttest_completed = _completed_session(db, student.id, "posttest")
    core_completed_items, core_completed = _core_progress(db, student.id)
    journey = build_journey_summary(db, student)
    return {
        "id": student.id,
        "full_name": student.name,
        "access_code": student.access_code,
        "grade_level": student.grade_level,
        "current_level": student.current_level,
        "status": "active" if student.is_active else "inactive",
        "posttest_enabled": student.posttest_enabled,
        "posttest_eligible": pretest_completed and journey["learning_journey_completed"] and not posttest_completed,
        "core_completed_items": core_completed_items,
        "core_total_items": 10,
        "core_completed": core_completed,
        "created_at": student.created_at,
    }


def _generate_access_code(db: Session) -> str:
    for _ in range(50):
        code = str(secrets.randbelow(900000) + 100000)
        if not db.query(Student).filter(Student.access_code == code).first():
            return code
    raise RuntimeError("تعذر إنشاء رمز دخول فريد")


def _ensure_unique_access_code(db: Session, code: str, *, excluding_student_id: int | None = None) -> None:
    query = db.query(Student).filter(Student.access_code == code)
    if excluding_student_id is not None:
        query = query.filter(Student.id != excluding_student_id)
    if query.first():
        raise HTTPException(status_code=409, detail="رمز الدخول مستخدم لطالب آخر، اختر رمزًا مختلفًا")


@router.get("/profile", response_model=schemas.StudentProfileResponse)
def student_profile(student: Student = Depends(get_current_student), db: Session = Depends(get_db)):
    active_session = db.query(AssessmentSession).filter(
        AssessmentSession.student_id == student.id,
        AssessmentSession.status == "in_progress",
    ).order_by(AssessmentSession.id.desc()).first()
    pretest_completed = _completed_session(db, student.id, "pretest")
    posttest_completed = _completed_session(db, student.id, "posttest")
    journey = build_journey_summary(db, student)

    if active_session and active_session.session_type in {"pretest", "posttest"}:
        next_action = "resume"
    elif not pretest_completed:
        next_action = "pretest"
    elif posttest_completed:
        next_action = "completed"
    elif journey["learning_journey_completed"] and student.posttest_enabled:
        next_action = "posttest"
    else:
        next_action = "learning"
    return {
        "id": student.id,
        "full_name": student.name,
        "access_code": student.access_code,
        "grade_level": student.grade_level,
        "current_level": student.current_level,
        "status": "active" if student.is_active else "inactive",
        "posttest_enabled": student.posttest_enabled,
        "next_action": next_action,
        "active_session": active_session,
    }


@router.get("/researcher/students", response_model=list[schemas.StudentResponse])
def list_students(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    students = db.query(Student).order_by(Student.created_at, Student.id).all()
    return [_student_payload(db, student) for student in students]


@router.get("/researcher/students/{student_id}", response_model=schemas.StudentResponse)
def get_student(student_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    student = db.query(Student).filter(Student.id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="الطالب غير موجود")
    return _student_payload(db, student)


@router.post("/researcher/students", status_code=status.HTTP_201_CREATED, response_model=schemas.StudentResponse)
def create_student(
    body: schemas.StudentCreateRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    db.query(User).filter(User.id == user.id).with_for_update().one()
    if db.query(Student).count() >= 15:
        raise HTTPException(status_code=409, detail="وصلت الدراسة إلى الحد الأقصى وهو 15 طالبًا")
    requested_code = body.access_code
    if requested_code:
        _ensure_unique_access_code(db, requested_code)
    for _ in range(5):
        code = requested_code or _generate_access_code(db)
        student = Student(access_code=code, name=body.full_name, grade_level=body.grade_level, current_level=1, is_active=True)
        try:
            with db.begin_nested():
                db.add(student)
                db.flush()
        except IntegrityError:
            if requested_code:
                raise HTTPException(status_code=409, detail="رمز الدخول مستخدم لطالب آخر")
            continue
        _audit(db, actor_id=user.id, action="student.create", entity_type="student", entity_id=str(student.id), details={"grade_level": 3, "access_code_mode": "manual" if requested_code else "generated"})
        db.commit()
        db.refresh(student)
        return _student_payload(db, student)
    raise HTTPException(status_code=503, detail="تعذر إنشاء رمز دخول للطالب، حاول مرة أخرى")


@router.patch("/researcher/students/{student_id}", response_model=schemas.StudentResponse)
def update_student(
    student_id: int,
    body: schemas.StudentUpdateRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    student = db.query(Student).filter(Student.id == student_id).with_for_update().first()
    if not student:
        raise HTTPException(status_code=404, detail="الطالب غير موجود")
    changes: dict[str, object] = {}
    if body.full_name is not None and body.full_name != student.name:
        changes["full_name"] = {"from": student.name, "to": body.full_name}
        student.name = body.full_name
    if body.is_active is not None and body.is_active != student.is_active:
        changes["is_active"] = {"from": student.is_active, "to": body.is_active}
        student.is_active = body.is_active
    if changes:
        _audit(db, actor_id=user.id, action="student.update", entity_type="student", entity_id=str(student.id), details=changes)
        db.commit()
        db.refresh(student)
    return _student_payload(db, student)


@router.post("/researcher/students/{student_id}/access-code", response_model=schemas.StudentResponse)
def update_student_access_code(
    student_id: int,
    body: schemas.StudentAccessCodeUpdateRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    student = db.query(Student).filter(Student.id == student_id).with_for_update().first()
    if not student:
        raise HTTPException(status_code=404, detail="الطالب غير موجود")
    new_code = body.access_code or _generate_access_code(db)
    _ensure_unique_access_code(db, new_code, excluding_student_id=student.id)
    old_code = student.access_code
    student.access_code = new_code
    _audit(db, actor_id=user.id, action="student.access_code.update", entity_type="student", entity_id=str(student.id), details={"mode": "manual" if body.access_code else "generated", "changed": old_code != new_code})
    db.commit()
    db.refresh(student)
    return _student_payload(db, student)


@router.post("/researcher/students/{student_id}/posttest-access", response_model=schemas.StudentResponse)
def set_posttest_access(
    student_id: int,
    body: schemas.StudentPosttestAccessRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    student = db.query(Student).filter(Student.id == student_id).with_for_update().first()
    if not student:
        raise HTTPException(status_code=404, detail="الطالب غير موجود")
    pretest_completed = _completed_session(db, student.id, "pretest")
    journey = build_journey_summary(db, student)
    posttest_completed = _completed_session(db, student.id, "posttest")
    if posttest_completed:
        raise HTTPException(status_code=409, detail="الاختبار البعدي مكتمل بالفعل")
    posttest_active = db.query(AssessmentSession.id).filter(
        AssessmentSession.student_id == student.id,
        AssessmentSession.session_type == "posttest",
        AssessmentSession.status == "in_progress",
    ).first()
    if posttest_active:
        raise HTTPException(status_code=409, detail="الاختبار البعدي قيد التنفيذ حاليًا")
    if body.enabled and not pretest_completed:
        raise HTTPException(status_code=409, detail="يجب إكمال الاختبار القبلي أولًا")
    if body.enabled and not journey["learning_journey_completed"]:
        raise HTTPException(
            status_code=409,
            detail="يجب إكمال الأنشطة التعليمية العشرة لكل مستوى في رحلة التعلم حتى المستوى الثالث قبل فتح الاختبار البعدي",
        )
    student.posttest_enabled = body.enabled
    student.posttest_enabled_at = datetime.now(timezone.utc) if body.enabled else None
    student.posttest_enabled_by = user.id if body.enabled else None
    _audit(db, actor_id=user.id, action="student.posttest_access.update", entity_type="student", entity_id=str(student.id), details={"enabled": body.enabled})
    db.commit()
    db.refresh(student)
    return _student_payload(db, student)


@router.get("/researcher/dashboard")
def researcher_dashboard(user: User = Depends(get_current_user)):
    return {"message": "مرحبًا بك في لوحة المشرف", "user_id": user.id, "username": user.username}


@router.get("/student/profile")
def student_profile_legacy(student: Student = Depends(get_current_student)):
    return {"message": "مرحبًا بك في مسارك", "student_id": student.id, "name": student.name}
