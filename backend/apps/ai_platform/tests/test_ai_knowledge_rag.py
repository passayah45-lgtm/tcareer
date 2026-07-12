import pytest
from django.core.management import call_command
from django.test import override_settings
from django.urls import reverse

from apps.ai_platform.models import (
    AIFeature,
    AIRequest,
    RetrievalEvaluationDataset,
    KnowledgeCollectionType,
    KnowledgeDocument,
    KnowledgeIndexStatus,
    KnowledgeVisibility,
    RetrievalEvent,
)
from apps.ai_platform.services import AIContextBuilder, AIService, KnowledgeIndexingService, RetrievalEvaluationService, RetrievalService, VectorBackendRegistry
from apps.careers.models import CareerResume, Portfolio, PortfolioSkill, VisibilityChoice
from apps.courses.tests.factories import EnrollmentFactory, LessonFactory, PublishedCourseFactory
from apps.organizations.models import Organization, OrganizationMembership, OrganizationRole, OrganizationType
from apps.tracks.models import CareerTrack
from apps.users.tests.factories import UserFactory


pytestmark = pytest.mark.django_db


def test_index_course_creates_documents_chunks_and_fresh_status():
    course = PublishedCourseFactory(title="Django Career Track", description="Learn Django APIs for backend careers")
    LessonFactory(course=course, title="Django models", content="Models map Python classes to database tables.")

    documents = KnowledgeIndexingService.index_course(course=course)

    assert len(documents) == 2
    assert KnowledgeDocument.objects.filter(index_status=KnowledgeIndexStatus.INDEXED).count() == 2
    assert KnowledgeDocument.objects.filter(collection__collection_type=KnowledgeCollectionType.LESSONS, chunks__text__icontains="database").exists()
    assert all(document.checksum for document in documents)
    assert all(document.last_indexed_at for document in documents)


def test_retrieval_returns_citations_and_tracks_analytics_event():
    user = UserFactory()
    document = KnowledgeIndexingService.index_document(
        collection_type=KnowledgeCollectionType.FAQS,
        source_type="faq",
        source_id="django",
        title="Django FAQ",
        text="Django is useful for Python backend development and API careers.",
    )

    result = RetrievalService.search(user=user, query="Python backend API", feature=AIFeature.COURSE_TUTOR, limit=3)

    assert result["citations"][0]["document_id"] == str(document.id)
    assert result["confidence"] > 0
    assert RetrievalEvent.objects.filter(user=user, feature=AIFeature.COURSE_TUTOR, result_count__gte=1).exists()


def test_private_knowledge_is_visible_only_to_owner_or_admin():
    owner = UserFactory()
    outsider = UserFactory()
    admin = UserFactory(role="platform_admin")
    KnowledgeIndexingService.index_document(
        collection_type=KnowledgeCollectionType.RESUMES,
        source_type="resume",
        source_id="private-resume",
        title="Private resume",
        text="Private Kubernetes and Django experience",
        owner=owner,
        visibility=KnowledgeVisibility.PRIVATE,
    )

    denied = RetrievalService.search(user=outsider, query="Kubernetes Django", include_private=True)
    owner_result = RetrievalService.search(user=owner, query="Kubernetes Django", include_private=True)
    admin_result = RetrievalService.search(user=admin, query="Kubernetes Django")

    assert denied["results"] == []
    assert owner_result["results"]
    assert admin_result["results"]


def test_context_builder_assembles_citations_without_fabrication():
    user = UserFactory()
    KnowledgeIndexingService.index_document(
        collection_type=KnowledgeCollectionType.LESSONS,
        source_type="lesson",
        source_id="variables",
        title="Python variables",
        text="Variables store reusable values in Python programs.",
    )

    context = AIContextBuilder.build(user=user, feature=AIFeature.COURSE_TUTOR, input_text="Explain variables")

    assert "Python variables" in context["context_text"]
    assert context["citations"][0]["source_id"] == "variables"


def test_ai_service_adds_retrieval_metadata_when_context_exists():
    user = UserFactory()
    KnowledgeIndexingService.index_document(
        collection_type=KnowledgeCollectionType.LESSONS,
        source_type="lesson",
        source_id="django-models",
        title="Django models",
        text="Django models define database structure for Python applications.",
    )

    result = AIService.generate_text(user=user, feature=AIFeature.COURSE_TUTOR, input_text="How do Django models work?")

    assert result["retrieval"]["citations"]
    assert result["request"].metadata["retrieval"]["confidence"] > 0
    assert "Django models" in result["request"].rendered_prompt["user"]


def test_knowledge_api_reindex_search_and_status(api_client):
    admin = UserFactory(role="platform_admin")
    api_client.force_authenticate(user=admin)

    reindex = api_client.post(
        reverse("ai_platform:knowledge-reindex"),
        {
            "collection_type": "faqs",
            "source_type": "document",
            "source_id": "career-faq",
            "title": "Career FAQ",
            "text": "T-Career connects verified certificates, portfolios, and jobs.",
            "visibility": "public",
        },
        format="json",
    )
    search = api_client.post(reverse("ai_platform:knowledge-search"), {"query": "verified certificates jobs", "feature": "career_advice"}, format="json")
    status = api_client.get(reverse("ai_platform:knowledge-index-status"))
    embeddings = api_client.get(reverse("ai_platform:knowledge-embedding-status"))
    citations = api_client.post(reverse("ai_platform:knowledge-citation-preview"), {"query": "portfolios jobs", "feature": "career_advice"}, format="json")

    assert reindex.status_code == 201
    assert search.status_code == 200
    assert search.json()["data"]["citations"]
    assert status.status_code == 200
    assert status.json()["data"]["collections"]
    assert "privacy_summary" in status.json()["data"]
    assert status.json()["data"]["privacy_summary"]["safe"] is True
    assert embeddings.status_code == 200
    assert citations.status_code == 200


@override_settings(DEBUG=False, AI_VECTOR_BACKEND="pgvector", AI_VECTOR_DIMENSIONS=16)
def test_vector_backend_selection_health_and_dimension_validation():
    backend = VectorBackendRegistry.get_backend()
    vector = backend.embed("Django APIs", dimensions=16)

    assert backend.name == "pgvector"
    assert VectorBackendRegistry.health_check()["status"] == "healthy"
    backend.validate_dimensions(vector, expected_dimensions=16)
    with pytest.raises(ValueError):
        backend.validate_dimensions(vector, expected_dimensions=8)


@override_settings(AI_KNOWLEDGE_AUTO_INDEX=True)
def test_automatic_indexing_trigger_and_stale_marking():
    course = PublishedCourseFactory(title="Fresh Python APIs")

    assert KnowledgeDocument.objects.filter(source_type="course", source_id=str(course.id), index_status=KnowledgeIndexStatus.INDEXED).exists()

    KnowledgeIndexingService.mark_stale(source_type="course", source_id=course.id, reason="course_archived")

    document = KnowledgeDocument.objects.get(source_type="course", source_id=str(course.id))
    assert document.index_status == KnowledgeIndexStatus.STALE
    assert document.stale_reason == "course_archived"


def test_reindex_command_dry_run_does_not_duplicate_documents():
    course = PublishedCourseFactory(title="Command Reindex")
    KnowledgeIndexingService.index_course(course=course)
    before = KnowledgeDocument.objects.count()

    call_command("reindex_ai_knowledge", "--source-type", "course", "--limit", "1", "--dry-run")

    assert KnowledgeDocument.objects.count() == before


def test_private_portfolio_retrieval_isolation():
    owner = UserFactory()
    outsider = UserFactory()
    portfolio = Portfolio.objects.create(user=owner, visibility=VisibilityChoice.PRIVATE, headline="Private Django portfolio", bio="Secret PostgreSQL project")
    KnowledgeIndexingService.index_portfolio(portfolio=portfolio)

    denied = RetrievalService.search(user=outsider, query="PostgreSQL project", collection_types=[KnowledgeCollectionType.PORTFOLIOS], include_private=True)
    allowed = RetrievalService.search(user=owner, query="PostgreSQL project", collection_types=[KnowledgeCollectionType.PORTFOLIOS], include_private=True)

    assert denied["results"] == []
    assert allowed["results"]


def test_private_resume_retrieval_isolation():
    owner = UserFactory()
    outsider = UserFactory()
    resume = CareerResume.objects.create(user=owner, title="Private resume", summary="Secret Kubernetes work", target_role="Backend Developer")
    KnowledgeIndexingService.index_resume(resume=resume)

    denied = RetrievalService.search(user=outsider, query="Kubernetes", collection_types=[KnowledgeCollectionType.RESUMES], include_private=True)
    allowed = RetrievalService.search(user=owner, query="Kubernetes", collection_types=[KnowledgeCollectionType.RESUMES], include_private=True)

    assert denied["results"] == []
    assert allowed["citations"][0]["visibility"] == KnowledgeVisibility.PRIVATE


def test_organization_document_isolation():
    member = UserFactory()
    outsider = UserFactory()
    organization = Organization.objects.create(name="Tenant RAG", organization_type=OrganizationType.COMPANY)
    OrganizationMembership.objects.create(organization=organization, user=member, role=OrganizationRole.COMPANY_ADMIN)
    KnowledgeIndexingService.index_document(
        collection_type=KnowledgeCollectionType.ORGANIZATION_DOCUMENTS,
        source_type="organization_document",
        source_id="policy",
        title="Tenant policy",
        text="Internal talent policy mentions Django cohorts",
        organization=organization,
        visibility=KnowledgeVisibility.ORGANIZATION,
    )

    denied = RetrievalService.search(user=outsider, organization=organization, query="Django cohorts", collection_types=[KnowledgeCollectionType.ORGANIZATION_DOCUMENTS])
    allowed = RetrievalService.search(user=member, organization=organization, query="Django cohorts", collection_types=[KnowledgeCollectionType.ORGANIZATION_DOCUMENTS])

    assert denied["results"] == []
    assert allowed["results"]


def test_private_course_retrieval_requires_enrollment_or_instructor():
    course = PublishedCourseFactory(status="draft", title="Private Course")
    lesson = LessonFactory(course=course, title="Private lesson", content="Hidden Django internals", is_published=False)
    enrolled = UserFactory()
    outsider = UserFactory()
    EnrollmentFactory(user=enrolled, course=course)
    KnowledgeIndexingService.index_lesson(lesson=lesson)

    denied = RetrievalService.search(user=outsider, query="Hidden Django", collection_types=[KnowledgeCollectionType.LESSONS], include_private=True)
    allowed = RetrievalService.search(user=enrolled, query="Hidden Django", collection_types=[KnowledgeCollectionType.LESSONS], include_private=True)

    assert denied["results"] == []
    assert allowed["results"]


def test_retrieval_evaluation_pass_and_fail():
    user = UserFactory(role="platform_admin")
    document = KnowledgeIndexingService.index_document(
        collection_type=KnowledgeCollectionType.FAQS,
        source_type="faq",
        source_id="rag-quality",
        title="RAG quality",
        text="Retrieval evaluation checks citations and ranking confidence.",
    )
    dataset = RetrievalEvaluationDataset.objects.create(
        name="RAG smoke eval",
        feature=AIFeature.CHAT,
        cases=[
            {"query": "citations ranking confidence", "expected_document_id": str(document.id), "minimum_confidence": 1},
            {"query": "unrelated astronomy", "expected_source_type": "missing", "minimum_confidence": 95},
        ],
        minimum_pass_rate="0.50",
    )

    result = RetrievalEvaluationService.run_dataset(dataset=dataset, user=user)
    run = result["run"]

    assert run.status == "completed"
    assert run.passed_cases == 1
    assert run.failed_cases == 1


@override_settings(AI_KNOWLEDGE_AUTO_INDEX=True)
def test_career_track_and_portfolio_skill_indexing_paths():
    track = CareerTrack.objects.create(
        title="Backend Developer",
        slug="backend-developer",
        short_description="Learn backend APIs",
        description="A path for Django and API engineering.",
        target_job_titles=["Backend Developer"],
        skills_acquired=["Python", "Django"],
    )
    owner = UserFactory()
    portfolio = Portfolio.objects.create(user=owner, visibility=VisibilityChoice.PUBLIC, headline="Backend learner")
    PortfolioSkill.objects.create(portfolio=portfolio, name="Django", category="Framework")

    assert KnowledgeDocument.objects.filter(source_type="career_track", source_id=str(track.id), collection__collection_type=KnowledgeCollectionType.CAREER_TRACKS).exists()
    assert KnowledgeDocument.objects.filter(source_type="portfolio", source_id=str(portfolio.id), redacted_text__icontains="Django").exists()
