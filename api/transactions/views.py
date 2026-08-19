from datetime import date

from django.db.models import Q, Sum
from django.utils.dateparse import parse_date
from rest_framework import generics
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Category, Transaction
from .serializers import CategorySerializer, ManualTransactionCreateSerializer, TransactionSerializer


def _month_bounds(month_str: str | None):
    """`month` no formato YYYY-MM. Sem parâmetro -> mês corrente."""
    if month_str:
        year, month = (int(p) for p in month_str.split("-"))
    else:
        today = date.today()
        year, month = today.year, today.month
    start = date(year, month, 1)
    end = date(year + 1, 1, 1) if month == 12 else date(year, month + 1, 1)
    return start, end


class CategoryListView(generics.ListAPIView):
    queryset = Category.objects.all().order_by("id")
    serializer_class = CategorySerializer
    pagination_class = None


class TransactionListCreateView(generics.ListCreateAPIView):
    def get_serializer_class(self):
        return ManualTransactionCreateSerializer if self.request.method == "POST" else TransactionSerializer

    def get_queryset(self):
        qs = Transaction.objects.filter(user=self.request.user).select_related("category", "account")

        month = self.request.query_params.get("month")
        start, end = _month_bounds(month)
        qs = qs.filter(date__gte=start, date__lt=end)

        category = self.request.query_params.get("category")
        if category:
            qs = qs.filter(category__slug=category)

        type_ = self.request.query_params.get("type")
        if type_ == "income":
            qs = qs.filter(amount_cents__gt=0)
        elif type_ == "expense":
            qs = qs.filter(amount_cents__lt=0)

        day = self.request.query_params.get("day")
        if day:
            qs = qs.filter(date=parse_date(day))

        search = self.request.query_params.get("search")
        if search:
            qs = qs.filter(Q(description__icontains=search))

        return qs.order_by("-date", "-created_at")


class TransactionDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = TransactionSerializer

    def get_queryset(self):
        return Transaction.objects.filter(user=self.request.user)


class SummaryView(APIView):
    """GET /api/summary?month= — balanço, somas por categoria, série diária.

    Todo agregado crítico é calculado no backend (front não soma nada).
    """

    def get(self, request):
        month = request.query_params.get("month")
        start, end = _month_bounds(month)
        qs = Transaction.objects.filter(user=request.user, date__gte=start, date__lt=end)

        income_cents = qs.filter(amount_cents__gt=0).aggregate(s=Sum("amount_cents"))["s"] or 0
        expense_cents = qs.filter(amount_cents__lt=0).aggregate(s=Sum("amount_cents"))["s"] or 0
        balance_cents = income_cents + expense_cents

        by_category = list(
            qs.values("category__slug", "category__name_pt", "category__color_light", "category__color_dark")
            .annotate(total_cents=Sum("amount_cents"))
            .order_by("total_cents")
        )

        daily = list(
            qs.values("date").annotate(total_cents=Sum("amount_cents")).order_by("date")
        )

        return Response(
            {
                "month": start.strftime("%Y-%m"),
                "income_cents": income_cents,
                "expense_cents": expense_cents,
                "balance_cents": balance_cents,
                "by_category": [
                    {
                        "category_slug": row["category__slug"],
                        "category_name": row["category__name_pt"],
                        "color_light": row["category__color_light"],
                        "color_dark": row["category__color_dark"],
                        "total_cents": row["total_cents"],
                    }
                    for row in by_category
                ],
                "daily": [{"date": row["date"], "total_cents": row["total_cents"]} for row in daily],
            }
        )
