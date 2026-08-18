import csv
from datetime import date
from io import BytesIO

from django.http import HttpResponse
from openpyxl import Workbook
from rest_framework.views import APIView

from transactions.models import Transaction


def _month_bounds(month_str: str | None):
    if month_str:
        year, month = (int(p) for p in month_str.split("-"))
    else:
        today = date.today()
        year, month = today.year, today.month
    start = date(year, month, 1)
    end = date(year + 1, 1, 1) if month == 12 else date(year, month + 1, 1)
    return start, end


def _rows(user, month_str):
    start, end = _month_bounds(month_str)
    qs = (
        Transaction.objects.filter(user=user, date__gte=start, date__lt=end)
        .select_related("category", "account")
        .order_by("date")
    )
    header = ["data", "descrição", "categoria", "valor", "origem", "conta"]
    yield header
    for tx in qs:
        yield [
            tx.date.isoformat(),
            tx.description,
            tx.category.name_pt,
            f"{tx.amount_cents / 100:.2f}",
            tx.origin,
            tx.account.name,
        ]


class ExportCsvView(APIView):
    def get(self, request):
        month = request.query_params.get("month")
        response = HttpResponse(content_type="text/csv; charset=utf-8")
        response["Content-Disposition"] = f'attachment; filename="finez-{month or "atual"}.csv"'
        writer = csv.writer(response)
        for row in _rows(request.user, month):
            writer.writerow(row)
        return response


class ExportXlsxView(APIView):
    def get(self, request):
        month = request.query_params.get("month")
        workbook = Workbook()
        sheet = workbook.active
        sheet.title = "Extrato"
        for row in _rows(request.user, month):
            sheet.append(row)

        buffer = BytesIO()
        workbook.save(buffer)
        buffer.seek(0)

        response = HttpResponse(
            buffer.read(),
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
        response["Content-Disposition"] = f'attachment; filename="finez-{month or "atual"}.xlsx"'
        return response
