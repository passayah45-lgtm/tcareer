from rest_framework import serializers

from apps.ai_platform.models import (
    AIBudgetPolicy,
    AIAuditExport,
    AICareerAssessment,
    AICareerCoachingSummary,
    AICareerGoal,
    AICareerRoadmap,
    AICareerSkillGap,
    AIRecruiterReport,
    AIGeneratedQuiz,
    AILearningTutorSession,
    AILessonIntelligence,
    AIQuizFeedback,
    AIStudyPlan,
    AIComparisonReport,
    AIConversation,
    AIEvaluationDataset,
    AIEvaluationReview,
    AIEvaluationRun,
    AICalibrationReport,
    AIFeatureFlag,
    AIFeature,
    AIFairnessReport,
    AIFeedback,
    AIChangeHistory,
    AIJob,
    AIInterviewAnswerEvaluation,
    AIInterviewDifficulty,
    AIInterviewQuestion,
    AIInterviewSession,
    AIInterviewSessionStatus,
    AIInterviewSessionType,
    AIInterviewTemplate,
    AIRoadmapHorizon,
    AIModelConfiguration,
    AIProvider,
    AIRequest,
    AIResponse,
    AIModerationResult,
    AIPromptTemplate,
    AIPrivacyReport,
    AIResponseCache,
    AIReleaseGate,
    AIUsage,
    KnowledgeChunk,
    KnowledgeCollection,
    KnowledgeCollectionType,
    KnowledgeDocument,
    KnowledgeIndexStatus,
    KnowledgeVisibility,
    RetrievalEvaluationDataset,
    RetrievalEvaluationRun,
    RetrievalEvaluationResult,
    RetrievalEvent,
    AIRedTeamResult,
    AIRedTeamSuite,
    VectorCollection,
    VectorDocument,
)


class AIProviderSerializer(serializers.ModelSerializer):
    class Meta:
        model = AIProvider
        fields = [
            "id",
            "name",
            "provider_type",
            "is_active",
            "is_default",
            "priority",
            "timeout_seconds",
            "max_retries",
            "health_status",
            "last_health_check_at",
            "last_error",
            "metadata",
            "created_at",
        ]
        read_only_fields = ["id", "health_status", "last_health_check_at", "last_error", "created_at"]


class AIModelConfigurationSerializer(serializers.ModelSerializer):
    provider_name = serializers.CharField(source="provider.name", read_only=True)

    class Meta:
        model = AIModelConfiguration
        fields = ["id", "provider", "provider_name", "model_name", "display_name", "is_active", "is_default", "max_tokens", "temperature", "timeout_seconds", "max_retries", "created_at"]
        read_only_fields = ["id", "created_at"]


class AIPromptTemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = AIPromptTemplate
        fields = ["id", "key", "name", "feature", "version", "locale", "variant", "system_prompt", "user_prompt", "variables", "is_active", "metadata", "created_at"]
        read_only_fields = ["id", "created_at"]


class AIConversationSerializer(serializers.ModelSerializer):
    class Meta:
        model = AIConversation
        fields = ["id", "title", "feature", "locale", "is_archived", "metadata", "created_at", "updated_at"]
        read_only_fields = fields


class AIRequestSerializer(serializers.ModelSerializer):
    response_text = serializers.CharField(source="response.output_text", read_only=True)

    class Meta:
        model = AIRequest
        fields = ["id", "feature", "operation", "status", "redacted_input", "safety_flags", "latency_ms", "error_message", "response_text", "created_at"]
        read_only_fields = fields


class AIUsageSerializer(serializers.ModelSerializer):
    provider_name = serializers.CharField(source="provider.name", read_only=True)

    class Meta:
        model = AIUsage
        fields = ["id", "feature", "provider_name", "model_name", "period_date", "request_count", "success_count", "failure_count", "input_tokens", "output_tokens", "total_tokens", "estimated_cost", "latency_ms_total"]
        read_only_fields = fields


class AIBudgetPolicySerializer(serializers.ModelSerializer):
    class Meta:
        model = AIBudgetPolicy
        fields = [
            "id",
            "scope",
            "organization",
            "user",
            "feature",
            "daily_request_limit",
            "monthly_request_limit",
            "daily_token_limit",
            "monthly_token_limit",
            "monthly_cost_limit",
            "alert_threshold_percent",
            "last_alert_sent_at",
            "is_active",
            "metadata",
            "created_at",
        ]
        read_only_fields = ["id", "last_alert_sent_at", "created_at"]


class AIModerationResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = AIModerationResult
        fields = ["id", "stage", "is_allowed", "severity", "categories", "pii_findings", "injection_findings", "raw_result", "created_at"]
        read_only_fields = fields


class AIFeatureFlagSerializer(serializers.ModelSerializer):
    class Meta:
        model = AIFeatureFlag
        fields = ["id", "feature", "is_enabled", "organization", "user", "reason", "metadata", "created_at"]
        read_only_fields = ["id", "created_at"]


class VectorCollectionSerializer(serializers.ModelSerializer):
    document_count = serializers.IntegerField(read_only=True, default=0)

    class Meta:
        model = VectorCollection
        fields = ["id", "name", "organization", "embedding_model", "dimensions", "metadata", "document_count", "created_at"]
        read_only_fields = ["id", "created_at"]


class VectorDocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = VectorDocument
        fields = ["id", "collection", "document_type", "object_id", "title", "redacted_content", "metadata", "created_at"]
        read_only_fields = ["id", "redacted_content", "metadata", "created_at"]


class AIEvaluationDatasetSerializer(serializers.ModelSerializer):
    class Meta:
        model = AIEvaluationDataset
        fields = ["id", "name", "feature", "dataset_type", "description", "examples", "expected_schema", "expected_score_min", "expected_score_max", "rubric", "risk_tags", "locale", "difficulty", "status", "reviewer_notes", "is_golden", "version", "metadata", "created_at"]
        read_only_fields = ["id", "created_at"]


class AIEvaluationRunSerializer(serializers.ModelSerializer):
    dataset_name = serializers.CharField(source="dataset.name", read_only=True)

    class Meta:
        model = AIEvaluationRun
        fields = ["id", "dataset", "dataset_name", "provider", "model_configuration", "status", "average_score", "confidence_score", "average_latency_ms", "estimated_cost", "report", "prompt_version", "notes", "started_at", "completed_at", "duration_seconds", "failure_reason", "aggregate_results", "created_at"]
        read_only_fields = fields


class AIJobSerializer(serializers.ModelSerializer):
    result = serializers.SerializerMethodField()

    class Meta:
        model = AIJob
        fields = ["id", "feature", "status", "progress_percentage", "retry_count", "input_payload", "failure_reason", "started_at", "completed_at", "result", "created_at"]
        read_only_fields = fields

    def get_result(self, obj):
        if not hasattr(obj, "result"):
            return None
        return obj.result.content


class AIChatRequestSerializer(serializers.Serializer):
    feature = serializers.ChoiceField(choices=AIFeature.choices, default=AIFeature.CHAT)
    input_text = serializers.CharField(max_length=12000)
    organization_id = serializers.UUIDField(required=False)
    conversation_id = serializers.UUIDField(required=False)
    locale = serializers.CharField(required=False, default="en")
    provider_type = serializers.CharField(required=False, allow_blank=True, default="")
    model_name = serializers.CharField(required=False, allow_blank=True, default="")
    variables = serializers.DictField(required=False, default=dict)
    stream = serializers.BooleanField(required=False, default=False)


class AIJobCreateSerializer(serializers.Serializer):
    feature = serializers.ChoiceField(choices=AIFeature.choices)
    input_payload = serializers.DictField()
    organization_id = serializers.UUIDField(required=False)


class VectorIndexSerializer(serializers.Serializer):
    collection = serializers.CharField(max_length=120)
    document_type = serializers.CharField(max_length=40)
    object_id = serializers.CharField(max_length=100)
    title = serializers.CharField(max_length=255, required=False, allow_blank=True, default="")
    content = serializers.CharField()
    organization_id = serializers.UUIDField(required=False)


class VectorSearchSerializer(serializers.Serializer):
    collection = serializers.CharField(max_length=120)
    query = serializers.CharField()
    document_type = serializers.CharField(required=False, allow_blank=True, default="")
    limit = serializers.IntegerField(required=False, min_value=1, max_value=20, default=5)
    organization_id = serializers.UUIDField(required=False)


class KnowledgeCollectionSerializer(serializers.ModelSerializer):
    document_count = serializers.IntegerField(read_only=True, default=0)
    chunk_count = serializers.IntegerField(read_only=True, default=0)

    class Meta:
        model = KnowledgeCollection
        fields = ["id", "name", "collection_type", "organization", "embedding_version", "vector_backend", "vector_dimensions", "health_status", "last_health_check_at", "last_health_error", "is_active", "metadata", "document_count", "chunk_count", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]


class KnowledgeDocumentSerializer(serializers.ModelSerializer):
    chunk_count = serializers.IntegerField(source="chunks.count", read_only=True)

    class Meta:
        model = KnowledgeDocument
        fields = ["id", "collection", "organization", "owner", "source_type", "source_id", "title", "version", "checksum", "embedding_version", "index_status", "visibility", "last_indexed_at", "source_updated_at", "last_successful_reindex_at", "freshness_score", "stale_reason", "error_message", "metadata", "chunk_count", "created_at", "updated_at"]
        read_only_fields = fields


class KnowledgeChunkSerializer(serializers.ModelSerializer):
    document_title = serializers.CharField(source="document.title", read_only=True)

    class Meta:
        model = KnowledgeChunk
        fields = ["id", "document", "document_title", "chunk_index", "text", "token_count", "metadata", "created_at"]
        read_only_fields = fields


class RetrievalEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = RetrievalEvent
        fields = ["id", "user", "organization", "feature", "query", "search_type", "latency_ms", "result_count", "source_count", "chunk_count", "context_size", "timed_out", "confidence", "cache_hit", "sources", "missing_knowledge", "metadata", "created_at"]
        read_only_fields = fields


class RetrievalEvaluationDatasetSerializer(serializers.ModelSerializer):
    class Meta:
        model = RetrievalEvaluationDataset
        fields = ["id", "name", "feature", "description", "cases", "minimum_pass_rate", "is_active", "metadata", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]


class RetrievalEvaluationRunSerializer(serializers.ModelSerializer):
    dataset_name = serializers.CharField(source="dataset.name", read_only=True)

    class Meta:
        model = RetrievalEvaluationRun
        fields = ["id", "dataset", "dataset_name", "status", "total_cases", "passed_cases", "failed_cases", "pass_rate", "average_confidence", "report", "failure_reason", "created_at"]
        read_only_fields = fields


class RetrievalEvaluationResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = RetrievalEvaluationResult
        fields = ["id", "run", "query", "expected_document_id", "expected_chunk_id", "expected_source_type", "expected_citation", "minimum_confidence", "ranking_position", "passed", "confidence", "retrieved_citations", "metadata", "created_at"]
        read_only_fields = fields


class RetrievalEvaluationRunRequestSerializer(serializers.Serializer):
    dataset_id = serializers.UUIDField()


class KnowledgeSearchSerializer(serializers.Serializer):
    query = serializers.CharField(max_length=12000)
    feature = serializers.ChoiceField(choices=AIFeature.choices, default=AIFeature.CHAT)
    collection_types = serializers.ListField(child=serializers.ChoiceField(choices=KnowledgeCollectionType.choices), required=False, default=list)
    search_type = serializers.ChoiceField(choices=["semantic", "hybrid", "keyword"], default="hybrid")
    organization_id = serializers.UUIDField(required=False)
    limit = serializers.IntegerField(required=False, min_value=1, max_value=20, default=5)
    include_private = serializers.BooleanField(required=False, default=False)
    metadata = serializers.DictField(required=False, default=dict)


class KnowledgeReindexSerializer(serializers.Serializer):
    collection_type = serializers.ChoiceField(choices=KnowledgeCollectionType.choices, required=False, default=KnowledgeCollectionType.FUTURE_DOCUMENTS)
    source_type = serializers.CharField(max_length=60)
    source_id = serializers.CharField(max_length=120, required=False, allow_blank=True, default="")
    title = serializers.CharField(max_length=255, required=False, allow_blank=True, default="")
    text = serializers.CharField(required=False, allow_blank=True, default="")
    visibility = serializers.ChoiceField(choices=KnowledgeVisibility.choices, default=KnowledgeVisibility.PUBLIC)
    organization_id = serializers.UUIDField(required=False)
    metadata = serializers.DictField(required=False, default=dict)


class KnowledgeStatusSerializer(serializers.Serializer):
    organization_id = serializers.UUIDField(required=False)
    collection_type = serializers.ChoiceField(choices=KnowledgeCollectionType.choices, required=False)


class ModerationSerializer(serializers.Serializer):
    text = serializers.CharField()
    stage = serializers.ChoiceField(choices=[("input", "Input"), ("output", "Output")], default="input")
    organization_id = serializers.UUIDField(required=False)


class CostReconciliationSerializer(serializers.Serializer):
    request_id = serializers.UUIDField()
    actual_cost = serializers.DecimalField(max_digits=12, decimal_places=6, required=False)
    provider_input_tokens = serializers.IntegerField(required=False, min_value=0)
    provider_output_tokens = serializers.IntegerField(required=False, min_value=0)


class EvaluationRunCreateSerializer(serializers.Serializer):
    dataset_id = serializers.UUIDField()
    provider_type = serializers.CharField(required=False, allow_blank=True, default="")
    model_name = serializers.CharField(required=False, allow_blank=True, default="")


class EvaluationRunFilterSerializer(serializers.Serializer):
    dataset_type = serializers.CharField(required=False, allow_blank=True, default="")
    feature = serializers.CharField(required=False, allow_blank=True, default="")
    provider = serializers.CharField(required=False, allow_blank=True, default="")
    prompt_version = serializers.CharField(required=False, allow_blank=True, default="")
    limit = serializers.IntegerField(required=False, min_value=1, max_value=100, default=20)
    dry_run = serializers.BooleanField(required=False, default=False)
    budget = serializers.DictField(required=False, default=dict)


class AIEvaluationReviewSerializer(serializers.ModelSerializer):
    dataset_name = serializers.CharField(source="result.run.dataset.name", read_only=True)

    class Meta:
        model = AIEvaluationReview
        fields = ["id", "result", "dataset_name", "assigned_to", "reviewed_by", "status", "manual_score", "hallucination_flag", "bias_flag", "unsafe_flag", "request_prompt_revision", "notes", "assigned_at", "reviewed_at", "created_at"]
        read_only_fields = ["id", "reviewed_by", "assigned_at", "reviewed_at", "created_at"]


class AIEvaluationReviewActionSerializer(serializers.Serializer):
    assigned_to = serializers.UUIDField(required=False)
    status = serializers.ChoiceField(choices=["pending", "approved", "rejected", "manual_review"], required=False, default="manual_review")
    manual_score = serializers.DecimalField(max_digits=5, decimal_places=2, required=False)
    hallucination_flag = serializers.BooleanField(required=False, default=False)
    bias_flag = serializers.BooleanField(required=False, default=False)
    unsafe_flag = serializers.BooleanField(required=False, default=False)
    request_prompt_revision = serializers.BooleanField(required=False, default=False)
    notes = serializers.CharField(required=False, allow_blank=True, default="")


class AIEvaluationReviewFilterSerializer(serializers.Serializer):
    feature = serializers.CharField(required=False, allow_blank=True, default="")
    dataset_type = serializers.CharField(required=False, allow_blank=True, default="")
    risk_tag = serializers.CharField(required=False, allow_blank=True, default="")
    status = serializers.CharField(required=False, allow_blank=True, default="")


class AIEvaluationReviewBulkAssignSerializer(serializers.Serializer):
    review_ids = serializers.ListField(child=serializers.UUIDField(), min_length=1)
    assigned_to = serializers.UUIDField()


class AIEvaluationReviewBulkApproveSerializer(serializers.Serializer):
    review_ids = serializers.ListField(child=serializers.UUIDField(), min_length=1)
    notes = serializers.CharField(required=False, allow_blank=True, default="")


class AIRedTeamSuiteSerializer(serializers.ModelSerializer):
    class Meta:
        model = AIRedTeamSuite
        fields = ["id", "name", "suite_type", "feature", "severity", "expected_safe_behavior", "cases", "is_active", "metadata", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]


class AIRedTeamResultSerializer(serializers.ModelSerializer):
    suite_name = serializers.CharField(source="suite.name", read_only=True)

    class Meta:
        model = AIRedTeamResult
        fields = ["id", "suite", "suite_name", "run", "case_name", "input_text", "output_text", "risk_severity", "risk_flags", "passed", "expected_safe_behavior", "mitigation_notes", "metadata", "created_at"]
        read_only_fields = fields


class AIReleaseGateSerializer(serializers.ModelSerializer):
    evaluation_run_status = serializers.CharField(source="evaluation_run.status", read_only=True)
    requested_by_email = serializers.CharField(source="requested_by.email", read_only=True)
    reviewed_by_email = serializers.CharField(source="reviewed_by.email", read_only=True)

    class Meta:
        model = AIReleaseGate
        fields = ["id", "change_type", "target_id", "feature", "status", "previous_version", "new_version", "thresholds", "gate_results", "evaluation_run", "evaluation_run_status", "requested_by", "requested_by_email", "reviewed_by", "reviewed_by_email", "promoted_at", "rolled_back_at", "rollback_reason", "metadata", "created_at", "updated_at"]
        read_only_fields = ["id", "status", "gate_results", "requested_by", "requested_by_email", "reviewed_by", "reviewed_by_email", "promoted_at", "rolled_back_at", "rollback_reason", "created_at", "updated_at"]


class AIReleaseGateCreateSerializer(serializers.Serializer):
    change_type = serializers.ChoiceField(choices=["prompt_template", "model_configuration", "provider", "feature_flag"])
    target_id = serializers.CharField(max_length=100)
    feature = serializers.ChoiceField(choices=AIFeature.choices)
    previous_version = serializers.DictField(required=False, default=dict)
    new_version = serializers.DictField(required=False, default=dict)
    evaluation_run_id = serializers.UUIDField(required=False)
    thresholds = serializers.DictField(required=False, default=dict)


class AIReleaseGateActionSerializer(serializers.Serializer):
    action = serializers.ChoiceField(choices=["promote", "rollback"])
    reason = serializers.CharField(required=False, allow_blank=True, default="")


class AIChangeHistorySerializer(serializers.ModelSerializer):
    changed_by_email = serializers.CharField(source="changed_by.email", read_only=True)

    class Meta:
        model = AIChangeHistory
        fields = ["id", "gate", "changed_by", "changed_by_email", "change_type", "target_id", "previous_version", "new_version", "approval_state", "evaluation_run", "promoted_at", "rolled_back_at", "rollback_reason", "metadata", "created_at"]
        read_only_fields = fields


class AIRedTeamRunSerializer(serializers.Serializer):
    suite_id = serializers.UUIDField()
    provider = serializers.CharField(required=False, allow_blank=True, default="")


class AIComparisonReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = AIComparisonReport
        fields = ["id", "comparison_type", "feature", "left_label", "right_label", "metrics", "winner", "generated_by", "metadata", "created_at"]
        read_only_fields = ["id", "metrics", "winner", "generated_by", "metadata", "created_at"]


class AIComparisonCreateSerializer(serializers.Serializer):
    comparison_type = serializers.ChoiceField(choices=["provider", "model", "prompt_version", "feature_version"])
    feature = serializers.ChoiceField(choices=AIFeature.choices)
    left_label = serializers.CharField(max_length=160)
    right_label = serializers.CharField(max_length=160)


class AIAuditExportSerializer(serializers.ModelSerializer):
    class Meta:
        model = AIAuditExport
        fields = ["id", "export_type", "file_format", "status", "file", "file_name", "row_count", "filters", "failure_reason", "completed_at", "created_at"]
        read_only_fields = fields


class AIAuditExportCreateSerializer(serializers.Serializer):
    export_type = serializers.ChoiceField(choices=["evaluation_runs", "safety_events", "privacy_events", "bias_events", "feedback", "provider_usage", "prompt_versions", "model_comparisons"])
    file_format = serializers.ChoiceField(choices=["csv", "xlsx"], default="csv")
    filters = serializers.DictField(required=False, default=dict)


class AICalibrationReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = AICalibrationReport
        fields = ["id", "request", "feature", "score_name", "score", "confidence_score", "confidence_level", "score_breakdown", "weighting", "evidence", "reasoning_summary", "uncertainty", "missing_information", "limitations", "recommended_next_action", "created_at"]
        read_only_fields = fields


class AIFairnessReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = AIFairnessReport
        fields = ["id", "request", "organization", "feature", "fairness_score", "bias_flags", "manual_review_required", "reviewed_by", "reviewed_at", "report", "created_at"]
        read_only_fields = fields


class AIPrivacyReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = AIPrivacyReport
        fields = ["id", "request", "organization", "feature", "findings", "redaction_count", "policy", "severity", "report", "created_at"]
        read_only_fields = fields


class AIFeedbackSerializer(serializers.ModelSerializer):
    class Meta:
        model = AIFeedback
        fields = ["id", "request", "feature", "rating", "comment", "provider", "model_name", "prompt_version", "metadata", "created_at"]
        read_only_fields = ["id", "provider", "model_name", "prompt_version", "metadata", "created_at"]


class AIFeedbackCreateSerializer(serializers.Serializer):
    request_id = serializers.UUIDField(required=False)
    feature = serializers.ChoiceField(choices=AIFeature.choices)
    rating = serializers.ChoiceField(choices=["helpful", "not_helpful", "incorrect", "hallucination", "unsafe", "biased", "incomplete"])
    comment = serializers.CharField(required=False, allow_blank=True, default="", max_length=2000)
    organization_id = serializers.UUIDField(required=False)
    metadata = serializers.DictField(required=False, default=dict)


class AIExplainScoreSerializer(serializers.Serializer):
    request_id = serializers.UUIDField(required=False)
    feature = serializers.ChoiceField(choices=AIFeature.choices)
    score_name = serializers.CharField(max_length=80)
    score = serializers.DecimalField(max_digits=6, decimal_places=2)
    evidence = serializers.ListField(child=serializers.CharField(), required=False, default=list)
    score_breakdown = serializers.DictField(required=False, default=dict)
    weighting = serializers.DictField(required=False, default=dict)


class AIBiasReportRequestSerializer(serializers.Serializer):
    text = serializers.CharField(max_length=12000)
    feature = serializers.ChoiceField(choices=AIFeature.choices)
    organization_id = serializers.UUIDField(required=False)


class AIPrivacyReportRequestSerializer(serializers.Serializer):
    text = serializers.CharField(max_length=12000)
    feature = serializers.ChoiceField(choices=AIFeature.choices)
    organization_id = serializers.UUIDField(required=False)


class AICacheSerializer(serializers.ModelSerializer):
    provider_name = serializers.CharField(source="provider.name", read_only=True)

    class Meta:
        model = AIResponseCache
        fields = ["id", "feature", "organization", "provider_name", "model_name", "hit_count", "last_hit_at", "expires_at", "metadata", "created_at"]
        read_only_fields = fields


class AIInterviewQuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = AIInterviewQuestion
        fields = ["id", "sequence", "question_text", "skill_area", "follow_up_to", "metadata", "created_at"]
        read_only_fields = fields


class AIInterviewAnswerEvaluationSerializer(serializers.ModelSerializer):
    question_text = serializers.CharField(source="question.question_text", read_only=True)

    class Meta:
        model = AIInterviewAnswerEvaluation
        fields = [
            "id",
            "question",
            "question_text",
            "answer_text",
            "clarity",
            "confidence",
            "technical_quality",
            "communication",
            "structure",
            "problem_solving",
            "accuracy",
            "professionalism",
            "overall_score",
            "strengths",
            "weaknesses",
            "better_answer",
            "tips",
            "next_practice_goal",
            "metadata",
            "created_at",
        ]
        read_only_fields = fields


class AIInterviewSessionSerializer(serializers.ModelSerializer):
    questions = AIInterviewQuestionSerializer(many=True, read_only=True)
    evaluations = AIInterviewAnswerEvaluationSerializer(many=True, read_only=True)
    organization_name = serializers.CharField(source="organization.name", read_only=True)

    class Meta:
        model = AIInterviewSession
        fields = [
            "id",
            "organization",
            "organization_name",
            "session_type",
            "difficulty",
            "status",
            "job_title",
            "industry",
            "experience_level",
            "company_type",
            "language",
            "skills",
            "history",
            "summary",
            "feedback",
            "overall_score",
            "confidence_trend",
            "communication_trend",
            "technical_trend",
            "provider",
            "model_configuration",
            "estimated_cost",
            "input_tokens",
            "output_tokens",
            "total_tokens",
            "started_at",
            "finished_at",
            "duration_seconds",
            "metadata",
            "questions",
            "evaluations",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields


class AIInterviewSessionCreateSerializer(serializers.Serializer):
    organization_id = serializers.UUIDField(required=False)
    session_type = serializers.ChoiceField(choices=AIInterviewSessionType.choices, default=AIInterviewSessionType.BEHAVIORAL)
    difficulty = serializers.ChoiceField(choices=AIInterviewDifficulty.choices, default=AIInterviewDifficulty.INTERMEDIATE)
    job_title = serializers.CharField(required=False, allow_blank=True, default="")
    industry = serializers.CharField(required=False, allow_blank=True, default="")
    experience_level = serializers.CharField(required=False, allow_blank=True, default="")
    company_type = serializers.CharField(required=False, allow_blank=True, default="")
    language = serializers.CharField(required=False, allow_blank=True, default="English")
    skills = serializers.ListField(child=serializers.CharField(max_length=80), required=False, default=list)
    resume_context = serializers.CharField(required=False, allow_blank=True, default="")
    portfolio_context = serializers.CharField(required=False, allow_blank=True, default="")


class AIInterviewAnswerSubmitSerializer(serializers.Serializer):
    question_id = serializers.UUIDField()
    answer_text = serializers.CharField(min_length=1, max_length=12000)


class AIInterviewTemplateSerializer(serializers.ModelSerializer):
    organization_name = serializers.CharField(source="organization.name", read_only=True)

    class Meta:
        model = AIInterviewTemplate
        fields = ["id", "organization", "organization_name", "title", "session_type", "difficulty", "job_title", "industry", "skills", "question_count", "is_active", "metadata", "created_at", "updated_at"]
        read_only_fields = ["id", "organization_name", "created_at", "updated_at"]


class AIInterviewTemplateCreateSerializer(serializers.Serializer):
    organization_id = serializers.UUIDField(required=False)
    title = serializers.CharField(max_length=180)
    session_type = serializers.ChoiceField(choices=AIInterviewSessionType.choices, default=AIInterviewSessionType.BEHAVIORAL)
    difficulty = serializers.ChoiceField(choices=AIInterviewDifficulty.choices, default=AIInterviewDifficulty.INTERMEDIATE)
    job_title = serializers.CharField(required=False, allow_blank=True, default="")
    industry = serializers.CharField(required=False, allow_blank=True, default="")
    skills = serializers.ListField(child=serializers.CharField(max_length=80), required=False, default=list)
    question_count = serializers.IntegerField(required=False, min_value=1, max_value=20, default=6)
    is_active = serializers.BooleanField(required=False, default=True)
    metadata = serializers.DictField(required=False, default=dict)


class AICareerGoalSerializer(serializers.ModelSerializer):
    class Meta:
        model = AICareerGoal
        fields = ["id", "title", "target_role", "target_industry", "target_country", "status", "progress_percentage", "milestones", "completed_milestones", "coaching_history", "metadata", "created_at", "updated_at"]
        read_only_fields = ["id", "coaching_history", "created_at", "updated_at"]


class AICareerGoalCreateSerializer(serializers.Serializer):
    title = serializers.CharField(max_length=160, required=False, allow_blank=True, default="")
    target_role = serializers.CharField(max_length=160)
    target_industry = serializers.CharField(max_length=160, required=False, allow_blank=True, default="")
    target_country = serializers.CharField(max_length=2, required=False, allow_blank=True, default="")
    milestones = serializers.ListField(child=serializers.DictField(), required=False, default=list)


class AICareerGoalUpdateSerializer(serializers.Serializer):
    title = serializers.CharField(max_length=160, required=False)
    target_role = serializers.CharField(max_length=160, required=False)
    target_industry = serializers.CharField(max_length=160, required=False, allow_blank=True)
    target_country = serializers.CharField(max_length=2, required=False, allow_blank=True)
    status = serializers.ChoiceField(choices=["active", "paused", "completed", "archived"], required=False)
    progress_percentage = serializers.IntegerField(required=False, min_value=0, max_value=100)
    milestones = serializers.ListField(child=serializers.DictField(), required=False)
    completed_milestones = serializers.ListField(child=serializers.DictField(), required=False)


class AICareerAssessmentSerializer(serializers.ModelSerializer):
    goal_title = serializers.CharField(source="goal.title", read_only=True)

    class Meta:
        model = AICareerAssessment
        fields = ["id", "goal", "goal_title", "readiness_score", "confidence_score", "strengths", "weaknesses", "growth_opportunities", "recommendations", "assessment", "model_name", "prompt_version", "estimated_cost", "created_at"]
        read_only_fields = fields


class AICareerRoadmapSerializer(serializers.ModelSerializer):
    goal_title = serializers.CharField(source="goal.title", read_only=True)

    class Meta:
        model = AICareerRoadmap
        fields = ["id", "goal", "goal_title", "horizon", "title", "roadmap", "milestones", "recommended_courses", "recommended_projects", "progress_percentage", "model_name", "estimated_cost", "created_at", "updated_at"]
        read_only_fields = fields


class AICareerSkillGapSerializer(serializers.ModelSerializer):
    goal_title = serializers.CharField(source="goal.title", read_only=True)

    class Meta:
        model = AICareerSkillGap
        fields = ["id", "goal", "goal_title", "comparison_type", "target", "missing_skills", "priority_skills", "estimated_learning_time", "recommended_courses", "recommended_projects", "confidence_score", "report", "created_at"]
        read_only_fields = fields


class AICareerCoachingSummarySerializer(serializers.ModelSerializer):
    goal_title = serializers.CharField(source="goal.title", read_only=True)

    class Meta:
        model = AICareerCoachingSummary
        fields = ["id", "goal", "goal_title", "week_start", "summary", "achievements", "missed_goals", "recommended_actions", "upcoming_priorities", "motivation_summary", "confidence_score", "metadata", "created_at"]
        read_only_fields = fields


class AIRecruiterReportSerializer(serializers.ModelSerializer):
    organization_name = serializers.CharField(source="organization.name", read_only=True, default="")
    job_title = serializers.CharField(source="job.title", read_only=True, default="")
    candidate_name = serializers.CharField(source="candidate.full_name", read_only=True, default="")

    class Meta:
        model = AIRecruiterReport
        fields = [
            "id",
            "organization",
            "organization_name",
            "job",
            "job_title",
            "candidate",
            "candidate_name",
            "report_type",
            "title",
            "score",
            "confidence_score",
            "candidate_ids",
            "report",
            "fairness_notes",
            "disclaimer",
            "model_name",
            "estimated_cost",
            "created_at",
        ]
        read_only_fields = fields


class AICareerAssessmentRequestSerializer(serializers.Serializer):
    goal_id = serializers.UUIDField(required=False)
    current_skills = serializers.ListField(child=serializers.CharField(max_length=80), required=False, default=list)
    education = serializers.CharField(required=False, allow_blank=True, default="")
    experience = serializers.CharField(required=False, allow_blank=True, default="")
    career_interests = serializers.ListField(child=serializers.CharField(max_length=120), required=False, default=list)
    preferred_industries = serializers.ListField(child=serializers.CharField(max_length=120), required=False, default=list)
    preferred_countries = serializers.ListField(child=serializers.CharField(max_length=2), required=False, default=list)
    preferred_work_style = serializers.CharField(required=False, allow_blank=True, default="")


class AICareerRoadmapRequestSerializer(serializers.Serializer):
    goal_id = serializers.UUIDField(required=False)
    horizon = serializers.ChoiceField(choices=AIRoadmapHorizon.choices, default=AIRoadmapHorizon.SIX_MONTHS)
    target_role = serializers.CharField(max_length=160, required=False, allow_blank=True, default="")
    skills = serializers.ListField(child=serializers.CharField(max_length=80), required=False, default=list)


class AICareerSkillGapRequestSerializer(serializers.Serializer):
    goal_id = serializers.UUIDField(required=False)
    comparison_type = serializers.ChoiceField(choices=["selected_job", "career_goal", "industry", "role", "company", "country"], default="career_goal")
    target = serializers.CharField(max_length=180, required=False, allow_blank=True, default="")
    desired_skills = serializers.ListField(child=serializers.CharField(max_length=80), required=False, default=list)


class AICareerWeeklyCoachingRequestSerializer(serializers.Serializer):
    goal_id = serializers.UUIDField(required=False)
    achievements = serializers.ListField(child=serializers.CharField(max_length=200), required=False, default=list)
    missed_goals = serializers.ListField(child=serializers.CharField(max_length=200), required=False, default=list)


class AIRecruiterCandidateAnalysisRequestSerializer(serializers.Serializer):
    candidate_id = serializers.UUIDField()
    organization_id = serializers.UUIDField(required=False)
    job_id = serializers.UUIDField(required=False)


class AIRecruiterRankingRequestSerializer(serializers.Serializer):
    job_id = serializers.UUIDField()
    candidate_ids = serializers.ListField(child=serializers.UUIDField(), min_length=1, max_length=50)
    sort_by = serializers.ChoiceField(
        choices=["best_fit", "highest_confidence", "highest_growth_potential", "highest_learning_activity"],
        default="best_fit",
    )


class AIRecruiterComparisonRequestSerializer(serializers.Serializer):
    candidate_ids = serializers.ListField(child=serializers.UUIDField(), min_length=2, max_length=10)
    organization_id = serializers.UUIDField(required=False)
    job_id = serializers.UUIDField(required=False)


class AIRecruiterJobAnalysisRequestSerializer(serializers.Serializer):
    job_id = serializers.UUIDField(required=False)
    title = serializers.CharField(max_length=255, required=False, allow_blank=True, default="")
    description = serializers.CharField(required=False, allow_blank=True, default="")

    def validate(self, attrs):
        if not attrs.get("job_id") and not attrs.get("description"):
            raise serializers.ValidationError("Provide either job_id or description.")
        return attrs


class AIRecruiterInterviewPlanRequestSerializer(serializers.Serializer):
    candidate_id = serializers.UUIDField()
    organization_id = serializers.UUIDField(required=False)
    job_id = serializers.UUIDField(required=False)


class AIRecruiterPipelineInsightsRequestSerializer(serializers.Serializer):
    organization_id = serializers.UUIDField()
    job_id = serializers.UUIDField(required=False)


class AILearningTutorSessionSerializer(serializers.ModelSerializer):
    course_title = serializers.CharField(source="course.title", read_only=True, default="")
    lesson_title = serializers.CharField(source="lesson.title", read_only=True, default="")

    class Meta:
        model = AILearningTutorSession
        fields = ["id", "course", "course_title", "lesson", "lesson_title", "question", "answer", "mode", "concepts", "confidence_score", "model_name", "estimated_cost", "context", "created_at"]
        read_only_fields = fields


class AILessonIntelligenceSerializer(serializers.ModelSerializer):
    course_title = serializers.CharField(source="course.title", read_only=True, default="")
    lesson_title = serializers.CharField(source="lesson.title", read_only=True, default="")

    class Meta:
        model = AILessonIntelligence
        fields = [
            "id",
            "lesson",
            "lesson_title",
            "course",
            "course_title",
            "summary",
            "key_concepts",
            "glossary",
            "important_formulas",
            "common_mistakes",
            "prerequisites",
            "learning_objectives",
            "estimated_study_time_minutes",
            "is_current",
            "model_name",
            "estimated_cost",
            "created_at",
        ]
        read_only_fields = fields


class AIStudyPlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = AIStudyPlan
        fields = ["id", "cadence", "pace", "available_minutes_per_day", "deadline", "title", "plan", "milestones", "weak_concepts", "recommended_lessons", "confidence_score", "model_name", "estimated_cost", "created_at"]
        read_only_fields = fields


class AIGeneratedQuizSerializer(serializers.ModelSerializer):
    course_title = serializers.CharField(source="course.title", read_only=True, default="")
    lesson_title = serializers.CharField(source="lesson.title", read_only=True, default="")

    class Meta:
        model = AIGeneratedQuiz
        fields = ["id", "course", "course_title", "lesson", "lesson_title", "title", "difficulty", "question_count", "learning_objectives", "questions", "is_instructor_reviewed", "is_published_to_students", "model_name", "estimated_cost", "created_at"]
        read_only_fields = fields


class AIQuizFeedbackSerializer(serializers.ModelSerializer):
    course_title = serializers.CharField(source="course.title", read_only=True, default="")

    class Meta:
        model = AIQuizFeedback
        fields = ["id", "course", "course_title", "quiz_attempt", "explanation", "correct_reasoning", "weak_topics", "recommended_lessons", "next_actions", "confidence_score", "model_name", "estimated_cost", "created_at"]
        read_only_fields = fields


class AICourseTutorRequestSerializer(serializers.Serializer):
    course_id = serializers.UUIDField()
    lesson_id = serializers.UUIDField(required=False)
    question = serializers.CharField(required=False, allow_blank=True, default="")
    mode = serializers.ChoiceField(
        choices=["explain", "question", "summarize", "examples", "simplify", "practice", "reading", "connect"],
        default="question",
    )


class AILessonIntelligenceRequestSerializer(serializers.Serializer):
    course_id = serializers.UUIDField()
    lesson_id = serializers.UUIDField()
    regenerate = serializers.BooleanField(default=False)


class AIStudyPlanRequestSerializer(serializers.Serializer):
    cadence = serializers.ChoiceField(choices=AIStudyPlan.Cadence.choices, default=AIStudyPlan.Cadence.WEEKLY)
    pace = serializers.ChoiceField(choices=AIStudyPlan.Pace.choices, default=AIStudyPlan.Pace.BALANCED)
    available_minutes_per_day = serializers.IntegerField(min_value=10, max_value=720, default=60)
    deadline = serializers.DateField(required=False)
    career_goal_id = serializers.UUIDField(required=False)


class AIGeneratedQuizRequestSerializer(serializers.Serializer):
    course_id = serializers.UUIDField()
    lesson_id = serializers.UUIDField(required=False)
    difficulty = serializers.ChoiceField(choices=AIGeneratedQuiz.Difficulty.choices, default=AIGeneratedQuiz.Difficulty.INTERMEDIATE)
    number_of_questions = serializers.IntegerField(min_value=1, max_value=25, default=5)
    learning_objectives = serializers.ListField(child=serializers.CharField(max_length=200), required=False, default=list)
    include_coding_foundation = serializers.BooleanField(default=False)


class AIQuizFeedbackRequestSerializer(serializers.Serializer):
    course_id = serializers.UUIDField()
    attempt_id = serializers.UUIDField(required=False)


class AIInstructorToolRequestSerializer(serializers.Serializer):
    course_id = serializers.UUIDField()
    lesson_id = serializers.UUIDField(required=False)
    tool = serializers.ChoiceField(
        choices=["lesson_summary", "quiz", "exercises", "objectives", "prerequisites", "confusing_lessons"],
        default="lesson_summary",
    )
    difficulty = serializers.ChoiceField(choices=AIGeneratedQuiz.Difficulty.choices, default=AIGeneratedQuiz.Difficulty.INTERMEDIATE)
    number_of_questions = serializers.IntegerField(min_value=1, max_value=25, default=5)


class AIInterviewStatusSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=[
        AIInterviewSessionStatus.ACTIVE,
        AIInterviewSessionStatus.PAUSED,
        AIInterviewSessionStatus.CANCELLED,
    ])
