import pytest
from rest_framework.test import APIClient

from accounts.models import Invite, User

pytestmark = pytest.mark.django_db


@pytest.fixture
def invite():
    return Invite.objects.create(code="FINEZ-TEST", max_uses=1)


def test_register_with_valid_invite_logs_user_in(invite):
    client = APIClient()
    response = client.post(
        "/api/auth/register",
        {
            "email": "nova@finez.app",
            "password": "senha-forte-123",
            "name": "Nova",
            "invite_code": invite.code,
        },
    )
    assert response.status_code == 201
    assert response.data["email"] == "nova@finez.app"

    me = client.get("/api/me")
    assert me.status_code == 200


def test_register_with_invalid_invite_is_rejected():
    client = APIClient()
    response = client.post(
        "/api/auth/register",
        {
            "email": "nova@finez.app",
            "password": "senha-forte-123",
            "name": "Nova",
            "invite_code": "NAO-EXISTE",
        },
    )
    assert response.status_code == 400


def test_register_with_exhausted_invite_is_rejected(invite):
    invite.used_count = invite.max_uses
    invite.save(update_fields=["used_count"])

    client = APIClient()
    response = client.post(
        "/api/auth/register",
        {
            "email": "nova@finez.app",
            "password": "senha-forte-123",
            "name": "Nova",
            "invite_code": invite.code,
        },
    )
    assert response.status_code == 400


def test_me_requires_authentication():
    client = APIClient()
    response = client.get("/api/me")
    assert response.status_code in (401, 403)


def test_delete_account_removes_user_data():
    user = User.objects.create_user(email="apagar@finez.app", password="senha-forte-123")
    client = APIClient()
    client.force_authenticate(user=user)

    response = client.delete("/api/me")
    assert response.status_code == 204

    user.refresh_from_db()
    assert user.is_active is False
    assert user.name is None
