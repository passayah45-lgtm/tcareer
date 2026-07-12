from decimal import Decimal
from rest_framework import serializers
from apps.users.serializers import UserSerializer
from common.uploads import UploadValidationService
from .models import (
    Course, Lesson, VideoLesson, Enrollment, LessonProgress,
    CourseStatus, LessonType, CourseLevel,
)


class VideoLessonSerializer(serializers.ModelSerializer):
    class Meta:
        model = VideoLesson
        fields = [
            "id", "hls_url", "thumbnail_url", "duration_seconds",
            "transcoding_status", "file_size_bytes",
        ]
        read_only_fields = fields


class LessonSerializer(serializers.ModelSerializer):
    video = VideoLessonSerializer(read_only=True)
    is_accessible = serializers.SerializerMethodField()

    class Meta:
        model = Lesson
        fields = [
            "id", "title", "lesson_type", "content", "position",
            "is_published", "is_free_preview", "video", "is_accessible",
        ]
        read_only_fields = ["id", "video", "is_accessible"]

    def get_is_accessible(self, obj):
        request = self.context.get("request")
        if not request or not request.user.is_authenticated:
            return obj.is_free_preview
        user = request.user
        if user.role in ("instructor", "admin"):
            return True
        return Enrollment.objects.filter(
            user=user, course=obj.course, status="active"
        ).exists() or obj.is_free_preview


class LessonCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Lesson
        fields = ["title", "lesson_type", "content", "position", "is_free_preview"]

    def validate_position(self, value):
        if value < 0:
            raise serializers.ValidationError("Position must be 0 or greater.")
        return value


class CourseListSerializer(serializers.ModelSerializer):
    instructor_name = serializers.CharField(source="instructor.full_name", read_only=True)
    total_lessons = serializers.ReadOnlyField()
    is_enrolled = serializers.SerializerMethodField()

    class Meta:
        model = Course
        fields = [
            "id", "title", "slug", "short_description", "thumbnail_url",
            "level", "status", "price", "language", "instructor_name",
            "total_lessons", "is_enrolled", "created_at",
        ]

    def get_is_enrolled(self, obj):
        request = self.context.get("request")
        if not request or not request.user.is_authenticated:
            return False
        return Enrollment.objects.filter(
            user=request.user, course=obj, status="active"
        ).exists()


class CourseDetailSerializer(serializers.ModelSerializer):
    instructor = UserSerializer(read_only=True)
    lessons = serializers.SerializerMethodField()
    total_lessons = serializers.ReadOnlyField()
    is_enrolled = serializers.SerializerMethodField()

    class Meta:
        model = Course
        fields = [
            "id", "title", "slug", "short_description", "description",
            "thumbnail_url", "preview_video_url", "level", "status",
            "price", "language", "tags", "requirements", "what_you_learn",
            "pass_threshold", "instructor", "lessons", "total_lessons",
            "is_enrolled", "created_at", "updated_at",
        ]

    def get_lessons(self, obj):
        lessons = obj.lessons.filter(is_published=True, deleted_at=None)
        return LessonSerializer(lessons, many=True, context=self.context).data

    def get_is_enrolled(self, obj):
        request = self.context.get("request")
        if not request or not request.user.is_authenticated:
            return False
        return Enrollment.objects.filter(
            user=request.user, course=obj, status="active"
        ).exists()


class CourseCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Course
        fields = [
            "title", "short_description", "description", "thumbnail_url",
            "level", "price", "language", "tags", "requirements",
            "what_you_learn", "pass_threshold",
        ]

    def validate_price(self, value):
        if value < Decimal("0"):
            raise serializers.ValidationError("Price cannot be negative.")
        return value

    def validate_pass_threshold(self, value):
        if not 1 <= value <= 100:
            raise serializers.ValidationError("Pass threshold must be between 1 and 100.")
        return value

    def create(self, validated_data):
        validated_data["instructor"] = self.context["request"].user
        return super().create(validated_data)


class CourseUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Course
        fields = [
            "title", "short_description", "description", "thumbnail_url",
            "preview_video_url", "level", "price", "language", "tags",
            "requirements", "what_you_learn", "pass_threshold", "status",
        ]

    def validate_status(self, value):
        course = self.instance
        if value == CourseStatus.PUBLISHED:
            if not course.lessons.filter(is_published=True).exists():
                raise serializers.ValidationError(
                    "A course must have at least one published lesson before publishing."
                )
        return value


class EnrollmentSerializer(serializers.ModelSerializer):
    course = CourseListSerializer(read_only=True)
    first_lesson_id = serializers.SerializerMethodField()

    class Meta:
        model = Enrollment
        fields = [
            "id", "course", "status", "amount_paid",
            "completed_at", "last_accessed_at", "created_at",
            "first_lesson_id",
        ]
        read_only_fields = ["id", "course", "status", "amount_paid", "completed_at", "last_accessed_at", "created_at"]

    def get_first_lesson_id(self, obj):
        lesson = obj.course.lessons.filter(
            is_published=True
        ).order_by("position").first()
        return str(lesson.id) if lesson else None


class LessonProgressSerializer(serializers.ModelSerializer):
    lesson_id = serializers.UUIDField(source="lesson.id", read_only=True)
    lesson_title = serializers.CharField(source="lesson.title", read_only=True)

    class Meta:
        model = LessonProgress
        fields = [
            "id", "lesson_id", "lesson_title", "is_completed",
            "watch_percentage", "last_position_seconds", "completed_at",
        ]
        read_only_fields = ["id", "lesson_id", "lesson_title", "completed_at"]


class UpdateProgressSerializer(serializers.Serializer):
    watch_percentage = serializers.IntegerField(min_value=0, max_value=100)
    last_position_seconds = serializers.IntegerField(min_value=0, required=False)

    def validate_watch_percentage(self, value):
        return min(value, 100)


class UploadUrlRequestSerializer(serializers.Serializer):
    file_name = serializers.CharField(max_length=255)
    content_type = serializers.ChoiceField(
        choices=["video/mp4", "video/quicktime", "video/x-msvideo", "video/webm"],
        default="video/mp4",
    )
    file_size = serializers.IntegerField(min_value=0, required=False, default=0)

    def validate(self, attrs):
        UploadValidationService.validate_metadata(
            file_name=attrs["file_name"],
            content_type=attrs["content_type"],
            file_size=attrs.get("file_size", 0),
            allowed_extensions={".mp4", ".mov", ".avi", ".webm"},
            allowed_mime_types={"video/mp4", "video/quicktime", "video/x-msvideo", "video/webm"},
            max_size_bytes=1024 * 1024 * 1024,
        )
        return attrs


class LessonReorderItemSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    position = serializers.IntegerField(min_value=0)


class LessonReorderSerializer(serializers.Serializer):
    lessons = LessonReorderItemSerializer(many=True, min_length=1)

    def validate_lessons(self, value):
        positions = [item['position'] for item in value]
        if len(positions) != len(set(positions)):
            raise serializers.ValidationError(
                'Lesson positions must be unique within the course.'
            )
        return value


class LessonInlineUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Lesson
        fields = ['title', 'lesson_type', 'content', 'is_published', 'is_free_preview']

    def validate_lesson_type(self, value):
        valid = [choice[0] for choice in LessonType.choices]
        if value not in valid:
            raise serializers.ValidationError(
                'Invalid lesson type. Choose from: ' + ', '.join(valid) + '.'
            )
        return value


class QuizQuestionBulkItemSerializer(serializers.Serializer):
    question_text = serializers.CharField(min_length=5, max_length=2000)
    options = serializers.ListField(
        child=serializers.CharField(max_length=500),
        min_length=2,
        max_length=4,
    )
    correct_index = serializers.IntegerField(min_value=0)
    explanation = serializers.CharField(max_length=2000, allow_blank=True, default='')
    position = serializers.IntegerField(min_value=0, default=0)

    def validate(self, data):
        options = data.get('options', [])
        correct_index = data.get('correct_index', 0)
        if any(not str(opt).strip() for opt in options):
            raise serializers.ValidationError({'options': 'Options cannot be empty strings.'})
        if correct_index >= len(options):
            raise serializers.ValidationError(
                {'correct_index': 'correct_index must be less than the number of options.'}
            )
        while len(options) < 4:
            options.append('Option ' + str(len(options) + 1))
        data['options'] = options
        return data


class QuizQuestionBulkCreateSerializer(serializers.Serializer):
    questions = QuizQuestionBulkItemSerializer(many=True, min_length=1)
    replace = serializers.BooleanField(default=False)

    def validate_questions(self, value):
        if len(value) > 50:
            raise serializers.ValidationError(
                'Cannot create more than 50 questions in a single request.'
            )
        return value
