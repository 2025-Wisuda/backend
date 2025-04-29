from django.core.management.base import BaseCommand
from custom_auth.seeds.group_seeder import GroupSeeder


class Command(BaseCommand):
    help = "Seed database with predefined groups"

    def handle(self, *args, **kwargs):
        GroupSeeder.seed()
        self.stdout.write(self.style.SUCCESS("Groups seeding completed successfully"))


def seed_groups():
    GroupSeeder.seed()
