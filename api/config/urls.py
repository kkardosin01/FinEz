from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include("accounts.urls")),
    path("api/", include("connections.urls")),
    path("api/", include("transactions.urls")),
    path("api/", include("budgets.urls")),
    path("api/", include("exports.urls")),
    path("api/whatsapp/", include("whatsapp.api_urls")),
    # Webhooks ficam fora de /api: endpoint público, assinatura verificada no corpo.
    path("webhooks/", include("connections.webhook_urls")),
    path("webhooks/", include("whatsapp.webhook_urls")),
    # Schema OpenAPI -> gera os tipos TS do front (drf-spectacular)
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
]
