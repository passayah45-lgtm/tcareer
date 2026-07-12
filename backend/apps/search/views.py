"""
Search API for T-Career.

Uses PostgreSQL icontains at MVP.
When the platform reaches 10,000+ courses, migrate to:
1. PostgreSQL full-text search with tsvector (no external service needed up to ~100k records)
2. Meilisearch or Elasticsearch for more complex relevance ranking beyond that

The current implementation is fast enough for the MVP catalog size
and requires zero additional infrastructure.
"""

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from django.db.models import Q

from apps.courses.models import Course, CourseStatus
from apps.tracks.models import CareerTrack
from apps.jobs.models import JobListing


@api_view(["GET"])
@permission_classes([AllowAny])
def search(request):
    """
    GET /api/v1/search/?q=python&type=all

    Unified search across courses, tracks, and jobs.
    type: all | course | track | job (default: all)
    limit: results per type (default: 5)
    """
    query = request.query_params.get("q", "").strip()
    search_type = request.query_params.get("type", "all")
    limit = min(int(request.query_params.get("limit", 5)), 20)

    if not query or len(query) < 2:
        return Response({
            "query": query,
            "courses": [],
            "tracks": [],
            "jobs": [],
            "total": 0,
        })

    results = {"query": query, "courses": [], "tracks": [], "jobs": [], "total": 0}

    if search_type in ("all", "course"):
        courses = Course.objects.filter(
            Q(title__icontains=query) |
            Q(short_description__icontains=query) |
            Q(tags__icontains=query),
            status=CourseStatus.PUBLISHED,
            deleted_at=None,
        ).select_related("instructor")[:limit]

        results["courses"] = [
            {
                "id": str(c.id),
                "title": c.title,
                "slug": c.slug,
                "short_description": c.short_description,
                "level": c.level,
                "price": str(c.price),
                "thumbnail_url": c.thumbnail_url,
                "instructor_name": c.instructor.full_name if c.instructor else "",
            }
            for c in courses
        ]

    if search_type in ("all", "track"):
        tracks = CareerTrack.objects.filter(
            Q(title__icontains=query) |
            Q(short_description__icontains=query) |
            Q(skills_acquired__icontains=query) |
            Q(target_job_titles__icontains=query),
            is_active=True,
        )[:limit]

        results["tracks"] = [
            {
                "id": str(t.id),
                "title": t.title,
                "slug": t.slug,
                "short_description": t.short_description,
                "category": t.category,
                "color": t.color,
                "duration_display": t.duration_display,
            }
            for t in tracks
        ]

    if search_type in ("all", "job"):
        jobs = JobListing.objects.filter(
            Q(title__icontains=query) |
            Q(company_name__icontains=query) |
            Q(description__icontains=query),
            is_active=True,
        )[:limit]

        results["jobs"] = [
            {
                "id": str(j.id),
                "title": j.title,
                "company_name": j.company_name,
                "location": j.location,
                "job_type_display": j.get_job_type_display(),
                "salary_display": j.salary_display,
            }
            for j in jobs
        ]

    results["total"] = (
        len(results["courses"]) +
        len(results["tracks"]) +
        len(results["jobs"])
    )

    return Response(results)
