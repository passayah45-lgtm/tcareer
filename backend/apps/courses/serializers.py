from decimal import Decimal

from rest_framework import serializers

from apps.users.serializers import UserSerializer
from common.uploads import UploadValidationService

from .models import (
    AcademicReviewerProfile,
    ContentReviewStatus,
    Course,
    CourseProject,
    CourseProjectReviewDecision,
    CourseReview,
    CourseStatus,
    Enrollment,
    Lesson,
    LessonProgress,
    LessonStructuredReview,
    LessonType,
    LessonVersion,
    ResourceLibraryItem,
    ReviewAssignment,
    ReviewDecision,
    ReviewPriority,
    ReviewTargetType,
    VideoLesson,
)


class VideoLessonSerializer(serializers.ModelSerializer):
    class Meta:
        model = VideoLesson
        fields = [
            "id",
            "hls_url",
            "thumbnail_url",
            "duration_seconds",
            "transcoding_status",
            "file_size_bytes",
        ]
        read_only_fields = fields


class LessonSerializer(serializers.ModelSerializer):
    video = VideoLessonSerializer(read_only=True)
    is_accessible = serializers.SerializerMethodField()

    class Meta:
        model = Lesson
        fields = [
            "id",
            "title",
            "lesson_type",
            "content",
            "position",
            "is_published",
            "is_free_preview",
            "video",
            "is_accessible",
        ]
        read_only_fields = ["id", "video", "is_accessible"]

    def get_is_accessible(self, obj):
        request = self.context.get("request")
        if not request or not request.user.is_authenticated:
            return obj.is_free_preview
        user = request.user
        if user.role in ("instructor", "admin"):
            return True
        return (
            Enrollment.objects.filter(user=user, course=obj.course, status="active").exists()
            or obj.is_free_preview
        )


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
            "id",
            "title",
            "slug",
            "short_description",
            "thumbnail_url",
            "level",
            "status",
            "price",
            "language",
            "instructor_name",
            "total_lessons",
            "is_enrolled",
            "created_at",
        ]

    def get_is_enrolled(self, obj):
        request = self.context.get("request")
        if not request or not request.user.is_authenticated:
            return False
        return Enrollment.objects.filter(user=request.user, course=obj, status="active").exists()


class CourseDetailSerializer(serializers.ModelSerializer):
    instructor = UserSerializer(read_only=True)
    lessons = serializers.SerializerMethodField()
    total_lessons = serializers.ReadOnlyField()
    is_enrolled = serializers.SerializerMethodField()

    class Meta:
        model = Course
        fields = [
            "id",
            "title",
            "slug",
            "short_description",
            "description",
            "thumbnail_url",
            "preview_video_url",
            "level",
            "status",
            "price",
            "language",
            "tags",
            "requirements",
            "what_you_learn",
            "pass_threshold",
            "instructor",
            "lessons",
            "total_lessons",
            "is_enrolled",
            "created_at",
            "updated_at",
        ]

    def get_lessons(self, obj):
        lessons = obj.lessons.filter(is_published=True, deleted_at=None)
        return LessonSerializer(lessons, many=True, context=self.context).data

    def get_is_enrolled(self, obj):
        request = self.context.get("request")
        if not request or not request.user.is_authenticated:
            return False
        return Enrollment.objects.filter(user=request.user, course=obj, status="active").exists()


class CourseCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Course
        fields = [
            "title",
            "short_description",
            "description",
            "thumbnail_url",
            "level",
            "price",
            "language",
            "tags",
            "requirements",
            "what_you_learn",
            "pass_threshold",
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
            "title",
            "short_description",
            "description",
            "thumbnail_url",
            "preview_video_url",
            "level",
            "price",
            "language",
            "tags",
            "requirements",
            "what_you_learn",
            "pass_threshold",
            "status",
        ]

    def validate_status(self, value):
        course = self.instance
        if value == CourseStatus.PUBLISHED:
            from .services import CourseService

            errors = CourseService.publish_validation_errors(course)
            if errors:
                raise serializers.ValidationError(" ".join(errors))
        return value


class EnrollmentSerializer(serializers.ModelSerializer):
    course = CourseListSerializer(read_only=True)
    first_lesson_id = serializers.SerializerMethodField()

    class Meta:
        model = Enrollment
        fields = [
            "id",
            "course",
            "status",
            "amount_paid",
            "completed_at",
            "last_accessed_at",
            "created_at",
            "first_lesson_id",
        ]
        read_only_fields = [
            "id",
            "course",
            "status",
            "amount_paid",
            "completed_at",
            "last_accessed_at",
            "created_at",
        ]

    def get_first_lesson_id(self, obj):
        lesson = obj.course.lessons.filter(is_published=True).order_by("position").first()
        return str(lesson.id) if lesson else None


class LessonProgressSerializer(serializers.ModelSerializer):
    lesson_id = serializers.UUIDField(source="lesson.id", read_only=True)
    lesson_title = serializers.CharField(source="lesson.title", read_only=True)

    class Meta:
        model = LessonProgress
        fields = [
            "id",
            "lesson_id",
            "lesson_title",
            "is_completed",
            "watch_percentage",
            "last_position_seconds",
            "completed_at",
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
        positions = [item["position"] for item in value]
        if len(positions) != len(set(positions)):
            raise serializers.ValidationError("Lesson positions must be unique within the course.")
        return value


class LessonInlineUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Lesson
        fields = ["title", "lesson_type", "content", "is_published", "is_free_preview"]

    def validate_lesson_type(self, value):
        valid = [choice[0] for choice in LessonType.choices]
        if value not in valid:
            raise serializers.ValidationError(
                "Invalid lesson type. Choose from: " + ", ".join(valid) + "."
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
    explanation = serializers.CharField(max_length=2000, allow_blank=True, default="")
    position = serializers.IntegerField(min_value=0, default=0)

    def validate(self, data):
        options = data.get("options", [])
        correct_index = data.get("correct_index", 0)
        if any(not str(opt).strip() for opt in options):
            raise serializers.ValidationError({"options": "Options cannot be empty strings."})
        if correct_index >= len(options):
            raise serializers.ValidationError(
                {"correct_index": "correct_index must be less than the number of options."}
            )
        while len(options) < 4:
            options.append("Option " + str(len(options) + 1))
        data["options"] = options
        return data


class QuizQuestionBulkCreateSerializer(serializers.Serializer):
    questions = QuizQuestionBulkItemSerializer(many=True, min_length=1)
    replace = serializers.BooleanField(default=False)

    def validate_questions(self, value):
        if len(value) > 50:
            raise serializers.ValidationError(
                "Cannot create more than 50 questions in a single request."
            )
        return value


class CourseReviewSerializer(serializers.ModelSerializer):
    reviewer_email = serializers.EmailField(source="reviewer.email", read_only=True)
    submitted_by_email = serializers.EmailField(source="submitted_by.email", read_only=True)

    class Meta:
        model = CourseReview
        fields = [
            "id",
            "course",
            "status",
            "reviewer_email",
            "submitted_by_email",
            "comments",
            "required_fixes",
            "reviewed_at",
            "created_at",
        ]
        read_only_fields = fields


class ReviewActionSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=ContentReviewStatus.choices)
    comments = serializers.CharField(required=False, allow_blank=True, default="")
    required_fixes = serializers.ListField(
        child=serializers.CharField(max_length=500),
        required=False,
        default=list,
    )


class SubmitCourseReviewSerializer(serializers.Serializer):
    comments = serializers.CharField(required=False, allow_blank=True, default="")


class LessonReviewActionSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=ContentReviewStatus.choices)
    comments = serializers.CharField(required=False, allow_blank=True, default="")


class LessonVersionSerializer(serializers.ModelSerializer):
    editor_email = serializers.EmailField(source="editor.email", read_only=True)

    class Meta:
        model = LessonVersion
        fields = [
            "id",
            "lesson",
            "version_number",
            "editor_email",
            "title",
            "lesson_type",
            "content",
            "summary_of_changes",
            "is_published_version",
            "created_at",
        ]
        read_only_fields = fields


class LessonVersionCreateSerializer(serializers.Serializer):
    summary_of_changes = serializers.CharField(required=False, allow_blank=True, default="")


class LessonVersionCompareSerializer(serializers.Serializer):
    left_version_id = serializers.UUIDField()
    right_version_id = serializers.UUIDField()


class CourseProjectSerializer(serializers.ModelSerializer):
    reviewed_by_email = serializers.EmailField(source="reviewed_by.email", read_only=True)

    class Meta:
        model = CourseProject
        fields = [
            "id",
            "course",
            "instructions",
            "required_deliverables",
            "rubric",
            "evaluation_criteria",
            "passing_score",
            "reviewer_notes",
            "example_solution",
            "resources",
            "version",
            "approval_state",
            "reviewed_by_email",
            "reviewed_at",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "course",
            "version",
            "approval_state",
            "reviewed_by_email",
            "reviewed_at",
            "created_at",
            "updated_at",
        ]


class CourseProjectReviewSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=ContentReviewStatus.choices)
    notes = serializers.CharField(required=False, allow_blank=True, default="")


class ResourceLibraryItemSerializer(serializers.ModelSerializer):
    owner_email = serializers.EmailField(source="owner.email", read_only=True)
    course_title = serializers.CharField(source="course.title", read_only=True)
    course_id = serializers.UUIDField(required=False, allow_null=True, write_only=True)

    class Meta:
        model = ResourceLibraryItem
        fields = [
            "id",
            "owner_email",
            "course",
            "course_id",
            "course_title",
            "title",
            "resource_type",
            "file_url",
            "storage_key",
            "file_name",
            "content_type",
            "file_size_bytes",
            "checksum",
            "description",
            "version",
            "visibility",
            "review_status",
            "review_notes",
            "download_count",
            "malware_scan_status",
            "malware_scanner",
            "malware_scanned_at",
            "malware_scan_result",
            "metadata",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "owner_email",
            "course",
            "course_title",
            "storage_key",
            "review_status",
            "review_notes",
            "download_count",
            "malware_scan_status",
            "malware_scanner",
            "malware_scanned_at",
            "malware_scan_result",
            "created_at",
            "updated_at",
        ]

    def validate(self, attrs):
        course_id = attrs.pop("course_id", None)
        if course_id:
            try:
                attrs["course"] = Course.objects.get(id=course_id, deleted_at=None)
            except Course.DoesNotExist as exc:
                raise serializers.ValidationError({"course_id": "Course not found."}) from exc
        return attrs


class AcademicReviewerProfileSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(source="user.email", read_only=True)
    user_id = serializers.UUIDField(source="user.id", read_only=True)

    class Meta:
        model = AcademicReviewerProfile
        fields = [
            "id",
            "user_id",
            "email",
            "reviewer_role",
            "organization",
            "subject_tags",
            "is_active",
            "max_active_assignments",
            "automatic_assignment_enabled",
            "created_at",
        ]
        read_only_fields = ["id", "email", "user_id", "created_at"]


class ReviewAssignmentSerializer(serializers.ModelSerializer):
    reviewer_email = serializers.EmailField(source="assigned_reviewer.email", read_only=True)
    assigned_by_email = serializers.EmailField(source="assigned_by.email", read_only=True)
    course_title = serializers.CharField(source="course.title", read_only=True)
    lesson_title = serializers.CharField(source="lesson.title", read_only=True)
    is_overdue = serializers.BooleanField(read_only=True)

    class Meta:
        model = ReviewAssignment
        fields = [
            "id",
            "target_type",
            "target_id",
            "course",
            "course_title",
            "lesson",
            "lesson_title",
            "assigned_reviewer",
            "reviewer_email",
            "assigned_by_email",
            "organization",
            "subject",
            "priority",
            "review_status",
            "due_date",
            "reassignment_history",
            "escalation_level",
            "escalated_to",
            "escalation_reason",
            "escalated_at",
            "completed_at",
            "is_overdue",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "course",
            "lesson",
            "reviewer_email",
            "assigned_by_email",
            "course_title",
            "lesson_title",
            "reassignment_history",
            "escalation_level",
            "escalated_to",
            "escalation_reason",
            "escalated_at",
            "completed_at",
            "is_overdue",
            "created_at",
            "updated_at",
        ]


class ReviewAssignmentCreateSerializer(serializers.Serializer):
    target_type = serializers.ChoiceField(choices=ReviewTargetType.choices)
    target_id = serializers.UUIDField()
    reviewer_id = serializers.UUIDField()
    due_date = serializers.DateTimeField(required=False, allow_null=True)
    priority = serializers.ChoiceField(
        choices=ReviewPriority.choices, default=ReviewPriority.NORMAL
    )
    subject = serializers.CharField(required=False, allow_blank=True, default="")


class ReviewReassignSerializer(serializers.Serializer):
    reviewer_id = serializers.UUIDField()
    reason = serializers.CharField(required=False, allow_blank=True, default="")


class InstructorReviewResponseSerializer(serializers.Serializer):
    response = serializers.CharField(max_length=4000)
    addressed = serializers.BooleanField(default=False)


class LessonStructuredReviewSerializer(serializers.ModelSerializer):
    reviewer_email = serializers.EmailField(source="reviewer.email", read_only=True)

    class Meta:
        model = LessonStructuredReview
        fields = [
            "id",
            "lesson",
            "assignment",
            "reviewer_email",
            "decision",
            "section_comments",
            "required_changes",
            "instructor_response",
            "addressed_at",
            "completed_at",
            "created_at",
        ]
        read_only_fields = fields


class StructuredLessonReviewActionSerializer(serializers.Serializer):
    decision = serializers.ChoiceField(choices=ReviewDecision.choices)
    section_comments = serializers.DictField(required=False, default=dict)
    required_changes = serializers.ListField(
        child=serializers.CharField(max_length=500),
        required=False,
        default=list,
    )


class CourseProjectReviewDecisionSerializer(serializers.ModelSerializer):
    reviewer_email = serializers.EmailField(source="reviewer.email", read_only=True)

    class Meta:
        model = CourseProjectReviewDecision
        fields = [
            "id",
            "project",
            "assignment",
            "reviewer_email",
            "decision",
            "project_version",
            "review_sections",
            "required_changes",
            "notes",
            "created_at",
        ]
        read_only_fields = fields


class StructuredProjectReviewActionSerializer(serializers.Serializer):
    decision = serializers.ChoiceField(choices=ReviewDecision.choices)
    review_sections = serializers.DictField(required=False, default=dict)
    required_changes = serializers.ListField(
        child=serializers.CharField(max_length=500),
        required=False,
        default=list,
    )
    notes = serializers.CharField(required=False, allow_blank=True, default="")


class ResourceUploadRequestSerializer(serializers.Serializer):
    course_id = serializers.UUIDField(required=False, allow_null=True)
    file_name = serializers.CharField(max_length=255)
    content_type = serializers.CharField(max_length=120)
    file_size = serializers.IntegerField(min_value=1)
    checksum = serializers.CharField(max_length=128, required=False, allow_blank=True, default="")
    visibility = serializers.ChoiceField(
        choices=["private", "course", "public"],
        default="private",
    )


class ResourceReviewActionSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=ContentReviewStatus.choices)
    notes = serializers.CharField(required=False, allow_blank=True, default="")


class ResourceScanActionSerializer(serializers.Serializer):
    provider = serializers.ChoiceField(
        choices=["disabled", "mock", "clamav", "external"],
        required=False,
    )
    sample_text = serializers.CharField(required=False, allow_blank=True, default="")


class PublishBlockerSerializer(serializers.Serializer):
    blockers = serializers.ListField()
    publish_ready = serializers.BooleanField()


class QualityDashboardSerializer(serializers.Serializer):
    summary = serializers.DictField()
    courses = serializers.ListField()


class InstructorAnalyticsSerializer(serializers.Serializer):
    courses_authored = serializers.IntegerField()
    lessons_created = serializers.IntegerField()
    lessons_approved = serializers.IntegerField()
    reviews_completed = serializers.IntegerField()
    courses_published = serializers.IntegerField()
    resources_created = serializers.IntegerField()
