from django.core.management.base import BaseCommand

from transactions.models import Category

# Paleta fixa de 8 cores de categoria + verde de entrada pra "income" (seção 2 do doc).
# Tons exatos são placeholder — validar com design antes do beta.
CATEGORIES = [
    (Category.Slug.GROCERIES, "Mercado", "#2E7D5B", "#4FA37D"),
    (Category.Slug.FOOD, "Alimentação", "#D97643", "#E0975F"),
    (Category.Slug.TRANSPORT, "Transporte", "#3B6FA0", "#6FA0D0"),
    (Category.Slug.SUBSCRIPTIONS, "Assinaturas", "#7B5EA7", "#A78BC9"),
    (Category.Slug.HEALTH, "Saúde", "#C24D7C", "#D97FA6"),
    (Category.Slug.LEISURE, "Lazer", "#B07B1E", "#E0A83E"),
    (Category.Slug.HOUSING, "Moradia", "#5B7553", "#8AA083"),
    (Category.Slug.INCOME, "Receita", "#0E7A4E", "#3DC98A"),
    (Category.Slug.OTHER, "Outros", "#75807A", "#8A948D"),
]


class Command(BaseCommand):
    help = "Semeia as 9 categorias fixas do sistema (idempotente)."

    def handle(self, *args, **options):
        for slug, name_pt, color_light, color_dark in CATEGORIES:
            _, created = Category.objects.update_or_create(
                slug=slug,
                defaults={"name_pt": name_pt, "color_light": color_light, "color_dark": color_dark},
            )
            action = "criada" if created else "atualizada"
            self.stdout.write(f"Categoria {slug}: {action}")
        self.stdout.write(self.style.SUCCESS("Categorias semeadas."))
