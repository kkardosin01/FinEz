from django.utils import timezone
from datetime import timedelta

from rest_framework.response import Response
from rest_framework.views import APIView

from .models import WhatsappLink, _generate_pairing_code

PAIRING_CODE_TTL_MINUTES = 15


class PairView(APIView):
    def post(self, request):
        """Gera (ou renova) o código de pareamento pra tela Conta."""
        link, _ = WhatsappLink.objects.get_or_create(
            user=request.user,
            defaults={"pairing_expires_at": timezone.now() + timedelta(minutes=PAIRING_CODE_TTL_MINUTES)},
        )
        if link.status != WhatsappLink.Status.ACTIVE:
            link.pairing_code = _generate_pairing_code()
            link.pairing_expires_at = timezone.now() + timedelta(minutes=PAIRING_CODE_TTL_MINUTES)
            link.status = WhatsappLink.Status.PENDING
            link.save(update_fields=["pairing_code", "pairing_expires_at", "status"])

        return Response(
            {
                "pairing_code": link.pairing_code,
                "expires_at": link.pairing_expires_at,
                "status": link.status,
            }
        )

    def get(self, request):
        link = WhatsappLink.objects.filter(user=request.user).first()
        if not link:
            return Response({"status": "unlinked"})
        return Response({"status": link.status, "phone_e164": link.phone_e164 if link.status == "active" else None})
