import io

from PIL import Image

from app.services.recognition_service import recognition_service


def make_test_image_file(filename: str = "face.jpg"):
    image = Image.new("RGB", (640, 640), color=(120, 130, 140))
    buffer = io.BytesIO()
    image.save(buffer, format="JPEG")
    buffer.seek(0)
    return filename, buffer, "image/jpeg"


def test_single_student_enrollment_and_attendance_count(client, teacher_auth_headers, monkeypatch):
    vector = [0.1] * 512

    def fake_detect_faces_in_photo(photo_path, photo_order=1):
        return [
            {
                "face_index": 1,
                "bounding_box": {"x": 10, "y": 10, "w": 200, "h": 200},
                "quality_score": 0.95,
                "embedding": vector,
            }
        ]

    def fake_generate_face_embedding(image_path, seed_text=None):
        return vector

    def fake_match_faces_against_class_roster(detected_faces, enrolled_students, photo_order=1):
        assert enrolled_students, "Expected at least one enrolled student for attendance matching."
        first_student = enrolled_students[0]
        return {
            "confident": [
                {
                    "face_id": "Face #1",
                    "student_id": first_student["id"],
                    "name": first_student["name"],
                    "student_number": first_student["student_number"],
                    "confidence_score": 0.99,
                    "confidence": "99%",
                    "source_photo_order": photo_order,
                }
            ],
            "review": [],
            "unknown": [],
            "not_detected": [],
        }

    monkeypatch.setattr(recognition_service, "detect_faces_in_photo", fake_detect_faces_in_photo)
    monkeypatch.setattr(recognition_service, "generate_face_embedding", fake_generate_face_embedding)
    monkeypatch.setattr(recognition_service, "match_faces_against_class_roster", fake_match_faces_against_class_roster)

    class_resp = client.post(
        "/api/v1/classes",
        json={
            "name": "E2E-CSE-A",
            "semester": 5,
            "academic_year": "2026-2027",
            "subject": "General",
        },
        headers=teacher_auth_headers,
    )
    assert class_resp.status_code == 201, class_resp.text
    class_id = class_resp.json()["id"]

    student_resp = client.post(
        "/api/v1/students",
        json={
            "student_number": "JYOTISH-001",
            "full_name": "Jyotish Kumar",
            "email": "jyotish.kumar@example.com",
            "class_id": class_id,
        },
        headers=teacher_auth_headers,
    )
    assert student_resp.status_code == 201, student_resp.text
    student_id = student_resp.json()["id"]

    enroll_filename, enroll_file, enroll_type = make_test_image_file("jyotish_enroll.jpg")
    enroll_resp = client.post(
        f"/api/v1/students/{student_id}/face-enrollment",
        files={"file": (enroll_filename, enroll_file, enroll_type)},
        headers=teacher_auth_headers,
    )
    assert enroll_resp.status_code == 200, enroll_resp.text
    assert enroll_resp.json()["student_name"] == "Jyotish Kumar"
    assert enroll_resp.json()["embedding_dimension"] == 512

    session_resp = client.post(
        "/api/v1/attendance-sessions",
        json={
            "class_id": class_id,
            "subject_name": "General",
            "session_date": "2026-09-01",
        },
        headers=teacher_auth_headers,
    )
    assert session_resp.status_code == 200, session_resp.text
    session_id = session_resp.json()["id"]

    att_filename, att_file, att_type = make_test_image_file("jyotish_attendance.jpg")
    upload_resp = client.post(
        f"/api/v1/attendance-sessions/{session_id}/photos",
        files={"file": (att_filename, att_file, att_type)},
        headers=teacher_auth_headers,
    )
    assert upload_resp.status_code == 200, upload_resp.text
    results = upload_resp.json()
    assert results["total_enrolled"] == 1
    assert len(results["confident"]) == 1
    assert results["confident"][0]["student_id"] == student_id
    assert len(results["not_detected"]) == 0
