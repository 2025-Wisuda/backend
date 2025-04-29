from django.core.management.base import BaseCommand
from custom_auth.management.commands.seed_users import seed_users
from custom_auth.management.commands.seed_groups import seed_groups
from schedule.management.commands.seed_lab_schedules import seed_lab_schedules


class Command(BaseCommand):
    help = "Seed all data"

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.SUCCESS("Seeding started..."))

        try:
            self.stdout.write(self.style.SUCCESS("Seeding Groups data..."))
            seed_groups()
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error seeding Groups: {e}"))

        try:
            self.stdout.write(self.style.SUCCESS("Seeding Users data..."))
            seed_users()
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error seeding Users: {e}"))

        try:
            self.stdout.write(self.style.SUCCESS("Seeding LabSchedule data..."))
            seed_lab_schedules()
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error seeding LabSchedules: {e}"))

        self.stdout.write(self.style.SUCCESS("Seeding completed!"))
