import factory
from faker import Faker
import random
from django.utils import timezone
from custom_auth.factories.user_factory import UserFactory
from schedule.models import LabSchedule
from datetime import datetime, timedelta

fake = Faker()


class LabScheduleFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = LabSchedule

    activity_type = factory.LazyFunction(
        lambda: random.choice(
            [choice[0] for choice in LabSchedule.ActivityType.choices]
        )
    )
    activity_description = factory.LazyAttribute(lambda _: fake.sentence())
    schedule_date = factory.LazyFunction(
        lambda: fake.date_between(start_date="today", end_date="+30d")
    )
    start_time = factory.LazyFunction(lambda: fake.time_object())
    end_time = factory.LazyAttribute(
        lambda o: (
            datetime.combine(datetime.today(), o.start_time)
            + timedelta(minutes=random.randint(30, 180))
        ).time()
    )

    created_by = factory.SubFactory(UserFactory)
    is_active = True
    approval_status = LabSchedule.ApprovalStatus.PENDING
    approved_by = None
    approval_time = None
    created_at = factory.LazyFunction(timezone.now)
    updated_at = factory.LazyFunction(timezone.now)

    @factory.post_generation
    def approval_status_and_time(self, create, extracted, **kwargs):
        if self.created_by.is_staff or self.created_by.is_superuser:
            self.approval_status = LabSchedule.ApprovalStatus.APPROVED
            self.approved_by = self.created_by
            self.approval_time = datetime.now()

    @factory.post_generation
    def check_for_conflicts(self, create, extracted, **kwargs):
        retries = 5
        for _ in range(retries):
            conflicting_schedules = LabSchedule.objects.filter(
                schedule_date=self.schedule_date,
                start_time__lt=self.end_time,
                end_time__gt=self.start_time,
            )
            if not conflicting_schedules.exists():
                break
            else:
                self.schedule_date = fake.date_between(
                    start_date="today", end_date="+30d"
                )
                self.start_time = fake.time_object()
                self.end_time = (
                    datetime.combine(datetime.today(), self.start_time)
                    + timedelta(minutes=random.randint(30, 180))
                ).time()
        else:
            raise ValueError(
                f"Unable to generate a unique schedule after {retries} retries."
            )
