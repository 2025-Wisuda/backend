from schedule.models import LabSchedule
from custom_auth.factories.user_factory import UserFactory
from schedule.factories.lab_schedule_factory import LabScheduleFactory


class LabScheduleSeeder:
    @staticmethod
    def seed():
        for _ in range(20):
            LabScheduleFactory()
        print("Lab schedule dummy data created")
