from datetime import date

from django.db.models import Sum
from rest_framework.response import Response
from rest_framework.views import APIView

from transactions.models import Transaction

from .models import Budget
from .serializers import BudgetSerializer, BudgetUpsertSerializer


def _month_start(month_str: str | None) -> date:
    if month_str:
        year, month = (int(p) for p in month_str.split("-"))
        return date(year, month, 1)
    today = date.today()
    return date(today.year, today.month, 1)


class BudgetListUpsertView(APIView):
    def get(self, request):
        month = _month_start(request.query_params.get("month"))
        next_month = date(month.year + 1, 1, 1) if month.month == 12 else date(month.year, month.month + 1, 1)

        budgets = list(Budget.objects.filter(user=request.user, month=month).select_related("category"))
        spent_by_category = dict(
            Transaction.objects.filter(
                user=request.user, date__gte=month, date__lt=next_month, amount_cents__lt=0
            )
            .values_list("category_id")
            .annotate(total=Sum("amount_cents"))
        )

        for budget in budgets:
            # Gasto é negativo no banco; orçamento é comparado em valor absoluto
            budget.spent_cents = abs(spent_by_category.get(budget.category_id, 0))

        return Response(BudgetSerializer(budgets, many=True).data)

    def put(self, request):
        serializer = BudgetUpsertSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        month = serializer.validated_data["month"].replace(day=1)

        result = []
        for item in serializer.validated_data["budgets"]:
            budget, _ = Budget.objects.update_or_create(
                user=request.user,
                category=item["category"],
                month=month,
                defaults={"amount_cents": item["amount_cents"]},
            )
            budget.spent_cents = 0
            result.append(budget)

        return Response(BudgetSerializer(result, many=True).data)
