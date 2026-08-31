from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_teacher_login_and_dashboard_flow():
    response = client.post(
        "/api/auth/login",
        json={"email": "ayesha.khan@facemark.local", "password": "Teacher@123"},
    )
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["teacher"]["teacher_id"] == "t-001"

    token = data["access_token"]
    me = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me.status_code == 200, me.text
    assert me.json()["teacher_id"] == "t-001"

    dashboard = client.get(
        "/api/dashboard/teacher/t-001",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert dashboard.status_code == 200, dashboard.text
    payload = dashboard.json()
    assert payload["section"]["section_name"] == "CSE-A"
    assert len(payload["subjects"]) >= 1
    assert set(payload["stats"]).issuperset({"total_sessions", "present", "review", "pending", "finalized"})


def test_attendance_session_flow_and_finalize():
    login = client.post(
        "/api/auth/login",
        json={"email": "ayesha.khan@facemark.local", "password": "Teacher@123"},
    )
    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    subjects = client.get("/api/sections/sec-cse-a/subjects", headers=headers)
    assert subjects.status_code == 200, subjects.text
    subject = subjects.json()[0]

    session = client.post(
        "/api/attendance/sessions",
        json={
            "teacher_id": "t-001",
            "section_id": "sec-cse-a",
            "subject_id": subject["subject_id"],
            "session_date": "2026-08-29",
            "notes": "Demo attendance session",
        },
        headers=headers,
    )
    assert session.status_code == 200, session.text
    session_id = session.json()["session_id"]

    detail = client.get(f"/api/attendance/sessions/{session_id}", headers=headers)
    assert detail.status_code == 200, detail.text
    assert len(detail.json()["students"]) >= 1

    recognition = client.post(f"/api/attendance/sessions/{session_id}/recognize", headers=headers)
    assert recognition.status_code == 200, recognition.text
    payload = recognition.json()
    assert "results" in payload
    assert set(payload["results"]).issubset({"confident", "uncertain", "unknown", "not_detected"})

    resolve = client.post(f"/api/attendance/sessions/{session_id}/resolve", headers=headers)
    assert resolve.status_code == 200, resolve.text
    assert resolve.json()["resolved_records"] >= 0

    finalize = client.post(
        f"/api/attendance/sessions/{session_id}/finalize",
        json={
            "teacher_id": "t-001",
            "decisions": {
                "st-001": "present",
                "st-002": "present",
                "st-003": "absent",
            },
        },
        headers=headers,
    )
    assert finalize.status_code == 200, finalize.text
    assert finalize.json()["status"] == "finalized"

    history = client.get("/api/attendance/history?section_id=sec-cse-a", headers=headers)
    assert history.status_code == 200, history.text
    assert len(history.json()) >= 1


def test_attendance_image_upload_flow():
    login = client.post(
        "/api/auth/login",
        json={"email": "ayesha.khan@facemark.local", "password": "Teacher@123"},
    )
    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    subjects = client.get("/api/sections/sec-cse-a/subjects", headers=headers)
    subject = subjects.json()[0]

    session = client.post(
        "/api/attendance/sessions",
        json={
            "teacher_id": "t-001",
            "section_id": "sec-cse-a",
            "subject_id": subject["subject_id"],
            "session_date": "2026-08-29",
            "notes": "Upload image flow test",
        },
        headers=headers,
    )
    session_id = session.json()["session_id"]

    file_bytes = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx\x9cc``\x00\x00\x00\x02\x00\x01\xe5\x27\x98\x3d\x00\x00\x00\x00IEND\xaeB`\x82"
    upload = client.post(
        f"/api/attendance/sessions/{session_id}/upload",
        files={"file": ("demo-upload.png", file_bytes, "image/png")},
        headers=headers,
    )
    assert upload.status_code == 200, upload.text
    payload = upload.json()
    assert payload["file_name"] == "demo-upload.png"
    assert payload["session_id"] == session_id
    assert payload["storage_url"].startswith("storage://demo/")


def test_attendance_database_verification_flow():
    login = client.post(
        "/api/auth/login",
        json={"email": "ayesha.khan@facemark.local", "password": "Teacher@123"},
    )
    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    subjects = client.get("/api/sections/sec-cse-a/subjects", headers=headers)
    subject = subjects.json()[0]

    session = client.post(
        "/api/attendance/sessions",
        json={
            "teacher_id": "t-001",
            "section_id": "sec-cse-a",
            "subject_id": subject["subject_id"],
            "session_date": "2026-08-29",
            "notes": "Database verification test",
        },
        headers=headers,
    )
    session_id = session.json()["session_id"]

    file_bytes = b"sample-image-content-for-student-matching"
    verify = client.post(
        f"/api/attendance/sessions/{session_id}/verify-image",
        files={"file": ("verification.png", file_bytes, "image/png")},
        headers=headers,
    )
    assert verify.status_code == 200, verify.text
    payload = verify.json()
    assert payload["session_id"] == session_id
    assert set(payload["results"]).issubset({"confident", "uncertain", "unknown", "not_detected"})
    assert any(payload["results"].get(bucket) for bucket in ["confident", "uncertain", "unknown", "not_detected"])
