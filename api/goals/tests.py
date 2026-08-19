import pytest
from rest_framework.test import APIClient

from accounts.models import User
from goals.models import GoalContribution, SavingsGoal

pytestmark = pytest.mark.django_db


@pytest.fixture
def user():
    return User.objects.create_user(email="teste@finez.app", password="senha-forte-123")


@pytest.fixture
def client(user):
    api_client = APIClient()
    api_client.force_authenticate(user=user)
    return api_client


def test_goals_requires_authentication():
    response = APIClient().get("/api/goals")
    assert response.status_code in (401, 403)


def test_create_goal(client):
    response = client.post(
        "/api/goals", {"name": "Viagem", "icon": "✈️", "target_cents": 500000}, format="json"
    )
    assert response.status_code == 201
    assert response.data["saved_cents"] == 0
    assert response.data["progress_pct"] == 0
    assert response.data["completed_at"] is None


def test_create_goal_with_non_positive_target_is_rejected(client):
    response = client.post("/api/goals", {"name": "Meta inválida", "target_cents": 0}, format="json")
    assert response.status_code == 400


def test_list_goals_only_returns_own(client, user):
    other_user = User.objects.create_user(email="outra@finez.app", password="senha-forte-123")
    SavingsGoal.objects.create(user=user, name="Minha meta", target_cents=10000)
    SavingsGoal.objects.create(user=other_user, name="Meta de outra pessoa", target_cents=10000)

    response = client.get("/api/goals")
    assert response.status_code == 200
    assert [g["name"] for g in response.data] == ["Minha meta"]


def test_update_goal_name_and_target(client, user):
    goal = SavingsGoal.objects.create(user=user, name="Meta", target_cents=10000)
    response = client.patch(f"/api/goals/{goal.id}", {"name": "Meta renomeada"}, format="json")
    assert response.status_code == 200
    assert response.data["name"] == "Meta renomeada"


def test_cannot_update_another_users_goal(client):
    other_user = User.objects.create_user(email="outra@finez.app", password="senha-forte-123")
    goal = SavingsGoal.objects.create(user=other_user, name="Meta", target_cents=10000)
    response = client.patch(f"/api/goals/{goal.id}", {"name": "hack"}, format="json")
    assert response.status_code == 404


def test_delete_goal(client, user):
    goal = SavingsGoal.objects.create(user=user, name="Meta", target_cents=10000)
    response = client.delete(f"/api/goals/{goal.id}")
    assert response.status_code == 204
    assert not SavingsGoal.objects.filter(id=goal.id).exists()


def test_contribute_increases_saved_cents_and_logs_history(client, user):
    goal = SavingsGoal.objects.create(user=user, name="Meta", target_cents=10000)
    response = client.post(f"/api/goals/{goal.id}/contribute", {"amount_cents": 3000, "note": "mesada"}, format="json")
    assert response.status_code == 200
    assert response.data["saved_cents"] == 3000
    assert response.data["progress_pct"] == 30

    contribution = GoalContribution.objects.get(goal=goal)
    assert contribution.amount_cents == 3000
    assert contribution.note == "mesada"


def test_contribute_reaching_target_marks_completed(client, user):
    goal = SavingsGoal.objects.create(user=user, name="Meta", target_cents=10000, saved_cents=8000)
    response = client.post(f"/api/goals/{goal.id}/contribute", {"amount_cents": 2000}, format="json")
    assert response.status_code == 200
    assert response.data["completed_at"] is not None
    assert response.data["progress_pct"] == 100


def test_withdrawal_below_zero_is_rejected(client, user):
    goal = SavingsGoal.objects.create(user=user, name="Meta", target_cents=10000, saved_cents=1000)
    response = client.post(f"/api/goals/{goal.id}/contribute", {"amount_cents": -2000}, format="json")
    assert response.status_code == 400
    goal.refresh_from_db()
    assert goal.saved_cents == 1000


def test_withdrawal_after_completion_reopens_goal(client, user):
    from django.utils import timezone

    goal = SavingsGoal.objects.create(
        user=user, name="Meta", target_cents=10000, saved_cents=10000, completed_at=timezone.now()
    )
    response = client.post(f"/api/goals/{goal.id}/contribute", {"amount_cents": -5000}, format="json")
    assert response.status_code == 200
    assert response.data["completed_at"] is None
    assert response.data["saved_cents"] == 5000


def test_contribute_with_zero_amount_is_rejected(client, user):
    goal = SavingsGoal.objects.create(user=user, name="Meta", target_cents=10000)
    response = client.post(f"/api/goals/{goal.id}/contribute", {"amount_cents": 0}, format="json")
    assert response.status_code == 400


def test_cannot_contribute_to_another_users_goal(client):
    other_user = User.objects.create_user(email="outra@finez.app", password="senha-forte-123")
    goal = SavingsGoal.objects.create(user=other_user, name="Meta", target_cents=10000)
    response = client.post(f"/api/goals/{goal.id}/contribute", {"amount_cents": 100}, format="json")
    assert response.status_code == 404


def test_goal_contributions_list_is_scoped_to_goal_and_user(client, user):
    other_user = User.objects.create_user(email="outra@finez.app", password="senha-forte-123")
    goal = SavingsGoal.objects.create(user=user, name="Meta", target_cents=10000)
    other_goal = SavingsGoal.objects.create(user=other_user, name="Outra", target_cents=10000)
    GoalContribution.objects.create(user=user, goal=goal, amount_cents=1000, note="a")
    GoalContribution.objects.create(user=user, goal=goal, amount_cents=500, note="b")
    GoalContribution.objects.create(user=other_user, goal=other_goal, amount_cents=999)

    response = client.get(f"/api/goals/{goal.id}/contributions")
    assert response.status_code == 200
    assert len(response.data) == 2
    assert {c["note"] for c in response.data} == {"a", "b"}
