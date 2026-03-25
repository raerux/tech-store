from django.core.management.base import BaseCommand
from store.seeds import run_seed

class Command(BaseCommand):
    help = "Popula banco com categorias e produtos iniciais"

    def handle(self, *args, **options):
        run_seed()
        self.stdout.write(self.style.SUCCESS("Seed executado com sucesso."))