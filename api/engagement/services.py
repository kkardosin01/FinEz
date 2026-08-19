"""Lógica de gamificação leve (seção 3): streak de registro de gastos + badges.

Fica fora de tasks.py porque é chamada de forma síncrona logo após criar a
transação (tanto no bot quanto na API web), pra poder devolver as badges
recém-conquistadas na hora — sem precisar de round-trip assíncrono.
"""
import logging
from datetime import date, timedelta

from .models import Badge, Streak

logger = logging.getLogger("finez")

STREAK_MILESTONES = {
    7: Badge.Slug.STREAK_7,
    30: Badge.Slug.STREAK_30,
    100: Badge.Slug.STREAK_100,
}


def record_activity(user, on_date: date | None = None) -> list[Badge]:
    """Atualiza o streak do usuário e devolve badges de streak recém-conquistadas."""
    today = on_date or date.today()
    streak, _ = Streak.objects.get_or_create(user=user)

    if streak.last_logged_date == today:
        return []  # já contabilizou hoje

    if streak.last_logged_date == today - timedelta(days=1):
        streak.current_streak += 1
    else:
        streak.current_streak = 1  # quebrou o streak (ou primeiro registro)
    streak.longest_streak = max(streak.longest_streak, streak.current_streak)
    streak.last_logged_date = today
    streak.save(update_fields=["current_streak", "longest_streak", "last_logged_date", "updated_at"])

    slug = STREAK_MILESTONES.get(streak.current_streak)
    if not slug:
        return []
    badge, created = award_badge(user, slug)
    return [badge] if created else []


def award_badge(user, slug: str) -> tuple[Badge, bool]:
    badge, created = Badge.objects.get_or_create(user=user, slug=slug)
    if created:
        logger.info("badge_earned", extra={"user_id": str(user.id), "slug": slug})
    return badge, created


def notify_badge_earned(user, badge: Badge) -> None:
    """Notifica via WhatsApp — usado quando a badge é ganha fora de um fluxo de chat
    (ex: tarefa periódica de orçamento em dia, meta batida pela web)."""
    from whatsapp.models import WhatsappLink
    from whatsapp.sender import send_whatsapp_message

    link = WhatsappLink.objects.filter(user=user, status=WhatsappLink.Status.ACTIVE).first()
    if link:
        send_whatsapp_message(link.phone_e164, f"🏆 conquista desbloqueada: {badge.get_slug_display()}!")
