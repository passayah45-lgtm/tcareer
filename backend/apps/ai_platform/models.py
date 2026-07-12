from decimal import Decimal

from django.conf import settings
from django.db import models
from django.utils import timezone

from common.models import BaseModel


class AIProviderType(models.TextChoices):
    OPENAI = "openai", "OpenAI"
    ANTHROPIC = "anthropic", "Anthropic"
    GOOGLE_GEMINI = "google_gemini", "Google Gemini"
    AZURE_OPENAI = "azure_openai", "Azure OpenAI"
    LOCAL = "local", "Local Model"
    MOCK = "mock", "Mock Provider"


class AIRequestStatus(models.TextChoices):
    PENDING = "pending", "Pending"
    RUNNING = "running", "Running"
    COMPLETED = "completed", "Completed"
    FAILED = "failed", "Failed"
    CANCELLED = "cancelled", "Cancelled"
    BLOCKED = "blocked", "Blocked"


class AIReviewStatus(models.TextChoices):
    PENDING = "pending", "Pending"
    AUTO_REVIEWED = "auto_reviewed", "Auto Reviewed"
    MANUAL_REVIEW = "manual_review", "Manual Review"
    APPROVED = "approved", "Approved"
    REJECTED = "rejected", "Rejected"


class AIJobStatus(models.TextChoices):
    QUEUED = "queued", "Queued"
    RUNNING = "running", "Running"
    COMPLETED = "completed", "Completed"
    FAILED = "failed", "Failed"
    CANCELLED = "cancelled", "Cancelled"


class AIDatasetType(models.TextChoices):
    GOLDEN = "golden", "Golden"
    RESUME_INTELLIGENCE = "resume_intelligence", "Resume Intelligence"
    PORTFOLIO_INTELLIGENCE = "portfolio_intelligence", "Portfolio Intelligence"
    INTERVIEW_COACH = "interview_coach", "Interview Coach"
    CAREER_COACH = "career_coach", "Career Coach"
    LEARNING_TUTOR = "learning_tutor", "Learning Tutor"
    JOB_MATCHING = "job_matching", "Job Matching"
    SKILL_EXTRACTION = "skill_extraction", "Skill Extraction"
    PROMPT_SECURITY = "prompt_security", "Prompt Security"
    PRIVACY_DLP = "privacy_dlp", "Privacy DLP"
    FAIRNESS = "fairness", "Fairness"
    HALLUCINATION = "hallucination", "Hallucination"


class AIDatasetStatus(models.TextChoices):
    DRAFT = "draft", "Draft"
    ACTIVE = "active", "Active"
    INACTIVE = "inactive", "Inactive"
    ARCHIVED = "archived", "Archived"


class AIReleaseStatus(models.TextChoices):
    DRAFT = "draft", "Draft"
    PENDING_REVIEW = "pending_review", "Pending Review"
    APPROVED = "approved", "Approved"
    REJECTED = "rejected", "Rejected"
    PROMOTED = "promoted", "Promoted"
    ROLLED_BACK = "rolled_back", "Rolled Back"


class AIReleaseChangeType(models.TextChoices):
    PROMPT_TEMPLATE = "prompt_template", "Prompt Template"
    MODEL_CONFIGURATION = "model_configuration", "Model Configuration"
    PROVIDER = "provider", "Provider"
    FEATURE_FLAG = "feature_flag", "Feature Flag"


class AIRiskSeverity(models.TextChoices):
    LOW = "low", "Low"
    MEDIUM = "medium", "Medium"
    HIGH = "high", "High"
    CRITICAL = "critical", "Critical"


class AIFeature(models.TextChoices):
    CHAT = "chat", "Chat"
    RESUME_REVIEW = "resume_review", "Resume Review"
    PORTFOLIO_REVIEW = "portfolio_review", "Portfolio Review"
    CAREER_ADVICE = "career_advice", "Career Advice"
    LEARNING_RECOMMENDATIONS = "learning_recommendations", "Learning Recommendations"
    JOB_MATCHING = "job_matching", "Job Matching"
    COURSE_TUTOR = "course_tutor", "Course Tutor"
    INTERVIEW_COACH = "interview_coach", "Interview Coach"
    SKILL_GAP_ANALYSIS = "skill_gap_analysis", "Skill Gap Analysis"
    APPLICATION_REVIEW = "application_review", "Application Review"
    COVER_LETTER = "cover_letter", "Cover Letter"


class AIInterviewSessionType(models.TextChoices):
    BEHAVIORAL = "behavioral", "Behavioral"
    TECHNICAL = "technical", "Technical"
    SYSTEM_DESIGN = "system_design", "System Design"
    CODING = "coding", "Coding"
    HR = "hr", "HR"
    LEADERSHIP = "leadership", "Leadership"
    LANGUAGE_INTERVIEW = "language_interview", "Language Interview"
    CUSTOM = "custom", "Custom Interview"


class AIInterviewDifficulty(models.TextChoices):
    BEGINNER = "beginner", "Beginner"
    INTERMEDIATE = "intermediate", "Intermediate"
    ADVANCED = "advanced", "Advanced"
    EXPERT = "expert", "Expert"


class AICareerGoalStatus(models.TextChoices):
    ACTIVE = "active", "Active"
    PAUSED = "paused", "Paused"
    COMPLETED = "completed", "Completed"
    ARCHIVED = "archived", "Archived"


class AIRoadmapHorizon(models.TextChoices):
    THREE_MONTHS = "3_months", "3 Months"
    SIX_MONTHS = "6_months", "6 Months"
    TWELVE_MONTHS = "12_months", "12 Months"
    TWENTY_FOUR_MONTHS = "24_months", "24 Months"


class AIInterviewSessionStatus(models.TextChoices):
    ACTIVE = "active", "Active"
    PAUSED = "paused", "Paused"
    COMPLETED = "completed", "Completed"
    CANCELLED = "cancelled", "Cancelled"


class AIProvider(BaseModel):
    name = models.CharField(max_length=100, unique=True)
    provider_type = models.CharField(max_length=30, choices=AIProviderType.choices, db_index=True)
    is_active = models.BooleanField(default=True, db_index=True)
    is_default = models.BooleanField(default=False, db_index=True)
    priority = models.PositiveSmallIntegerField(default=100)
    timeout_seconds = models.PositiveSmallIntegerField(default=30)
    max_retries = models.PositiveSmallIntegerField(default=1)
    configuration = models.JSONField(default=dict, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    health_status = models.CharField(max_length=30, default="unknown", db_index=True)
    last_health_check_at = models.DateTimeField(null=True, blank=True)
    last_error = models.TextField(blank=True, default="")

    class Meta:
        db_table = "ai_providers"
        ordering = ["priority", "name"]

    def __str__(self):
        return self.name


class AIModelConfiguration(BaseModel):
    provider = models.ForeignKey(AIProvider, on_delete=models.CASCADE, related_name="model_configurations")
    model_name = models.CharField(max_length=120)
    display_name = models.CharField(max_length=160, blank=True, default="")
    is_active = models.BooleanField(default=True, db_index=True)
    is_default = models.BooleanField(default=False, db_index=True)
    max_tokens = models.PositiveIntegerField(default=1000)
    temperature = models.DecimalField(max_digits=4, decimal_places=2, default=Decimal("0.30"))
    input_token_cost = models.DecimalField(max_digits=12, decimal_places=8, default=Decimal("0.00000000"))
    output_token_cost = models.DecimalField(max_digits=12, decimal_places=8, default=Decimal("0.00000000"))
    timeout_seconds = models.PositiveSmallIntegerField(default=30)
    max_retries = models.PositiveSmallIntegerField(default=1)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = "ai_model_configurations"
        unique_together = [("provider", "model_name")]
        indexes = [models.Index(fields=["provider", "is_default"], name="ai_model_provider_default_idx")]

    def __str__(self):
        return f"{self.provider.name}:{self.model_name}"


class AIPromptTemplate(BaseModel):
    key = models.CharField(max_length=100, db_index=True)
    name = models.CharField(max_length=160)
    feature = models.CharField(max_length=50, choices=AIFeature.choices, db_index=True)
    version = models.PositiveIntegerField(default=1)
    locale = models.CharField(max_length=20, default="en", db_index=True)
    variant = models.CharField(max_length=50, blank=True, default="")
    system_prompt = models.TextField(blank=True, default="")
    user_prompt = models.TextField()
    variables = models.JSONField(default=list, blank=True)
    is_active = models.BooleanField(default=True, db_index=True)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = "ai_prompt_templates"
        unique_together = [("key", "version", "locale", "variant")]
        indexes = [models.Index(fields=["key", "is_active", "locale"], name="ai_prompt_key_locale_idx")]

    def __str__(self):
        return f"{self.key} v{self.version} ({self.locale})"


class AIConversation(BaseModel):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="ai_conversations")
    organization = models.ForeignKey("organizations.Organization", on_delete=models.SET_NULL, null=True, blank=True, related_name="ai_conversations")
    title = models.CharField(max_length=200, blank=True, default="")
    feature = models.CharField(max_length=50, choices=AIFeature.choices, default=AIFeature.CHAT, db_index=True)
    locale = models.CharField(max_length=20, default="en")
    is_archived = models.BooleanField(default=False, db_index=True)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = "ai_conversations"
        indexes = [
            models.Index(fields=["user", "feature", "created_at"], name="ai_conv_user_feature_idx"),
            models.Index(fields=["organization", "feature"], name="ai_conv_org_feature_idx"),
        ]

    def __str__(self):
        return self.title or f"{self.feature} conversation"


class AIRequest(BaseModel):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="ai_requests")
    organization = models.ForeignKey("organizations.Organization", on_delete=models.SET_NULL, null=True, blank=True, related_name="ai_requests")
    course = models.ForeignKey("courses.Course", on_delete=models.SET_NULL, null=True, blank=True, related_name="ai_requests")
    conversation = models.ForeignKey(AIConversation, on_delete=models.SET_NULL, null=True, blank=True, related_name="requests")
    prompt_template = models.ForeignKey(AIPromptTemplate, on_delete=models.SET_NULL, null=True, blank=True, related_name="requests")
    provider = models.ForeignKey(AIProvider, on_delete=models.SET_NULL, null=True, blank=True, related_name="requests")
    model_configuration = models.ForeignKey(AIModelConfiguration, on_delete=models.SET_NULL, null=True, blank=True, related_name="requests")
    feature = models.CharField(max_length=50, choices=AIFeature.choices, db_index=True)
    operation = models.CharField(max_length=50, default="generate_text", db_index=True)
    status = models.CharField(max_length=20, choices=AIRequestStatus.choices, default=AIRequestStatus.PENDING, db_index=True)
    input_text = models.TextField(blank=True, default="")
    redacted_input = models.TextField(blank=True, default="")
    rendered_prompt = models.JSONField(default=dict, blank=True)
    safety_flags = models.JSONField(default=list, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    latency_ms = models.PositiveIntegerField(default=0)
    error_message = models.TextField(blank=True, default="")
    cancelled_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "ai_requests"
        indexes = [
            models.Index(fields=["user", "feature", "created_at"], name="ai_req_user_feature_idx"),
            models.Index(fields=["organization", "feature"], name="ai_req_org_feature_idx"),
            models.Index(fields=["provider", "status"], name="ai_req_provider_status_idx"),
        ]


class AIResponse(BaseModel):
    request = models.OneToOneField(AIRequest, on_delete=models.CASCADE, related_name="response")
    output_text = models.TextField(blank=True, default="")
    raw_response = models.JSONField(default=dict, blank=True)
    finish_reason = models.CharField(max_length=80, blank=True, default="")
    safety_flags = models.JSONField(default=list, blank=True)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = "ai_responses"


class AITokenUsage(BaseModel):
    request = models.OneToOneField(AIRequest, on_delete=models.CASCADE, related_name="token_usage")
    provider = models.ForeignKey(AIProvider, on_delete=models.SET_NULL, null=True, blank=True, related_name="token_usages")
    model_name = models.CharField(max_length=120, blank=True, default="")
    input_tokens = models.PositiveIntegerField(default=0)
    output_tokens = models.PositiveIntegerField(default=0)
    total_tokens = models.PositiveIntegerField(default=0)
    estimated_cost = models.DecimalField(max_digits=12, decimal_places=6, default=Decimal("0.000000"))
    provider_reported_input_tokens = models.PositiveIntegerField(default=0)
    provider_reported_output_tokens = models.PositiveIntegerField(default=0)
    actual_cost = models.DecimalField(max_digits=12, decimal_places=6, null=True, blank=True)
    cost_variance = models.DecimalField(max_digits=12, decimal_places=6, default=Decimal("0.000000"))

    class Meta:
        db_table = "ai_token_usage"
        indexes = [models.Index(fields=["provider", "model_name"], name="ai_token_provider_model_idx")]


class AIUsage(BaseModel):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True, related_name="ai_usage_records")
    organization = models.ForeignKey("organizations.Organization", on_delete=models.CASCADE, null=True, blank=True, related_name="ai_usage_records")
    course = models.ForeignKey("courses.Course", on_delete=models.SET_NULL, null=True, blank=True, related_name="ai_usage_records")
    feature = models.CharField(max_length=50, choices=AIFeature.choices, db_index=True)
    provider = models.ForeignKey(AIProvider, on_delete=models.SET_NULL, null=True, blank=True, related_name="usage_records")
    model_name = models.CharField(max_length=120, blank=True, default="")
    period_date = models.DateField(db_index=True)
    request_count = models.PositiveIntegerField(default=0)
    success_count = models.PositiveIntegerField(default=0)
    failure_count = models.PositiveIntegerField(default=0)
    input_tokens = models.PositiveIntegerField(default=0)
    output_tokens = models.PositiveIntegerField(default=0)
    total_tokens = models.PositiveIntegerField(default=0)
    estimated_cost = models.DecimalField(max_digits=12, decimal_places=6, default=Decimal("0.000000"))
    latency_ms_total = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = "ai_usage"
        unique_together = [("user", "organization", "course", "feature", "provider", "model_name", "period_date")]
        indexes = [
            models.Index(fields=["organization", "feature", "period_date"], name="ai_usage_org_feature_date_idx"),
            models.Index(fields=["user", "feature", "period_date"], name="ai_usage_user_feature_date_idx"),
        ]


class AIBudgetPolicy(BaseModel):
    scope = models.CharField(max_length=30, choices=[("global", "Global"), ("organization", "Organization"), ("user", "User"), ("feature", "Feature")], db_index=True)
    organization = models.ForeignKey("organizations.Organization", on_delete=models.CASCADE, null=True, blank=True, related_name="ai_budget_policies")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True, related_name="ai_budget_policies")
    feature = models.CharField(max_length=50, choices=AIFeature.choices, blank=True, default="", db_index=True)
    daily_request_limit = models.PositiveIntegerField(null=True, blank=True)
    monthly_request_limit = models.PositiveIntegerField(null=True, blank=True)
    daily_token_limit = models.PositiveIntegerField(null=True, blank=True)
    monthly_token_limit = models.PositiveIntegerField(null=True, blank=True)
    monthly_cost_limit = models.DecimalField(max_digits=12, decimal_places=4, null=True, blank=True)
    alert_threshold_percent = models.PositiveSmallIntegerField(default=80)
    last_alert_sent_at = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True, db_index=True)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = "ai_budget_policies"
        indexes = [models.Index(fields=["scope", "feature", "is_active"], name="ai_budget_scope_feature_idx")]


class AIJob(BaseModel):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="ai_jobs")
    organization = models.ForeignKey("organizations.Organization", on_delete=models.SET_NULL, null=True, blank=True, related_name="ai_jobs")
    feature = models.CharField(max_length=50, choices=AIFeature.choices, db_index=True)
    status = models.CharField(max_length=20, choices=AIJobStatus.choices, default=AIJobStatus.QUEUED, db_index=True)
    progress_percentage = models.PositiveSmallIntegerField(default=0)
    retry_count = models.PositiveIntegerField(default=0)
    input_payload = models.JSONField(default=dict, blank=True)
    failure_reason = models.TextField(blank=True, default="")
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = "ai_jobs"
        indexes = [models.Index(fields=["organization", "feature", "status"], name="ai_job_org_feature_status_idx")]


class AIResult(BaseModel):
    job = models.OneToOneField(AIJob, on_delete=models.CASCADE, related_name="result", null=True, blank=True)
    request = models.ForeignKey(AIRequest, on_delete=models.SET_NULL, null=True, blank=True, related_name="results")
    result_type = models.CharField(max_length=80, default="text")
    content = models.JSONField(default=dict, blank=True)
    summary = models.TextField(blank=True, default="")
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = "ai_results"


class AIModerationResult(BaseModel):
    request = models.ForeignKey(AIRequest, on_delete=models.CASCADE, null=True, blank=True, related_name="moderation_results")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="ai_moderation_results")
    organization = models.ForeignKey("organizations.Organization", on_delete=models.SET_NULL, null=True, blank=True, related_name="ai_moderation_results")
    stage = models.CharField(max_length=20, choices=[("input", "Input"), ("output", "Output")], db_index=True)
    is_allowed = models.BooleanField(default=True, db_index=True)
    severity = models.CharField(max_length=20, default="info", db_index=True)
    categories = models.JSONField(default=list, blank=True)
    pii_findings = models.JSONField(default=list, blank=True)
    injection_findings = models.JSONField(default=list, blank=True)
    provider = models.ForeignKey(AIProvider, on_delete=models.SET_NULL, null=True, blank=True, related_name="moderation_results")
    raw_result = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = "ai_moderation_results"
        indexes = [models.Index(fields=["organization", "stage", "is_allowed"], name="ai_mod_org_stage_allowed_idx")]


class AIFeatureFlag(BaseModel):
    feature = models.CharField(max_length=50, choices=AIFeature.choices, db_index=True)
    is_enabled = models.BooleanField(default=True, db_index=True)
    organization = models.ForeignKey("organizations.Organization", on_delete=models.CASCADE, null=True, blank=True, related_name="ai_feature_flags")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True, related_name="ai_feature_flags")
    reason = models.CharField(max_length=255, blank=True, default="")
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = "ai_feature_flags"
        unique_together = [("feature", "organization", "user")]
        indexes = [models.Index(fields=["feature", "is_enabled"], name="ai_flag_feature_enabled_idx")]


class VectorCollection(BaseModel):
    name = models.CharField(max_length=120, unique=True)
    organization = models.ForeignKey("organizations.Organization", on_delete=models.CASCADE, null=True, blank=True, related_name="vector_collections")
    embedding_model = models.CharField(max_length=120, default="mock-embedding")
    dimensions = models.PositiveIntegerField(default=16)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = "ai_vector_collections"


class VectorDocument(BaseModel):
    collection = models.ForeignKey(VectorCollection, on_delete=models.CASCADE, related_name="documents")
    document_type = models.CharField(max_length=40, db_index=True)
    object_id = models.CharField(max_length=100, db_index=True)
    title = models.CharField(max_length=255, blank=True, default="")
    content = models.TextField()
    redacted_content = models.TextField(blank=True, default="")
    embedding = models.JSONField(default=list, blank=True)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = "ai_vector_documents"
        unique_together = [("collection", "document_type", "object_id")]
        indexes = [models.Index(fields=["collection", "document_type"], name="ai_vec_collection_type_idx")]


class KnowledgeCollectionType(models.TextChoices):
    COURSES = "courses", "Courses"
    LESSONS = "lessons", "Lessons"
    QUIZZES = "quizzes", "Quizzes"
    CAREER_TRACKS = "career_tracks", "Career Tracks"
    RESUMES = "resumes", "Resumes"
    PORTFOLIOS = "portfolios", "Portfolios"
    JOBS = "jobs", "Jobs"
    SKILLS = "skills", "Skills"
    CERTIFICATES = "certificates", "Certificates"
    FAQS = "faqs", "FAQs"
    POLICIES = "policies", "Policies"
    ORGANIZATION_DOCUMENTS = "organization_documents", "Organization Documents"
    FUTURE_DOCUMENTS = "future_documents", "Future Documents"


class KnowledgeIndexStatus(models.TextChoices):
    QUEUED = "queued", "Queued"
    INDEXING = "indexing", "Indexing"
    INDEXED = "indexed", "Indexed"
    FAILED = "failed", "Failed"
    STALE = "stale", "Stale"


class KnowledgeVisibility(models.TextChoices):
    PUBLIC = "public", "Public"
    ORGANIZATION = "organization", "Organization"
    PRIVATE = "private", "Private"


class KnowledgeCollection(BaseModel):
    name = models.CharField(max_length=160)
    collection_type = models.CharField(max_length=40, choices=KnowledgeCollectionType.choices, db_index=True)
    organization = models.ForeignKey("organizations.Organization", on_delete=models.CASCADE, null=True, blank=True, related_name="knowledge_collections")
    embedding_version = models.CharField(max_length=120, default="deterministic-v1", db_index=True)
    vector_backend = models.CharField(max_length=40, default="local", db_index=True)
    vector_dimensions = models.PositiveIntegerField(default=16)
    health_status = models.CharField(max_length=30, default="unknown", db_index=True)
    last_health_check_at = models.DateTimeField(null=True, blank=True)
    last_health_error = models.TextField(blank=True, default="")
    is_active = models.BooleanField(default=True, db_index=True)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = "ai_knowledge_collections"
        unique_together = [("collection_type", "organization", "embedding_version")]
        indexes = [
            models.Index(fields=["collection_type", "is_active"], name="ai_know_collection_active_idx"),
            models.Index(fields=["organization", "collection_type"], name="ai_know_collection_org_idx"),
        ]

    def __str__(self):
        return f"{self.collection_type}:{self.name}"


class KnowledgeDocument(BaseModel):
    collection = models.ForeignKey(KnowledgeCollection, on_delete=models.CASCADE, related_name="documents")
    organization = models.ForeignKey("organizations.Organization", on_delete=models.SET_NULL, null=True, blank=True, related_name="knowledge_documents")
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="knowledge_documents")
    source_type = models.CharField(max_length=60, db_index=True)
    source_id = models.CharField(max_length=120, db_index=True)
    title = models.CharField(max_length=255, blank=True, default="")
    text = models.TextField()
    redacted_text = models.TextField(blank=True, default="")
    version = models.CharField(max_length=80, default="1", db_index=True)
    checksum = models.CharField(max_length=64, db_index=True)
    embedding_version = models.CharField(max_length=120, default="deterministic-v1", db_index=True)
    index_status = models.CharField(max_length=20, choices=KnowledgeIndexStatus.choices, default=KnowledgeIndexStatus.QUEUED, db_index=True)
    visibility = models.CharField(max_length=20, choices=KnowledgeVisibility.choices, default=KnowledgeVisibility.PUBLIC, db_index=True)
    last_indexed_at = models.DateTimeField(null=True, blank=True)
    source_updated_at = models.DateTimeField(null=True, blank=True)
    last_successful_reindex_at = models.DateTimeField(null=True, blank=True)
    freshness_score = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal("0.00"))
    stale_reason = models.CharField(max_length=120, blank=True, default="")
    error_message = models.TextField(blank=True, default="")
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = "ai_knowledge_documents"
        unique_together = [("collection", "source_type", "source_id")]
        indexes = [
            models.Index(fields=["collection", "index_status"], name="ai_know_doc_status_idx"),
            models.Index(fields=["source_type", "source_id"], name="ai_know_doc_source_idx"),
            models.Index(fields=["organization", "visibility"], name="ai_know_doc_org_vis_idx"),
            models.Index(fields=["embedding_version", "index_status"], name="ai_know_doc_embed_idx"),
        ]

    def __str__(self):
        return self.title or f"{self.source_type}:{self.source_id}"


class KnowledgeChunk(BaseModel):
    document = models.ForeignKey(KnowledgeDocument, on_delete=models.CASCADE, related_name="chunks")
    chunk_index = models.PositiveIntegerField()
    text = models.TextField()
    embedding = models.JSONField(default=list, blank=True)
    token_count = models.PositiveIntegerField(default=0)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = "ai_knowledge_chunks"
        unique_together = [("document", "chunk_index")]
        indexes = [
            models.Index(fields=["document", "chunk_index"], name="ai_know_chunk_order_idx"),
        ]


class RetrievalEvent(BaseModel):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="ai_retrieval_events")
    organization = models.ForeignKey("organizations.Organization", on_delete=models.SET_NULL, null=True, blank=True, related_name="ai_retrieval_events")
    feature = models.CharField(max_length=50, choices=AIFeature.choices, default=AIFeature.CHAT, db_index=True)
    query = models.TextField()
    search_type = models.CharField(max_length=30, default="hybrid", db_index=True)
    latency_ms = models.PositiveIntegerField(default=0)
    result_count = models.PositiveIntegerField(default=0)
    source_count = models.PositiveIntegerField(default=0)
    chunk_count = models.PositiveIntegerField(default=0)
    context_size = models.PositiveIntegerField(default=0)
    timed_out = models.BooleanField(default=False, db_index=True)
    confidence = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal("0.00"))
    cache_hit = models.BooleanField(default=False, db_index=True)
    sources = models.JSONField(default=list, blank=True)
    missing_knowledge = models.JSONField(default=list, blank=True)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = "ai_retrieval_events"
        indexes = [
            models.Index(fields=["feature", "created_at"], name="ai_retrieval_feature_date_idx"),
            models.Index(fields=["organization", "feature"], name="ai_retrieval_org_feature_idx"),
        ]


class RetrievalEvaluationDataset(BaseModel):
    name = models.CharField(max_length=160, unique=True)
    feature = models.CharField(max_length=50, choices=AIFeature.choices, default=AIFeature.CHAT, db_index=True)
    description = models.TextField(blank=True, default="")
    cases = models.JSONField(default=list, blank=True)
    minimum_pass_rate = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal("0.80"))
    is_active = models.BooleanField(default=True, db_index=True)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = "ai_retrieval_evaluation_datasets"


class RetrievalEvaluationRun(BaseModel):
    dataset = models.ForeignKey(RetrievalEvaluationDataset, on_delete=models.CASCADE, related_name="runs")
    run_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="ai_retrieval_evaluation_runs")
    status = models.CharField(max_length=20, choices=AIJobStatus.choices, default=AIJobStatus.QUEUED, db_index=True)
    total_cases = models.PositiveIntegerField(default=0)
    passed_cases = models.PositiveIntegerField(default=0)
    failed_cases = models.PositiveIntegerField(default=0)
    pass_rate = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal("0.00"))
    average_confidence = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal("0.00"))
    report = models.JSONField(default=dict, blank=True)
    failure_reason = models.TextField(blank=True, default="")

    class Meta:
        db_table = "ai_retrieval_evaluation_runs"


class RetrievalEvaluationResult(BaseModel):
    run = models.ForeignKey(RetrievalEvaluationRun, on_delete=models.CASCADE, related_name="results")
    query = models.TextField()
    expected_document_id = models.CharField(max_length=120, blank=True, default="")
    expected_chunk_id = models.CharField(max_length=120, blank=True, default="")
    expected_source_type = models.CharField(max_length=60, blank=True, default="")
    expected_citation = models.JSONField(default=dict, blank=True)
    minimum_confidence = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal("0.00"))
    ranking_position = models.PositiveIntegerField(null=True, blank=True)
    passed = models.BooleanField(default=False, db_index=True)
    confidence = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal("0.00"))
    retrieved_citations = models.JSONField(default=list, blank=True)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = "ai_retrieval_evaluation_results"
        indexes = [models.Index(fields=["run", "passed"], name="ai_retrieval_eval_pass_idx")]


class AIEvaluationDataset(BaseModel):
    name = models.CharField(max_length=160, unique=True)
    feature = models.CharField(max_length=50, choices=AIFeature.choices, db_index=True)
    dataset_type = models.CharField(max_length=50, choices=AIDatasetType.choices, default=AIDatasetType.RESUME_INTELLIGENCE, db_index=True)
    description = models.TextField(blank=True, default="")
    examples = models.JSONField(default=list, blank=True)
    expected_schema = models.JSONField(default=dict, blank=True)
    expected_score_min = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    expected_score_max = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    rubric = models.JSONField(default=dict, blank=True)
    risk_tags = models.JSONField(default=list, blank=True)
    locale = models.CharField(max_length=20, default="en", db_index=True)
    difficulty = models.CharField(max_length=30, blank=True, default="", db_index=True)
    status = models.CharField(max_length=20, choices=AIDatasetStatus.choices, default=AIDatasetStatus.ACTIVE, db_index=True)
    reviewer_notes = models.TextField(blank=True, default="")
    is_golden = models.BooleanField(default=True, db_index=True)
    version = models.PositiveIntegerField(default=1)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = "ai_evaluation_datasets"


class AIEvaluationRun(BaseModel):
    dataset = models.ForeignKey(AIEvaluationDataset, on_delete=models.CASCADE, related_name="runs")
    provider = models.ForeignKey(AIProvider, on_delete=models.SET_NULL, null=True, blank=True, related_name="evaluation_runs")
    model_configuration = models.ForeignKey(AIModelConfiguration, on_delete=models.SET_NULL, null=True, blank=True, related_name="evaluation_runs")
    prompt_template = models.ForeignKey(AIPromptTemplate, on_delete=models.SET_NULL, null=True, blank=True, related_name="evaluation_runs")
    status = models.CharField(max_length=20, choices=AIJobStatus.choices, default=AIJobStatus.QUEUED, db_index=True)
    average_score = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    confidence_score = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    average_latency_ms = models.PositiveIntegerField(default=0)
    estimated_cost = models.DecimalField(max_digits=12, decimal_places=6, default=Decimal("0.000000"))
    report = models.JSONField(default=dict, blank=True)
    prompt_version = models.CharField(max_length=80, blank=True, default="")
    notes = models.TextField(blank=True, default="")
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    duration_seconds = models.PositiveIntegerField(default=0)
    failure_reason = models.TextField(blank=True, default="")
    aggregate_results = models.JSONField(default=dict, blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="ai_evaluation_runs")

    class Meta:
        db_table = "ai_evaluation_runs"


class AIEvaluationResult(BaseModel):
    run = models.ForeignKey(AIEvaluationRun, on_delete=models.CASCADE, related_name="results")
    input_text = models.TextField()
    expected_output = models.TextField(blank=True, default="")
    actual_output = models.TextField(blank=True, default="")
    score = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    confidence_score = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    score_breakdown = models.JSONField(default=dict, blank=True)
    latency_ms = models.PositiveIntegerField(default=0)
    estimated_cost = models.DecimalField(max_digits=12, decimal_places=6, default=Decimal("0.000000"))
    hallucination_notes = models.TextField(blank=True, default="")
    bias_flags = models.JSONField(default=list, blank=True)
    privacy_flags = models.JSONField(default=list, blank=True)
    prompt_security_flags = models.JSONField(default=list, blank=True)
    manual_score = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    review_status = models.CharField(max_length=30, choices=AIReviewStatus.choices, default=AIReviewStatus.AUTO_REVIEWED, db_index=True)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = "ai_evaluation_results"


class AIEvaluationReview(BaseModel):
    result = models.ForeignKey(AIEvaluationResult, on_delete=models.CASCADE, related_name="reviews")
    assigned_to = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="assigned_ai_evaluation_reviews")
    reviewed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="completed_ai_evaluation_reviews")
    status = models.CharField(max_length=30, choices=AIReviewStatus.choices, default=AIReviewStatus.PENDING, db_index=True)
    manual_score = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    hallucination_flag = models.BooleanField(default=False, db_index=True)
    bias_flag = models.BooleanField(default=False, db_index=True)
    unsafe_flag = models.BooleanField(default=False, db_index=True)
    request_prompt_revision = models.BooleanField(default=False, db_index=True)
    notes = models.TextField(blank=True, default="")
    assigned_at = models.DateTimeField(null=True, blank=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "ai_evaluation_reviews"
        indexes = [models.Index(fields=["status", "assigned_to"], name="ai_eval_review_queue_idx")]


class AIRedTeamSuite(BaseModel):
    name = models.CharField(max_length=160, unique=True)
    suite_type = models.CharField(max_length=50, choices=[
        ("prompt_injection", "Prompt Injection"),
        ("jailbreak", "Jailbreak"),
        ("malicious_resume", "Malicious Resume"),
        ("malicious_portfolio", "Malicious Portfolio"),
        ("malicious_interview_answer", "Malicious Interview Answer"),
        ("unsafe_url", "Unsafe URL"),
        ("hidden_instruction", "Hidden Instruction"),
        ("rag_poisoning", "RAG Poisoning"),
        ("pii_leakage", "PII Leakage"),
        ("bias_trigger", "Bias Trigger"),
        ("hallucination_trap", "Hallucination Trap"),
    ], db_index=True)
    feature = models.CharField(max_length=50, choices=AIFeature.choices, default=AIFeature.CHAT, db_index=True)
    severity = models.CharField(max_length=20, choices=AIRiskSeverity.choices, default=AIRiskSeverity.MEDIUM, db_index=True)
    expected_safe_behavior = models.TextField(blank=True, default="")
    cases = models.JSONField(default=list, blank=True)
    is_active = models.BooleanField(default=True, db_index=True)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = "ai_red_team_suites"


class AIRedTeamResult(BaseModel):
    suite = models.ForeignKey(AIRedTeamSuite, on_delete=models.CASCADE, related_name="results")
    run = models.ForeignKey(AIEvaluationRun, on_delete=models.SET_NULL, null=True, blank=True, related_name="red_team_results")
    case_name = models.CharField(max_length=160, blank=True, default="")
    input_text = models.TextField()
    output_text = models.TextField(blank=True, default="")
    risk_severity = models.CharField(max_length=20, choices=AIRiskSeverity.choices, default=AIRiskSeverity.LOW, db_index=True)
    risk_flags = models.JSONField(default=list, blank=True)
    passed = models.BooleanField(default=True, db_index=True)
    expected_safe_behavior = models.TextField(blank=True, default="")
    mitigation_notes = models.TextField(blank=True, default="")
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = "ai_red_team_results"
        indexes = [models.Index(fields=["suite", "risk_severity", "passed"], name="ai_red_team_suite_risk_idx")]


class AIReleaseGate(BaseModel):
    change_type = models.CharField(max_length=40, choices=AIReleaseChangeType.choices, db_index=True)
    target_id = models.CharField(max_length=100, db_index=True)
    feature = models.CharField(max_length=50, choices=AIFeature.choices, db_index=True)
    status = models.CharField(max_length=30, choices=AIReleaseStatus.choices, default=AIReleaseStatus.DRAFT, db_index=True)
    previous_version = models.JSONField(default=dict, blank=True)
    new_version = models.JSONField(default=dict, blank=True)
    thresholds = models.JSONField(default=dict, blank=True)
    gate_results = models.JSONField(default=dict, blank=True)
    evaluation_run = models.ForeignKey(AIEvaluationRun, on_delete=models.SET_NULL, null=True, blank=True, related_name="release_gates")
    requested_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="requested_ai_release_gates")
    reviewed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="reviewed_ai_release_gates")
    promoted_at = models.DateTimeField(null=True, blank=True)
    rolled_back_at = models.DateTimeField(null=True, blank=True)
    rollback_reason = models.TextField(blank=True, default="")
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = "ai_release_gates"
        indexes = [models.Index(fields=["feature", "status", "change_type"], name="ai_release_feature_status_idx")]


class AIChangeHistory(BaseModel):
    gate = models.ForeignKey(AIReleaseGate, on_delete=models.CASCADE, related_name="change_history")
    changed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="ai_change_history")
    change_type = models.CharField(max_length=40, choices=AIReleaseChangeType.choices, db_index=True)
    target_id = models.CharField(max_length=100, db_index=True)
    previous_version = models.JSONField(default=dict, blank=True)
    new_version = models.JSONField(default=dict, blank=True)
    approval_state = models.CharField(max_length=30, choices=AIReleaseStatus.choices, default=AIReleaseStatus.DRAFT, db_index=True)
    evaluation_run = models.ForeignKey(AIEvaluationRun, on_delete=models.SET_NULL, null=True, blank=True, related_name="change_history")
    promoted_at = models.DateTimeField(null=True, blank=True)
    rolled_back_at = models.DateTimeField(null=True, blank=True)
    rollback_reason = models.TextField(blank=True, default="")
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = "ai_change_history"
        indexes = [models.Index(fields=["change_type", "approval_state", "created_at"], name="ai_change_type_state_idx")]


class AIComparisonReport(BaseModel):
    comparison_type = models.CharField(max_length=40, choices=[
        ("provider", "Provider"),
        ("model", "Model"),
        ("prompt_version", "Prompt Version"),
        ("feature_version", "Feature Version"),
    ], db_index=True)
    feature = models.CharField(max_length=50, choices=AIFeature.choices, db_index=True)
    left_label = models.CharField(max_length=160)
    right_label = models.CharField(max_length=160)
    metrics = models.JSONField(default=dict, blank=True)
    winner = models.CharField(max_length=160, blank=True, default="")
    generated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="ai_comparison_reports")
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = "ai_comparison_reports"
        indexes = [models.Index(fields=["comparison_type", "feature", "created_at"], name="ai_compare_type_feature_idx")]


class AIAuditExport(BaseModel):
    class Status(models.TextChoices):
        QUEUED = "queued", "Queued"
        PROCESSING = "processing", "Processing"
        COMPLETED = "completed", "Completed"
        FAILED = "failed", "Failed"

    export_type = models.CharField(max_length=50, choices=[
        ("evaluation_runs", "Evaluation Runs"),
        ("safety_events", "Safety Events"),
        ("privacy_events", "Privacy Events"),
        ("bias_events", "Bias Events"),
        ("feedback", "Feedback"),
        ("provider_usage", "Provider Usage"),
        ("prompt_versions", "Prompt Versions"),
        ("model_comparisons", "Model Comparisons"),
    ], db_index=True)
    file_format = models.CharField(max_length=10, choices=[("csv", "CSV"), ("xlsx", "XLSX")], default="csv")
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.QUEUED, db_index=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="ai_audit_exports")
    file = models.FileField(upload_to="ai-audit-exports/", null=True, blank=True)
    file_name = models.CharField(max_length=255, blank=True, default="")
    row_count = models.PositiveIntegerField(default=0)
    filters = models.JSONField(default=dict, blank=True)
    failure_reason = models.TextField(blank=True, default="")
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "ai_audit_exports"
        indexes = [models.Index(fields=["export_type", "status", "created_at"], name="ai_export_type_status_idx")]


class AICalibrationReport(BaseModel):
    request = models.ForeignKey(AIRequest, on_delete=models.CASCADE, null=True, blank=True, related_name="calibration_reports")
    feature = models.CharField(max_length=50, choices=AIFeature.choices, db_index=True)
    score_name = models.CharField(max_length=80, db_index=True)
    score = models.DecimalField(max_digits=6, decimal_places=2, default=Decimal("0.00"))
    confidence_score = models.DecimalField(max_digits=6, decimal_places=2, default=Decimal("0.00"))
    confidence_level = models.CharField(max_length=20, default="medium", db_index=True)
    score_breakdown = models.JSONField(default=dict, blank=True)
    weighting = models.JSONField(default=dict, blank=True)
    evidence = models.JSONField(default=list, blank=True)
    reasoning_summary = models.TextField(blank=True, default="")
    uncertainty = models.JSONField(default=dict, blank=True)
    missing_information = models.JSONField(default=list, blank=True)
    limitations = models.JSONField(default=list, blank=True)
    recommended_next_action = models.TextField(blank=True, default="")

    class Meta:
        db_table = "ai_calibration_reports"
        indexes = [models.Index(fields=["feature", "score_name", "created_at"], name="ai_cal_feature_score_idx")]


class AIFairnessReport(BaseModel):
    request = models.ForeignKey(AIRequest, on_delete=models.CASCADE, null=True, blank=True, related_name="fairness_reports")
    organization = models.ForeignKey("organizations.Organization", on_delete=models.SET_NULL, null=True, blank=True, related_name="ai_fairness_reports")
    feature = models.CharField(max_length=50, choices=AIFeature.choices, db_index=True)
    fairness_score = models.DecimalField(max_digits=6, decimal_places=2, default=Decimal("100.00"))
    bias_flags = models.JSONField(default=list, blank=True)
    manual_review_required = models.BooleanField(default=False, db_index=True)
    reviewed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="ai_fairness_reviews")
    reviewed_at = models.DateTimeField(null=True, blank=True)
    report = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = "ai_fairness_reports"
        indexes = [models.Index(fields=["organization", "feature", "created_at"], name="ai_fair_org_feature_idx")]


class AIPrivacyReport(BaseModel):
    request = models.ForeignKey(AIRequest, on_delete=models.CASCADE, null=True, blank=True, related_name="privacy_reports")
    organization = models.ForeignKey("organizations.Organization", on_delete=models.SET_NULL, null=True, blank=True, related_name="ai_privacy_reports")
    feature = models.CharField(max_length=50, choices=AIFeature.choices, db_index=True)
    findings = models.JSONField(default=list, blank=True)
    redaction_count = models.PositiveIntegerField(default=0)
    policy = models.JSONField(default=dict, blank=True)
    severity = models.CharField(max_length=20, default="info", db_index=True)
    report = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = "ai_privacy_reports"
        indexes = [models.Index(fields=["organization", "feature", "severity"], name="ai_priv_org_feature_idx")]


class AIFeedback(BaseModel):
    request = models.ForeignKey(AIRequest, on_delete=models.SET_NULL, null=True, blank=True, related_name="feedback_items")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="ai_feedback_items")
    organization = models.ForeignKey("organizations.Organization", on_delete=models.SET_NULL, null=True, blank=True, related_name="ai_feedback_items")
    feature = models.CharField(max_length=50, choices=AIFeature.choices, db_index=True)
    rating = models.CharField(max_length=30, choices=[
        ("helpful", "Helpful"),
        ("not_helpful", "Not Helpful"),
        ("incorrect", "Incorrect"),
        ("hallucination", "Hallucination"),
        ("unsafe", "Unsafe"),
        ("biased", "Biased"),
        ("incomplete", "Incomplete"),
    ], db_index=True)
    comment = models.TextField(blank=True, default="")
    provider = models.ForeignKey(AIProvider, on_delete=models.SET_NULL, null=True, blank=True, related_name="feedback_items")
    model_name = models.CharField(max_length=120, blank=True, default="")
    prompt_version = models.CharField(max_length=80, blank=True, default="")
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = "ai_feedback"
        indexes = [models.Index(fields=["feature", "rating", "created_at"], name="ai_feedback_feature_rating_idx")]


class AIResponseCache(BaseModel):
    cache_key = models.CharField(max_length=128, unique=True, db_index=True)
    feature = models.CharField(max_length=50, choices=AIFeature.choices, db_index=True)
    organization = models.ForeignKey("organizations.Organization", on_delete=models.CASCADE, null=True, blank=True, related_name="ai_response_cache")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True, related_name="ai_response_cache")
    redacted_input_hash = models.CharField(max_length=128, db_index=True)
    response_text = models.TextField()
    provider = models.ForeignKey(AIProvider, on_delete=models.SET_NULL, null=True, blank=True, related_name="cached_responses")
    model_name = models.CharField(max_length=120, blank=True, default="")
    usage = models.JSONField(default=dict, blank=True)
    hit_count = models.PositiveIntegerField(default=0)
    last_hit_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True, db_index=True)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = "ai_response_cache"
        indexes = [
            models.Index(fields=["feature", "organization", "created_at"], name="ai_cache_feature_org_idx"),
            models.Index(fields=["redacted_input_hash"], name="ai_cache_input_hash_idx"),
        ]


class AIInterviewSession(BaseModel):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="ai_interview_sessions")
    organization = models.ForeignKey("organizations.Organization", on_delete=models.SET_NULL, null=True, blank=True, related_name="ai_interview_sessions")
    session_type = models.CharField(max_length=30, choices=AIInterviewSessionType.choices, default=AIInterviewSessionType.BEHAVIORAL, db_index=True)
    difficulty = models.CharField(max_length=20, choices=AIInterviewDifficulty.choices, default=AIInterviewDifficulty.INTERMEDIATE, db_index=True)
    status = models.CharField(max_length=20, choices=AIInterviewSessionStatus.choices, default=AIInterviewSessionStatus.ACTIVE, db_index=True)
    job_title = models.CharField(max_length=160, blank=True, default="")
    industry = models.CharField(max_length=120, blank=True, default="")
    experience_level = models.CharField(max_length=80, blank=True, default="")
    company_type = models.CharField(max_length=120, blank=True, default="")
    language = models.CharField(max_length=40, default="English")
    skills = models.JSONField(default=list, blank=True)
    resume_context = models.TextField(blank=True, default="")
    portfolio_context = models.TextField(blank=True, default="")
    history = models.JSONField(default=list, blank=True)
    summary = models.TextField(blank=True, default="")
    feedback = models.JSONField(default=dict, blank=True)
    overall_score = models.PositiveSmallIntegerField(default=0)
    confidence_trend = models.JSONField(default=list, blank=True)
    communication_trend = models.JSONField(default=list, blank=True)
    technical_trend = models.JSONField(default=list, blank=True)
    provider = models.ForeignKey(AIProvider, on_delete=models.SET_NULL, null=True, blank=True, related_name="interview_sessions")
    model_configuration = models.ForeignKey(AIModelConfiguration, on_delete=models.SET_NULL, null=True, blank=True, related_name="interview_sessions")
    estimated_cost = models.DecimalField(max_digits=12, decimal_places=6, default=Decimal("0.000000"))
    input_tokens = models.PositiveIntegerField(default=0)
    output_tokens = models.PositiveIntegerField(default=0)
    total_tokens = models.PositiveIntegerField(default=0)
    started_at = models.DateTimeField(default=timezone.now)
    finished_at = models.DateTimeField(null=True, blank=True)
    duration_seconds = models.PositiveIntegerField(default=0)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = "ai_interview_sessions"
        indexes = [
            models.Index(fields=["user", "status", "created_at"], name="ai_int_user_status_idx"),
            models.Index(fields=["organization", "status"], name="ai_int_org_status_idx"),
            models.Index(fields=["session_type", "difficulty"], name="ai_int_type_diff_idx"),
        ]

    def __str__(self):
        return f"{self.get_session_type_display()} interview for {self.user}"


class AIInterviewQuestion(BaseModel):
    session = models.ForeignKey(AIInterviewSession, on_delete=models.CASCADE, related_name="questions")
    ai_request = models.ForeignKey(AIRequest, on_delete=models.SET_NULL, null=True, blank=True, related_name="interview_questions")
    ai_response = models.ForeignKey(AIResponse, on_delete=models.SET_NULL, null=True, blank=True, related_name="interview_questions")
    sequence = models.PositiveIntegerField(default=1)
    question_text = models.TextField()
    skill_area = models.CharField(max_length=120, blank=True, default="")
    follow_up_to = models.ForeignKey("self", on_delete=models.SET_NULL, null=True, blank=True, related_name="follow_ups")
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = "ai_interview_questions"
        ordering = ["sequence", "created_at"]
        unique_together = [("session", "sequence")]
        indexes = [models.Index(fields=["session", "sequence"], name="ai_int_question_seq_idx")]


class AIInterviewAnswerEvaluation(BaseModel):
    session = models.ForeignKey(AIInterviewSession, on_delete=models.CASCADE, related_name="evaluations")
    question = models.ForeignKey(AIInterviewQuestion, on_delete=models.CASCADE, related_name="evaluations")
    ai_request = models.ForeignKey(AIRequest, on_delete=models.SET_NULL, null=True, blank=True, related_name="interview_evaluations")
    ai_response = models.ForeignKey(AIResponse, on_delete=models.SET_NULL, null=True, blank=True, related_name="interview_evaluations")
    answer_text = models.TextField()
    clarity = models.PositiveSmallIntegerField(default=0)
    confidence = models.PositiveSmallIntegerField(default=0)
    technical_quality = models.PositiveSmallIntegerField(default=0)
    communication = models.PositiveSmallIntegerField(default=0)
    structure = models.PositiveSmallIntegerField(default=0)
    problem_solving = models.PositiveSmallIntegerField(default=0)
    accuracy = models.PositiveSmallIntegerField(default=0)
    professionalism = models.PositiveSmallIntegerField(default=0)
    overall_score = models.PositiveSmallIntegerField(default=0)
    strengths = models.JSONField(default=list, blank=True)
    weaknesses = models.JSONField(default=list, blank=True)
    better_answer = models.TextField(blank=True, default="")
    tips = models.JSONField(default=list, blank=True)
    next_practice_goal = models.CharField(max_length=255, blank=True, default="")
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = "ai_interview_answer_evaluations"
        indexes = [
            models.Index(fields=["session", "created_at"], name="ai_int_eval_session_idx"),
            models.Index(fields=["overall_score"], name="ai_int_eval_score_idx"),
        ]


class AIInterviewTemplate(BaseModel):
    organization = models.ForeignKey("organizations.Organization", on_delete=models.CASCADE, null=True, blank=True, related_name="ai_interview_templates")
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="ai_interview_templates")
    title = models.CharField(max_length=180)
    session_type = models.CharField(max_length=30, choices=AIInterviewSessionType.choices, default=AIInterviewSessionType.BEHAVIORAL)
    difficulty = models.CharField(max_length=20, choices=AIInterviewDifficulty.choices, default=AIInterviewDifficulty.INTERMEDIATE)
    job_title = models.CharField(max_length=160, blank=True, default="")
    industry = models.CharField(max_length=120, blank=True, default="")
    skills = models.JSONField(default=list, blank=True)
    question_count = models.PositiveSmallIntegerField(default=6)
    is_active = models.BooleanField(default=True, db_index=True)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = "ai_interview_templates"
        indexes = [models.Index(fields=["organization", "is_active"], name="ai_int_tpl_org_active_idx")]

    def __str__(self):
        return self.title


class AICareerGoal(BaseModel):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="ai_career_goals")
    title = models.CharField(max_length=160)
    target_role = models.CharField(max_length=160, db_index=True)
    target_industry = models.CharField(max_length=160, blank=True, default="")
    target_country = models.CharField(max_length=2, blank=True, default="")
    status = models.CharField(max_length=20, choices=AICareerGoalStatus.choices, default=AICareerGoalStatus.ACTIVE, db_index=True)
    progress_percentage = models.PositiveSmallIntegerField(default=0)
    milestones = models.JSONField(default=list, blank=True)
    completed_milestones = models.JSONField(default=list, blank=True)
    coaching_history = models.JSONField(default=list, blank=True)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = "ai_career_goals"
        indexes = [models.Index(fields=["user", "status"], name="ai_goal_user_status_idx")]

    def __str__(self):
        return f"{self.user_id}:{self.target_role}"


class AICareerAssessment(BaseModel):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="ai_career_assessments")
    goal = models.ForeignKey(AICareerGoal, on_delete=models.SET_NULL, null=True, blank=True, related_name="assessments")
    request = models.ForeignKey(AIRequest, on_delete=models.SET_NULL, null=True, blank=True, related_name="career_assessments")
    readiness_score = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal("0.00"))
    confidence_score = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal("0.00"))
    strengths = models.JSONField(default=list, blank=True)
    weaknesses = models.JSONField(default=list, blank=True)
    growth_opportunities = models.JSONField(default=list, blank=True)
    recommendations = models.JSONField(default=list, blank=True)
    assessment = models.JSONField(default=dict, blank=True)
    model_name = models.CharField(max_length=120, blank=True, default="")
    prompt_version = models.CharField(max_length=80, blank=True, default="")
    estimated_cost = models.DecimalField(max_digits=12, decimal_places=6, default=Decimal("0.000000"))

    class Meta:
        db_table = "ai_career_assessments"
        indexes = [models.Index(fields=["user", "created_at"], name="ai_career_assess_user_idx")]


class AICareerRoadmap(BaseModel):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="ai_career_roadmaps")
    goal = models.ForeignKey(AICareerGoal, on_delete=models.SET_NULL, null=True, blank=True, related_name="roadmaps")
    request = models.ForeignKey(AIRequest, on_delete=models.SET_NULL, null=True, blank=True, related_name="career_roadmaps")
    horizon = models.CharField(max_length=20, choices=AIRoadmapHorizon.choices, default=AIRoadmapHorizon.SIX_MONTHS, db_index=True)
    title = models.CharField(max_length=180, blank=True, default="")
    roadmap = models.JSONField(default=dict, blank=True)
    milestones = models.JSONField(default=list, blank=True)
    recommended_courses = models.JSONField(default=list, blank=True)
    recommended_projects = models.JSONField(default=list, blank=True)
    progress_percentage = models.PositiveSmallIntegerField(default=0)
    model_name = models.CharField(max_length=120, blank=True, default="")
    estimated_cost = models.DecimalField(max_digits=12, decimal_places=6, default=Decimal("0.000000"))

    class Meta:
        db_table = "ai_career_roadmaps"
        indexes = [models.Index(fields=["user", "horizon", "created_at"], name="ai_road_user_horizon_idx")]


class AICareerSkillGap(BaseModel):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="ai_career_skill_gaps")
    goal = models.ForeignKey(AICareerGoal, on_delete=models.SET_NULL, null=True, blank=True, related_name="skill_gaps")
    request = models.ForeignKey(AIRequest, on_delete=models.SET_NULL, null=True, blank=True, related_name="career_skill_gaps")
    comparison_type = models.CharField(max_length=40, default="career_goal", db_index=True)
    target = models.CharField(max_length=180, blank=True, default="")
    missing_skills = models.JSONField(default=list, blank=True)
    priority_skills = models.JSONField(default=list, blank=True)
    estimated_learning_time = models.JSONField(default=dict, blank=True)
    recommended_courses = models.JSONField(default=list, blank=True)
    recommended_projects = models.JSONField(default=list, blank=True)
    confidence_score = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal("0.00"))
    report = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = "ai_career_skill_gaps"
        indexes = [models.Index(fields=["user", "comparison_type", "created_at"], name="ai_gap_user_type_idx")]


class AICareerCoachingSummary(BaseModel):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="ai_career_coaching_summaries")
    goal = models.ForeignKey(AICareerGoal, on_delete=models.SET_NULL, null=True, blank=True, related_name="coaching_summaries")
    request = models.ForeignKey(AIRequest, on_delete=models.SET_NULL, null=True, blank=True, related_name="career_coaching_summaries")
    week_start = models.DateField(db_index=True)
    summary = models.TextField(blank=True, default="")
    achievements = models.JSONField(default=list, blank=True)
    missed_goals = models.JSONField(default=list, blank=True)
    recommended_actions = models.JSONField(default=list, blank=True)
    upcoming_priorities = models.JSONField(default=list, blank=True)
    motivation_summary = models.TextField(blank=True, default="")
    confidence_score = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal("0.00"))
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = "ai_career_coaching_summaries"
        indexes = [models.Index(fields=["user", "week_start"], name="ai_coach_user_week_idx")]


class AIRecruiterReport(BaseModel):
    class ReportType(models.TextChoices):
        CANDIDATE_ANALYSIS = "candidate_analysis", "Candidate Analysis"
        CANDIDATE_RANKING = "candidate_ranking", "Candidate Ranking"
        CANDIDATE_COMPARISON = "candidate_comparison", "Candidate Comparison"
        JOB_ANALYSIS = "job_analysis", "Job Analysis"
        INTERVIEW_PLAN = "interview_plan", "Interview Plan"
        PIPELINE_INSIGHTS = "pipeline_insights", "Pipeline Insights"

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="ai_recruiter_reports")
    organization = models.ForeignKey("organizations.Organization", on_delete=models.SET_NULL, null=True, blank=True, related_name="ai_recruiter_reports")
    job = models.ForeignKey("jobs.JobListing", on_delete=models.SET_NULL, null=True, blank=True, related_name="ai_recruiter_reports")
    candidate = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="ai_recruiter_candidate_reports")
    request = models.ForeignKey(AIRequest, on_delete=models.SET_NULL, null=True, blank=True, related_name="recruiter_reports")
    report_type = models.CharField(max_length=40, choices=ReportType.choices, db_index=True)
    title = models.CharField(max_length=180, blank=True, default="")
    score = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal("0.00"))
    confidence_score = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal("0.00"))
    candidate_ids = models.JSONField(default=list, blank=True)
    report = models.JSONField(default=dict, blank=True)
    fairness_notes = models.TextField(blank=True, default="")
    disclaimer = models.TextField(blank=True, default="AI assistance is advisory. Do not automatically reject candidates or make hiring decisions solely from AI output.")
    model_name = models.CharField(max_length=120, blank=True, default="")
    estimated_cost = models.DecimalField(max_digits=12, decimal_places=6, default=Decimal("0.000000"))

    class Meta:
        db_table = "ai_recruiter_reports"
        indexes = [models.Index(fields=["user", "report_type", "created_at"], name="ai_rec_user_type_idx"), models.Index(fields=["organization", "report_type"], name="ai_rec_org_type_idx")]


class AILearningTutorSession(BaseModel):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="ai_learning_tutor_sessions")
    course = models.ForeignKey("courses.Course", on_delete=models.CASCADE, related_name="ai_tutor_sessions")
    lesson = models.ForeignKey("courses.Lesson", on_delete=models.SET_NULL, null=True, blank=True, related_name="ai_tutor_sessions")
    request = models.ForeignKey(AIRequest, on_delete=models.SET_NULL, null=True, blank=True, related_name="learning_tutor_sessions")
    question = models.TextField(blank=True, default="")
    answer = models.TextField(blank=True, default="")
    mode = models.CharField(max_length=40, default="question", db_index=True)
    context = models.JSONField(default=dict, blank=True)
    concepts = models.JSONField(default=list, blank=True)
    confidence_score = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal("0.00"))
    model_name = models.CharField(max_length=120, blank=True, default="")
    estimated_cost = models.DecimalField(max_digits=12, decimal_places=6, default=Decimal("0.000000"))

    class Meta:
        db_table = "ai_learning_tutor_sessions"
        indexes = [models.Index(fields=["user", "course", "created_at"], name="ai_tutor_user_course_idx")]


class AILessonIntelligence(BaseModel):
    lesson = models.ForeignKey("courses.Lesson", on_delete=models.CASCADE, related_name="ai_intelligence_reports")
    course = models.ForeignKey("courses.Course", on_delete=models.CASCADE, related_name="ai_lesson_intelligence")
    generated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="ai_lesson_intelligence_generated")
    request = models.ForeignKey(AIRequest, on_delete=models.SET_NULL, null=True, blank=True, related_name="lesson_intelligence_reports")
    content_hash = models.CharField(max_length=64, db_index=True)
    summary = models.TextField(blank=True, default="")
    key_concepts = models.JSONField(default=list, blank=True)
    glossary = models.JSONField(default=dict, blank=True)
    important_formulas = models.JSONField(default=list, blank=True)
    common_mistakes = models.JSONField(default=list, blank=True)
    prerequisites = models.JSONField(default=list, blank=True)
    learning_objectives = models.JSONField(default=list, blank=True)
    estimated_study_time_minutes = models.PositiveIntegerField(default=0)
    is_current = models.BooleanField(default=True, db_index=True)
    model_name = models.CharField(max_length=120, blank=True, default="")
    estimated_cost = models.DecimalField(max_digits=12, decimal_places=6, default=Decimal("0.000000"))

    class Meta:
        db_table = "ai_lesson_intelligence"
        indexes = [models.Index(fields=["lesson", "is_current"], name="ai_lesson_current_idx")]


class AIStudyPlan(BaseModel):
    class Pace(models.TextChoices):
        RELAXED = "relaxed", "Relaxed"
        BALANCED = "balanced", "Balanced"
        INTENSIVE = "intensive", "Intensive"

    class Cadence(models.TextChoices):
        DAILY = "daily", "Daily"
        WEEKLY = "weekly", "Weekly"
        MONTHLY = "monthly", "Monthly"

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="ai_study_plans")
    request = models.ForeignKey(AIRequest, on_delete=models.SET_NULL, null=True, blank=True, related_name="study_plans")
    cadence = models.CharField(max_length=20, choices=Cadence.choices, default=Cadence.WEEKLY, db_index=True)
    pace = models.CharField(max_length=20, choices=Pace.choices, default=Pace.BALANCED)
    available_minutes_per_day = models.PositiveIntegerField(default=60)
    deadline = models.DateField(null=True, blank=True)
    title = models.CharField(max_length=180, blank=True, default="")
    plan = models.JSONField(default=dict, blank=True)
    milestones = models.JSONField(default=list, blank=True)
    weak_concepts = models.JSONField(default=list, blank=True)
    recommended_lessons = models.JSONField(default=list, blank=True)
    confidence_score = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal("0.00"))
    model_name = models.CharField(max_length=120, blank=True, default="")
    estimated_cost = models.DecimalField(max_digits=12, decimal_places=6, default=Decimal("0.000000"))

    class Meta:
        db_table = "ai_study_plans"
        indexes = [models.Index(fields=["user", "cadence", "created_at"], name="ai_plan_user_cad_idx")]


class AIGeneratedQuiz(BaseModel):
    class Difficulty(models.TextChoices):
        BEGINNER = "beginner", "Beginner"
        INTERMEDIATE = "intermediate", "Intermediate"
        ADVANCED = "advanced", "Advanced"

    generated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="ai_generated_quizzes")
    course = models.ForeignKey("courses.Course", on_delete=models.CASCADE, related_name="ai_generated_quizzes")
    lesson = models.ForeignKey("courses.Lesson", on_delete=models.SET_NULL, null=True, blank=True, related_name="ai_generated_quizzes")
    request = models.ForeignKey(AIRequest, on_delete=models.SET_NULL, null=True, blank=True, related_name="generated_quizzes")
    title = models.CharField(max_length=180)
    difficulty = models.CharField(max_length=20, choices=Difficulty.choices, default=Difficulty.INTERMEDIATE, db_index=True)
    question_count = models.PositiveSmallIntegerField(default=5)
    learning_objectives = models.JSONField(default=list, blank=True)
    questions = models.JSONField(default=list, blank=True)
    is_instructor_reviewed = models.BooleanField(default=False, db_index=True)
    is_published_to_students = models.BooleanField(default=False, db_index=True)
    model_name = models.CharField(max_length=120, blank=True, default="")
    estimated_cost = models.DecimalField(max_digits=12, decimal_places=6, default=Decimal("0.000000"))

    class Meta:
        db_table = "ai_generated_quizzes"
        indexes = [models.Index(fields=["course", "lesson", "created_at"], name="ai_quiz_course_less_idx")]


class AIQuizFeedback(BaseModel):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="ai_quiz_feedback")
    course = models.ForeignKey("courses.Course", on_delete=models.CASCADE, related_name="ai_quiz_feedback")
    quiz_attempt = models.ForeignKey("assessments.QuizAttempt", on_delete=models.SET_NULL, null=True, blank=True, related_name="ai_feedback")
    request = models.ForeignKey(AIRequest, on_delete=models.SET_NULL, null=True, blank=True, related_name="quiz_feedback")
    explanation = models.TextField(blank=True, default="")
    correct_reasoning = models.JSONField(default=list, blank=True)
    weak_topics = models.JSONField(default=list, blank=True)
    recommended_lessons = models.JSONField(default=list, blank=True)
    next_actions = models.JSONField(default=list, blank=True)
    confidence_score = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal("0.00"))
    model_name = models.CharField(max_length=120, blank=True, default="")
    estimated_cost = models.DecimalField(max_digits=12, decimal_places=6, default=Decimal("0.000000"))

    class Meta:
        db_table = "ai_quiz_feedback"
        indexes = [models.Index(fields=["user", "course", "created_at"], name="ai_feedback_user_course_idx")]
