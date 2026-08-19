from rest_framework import generics

from .models import Subscription
from .serializers import SubscriptionSerializer


class SubscriptionListView(generics.ListAPIView):
    serializer_class = SubscriptionSerializer
    pagination_class = None

    def get_queryset(self):
        return (
            Subscription.objects.filter(user=self.request.user)
            .select_related("category")
            .order_by("-amount_cents")
        )


class SubscriptionDetailView(generics.RetrieveUpdateAPIView):
    serializer_class = SubscriptionSerializer

    def get_queryset(self):
        return Subscription.objects.filter(user=self.request.user)
