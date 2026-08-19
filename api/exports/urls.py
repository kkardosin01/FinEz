from django.urls import path

from .views import ExportCsvView, ExportXlsxView, ImportTransactionsView

urlpatterns = [
    path("exports/csv", ExportCsvView.as_view(), name="export-csv"),
    path("exports/xlsx", ExportXlsxView.as_view(), name="export-xlsx"),
    path("imports/transactions", ImportTransactionsView.as_view(), name="import-transactions"),
]
