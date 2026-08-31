import pytest

def test_list_assigned_classes(client, teacher_auth_headers):
    response = client.get("/api/v1/classes", headers=teacher_auth_headers)
    assert response.status_code == 200
    classes = response.json()
    assert len(classes) >= 1
    csea = next((c for c in classes if c["name"] == "CSE-A"), None)
    assert csea is not None
    assert csea["student_count"] == 32

def test_get_class_details(client, teacher_auth_headers):
    # List to get class ID
    list_resp = client.get("/api/v1/classes", headers=teacher_auth_headers)
    class_id = list_resp.json()[0]["id"]

    response = client.get(f"/api/v1/classes/{class_id}", headers=teacher_auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == class_id
    assert "student_count" in data

def test_get_class_roster_candidate_scoping(client, teacher_auth_headers):
    list_resp = client.get("/api/v1/classes", headers=teacher_auth_headers)
    csea_id = next(c["id"] for c in list_resp.json() if c["name"] == "CSE-A")

    response = client.get(f"/api/v1/classes/{csea_id}/students", headers=teacher_auth_headers)
    assert response.status_code == 200
    roster = response.json()
    assert len(roster) == 32
    assert any(s["name"] == "Rahul Verma" for s in roster)
