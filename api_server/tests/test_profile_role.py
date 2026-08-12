from app.api.routes.account import profile as profile_route
from app.schemas.account import AuthenticatedUser, UserProfileUpsertRequest


def test_profile_upsert_accepts_only_supported_user_roles():
    assert UserProfileUpsertRequest(userRole="recruiter").userRole == "recruiter"
    assert UserProfileUpsertRequest(userRole="candidate").userRole == "candidate"


def test_profile_upsert_forwards_verified_users_role(monkeypatch):
    captured = {}

    def fake_upsert(user, **kwargs):
        captured["user"] = user
        captured.update(kwargs)
        return {"uid": user.uid, "userRole": kwargs["user_role"]}

    monkeypatch.setattr(profile_route.profile_service, "upsert_user_profile", fake_upsert)
    user = AuthenticatedUser(uid="firebase-uid", email="candidate@example.test")

    result = profile_route.upsert_profile(
        UserProfileUpsertRequest(userRole="candidate"),
        current_user=user,
    )

    assert captured["user"].uid == "firebase-uid"
    assert captured["user_role"] == "candidate"
    assert result["userRole"] == "candidate"
