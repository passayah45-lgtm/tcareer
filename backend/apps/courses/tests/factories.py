import factory
from factory.django import DjangoModelFactory
from faker import Faker

from apps.users.tests.factories import UserFactory, InstructorFactory
from apps.courses.models import (
    Course, Lesson, VideoLesson, Enrollment, LessonProgress,
    CourseStatus, LessonType, TranscodingStatus, EnrollmentStatus,
)

fake = Faker()


class CourseFactory(DjangoModelFactory):
    class Meta:
        model = Course

    instructor = factory.SubFactory(InstructorFactory)
    title = factory.LazyFunction(lambda: fake.sentence(nb_words=4).rstrip("."))
    short_description = factory.LazyFunction(lambda: fake.sentence())
    description = factory.LazyFunction(lambda: fake.paragraph(nb_sentences=5))
    level = "beginner"
    status = CourseStatus.DRAFT
    price = factory.LazyFunction(lambda: fake.pydecimal(left_digits=2, right_digits=2, min_value=1, max_value=99))
    requirements = factory.LazyFunction(lambda: ["Basic computer literacy"])
    what_you_learn = factory.LazyFunction(lambda: ["Complete the course objectives"])


class PublishedCourseFactory(CourseFactory):
    status = CourseStatus.PUBLISHED


class FreeCourseFactory(CourseFactory):
    price = 0
    status = CourseStatus.PUBLISHED


class LessonFactory(DjangoModelFactory):
    class Meta:
        model = Lesson

    course = factory.SubFactory(CourseFactory)
    title = factory.LazyFunction(lambda: fake.sentence(nb_words=5).rstrip("."))
    lesson_type = LessonType.VIDEO
    content = factory.LazyFunction(lambda: fake.paragraph())
    position = factory.Sequence(lambda n: (n + 1) * 10)
    is_published = True


class VideoLessonFactory(DjangoModelFactory):
    class Meta:
        model = VideoLesson

    lesson = factory.SubFactory(LessonFactory)
    hls_url = factory.LazyFunction(lambda: f"https://cdn.tcareer.com/hls/{fake.uuid4()}/master.m3u8")
    thumbnail_url = factory.LazyFunction(lambda: f"https://cdn.tcareer.com/thumbnails/{fake.uuid4()}.jpg")
    duration_seconds = factory.LazyFunction(lambda: fake.random_int(min=60, max=3600))
    transcoding_status = TranscodingStatus.COMPLETE


class EnrollmentFactory(DjangoModelFactory):
    class Meta:
        model = Enrollment

    user = factory.SubFactory(UserFactory)
    course = factory.SubFactory(PublishedCourseFactory)
    status = EnrollmentStatus.ACTIVE
    amount_paid = factory.LazyAttribute(lambda o: o.course.price)


class LessonProgressFactory(DjangoModelFactory):
    class Meta:
        model = LessonProgress

    enrollment = factory.SubFactory(EnrollmentFactory)
    lesson = factory.LazyAttribute(lambda o: o.enrollment.course.lessons.first())
    is_completed = False
    watch_percentage = 0
