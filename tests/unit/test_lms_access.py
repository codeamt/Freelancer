import pytest


@pytest.mark.asyncio
async def test_enrollment_check_allows_access(monkeypatch):
    from app.add_ons.domains.lms import dependencies

    async def fake_check(db, user_id, course_id):
        return True

    monkeypatch.setattr(dependencies.EnrollmentService, "check_enrollment_access", fake_check)

    ok = await dependencies.verify_course_access(course_id=1, user_id=2, db=object())
    assert ok is True


@pytest.mark.asyncio
async def test_enrollment_check_denies_access(monkeypatch):
    from app.add_ons.domains.lms import dependencies
    from starlette.exceptions import HTTPException

    async def fake_check(db, user_id, course_id):
        return False

    monkeypatch.setattr(dependencies.EnrollmentService, "check_enrollment_access", fake_check)

    raised = False
    try:
        await dependencies.verify_course_access(course_id=1, user_id=2, db=object())
    except HTTPException as e:
        raised = True
        assert e.status_code == 403

    assert raised is True
