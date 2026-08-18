import secrets
import string

from django.core.management.base import BaseCommand

from accounts.models import Invite


def _random_suffix(length=4):
    alphabet = string.ascii_uppercase + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(length))


class Command(BaseCommand):
    help = "Gera um código de convite (beta fechado). Ex.: python manage.py create_invite --max-uses 1"

    def add_arguments(self, parser):
        parser.add_argument("--max-uses", type=int, default=1)
        parser.add_argument("--code", type=str, default=None, help="Código customizado (opcional)")

    def handle(self, *args, **options):
        code = options["code"] or f"FINEZ-{_random_suffix()}"
        invite = Invite.objects.create(code=code, max_uses=options["max_uses"])
        self.stdout.write(self.style.SUCCESS(f"Convite criado: {invite.code} (usos: {invite.max_uses})"))
