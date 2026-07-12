import factory
from factory.django import DjangoModelFactory
from faker import Faker

from apps.users.models import User, UserRole, OAuthAccount

fake = Faker()


class UserFactory(DjangoModelFactory):
    """
    Creates User instances for tests.
    Usage:
        user = UserFactory()
        instructor = UserFactory(role=UserRole.INSTRUCTOR)
        user = UserFactory(email="specific@email.com")
    """

    class Meta:
        model = User
        skip_postgeneration_save = True

    email = factory.LazyFunction(lambda: fake.unique.email())
    full_name = factory.LazyFunction(lambda: fake.name())
    role = UserRole.STUDENT
    is_active = True
    is_verified = False
    is_staff = False

    @factory.post_generation
    def password(obj, create, extracted, **kwargs):
        # Default password is "TestPass123!" unless overridden
        password = extracted or "TestPass123!"
        obj.set_password(password)
        if create:
            obj.save(update_fields=["password"])


class InstructorFactory(UserFactory):
    role = UserRole.INSTRUCTOR
    is_verified = True


class RecruiterFactory(UserFactory):
    role = UserRole.RECRUITER
    is_verified = True


class AdminFactory(UserFactory):
    role = UserRole.ADMIN
    is_staff = True
    is_superuser = True
    is_verified = True


class OAuthAccountFactory(DjangoModelFactory):
    class Meta:
        model = OAuthAccount

    user = factory.SubFactory(UserFactory)
    provider = "google-oauth2"
    provider_uid = factory.LazyFunction(lambda: str(fake.unique.random_number(digits=15)))
    extra_data = factory.LazyAttribute(lambda o: {
        "email": o.user.email,
        "name": o.user.full_name,
        "picture": "https://lh3.googleusercontent.com/test",
    })
