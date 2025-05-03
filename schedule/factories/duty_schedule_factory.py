import factory
from faker import Faker
import random
from datetime import timedelta
from django.utils import timezone
from schedule.models import DutySchedule
from custom_auth.factories.user_factory import UserFactory

fake = Faker()


class DutyScheduleFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = DutySchedule

    days = factory.LazyFunction(
        lambda: random.choice([choice[0] for choice in DutySchedule.Days.choices])
    )
    start_date = factory.LazyFunction(
        lambda: fake.date_between(start_date="today", end_date="+10d")
    )
    end_date = factory.LazyAttribute(
        lambda o: o.start_date + timedelta(days=random.randint(7, 30))
    )
    start_time = factory.LazyFunction(lambda: fake.time_object())
    end_time = factory.LazyAttribute(
        lambda o: (
            timezone.datetime.combine(timezone.now().date(), o.start_time)
            + timedelta(hours=1)
        ).time()
    )
    is_active = True
    created_at = factory.LazyFunction(timezone.now)
    updated_at = factory.LazyFunction(timezone.now)

    @factory.post_generation
    def teaching_assistants(self, create, extracted, **kwargs):
        if not create:
            return
        if extracted:
            for user in extracted:
                self.teaching_assistants.add(user)
        else:
            self.teaching_assistants.add(UserFactory())

    @factory.post_generation
    def assign_dates(self, create, extracted, **kwargs):
        if create:
            self.assign_duty_dates()
