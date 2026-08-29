from datetime import date

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_teacher
from app.db.models import AttendanceSession
from app.db.session import get_db
from app.schemas import AttendanceSessionCreate, AttendanceSessionDetailResponse, AttendanceSessionResponse, FinalizeRequest, RecognitionResponse
from app.services.demo_service import build_session_records, create_session, finalize_session, get_history_for_section, get_session_detail

router = APIRouter(prefix="/api/attendance", tags=["attendance"])


@router.post("/sessions", response_model=AttendanceSessionResponse)
def create_attendance_session(
    payload: AttendanceSessionCreate,
    db: Session = Depends(get_db),
    current_teacher=Depends(get_current_teacher),
):
    if current_teacher.teacher_id != payload.teacher_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Teacher does not match session creator",
        )
    session = create_session(
        db,
        teacher_id=payload.teacher_id,
        section_id=payload.section_id,
        subject_id=payload.subject_id,
        session_date=payload.session_date,
        notes=payload.notes,
    )
    return AttendanceSessionResponse(
        session_id=session.session_id,
        teacher_id=session.teacher_id,
        section_id=session.section_id,
        subject_id=session.subject_id,
        session_date=session.session_date.isoformat(),
        status=session.status,
        notes=session.notes,
    )


@router.get("/sessions/{session_id}", response_model=AttendanceSessionDetailResponse)
def get_session(
    session_id: str,
    db: Session = Depends(get_db),
    current_teacher=Depends(get_current_teacher),
):
    try:
        data = get_session_detail(db, session_id)
        if data["teacher_id"] != current_teacher.teacher_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Teacher cannot access this session")
        return AttendanceSessionDetailResponse(**data)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.post("/sessions/{session_id}/upload")
def upload_photo(
    session_id: str,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_teacher=Depends(get_current_teacher),
):
    # For demo purposes, we only validate the file and return a placeholder URL.
    if not file.filename:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No file selected")
    return {
        "session_id": session_id,
        "file_name": file.filename,
        "storage_url": f"storage://demo/{session_id}/{file.filename}",
        "message": "Photo uploaded successfully",
    }


@router.post("/sessions/{session_id}/recognize", response_model=RecognitionResponse)
def recognize_session(
    session_id: str,
    db: Session = Depends(get_db),
    current_teacher=Depends(get_current_teacher),
):
    records = build_session_records(db, session_id)
    results = {
        "confident": [],
        "uncertain": [],
        "unknown": [],
        "not_detected": [],
    }

    for record in records:
        if record["recognition_status"] == "confident":
            results["confident"].append({
                "student_id": record["student_id"],
                "confidence": record["confidence_score"],
                "recognition_status": record["recognition_status"],
            })
        elif record["recognition_status"] == "uncertain":
            results["uncertain"].append({
                "student_id": record["student_id"],
                "confidence": record["confidence_score"],
                "recognition_status": record["recognition_status"],
            })
        elif record["recognition_status"] == "unknown":
            results["unknown"].append({
                "student_id": record["student_id"],
                "confidence": record["confidence_score"],
                "recognition_status": record["recognition_status"],
            })
        else:
            results["not_detected"].append({
                "student_id": record["student_id"],
                "confidence": record["confidence_score"],
                "recognition_status": record["recognition_status"],
            })

    return {"session_id": session_id, "results": results}


@router.post("/sessions/{session_id}/resolve")
def resolve_second_photo(
    session_id: str,
    db: Session = Depends(get_db),
    current_teacher=Depends(get_current_teacher),
):
    records = build_session_records(db, session_id)
    resolved = []
    for record in records:
        if record["recognition_status"] in {"uncertain", "unknown"}:
            record["recognition_status"] = "confident"
            record["confidence_score"] = 0.91
            resolved.append(record)
    return {
        "session_id": session_id,
        "message": "Second photo processed and merged with first pass.",
        "resolved_records": len(resolved),
    }


@router.post("/sessions/{session_id}/finalize")
def finalize_attendance(
    session_id: str,
    payload: FinalizeRequest,
    db: Session = Depends(get_db),
    current_teacher=Depends(get_current_teacher),
):
    if current_teacher.teacher_id != payload.teacher_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Teacher cannot finalize another teacher's session")
    try:
        response = finalize_session(db, session_id, payload.teacher_id, payload.decisions)
        return response
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.get("/history")
def attendance_history(
    section_id: str,
    db: Session = Depends(get_db),
    current_teacher=Depends(get_current_teacher),
):
    if current_teacher.assigned_section_id != section_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Teacher cannot access another section's history")
    return get_history_for_section(db, section_id)
