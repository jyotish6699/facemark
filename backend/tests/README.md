# Backend Test Guide

## Purpose

This folder contains the backend test suite for FaceMark.

The goal is to validate the core workflow using fake data and the PostgreSQL demo database.

We follow a simple test structure:

- `unit/` for isolated logic checks
- `integration/` for API and database workflow validation

---

## Test structure

```text
backend/
  tests/
    unit/
    integration/
```

---

## Required test coverage

### Unit tests

- password hashing/verification
- JWT creation and validation
- subject list filtering
- attendance status transitions
- recognition classification logic
- duplicate prevention logic
- merge logic for second photo

### Integration tests

- teacher login with fake credentials
- dashboard loads assigned section data
- subject list loads for the section
- attendance session is created
- first-pass recognition records are created
- second-pass merge updates uncertain/unknown records
- attendance finalization locks session
- history endpoint returns finalized records

---

## Test philosophy

These tests should be:

- small
- deterministic
- realistic to the hackathon flow
- fast to run locally

We are not writing exhaustive enterprise tests. We are testing the exact demo features that matter for the product.

---

## Example test cases

### Unit

- `test_password_hash_matches_input`
- `test_jwt_contains_teacher_id`
- `test_recognition_classifies_confident_match`
- `test_second_pass_merges_without_duplicate_count`

### Integration

- `test_teacher_login_success`
- `test_dashboard_returns_section_summary`
- `test_create_attendance_session_success`
- `test_finalize_session_updates_history`

---

## Tools

Use pytest for Python backend tests.

Example command:

```bash
pytest -q
```

---

## Implementation reminder

The backend tests should use the same fake teacher and student data as the demo database.

This ensures the app behaves like a real production flow during validation and presentation.
