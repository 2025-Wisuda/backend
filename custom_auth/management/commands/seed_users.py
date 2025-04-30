from django.core.management.base import BaseCommand
from custom_auth.seeds.user_seeder import UserSeeder 
class Command(BaseCommand):
    help = 'Seed database with dummy users including one admin'

    def handle(self, *args, **kwargs):
        UserSeeder.seed()

        self.stdout.write(self.style.SUCCESS('Seeding completed successfully'))
