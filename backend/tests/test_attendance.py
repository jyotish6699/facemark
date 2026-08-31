import io
import pytest
from PIL import Image

def create_mock_image():
    """Generates a dummy test JPEG image buffer."""
    img = Image.new("RGB", (640, 480), color=(73, 109, 137))
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    buf.seek(0)
    return buf

def test_full_attendance_lifecycle(client, teacher_auth_headers):
    # 1. Get CSE-A Class ID
    classes_resp = client.get("/api/v1/classes", headers=teacher_auth_headers)
    csea_id = next(c["id"] for c in classes_resp.json() if c["name"] == "CSE-A")

    # 2. Create Attendance Session
    session_resp = client.post("/api/v1/attendance-sessions", json={
        "class_id": csea_id,
        "subject_name": "Operating Systems",
        "session_date": "2026-08-29"
    }, headers=teacher_auth_headers)
    assert session_resp.status_code == 200
    session_data = session_resp.json()
    session_id = session_data["id"]
    assert session_data["status"] == "OPEN"
    assert session_data["student_count"] == 32

    # 3. Upload Photo 1
    photo1 = create_mock_image()
    upload1_resp = client.post(
        f"/api/v1/attendance-sessions/{session_id}/photos",
        files={"file": ("class_photo_1.jpg", photo1, "image/jpeg")},
        headers=teacher_auth_headers
    )
    assert upload1_resp.status_code == 200
    results1 = upload1_resp.json()
    assert results1["photo_count"] == 1
    assert "confident" in results1
    assert "review" in results1
    assert "unknown" in results1
    assert "not_detected" in results1

    # 4. Upload Photo 2 (Resolution / Merge pass with distinct photo content)
    img2 = Image.new("RGB", (800, 600), color=(120, 150, 90))
    photo2 = io.BytesIO()
    img2.save(photo2, format="JPEG")
    photo2.seek(0)
    upload2_resp = client.post(
        f"/api/v1/attendance-sessions/{session_id}/photos",
        files={"file": ("class_photo_2.jpg", photo2, "image/jpeg")},
        headers=teacher_auth_headers
    )
    assert upload2_resp.status_code == 200
    results2 = upload2_resp.json()
    assert results2["photo_count"] == 2

    # 5. Get Review Table for Teacher Review
    review_resp = client.get(f"/api/v1/attendance-sessions/{session_id}/review-table", headers=teacher_auth_headers)
    assert review_resp.status_code == 200
    review_data = review_resp.json()
    assert len(review_data["students"]) == 32

    # 6. Finalize Attendance Session
    first_student_id = review_data["students"][0]["id"]
    finalize_resp = client.post(
        f"/api/v1/attendance-sessions/{session_id}/finalize",
        json={
            "updates": [
                {"student_id": first_student_id, "final_status": "PRESENT"}
            ]
        },
        headers=teacher_auth_headers
    )
    assert finalize_resp.status_code == 200
    final_data = finalize_resp.json()
    assert final_data["status"] == "FINALIZED"
    assert final_data["total_students"] == 32

    # 7. Verify History Record
    history_resp = client.get(f"/api/v1/history/classes/{csea_id}", headers=teacher_auth_headers)
    assert history_resp.status_code == 200
    history = history_resp.json()
    assert len(history) >= 1
    assert any(h["session_id"] == session_id for h in history)
