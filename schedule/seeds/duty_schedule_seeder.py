from schedule.models import DutySchedule
from schedule.factories.duty_schedule_factory import DutyScheduleFactory
from custom_auth.factories.user_factory import UserFactory


class DutyScheduleSeeder:
    @staticmethod
    def seed():
        for _ in range(10):
            DutyScheduleFactory(teaching_assistants=[UserFactory()])
        print("Duty schedule dummy data created")
