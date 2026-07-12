from rest_framework import serializers
from .models import CareerTrack, TrackCourse, UserTrackEnrollment


class TrackCourseSerializer(serializers.ModelSerializer):
    course_id = serializers.UUIDField(source="course.id", read_only=True)
    course_title = serializers.CharField(source="course.title", read_only=True)
    course_slug = serializers.CharField(source="course.slug", read_only=True)
    course_level = serializers.CharField(source="course.level", read_only=True)
    course_price = serializers.CharField(source="course.price", read_only=True)
    course_thumbnail = serializers.CharField(
        source="course.thumbnail_url", read_only=True
    )
    stage_display = serializers.CharField(source="get_stage_display", read_only=True)
    is_enrolled = serializers.SerializerMethodField()
    is_course_completed = serializers.SerializerMethodField()

    class Meta:
        model = TrackCourse
        fields = [
            "id", "position", "stage", "stage_display", "is_required", "notes",
            "course_id", "course_title", "course_slug", "course_level",
            "course_price", "course_thumbnail", "is_enrolled", "is_course_completed",
        ]

    def get_is_enrolled(self, obj):
        request = self.context.get("request")
        if not request or not request.user.is_authenticated:
            return False
        from apps.courses.models import Enrollment
        return Enrollment.objects.filter(
            user=request.user, course=obj.course
        ).exists()

    def get_is_course_completed(self, obj):
        request = self.context.get("request")
        if not request or not request.user.is_authenticated:
            return False
        from apps.courses.models import Enrollment, EnrollmentStatus
        return Enrollment.objects.filter(
            user=request.user,
            course=obj.course,
            status=EnrollmentStatus.COMPLETED,
        ).exists()


class CareerTrackListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for the track listing page."""

    total_courses = serializers.ReadOnlyField()
    required_courses_count = serializers.ReadOnlyField()
    duration_display = serializers.ReadOnlyField()
    category_display = serializers.CharField(source="get_category_display", read_only=True)
    is_enrolled = serializers.SerializerMethodField()

    class Meta:
        model = CareerTrack
        fields = [
            "id", "title", "slug", "short_description", "category",
            "category_display", "difficulty", "icon", "color",
            "target_job_titles", "skills_acquired", "duration_display",
            "estimated_weeks_min", "estimated_weeks_max",
            "avg_salary_min", "avg_salary_max", "total_courses",
            "required_courses_count", "is_enrolled", "position",
        ]

    def get_is_enrolled(self, obj):
        request = self.context.get("request")
        if not request or not request.user.is_authenticated:
            return False
        return UserTrackEnrollment.objects.filter(
            user=request.user, track=obj
        ).exists()


class CareerTrackDetailSerializer(CareerTrackListSerializer):
    """Full serializer including courses for the track detail page."""

    courses_by_stage = serializers.SerializerMethodField()
    user_enrollment = serializers.SerializerMethodField()

    class Meta(CareerTrackListSerializer.Meta):
        fields = CareerTrackListSerializer.Meta.fields + [
            "description", "courses_by_stage", "user_enrollment",
        ]

    def get_courses_by_stage(self, obj):
        stages = {1: "Foundation", 2: "Core Skills", 3: "Advanced"}
        result = []
        for stage_num, stage_name in stages.items():
            courses = obj.track_courses.filter(stage=stage_num).order_by("position")
            if courses.exists():
                result.append({
                    "stage": stage_num,
                    "stage_name": stage_name,
                    "courses": TrackCourseSerializer(
                        courses, many=True, context=self.context
                    ).data,
                })
        return result

    def get_user_enrollment(self, obj):
        request = self.context.get("request")
        if not request or not request.user.is_authenticated:
            return None
        try:
            enrollment = UserTrackEnrollment.objects.get(
                user=request.user, track=obj
            )
            return UserTrackEnrollmentSerializer(enrollment).data
        except UserTrackEnrollment.DoesNotExist:
            return None


class UserTrackEnrollmentSerializer(serializers.ModelSerializer):
    track_title = serializers.CharField(source="track.title", read_only=True)
    track_slug = serializers.CharField(source="track.slug", read_only=True)
    track_icon = serializers.CharField(source="track.icon", read_only=True)
    track_color = serializers.CharField(source="track.color", read_only=True)
    progress_percentage = serializers.ReadOnlyField()
    current_stage_display = serializers.CharField(
        source="get_current_stage_display", read_only=True
    )
    next_course = serializers.SerializerMethodField()
    total_required = serializers.SerializerMethodField()

    class Meta:
        model = UserTrackEnrollment
        fields = [
            "id", "track_title", "track_slug", "track_icon", "track_color",
            "current_stage", "current_stage_display", "courses_completed",
            "total_required", "progress_percentage", "is_completed",
            "completed_at", "last_activity_at", "created_at", "next_course",
        ]

    def get_next_course(self, obj):
        next_tc = obj.next_course
        if not next_tc:
            return None
        return {
            "course_id": str(next_tc.course.id),
            "course_title": next_tc.course.title,
            "course_slug": next_tc.course.slug,
            "stage": next_tc.stage,
            "position": next_tc.position,
        }

    def get_total_required(self, obj):
        return obj.track.required_courses_count
