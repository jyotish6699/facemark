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
