from django.contrib import admin

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
    AIEvaluationResult,
    AIEvaluationRun,
    AICalibrationReport,
    AIFeatureFlag,
    AIFairnessReport,
    AIFeedback,
    AIChangeHistory,
    AIInterviewAnswerEvaluation,
    AIInterviewQuestion,
    AIInterviewSession,
    AIInterviewTemplate,
    AIJob,
    AIModelConfiguration,
    AIProvider,
    AIRequest,
    AIResponse,
    AIResult,
    AIModerationResult,
    AIPromptTemplate,
    AIPrivacyReport,
    AIResponseCache,
    AIReleaseGate,
    AITokenUsage,
    AIUsage,
    KnowledgeChunk,
    KnowledgeCollection,
    KnowledgeDocument,
    RetrievalEvaluationDataset,
    RetrievalEvaluationRun,
    RetrievalEvaluationResult,
    RetrievalEvent,
    AIRedTeamResult,
    AIRedTeamSuite,
    VectorCollection,
    VectorDocument,
)


@admin.register(AIProvider)
class AIProviderAdmin(admin.ModelAdmin):
    list_display = ("name", "provider_type", "is_active", "is_default", "priority", "timeout_seconds")
    list_filter = ("provider_type", "is_active", "is_default")
    search_fields = ("name",)
    readonly_fields = ("id", "created_at", "updated_at")


@admin.register(AIModelConfiguration)
class AIModelConfigurationAdmin(admin.ModelAdmin):
    list_display = ("provider", "model_name", "is_active", "is_default", "max_tokens", "temperature")
    list_filter = ("provider", "is_active", "is_default")
    search_fields = ("provider__name", "model_name", "display_name")
    readonly_fields = ("id", "created_at", "updated_at")


@admin.register(AIPromptTemplate)
class AIPromptTemplateAdmin(admin.ModelAdmin):
    list_display = ("key", "feature", "version", "locale", "variant", "is_active")
    list_filter = ("feature", "locale", "variant", "is_active")
    search_fields = ("key", "name", "system_prompt", "user_prompt")
    readonly_fields = ("id", "created_at", "updated_at")


@admin.register(AIConversation)
class AIConversationAdmin(admin.ModelAdmin):
    list_display = ("user", "organization", "feature", "title", "is_archived", "created_at")
    list_filter = ("feature", "is_archived")
    search_fields = ("user__email", "organization__name", "title")
    readonly_fields = ("id", "created_at", "updated_at")


@admin.register(AIRequest)
class AIRequestAdmin(admin.ModelAdmin):
    list_display = ("user", "organization", "feature", "provider", "status", "latency_ms", "created_at")
    list_filter = ("feature", "status", "provider")
    search_fields = ("user__email", "organization__name", "redacted_input", "error_message")
    readonly_fields = ("id", "input_text", "redacted_input", "rendered_prompt", "safety_flags", "metadata", "created_at", "updated_at")


@admin.register(AIResponse)
class AIResponseAdmin(admin.ModelAdmin):
    list_display = ("request", "finish_reason", "created_at")
    search_fields = ("output_text",)
    readonly_fields = ("id", "request", "output_text", "raw_response", "safety_flags", "metadata", "created_at", "updated_at")


@admin.register(AITokenUsage)
class AITokenUsageAdmin(admin.ModelAdmin):
    list_display = ("request", "provider", "model_name", "total_tokens", "estimated_cost")
    list_filter = ("provider", "model_name")
    readonly_fields = ("id", "created_at", "updated_at")


@admin.register(AIUsage)
class AIUsageAdmin(admin.ModelAdmin):
    list_display = ("period_date", "organization", "user", "feature", "provider", "request_count", "total_tokens", "estimated_cost")
    list_filter = ("feature", "provider", "period_date")
    search_fields = ("user__email", "organization__name", "model_name")
    readonly_fields = ("id", "created_at", "updated_at")


@admin.register(AIBudgetPolicy)
class AIBudgetPolicyAdmin(admin.ModelAdmin):
    list_display = ("scope", "organization", "user", "feature", "daily_request_limit", "monthly_request_limit", "is_active")
    list_filter = ("scope", "feature", "is_active")
    search_fields = ("organization__name", "user__email", "feature")
    readonly_fields = ("id", "created_at", "updated_at")


@admin.register(AIJob)
class AIJobAdmin(admin.ModelAdmin):
    list_display = ("user", "organization", "feature", "status", "progress_percentage", "retry_count", "created_at")
    list_filter = ("feature", "status")
    search_fields = ("user__email", "organization__name", "failure_reason")
    readonly_fields = ("id", "created_at", "updated_at")


@admin.register(AIResult)
class AIResultAdmin(admin.ModelAdmin):
    list_display = ("job", "request", "result_type", "created_at")
    search_fields = ("summary",)
    readonly_fields = ("id", "content", "metadata", "created_at", "updated_at")


@admin.register(AIModerationResult)
class AIModerationResultAdmin(admin.ModelAdmin):
    list_display = ("stage", "is_allowed", "severity", "user", "organization", "created_at")
    list_filter = ("stage", "is_allowed", "severity")
    search_fields = ("user__email", "organization__name")
    readonly_fields = ("id", "categories", "pii_findings", "injection_findings", "raw_result", "created_at", "updated_at")


@admin.register(AIFeatureFlag)
class AIFeatureFlagAdmin(admin.ModelAdmin):
    list_display = ("feature", "is_enabled", "organization", "user", "reason", "created_at")
    list_filter = ("feature", "is_enabled")
    search_fields = ("organization__name", "user__email", "reason")
    readonly_fields = ("id", "created_at", "updated_at")


@admin.register(VectorCollection)
class VectorCollectionAdmin(admin.ModelAdmin):
    list_display = ("name", "organization", "embedding_model", "dimensions", "created_at")
    search_fields = ("name", "organization__name")
    readonly_fields = ("id", "created_at", "updated_at")


@admin.register(VectorDocument)
class VectorDocumentAdmin(admin.ModelAdmin):
    list_display = ("collection", "document_type", "object_id", "title", "created_at")
    list_filter = ("document_type",)
    search_fields = ("title", "object_id", "redacted_content")
    readonly_fields = ("id", "embedding", "metadata", "created_at", "updated_at")


@admin.register(KnowledgeCollection)
class KnowledgeCollectionAdmin(admin.ModelAdmin):
    list_display = ("name", "collection_type", "organization", "embedding_version", "vector_backend", "is_active", "created_at")
    list_filter = ("collection_type", "vector_backend", "is_active")
    search_fields = ("name", "organization__name")
    readonly_fields = ("id", "created_at", "updated_at")


@admin.register(KnowledgeDocument)
class KnowledgeDocumentAdmin(admin.ModelAdmin):
    list_display = ("title", "collection", "source_type", "source_id", "visibility", "index_status", "last_indexed_at")
    list_filter = ("source_type", "visibility", "index_status", "embedding_version")
    search_fields = ("title", "source_id", "redacted_text")
    readonly_fields = ("id", "checksum", "redacted_text", "metadata", "created_at", "updated_at")


@admin.register(KnowledgeChunk)
class KnowledgeChunkAdmin(admin.ModelAdmin):
    list_display = ("document", "chunk_index", "token_count", "created_at")
    search_fields = ("text", "document__title")
    readonly_fields = ("id", "embedding", "metadata", "created_at", "updated_at")


@admin.register(RetrievalEvent)
class RetrievalEventAdmin(admin.ModelAdmin):
    list_display = ("feature", "organization", "user", "search_type", "result_count", "confidence", "latency_ms", "created_at")
    list_filter = ("feature", "search_type", "cache_hit")
    search_fields = ("query", "user__email", "organization__name")
    readonly_fields = ("id", "sources", "missing_knowledge", "metadata", "created_at", "updated_at")


@admin.register(RetrievalEvaluationDataset)
class RetrievalEvaluationDatasetAdmin(admin.ModelAdmin):
    list_display = ("name", "feature", "minimum_pass_rate", "is_active", "created_at")
    list_filter = ("feature", "is_active")
    search_fields = ("name", "description")
    readonly_fields = ("id", "created_at", "updated_at")


@admin.register(RetrievalEvaluationRun)
class RetrievalEvaluationRunAdmin(admin.ModelAdmin):
    list_display = ("dataset", "status", "total_cases", "passed_cases", "pass_rate", "average_confidence", "created_at")
    list_filter = ("status",)
    readonly_fields = ("id", "report", "failure_reason", "created_at", "updated_at")


@admin.register(RetrievalEvaluationResult)
class RetrievalEvaluationResultAdmin(admin.ModelAdmin):
    list_display = ("run", "passed", "ranking_position", "confidence", "created_at")
    list_filter = ("passed",)
    search_fields = ("query", "expected_document_id", "expected_source_type")
    readonly_fields = ("id", "retrieved_citations", "metadata", "created_at", "updated_at")


@admin.register(AIEvaluationDataset)
class AIEvaluationDatasetAdmin(admin.ModelAdmin):
    list_display = ("name", "feature", "created_at")
    list_filter = ("feature",)
    search_fields = ("name", "description")
    readonly_fields = ("id", "created_at", "updated_at")


@admin.register(AIEvaluationRun)
class AIEvaluationRunAdmin(admin.ModelAdmin):
    list_display = ("dataset", "provider", "status", "average_score", "average_latency_ms", "estimated_cost", "created_at")
    list_filter = ("status", "provider")
    readonly_fields = ("id", "created_at", "updated_at")


@admin.register(AIEvaluationResult)
class AIEvaluationResultAdmin(admin.ModelAdmin):
    list_display = ("run", "score", "manual_score", "latency_ms", "estimated_cost", "created_at")
    search_fields = ("input_text", "expected_output", "actual_output", "hallucination_notes")
    readonly_fields = ("id", "metadata", "created_at", "updated_at")


@admin.register(AIInterviewSession)
class AIInterviewSessionAdmin(admin.ModelAdmin):
    list_display = ("user", "organization", "session_type", "difficulty", "status", "overall_score", "estimated_cost", "created_at")
    list_filter = ("session_type", "difficulty", "status")
    search_fields = ("user__email", "organization__name", "job_title", "industry")
    readonly_fields = ("id", "history", "feedback", "metadata", "created_at", "updated_at")


@admin.register(AIInterviewQuestion)
class AIInterviewQuestionAdmin(admin.ModelAdmin):
    list_display = ("session", "sequence", "skill_area", "created_at")
    search_fields = ("question_text", "skill_area", "session__user__email")
    readonly_fields = ("id", "metadata", "created_at", "updated_at")


@admin.register(AIInterviewAnswerEvaluation)
class AIInterviewAnswerEvaluationAdmin(admin.ModelAdmin):
    list_display = ("session", "question", "overall_score", "clarity", "technical_quality", "created_at")
    list_filter = ("overall_score",)
    search_fields = ("answer_text", "better_answer", "session__user__email")
    readonly_fields = ("id", "strengths", "weaknesses", "tips", "metadata", "created_at", "updated_at")


@admin.register(AIInterviewTemplate)
class AIInterviewTemplateAdmin(admin.ModelAdmin):
    list_display = ("title", "organization", "session_type", "difficulty", "question_count", "is_active")
    list_filter = ("session_type", "difficulty", "is_active")
    search_fields = ("title", "organization__name", "job_title", "industry")
    readonly_fields = ("id", "metadata", "created_at", "updated_at")


@admin.register(AICareerGoal)
class AICareerGoalAdmin(admin.ModelAdmin):
    list_display = ("user", "target_role", "status", "progress_percentage", "created_at")
    list_filter = ("status", "target_country")
    search_fields = ("user__email", "title", "target_role", "target_industry")
    readonly_fields = ("id", "coaching_history", "created_at", "updated_at")


@admin.register(AICareerAssessment)
class AICareerAssessmentAdmin(admin.ModelAdmin):
    list_display = ("user", "goal", "readiness_score", "confidence_score", "estimated_cost", "created_at")
    list_filter = ("created_at",)
    search_fields = ("user__email", "goal__target_role")
    readonly_fields = ("id", "assessment", "created_at", "updated_at")


@admin.register(AICareerRoadmap)
class AICareerRoadmapAdmin(admin.ModelAdmin):
    list_display = ("user", "goal", "horizon", "title", "progress_percentage", "created_at")
    list_filter = ("horizon",)
    search_fields = ("user__email", "title", "goal__target_role")
    readonly_fields = ("id", "roadmap", "milestones", "recommended_courses", "recommended_projects", "created_at", "updated_at")


@admin.register(AICareerSkillGap)
class AICareerSkillGapAdmin(admin.ModelAdmin):
    list_display = ("user", "goal", "comparison_type", "target", "confidence_score", "created_at")
    list_filter = ("comparison_type",)
    search_fields = ("user__email", "target", "goal__target_role")
    readonly_fields = ("id", "missing_skills", "priority_skills", "report", "created_at", "updated_at")


@admin.register(AICareerCoachingSummary)
class AICareerCoachingSummaryAdmin(admin.ModelAdmin):
    list_display = ("user", "goal", "week_start", "confidence_score", "created_at")
    list_filter = ("week_start",)
    search_fields = ("user__email", "summary", "goal__target_role")
    readonly_fields = ("id", "achievements", "missed_goals", "recommended_actions", "upcoming_priorities", "metadata", "created_at", "updated_at")


@admin.register(AIRecruiterReport)
class AIRecruiterReportAdmin(admin.ModelAdmin):
    list_display = ("title", "report_type", "user", "organization", "job", "candidate", "score", "confidence_score", "created_at")
    list_filter = ("report_type", "organization")
    search_fields = ("title", "user__email", "candidate__email", "organization__name", "job__title")
    readonly_fields = ("id", "candidate_ids", "report", "fairness_notes", "disclaimer", "created_at", "updated_at")


@admin.register(AILearningTutorSession)
class AILearningTutorSessionAdmin(admin.ModelAdmin):
    list_display = ("user", "course", "lesson", "mode", "confidence_score", "created_at")
    list_filter = ("mode", "course")
    search_fields = ("user__email", "course__title", "lesson__title", "question", "answer")
    readonly_fields = ("id", "context", "concepts", "created_at", "updated_at")


@admin.register(AILessonIntelligence)
class AILessonIntelligenceAdmin(admin.ModelAdmin):
    list_display = ("lesson", "course", "generated_by", "is_current", "estimated_study_time_minutes", "created_at")
    list_filter = ("is_current", "course")
    search_fields = ("lesson__title", "course__title", "summary")
    readonly_fields = ("id", "key_concepts", "glossary", "important_formulas", "common_mistakes", "prerequisites", "learning_objectives", "created_at", "updated_at")


@admin.register(AIStudyPlan)
class AIStudyPlanAdmin(admin.ModelAdmin):
    list_display = ("user", "title", "cadence", "pace", "available_minutes_per_day", "confidence_score", "created_at")
    list_filter = ("cadence", "pace")
    search_fields = ("user__email", "title")
    readonly_fields = ("id", "plan", "milestones", "weak_concepts", "recommended_lessons", "created_at", "updated_at")


@admin.register(AIGeneratedQuiz)
class AIGeneratedQuizAdmin(admin.ModelAdmin):
    list_display = ("title", "course", "lesson", "difficulty", "question_count", "is_instructor_reviewed", "is_published_to_students", "created_at")
    list_filter = ("difficulty", "is_instructor_reviewed", "is_published_to_students")
    search_fields = ("title", "course__title", "lesson__title")
    readonly_fields = ("id", "learning_objectives", "questions", "created_at", "updated_at")


@admin.register(AIQuizFeedback)
class AIQuizFeedbackAdmin(admin.ModelAdmin):
    list_display = ("user", "course", "quiz_attempt", "confidence_score", "created_at")
    list_filter = ("course",)
    search_fields = ("user__email", "course__title", "explanation")
    readonly_fields = ("id", "correct_reasoning", "weak_topics", "recommended_lessons", "next_actions", "created_at", "updated_at")


@admin.register(AICalibrationReport)
class AICalibrationReportAdmin(admin.ModelAdmin):
    list_display = ("feature", "score_name", "score", "confidence_score", "confidence_level", "created_at")
    list_filter = ("feature", "score_name", "confidence_level")
    search_fields = ("reasoning_summary", "recommended_next_action")
    readonly_fields = ("id", "score_breakdown", "weighting", "evidence", "uncertainty", "missing_information", "limitations", "created_at", "updated_at")


@admin.register(AIFairnessReport)
class AIFairnessReportAdmin(admin.ModelAdmin):
    list_display = ("feature", "organization", "fairness_score", "manual_review_required", "created_at")
    list_filter = ("feature", "manual_review_required")
    search_fields = ("organization__name",)
    readonly_fields = ("id", "bias_flags", "report", "created_at", "updated_at")


@admin.register(AIPrivacyReport)
class AIPrivacyReportAdmin(admin.ModelAdmin):
    list_display = ("feature", "organization", "severity", "redaction_count", "created_at")
    list_filter = ("feature", "severity")
    search_fields = ("organization__name",)
    readonly_fields = ("id", "findings", "policy", "report", "created_at", "updated_at")


@admin.register(AIFeedback)
class AIFeedbackAdmin(admin.ModelAdmin):
    list_display = ("feature", "rating", "user", "organization", "provider", "created_at")
    list_filter = ("feature", "rating", "provider")
    search_fields = ("user__email", "organization__name", "comment")
    readonly_fields = ("id", "metadata", "created_at", "updated_at")


@admin.register(AIResponseCache)
class AIResponseCacheAdmin(admin.ModelAdmin):
    list_display = ("feature", "organization", "provider", "model_name", "hit_count", "expires_at")
    list_filter = ("feature", "provider")
    search_fields = ("cache_key", "redacted_input_hash")
    readonly_fields = ("id", "cache_key", "response_text", "usage", "metadata", "created_at", "updated_at")


@admin.register(AIEvaluationReview)
class AIEvaluationReviewAdmin(admin.ModelAdmin):
    list_display = ("result", "assigned_to", "reviewed_by", "status", "manual_score", "hallucination_flag", "bias_flag", "unsafe_flag")
    list_filter = ("status", "hallucination_flag", "bias_flag", "unsafe_flag", "request_prompt_revision")
    search_fields = ("notes", "assigned_to__email", "reviewed_by__email")
    readonly_fields = ("id", "assigned_at", "reviewed_at", "created_at", "updated_at")


@admin.register(AIRedTeamSuite)
class AIRedTeamSuiteAdmin(admin.ModelAdmin):
    list_display = ("name", "suite_type", "feature", "severity", "is_active", "created_at")
    list_filter = ("suite_type", "feature", "severity", "is_active")
    search_fields = ("name",)
    readonly_fields = ("id", "created_at", "updated_at")


@admin.register(AIRedTeamResult)
class AIRedTeamResultAdmin(admin.ModelAdmin):
    list_display = ("suite", "case_name", "risk_severity", "passed", "created_at")
    list_filter = ("risk_severity", "passed")
    search_fields = ("case_name", "input_text", "mitigation_notes")
    readonly_fields = ("id", "risk_flags", "expected_safe_behavior", "metadata", "created_at", "updated_at")


@admin.register(AIReleaseGate)
class AIReleaseGateAdmin(admin.ModelAdmin):
    list_display = ("change_type", "feature", "target_id", "status", "requested_by", "reviewed_by", "created_at")
    list_filter = ("change_type", "feature", "status")
    search_fields = ("target_id", "requested_by__email", "reviewed_by__email")
    readonly_fields = ("id", "gate_results", "promoted_at", "rolled_back_at", "created_at", "updated_at")


@admin.register(AIChangeHistory)
class AIChangeHistoryAdmin(admin.ModelAdmin):
    list_display = ("change_type", "target_id", "approval_state", "changed_by", "created_at")
    list_filter = ("change_type", "approval_state")
    search_fields = ("target_id", "changed_by__email", "rollback_reason")
    readonly_fields = ("id", "previous_version", "new_version", "metadata", "created_at", "updated_at")


@admin.register(AIComparisonReport)
class AIComparisonReportAdmin(admin.ModelAdmin):
    list_display = ("comparison_type", "feature", "left_label", "right_label", "winner", "created_at")
    list_filter = ("comparison_type", "feature")
    search_fields = ("left_label", "right_label", "winner")
    readonly_fields = ("id", "metrics", "metadata", "created_at", "updated_at")


@admin.register(AIAuditExport)
class AIAuditExportAdmin(admin.ModelAdmin):
    list_display = ("export_type", "file_format", "status", "row_count", "created_by", "created_at")
    list_filter = ("export_type", "file_format", "status")
    search_fields = ("file_name", "created_by__email")
    readonly_fields = ("id", "file", "filters", "failure_reason", "completed_at", "created_at", "updated_at")
