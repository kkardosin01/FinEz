from django.urls import path

from .views import ExportCsvView, ExportXlsxView

urlpatterns = [
    path("exports/csv", ExportCsvView.as_view(), name="export-csv"),
    path("exports/xlsx", ExportXlsxView.as_view(), name="export-xlsx"),
]
