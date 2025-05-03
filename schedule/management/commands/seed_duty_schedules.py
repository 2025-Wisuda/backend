from django.core.management.base import BaseCommand
from schedule.seeds.duty_schedule_seeder import DutyScheduleSeeder


class Command(BaseCommand):
    help = "Seed database with dummy duty schedules"

    def handle(self, *args, **kwargs):
        DutyScheduleSeeder.seed()
        self.stdout.write(
            self.style.SUCCESS("Duty schedules seeding completed successfully")
        )


def seed_duty_schedules():
    DutyScheduleSeeder.seed()
