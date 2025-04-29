import factory
from faker import Faker
from django.contrib.auth import get_user_model
import random

fake = Faker()
User = get_user_model()


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User

    username = factory.LazyAttribute(lambda _: fake.unique.user_name())
    email = factory.LazyAttribute(lambda _: fake.unique.email())
    first_name = factory.LazyAttribute(lambda _: fake.first_name())
    last_name = factory.LazyAttribute(lambda _: fake.last_name())
    is_active = True

    @factory.lazy_attribute
    def student_id(self):
        return (
            fake.unique.random_number(digits=10)
            if random.choice([True, False])
            else None
        )

    @factory.lazy_attribute
    def employee_id(self):
        return fake.unique.random_number(digits=18) if self.student_id is None else None

    @factory.post_generation
    def set_password(obj, create, extracted, **kwargs):
        obj.set_password("password")
        if create:
            obj.save()
