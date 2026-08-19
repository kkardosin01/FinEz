from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView

from engagement.models import Badge
from engagement.services import award_badge, notify_badge_earned

from .models import GoalContribution, SavingsGoal
from .serializers import ContributeSerializer, GoalContributionSerializer, SavingsGoalSerializer


class GoalListCreateView(generics.ListCreateAPIView):
    serializer_class = SavingsGoalSerializer
    pagination_class = None

    def get_queryset(self):
        return SavingsGoal.objects.filter(user=self.request.user).order_by("-created_at")

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class GoalDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = SavingsGoalSerializer

    def get_queryset(self):
        return SavingsGoal.objects.filter(user=self.request.user)


class GoalContributeView(APIView):
    """POST /api/goals/<id>/contribute — registra aporte (positivo) ou resgate (negativo)."""

    def post(self, request, pk):
        goal = get_object_or_404(SavingsGoal, pk=pk, user=request.user)
        serializer = ContributeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        amount_cents = serializer.validated_data["amount_cents"]

        new_saved = goal.saved_cents + amount_cents
        if new_saved < 0:
            return Response(
                {"amount_cents": "resgate maior que o valor guardado"}, status=status.HTTP_400_BAD_REQUEST
            )

        just_completed = False
        with transaction.atomic():
            GoalContribution.objects.create(
                user=request.user,
                goal=goal,
                amount_cents=amount_cents,
                note=serializer.validated_data.get("note", ""),
            )
            goal.saved_cents = new_saved
            if new_saved >= goal.target_cents and not goal.completed_at:
                goal.completed_at = timezone.now()
                just_completed = True
            elif new_saved < goal.target_cents and goal.completed_at:
                goal.completed_at = None  # resgate depois de completar reabre a meta
            goal.save(update_fields=["saved_cents", "completed_at", "updated_at"])

        if just_completed:
            badge, created = award_badge(request.user, Badge.Slug.GOAL_ACHIEVER)
            if created:
                notify_badge_earned(request.user, badge)

        return Response(SavingsGoalSerializer(goal).data)


class GoalContributionListView(generics.ListAPIView):
    serializer_class = GoalContributionSerializer
    pagination_class = None

    def get_queryset(self):
        return GoalContribution.objects.filter(user=self.request.user, goal_id=self.kwargs["pk"])
