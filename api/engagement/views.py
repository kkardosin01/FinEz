from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Badge, Streak
from .serializers import BadgeSerializer, StreakSerializer


class GamificationSummaryView(APIView):
    """GET /api/engagement/summary — streak atual + badges conquistadas."""

    def get(self, request):
        streak, _ = Streak.objects.get_or_create(user=request.user)
        badges = Badge.objects.filter(user=request.user)
        return Response(
            {
                "streak": StreakSerializer(streak).data,
                "badges": BadgeSerializer(badges, many=True).data,
            }
        )
