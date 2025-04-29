import factory
from faker import Faker
import random
from django.utils import timezone
from custom_auth.factories.user_factory import UserFactory
from schedule.models import LabSchedule

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
    end_time = factory.LazyFunction(lambda: fake.time_object())
    created_by = factory.SubFactory(UserFactory)
    is_active = True
