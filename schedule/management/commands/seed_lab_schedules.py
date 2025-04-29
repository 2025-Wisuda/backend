from django.core.management.base import BaseCommand
from schedule.seeds.lab_schedule_seeder import LabScheduleSeeder


class Command(BaseCommand):
    help = "Seed database with dummy lab schedules"

    def handle(self, *args, **kwargs):
        LabScheduleSeeder.seed()
        self.stdout.write(
            self.style.SUCCESS("Lab schedules seeding completed successfully")
        )


def seed_lab_schedules():
    LabScheduleSeeder.seed()
