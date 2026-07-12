import json

from django.contrib.auth import get_user_model
from django.db.models import Avg, Count, Q, Sum
from django.http import StreamingHttpResponse
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes, throttle_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.ai_platform.models import (
    AIBudgetPolicy,
    AIAuditExport,
    AICareerGoal,
    AIRecruiterReport,
    AIGeneratedQuiz,
    AILearningTutorSession,
    AILessonIntelligence,
    AIQuizFeedback,
    AIStudyPlan,
    AIComparisonReport,
    AIConversation,
    AIChangeHistory,
    AIEvaluationDataset,
    AIEvaluationReview,
    AIEvaluationResult,
    AIEvaluationRun,
    AICalibrationReport,
    AIFeatureFlag,
    AIFairnessReport,
    AIFeedback,
    AIFeature,
    AIJob,
    AIInterviewQuestion,
    AIInterviewSession,
    AIInterviewTemplate,
    AIModelConfiguration,
    AIProvider,
    AIRequest,
    AIResponseCache,
    AIPromptTemplate,
    AIReleaseGate,
    AIUsage,
    AIRedTeamSuite,
    KnowledgeCollection,
    KnowledgeDocument,
    KnowledgeIndexStatus,
    RetrievalEvaluationDataset,
    RetrievalEvaluationRun,
    RetrievalEvent,
    VectorCollection,
)
from apps.ai_platform.serializers import (
    AIBudgetPolicySerializer,
    AIAuditExportCreateSerializer,
    AIAuditExportSerializer,
    AICareerAssessmentRequestSerializer,
    AICareerAssessmentSerializer,
    AICareerCoachingSummarySerializer,
    AICareerGoalCreateSerializer,
    AICareerGoalSerializer,
    AICareerGoalUpdateSerializer,
    AICareerRoadmapRequestSerializer,
    AICareerRoadmapSerializer,
    AICareerSkillGapRequestSerializer,
    AICareerSkillGapSerializer,
    AICareerWeeklyCoachingRequestSerializer,
    AIRecruiterCandidateAnalysisRequestSerializer,
    AIRecruiterComparisonRequestSerializer,
    AIRecruiterInterviewPlanRequestSerializer,
    AIRecruiterJobAnalysisRequestSerializer,
    AIRecruiterPipelineInsightsRequestSerializer,
    AIRecruiterRankingRequestSerializer,
    AIRecruiterReportSerializer,
    AICourseTutorRequestSerializer,
    AIGeneratedQuizRequestSerializer,
    AIGeneratedQuizSerializer,
    AIInstructorToolRequestSerializer,
    AILearningTutorSessionSerializer,
    AILessonIntelligenceRequestSerializer,
    AILessonIntelligenceSerializer,
    AIQuizFeedbackRequestSerializer,
    AIQuizFeedbackSerializer,
    AIStudyPlanRequestSerializer,
    AIStudyPlanSerializer,
    AIChatRequestSerializer,
    AIComparisonCreateSerializer,
    AIComparisonReportSerializer,
    AIConversationSerializer,
    CostReconciliationSerializer,
    AIEvaluationDatasetSerializer,
    AIEvaluationReviewBulkApproveSerializer,
    AIEvaluationReviewBulkAssignSerializer,
    AIEvaluationReviewActionSerializer,
    AIEvaluationReviewFilterSerializer,
    AIEvaluationReviewSerializer,
    AIEvaluationRunSerializer,
    EvaluationRunFilterSerializer,
    AIFeatureFlagSerializer,
    AIInterviewAnswerEvaluationSerializer,
    AIInterviewAnswerSubmitSerializer,
    AIInterviewQuestionSerializer,
    AIInterviewSessionCreateSerializer,
    AIInterviewSessionSerializer,
    AIInterviewTemplateCreateSerializer,
    AIInterviewTemplateSerializer,
    AIJobCreateSerializer,
    AIJobSerializer,
    AIModelConfigurationSerializer,
    AIProviderSerializer,
    AIChangeHistorySerializer,
    AIReleaseGateActionSerializer,
    AIReleaseGateCreateSerializer,
    AIReleaseGateSerializer,
    AIRequestSerializer,
    AIModerationResultSerializer,
    AIPromptTemplateSerializer,
    AIBiasReportRequestSerializer,
    AICacheSerializer,
    AICalibrationReportSerializer,
    AIExplainScoreSerializer,
    AIFairnessReportSerializer,
    AIFeedbackCreateSerializer,
    AIFeedbackSerializer,
    AIPrivacyReportRequestSerializer,
    AIPrivacyReportSerializer,
    AIRedTeamRunSerializer,
    AIRedTeamResultSerializer,
    AIRedTeamSuiteSerializer,
    AIUsageSerializer,
    ModerationSerializer,
    KnowledgeCollectionSerializer,
    KnowledgeDocumentSerializer,
    KnowledgeReindexSerializer,
    KnowledgeSearchSerializer,
    KnowledgeStatusSerializer,
    RetrievalEventSerializer,
    RetrievalEvaluationDatasetSerializer,
    RetrievalEvaluationRunRequestSerializer,
    RetrievalEvaluationRunSerializer,
    VectorCollectionSerializer,
    VectorIndexSerializer,
    VectorSearchSerializer,
)
from apps.ai_platform.services import AICacheService, AICalibrationService, AICareerCoachService, AIEvaluationOpsService, AIEvaluationService, AIFairnessService, AIFeedbackService, AIInterviewCoachService, AILearningTutorService, AIRecruiterCopilotService, AIModerationService, AIPrivacyService, AIQualityDashboardService, AIReleaseGateService, AIService, AIVectorService, AIContextBuilder, KnowledgeIndexingService, RetrievalEvaluationService, RetrievalService, VectorBackendRegistry
from apps.assessments.models import QuizAttempt
from apps.courses.models import Course, Lesson
from apps.jobs.models import JobListing
from apps.organizations.models import Organization
from common.exceptions import PermissionError
from common.permission_service import PermissionService
from common.throttles import AIRateThrottle


User = get_user_model()


def _organization_for_user(user, organization_id):
    if not organization_id:
        return None
    organization = get_object_or_404(Organization, id=organization_id)
    if not PermissionService.can_view_organization(user, organization):
        raise PermissionError("You cannot access AI data for this organization.")
    return organization


def _require_ai_admin(user):
    if not PermissionService.is_platform_admin(user):
        raise PermissionError("AI administration requires platform admin access.")


def _get_interview_session(user, session_id):
    session = get_object_or_404(
        AIInterviewSession.objects.select_related("organization", "user", "provider", "model_configuration").prefetch_related("questions", "evaluations__question"),
        id=session_id,
    )
    if PermissionService.is_platform_admin(user) or session.user_id == user.id:
        return session
    if session.organization and PermissionService.can_view_organization(user, session.organization):
        return session
    raise PermissionError("You cannot access this interview session.")


def _career_goal_for_user(user, goal_id):
    if not goal_id:
        return None
    goal = get_object_or_404(AICareerGoal, id=goal_id)
    if goal.user_id == user.id or PermissionService.is_platform_admin(user):
        return goal
    raise PermissionError("You cannot access this career goal.")


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def ai_overview(request):
    usage = AIUsage.objects.filter(user=request.user)
    return Response({
        "providers_configured": AIProvider.objects.filter(is_active=True).count(),
        "requests": AIRequest.objects.filter(user=request.user).count(),
        "conversations": AIConversation.objects.filter(user=request.user, is_archived=False).count(),
        "usage": {
            "requests": usage.aggregate(total=Sum("request_count"))["total"] or 0,
            "tokens": usage.aggregate(total=Sum("total_tokens"))["total"] or 0,
            "estimated_cost": str(usage.aggregate(total=Sum("estimated_cost"))["total"] or 0),
        },
        "features": [choice[0] for choice in AIFeature.choices],
    })


@api_view(["POST"])
@permission_classes([IsAuthenticated])
@throttle_classes([AIRateThrottle])
def ai_chat(request):
    serializer = AIChatRequestSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    organization = _organization_for_user(request.user, serializer.validated_data.get("organization_id"))
    if serializer.validated_data.get("stream"):
        def event_stream():
            for event in AIService.stream_text(
                user=request.user,
                organization=organization,
                feature=serializer.validated_data["feature"],
                input_text=serializer.validated_data["input_text"],
                variables=serializer.validated_data["variables"],
                provider_type=serializer.validated_data["provider_type"],
                model_name=serializer.validated_data["model_name"],
                locale=serializer.validated_data["locale"],
            ):
                yield f"data: {json.dumps(event)}\n\n"

        response = StreamingHttpResponse(event_stream(), content_type="text/event-stream")
        response["Cache-Control"] = "no-cache"
        response["X-Accel-Buffering"] = "no"
        return response
    conversation = None
    if serializer.validated_data.get("conversation_id"):
        conversation = get_object_or_404(AIConversation, id=serializer.validated_data["conversation_id"], user=request.user)
    elif serializer.validated_data["feature"] == AIFeature.CHAT:
        conversation = AIConversation.objects.create(user=request.user, organization=organization, feature=serializer.validated_data["feature"], title="AI chat")
    result = AIService.generate_text(
        user=request.user,
        organization=organization,
        conversation=conversation,
        feature=serializer.validated_data["feature"],
        input_text=serializer.validated_data["input_text"],
        variables=serializer.validated_data["variables"],
        provider_type=serializer.validated_data["provider_type"],
        model_name=serializer.validated_data["model_name"],
        locale=serializer.validated_data["locale"],
    )
    return Response({
        "request": AIRequestSerializer(result["request"]).data,
        "conversation": AIConversationSerializer(conversation).data if conversation else None,
        "text": result["text"],
        "usage": result["usage"],
    })


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def cancel_generation(request, request_id):
    ai_request = AIService.cancel_request(user=request.user, request_id=request_id)
    return Response(AIRequestSerializer(ai_request).data)


def _feature_endpoint(request, feature):
    payload = request.data.copy()
    payload["feature"] = feature
    serializer = AIChatRequestSerializer(data=payload)
    serializer.is_valid(raise_exception=True)
    organization = _organization_for_user(request.user, serializer.validated_data.get("organization_id"))
    result = AIService.generate_text(
        user=request.user,
        organization=organization,
        feature=feature,
        input_text=serializer.validated_data["input_text"],
        variables=serializer.validated_data["variables"],
        locale=serializer.validated_data["locale"],
    )
    return Response({"request": AIRequestSerializer(result["request"]).data, "text": result["text"], "usage": result["usage"]})


@api_view(["POST"])
@permission_classes([IsAuthenticated])
@throttle_classes([AIRateThrottle])
def resume_review(request):
    return _feature_endpoint(request, AIFeature.RESUME_REVIEW)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
@throttle_classes([AIRateThrottle])
def portfolio_review(request):
    return _feature_endpoint(request, AIFeature.PORTFOLIO_REVIEW)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
@throttle_classes([AIRateThrottle])
def career_advice(request):
    return _feature_endpoint(request, AIFeature.CAREER_ADVICE)


@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
@throttle_classes([AIRateThrottle])
def career_goals(request):
    if request.method == "GET":
        goals = AICareerGoal.objects.filter(user=request.user).order_by("-created_at")
        return Response(AICareerGoalSerializer(goals, many=True).data)
    serializer = AICareerGoalCreateSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    goal = AICareerCoachService.create_goal(user=request.user, **serializer.validated_data)
    return Response(AICareerGoalSerializer(goal).data, status=status.HTTP_201_CREATED)


@api_view(["PATCH"])
@permission_classes([IsAuthenticated])
def career_goal_detail(request, goal_id):
    goal = _career_goal_for_user(request.user, goal_id)
    serializer = AICareerGoalUpdateSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    goal = AICareerCoachService.update_goal(user=request.user, goal=goal, **serializer.validated_data)
    return Response(AICareerGoalSerializer(goal).data)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
@throttle_classes([AIRateThrottle])
def career_assessment(request):
    serializer = AICareerAssessmentRequestSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    goal = _career_goal_for_user(request.user, serializer.validated_data.get("goal_id"))
    assessment = AICareerCoachService.assess(user=request.user, goal=goal, payload=serializer.validated_data)
    return Response(AICareerAssessmentSerializer(assessment).data, status=status.HTTP_201_CREATED)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
@throttle_classes([AIRateThrottle])
def career_roadmap(request):
    serializer = AICareerRoadmapRequestSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    goal = _career_goal_for_user(request.user, serializer.validated_data.get("goal_id"))
    roadmap = AICareerCoachService.generate_roadmap(user=request.user, goal=goal, horizon=serializer.validated_data["horizon"], payload=serializer.validated_data)
    return Response(AICareerRoadmapSerializer(roadmap).data, status=status.HTTP_201_CREATED)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
@throttle_classes([AIRateThrottle])
def career_skill_gap(request):
    serializer = AICareerSkillGapRequestSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    goal = _career_goal_for_user(request.user, serializer.validated_data.get("goal_id"))
    report = AICareerCoachService.skill_gap(user=request.user, goal=goal, payload=serializer.validated_data)
    return Response(AICareerSkillGapSerializer(report).data, status=status.HTTP_201_CREATED)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
@throttle_classes([AIRateThrottle])
def career_learning_recommendations(request):
    serializer = AICareerSkillGapRequestSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    goal = _career_goal_for_user(request.user, serializer.validated_data.get("goal_id"))
    return Response(AICareerCoachService.learning_recommendations(user=request.user, goal=goal, payload=serializer.validated_data))


@api_view(["POST"])
@permission_classes([IsAuthenticated])
@throttle_classes([AIRateThrottle])
def career_weekly_coaching(request):
    serializer = AICareerWeeklyCoachingRequestSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    goal = _career_goal_for_user(request.user, serializer.validated_data.get("goal_id"))
    summary = AICareerCoachService.weekly_coaching(user=request.user, goal=goal, payload=serializer.validated_data)
    return Response(AICareerCoachingSummarySerializer(summary).data, status=status.HTTP_201_CREATED)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def career_history(request):
    records = AICareerCoachService.history(user=request.user)
    return Response({
        "assessments": AICareerAssessmentSerializer(records["assessments"], many=True).data,
        "roadmaps": AICareerRoadmapSerializer(records["roadmaps"], many=True).data,
        "skill_gaps": AICareerSkillGapSerializer(records["skill_gaps"], many=True).data,
        "coaching": AICareerCoachingSummarySerializer(records["coaching"], many=True).data,
    })


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def career_analytics(request):
    return Response(AICareerCoachService.analytics(user=request.user))


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def career_recruiter_summary(request, candidate_id):
    candidate = get_object_or_404(User, id=candidate_id)
    return Response(AICareerCoachService.recruiter_summary(recruiter=request.user, candidate=candidate))


def _job_for_recruiter(user, job_id):
    if not job_id:
        return None
    job = get_object_or_404(JobListing.objects.select_related("organization", "posted_by"), id=job_id)
    if not PermissionService.can_manage_job(user, job):
        raise PermissionError("You cannot access recruiter AI for this job.")
    return job


def _candidates_by_ids(candidate_ids):
    candidates = {str(candidate.id): candidate for candidate in User.objects.filter(id__in=candidate_ids)}
    ordered = []
    missing = []
    for candidate_id in candidate_ids:
        candidate = candidates.get(str(candidate_id))
        if candidate:
            ordered.append(candidate)
        else:
            missing.append(str(candidate_id))
    if missing:
        raise PermissionError(f"Candidate not found or unavailable: {', '.join(missing)}")
    return ordered


@api_view(["POST"])
@permission_classes([IsAuthenticated])
@throttle_classes([AIRateThrottle])
def recruiter_candidate_analysis(request):
    serializer = AIRecruiterCandidateAnalysisRequestSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    organization = _organization_for_user(request.user, serializer.validated_data.get("organization_id"))
    job = _job_for_recruiter(request.user, serializer.validated_data.get("job_id"))
    candidate = get_object_or_404(User, id=serializer.validated_data["candidate_id"])
    report = AIRecruiterCopilotService.analyze_candidate(user=request.user, candidate=candidate, organization=organization or getattr(job, "organization", None), job=job)
    return Response(AIRecruiterReportSerializer(report).data, status=status.HTTP_201_CREATED)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
@throttle_classes([AIRateThrottle])
def recruiter_candidate_ranking(request):
    serializer = AIRecruiterRankingRequestSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    job = _job_for_recruiter(request.user, serializer.validated_data["job_id"])
    candidates = _candidates_by_ids(serializer.validated_data["candidate_ids"])
    report = AIRecruiterCopilotService.rank_candidates(user=request.user, job=job, candidates=candidates, sort_by=serializer.validated_data["sort_by"])
    return Response(AIRecruiterReportSerializer(report).data, status=status.HTTP_201_CREATED)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
@throttle_classes([AIRateThrottle])
def recruiter_candidate_comparison(request):
    serializer = AIRecruiterComparisonRequestSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    organization = _organization_for_user(request.user, serializer.validated_data.get("organization_id"))
    job = _job_for_recruiter(request.user, serializer.validated_data.get("job_id"))
    candidates = _candidates_by_ids(serializer.validated_data["candidate_ids"])
    report = AIRecruiterCopilotService.compare_candidates(user=request.user, candidates=candidates, organization=organization or getattr(job, "organization", None), job=job)
    return Response(AIRecruiterReportSerializer(report).data, status=status.HTTP_201_CREATED)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
@throttle_classes([AIRateThrottle])
def recruiter_job_analysis(request):
    serializer = AIRecruiterJobAnalysisRequestSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    job = _job_for_recruiter(request.user, serializer.validated_data.get("job_id"))
    report = AIRecruiterCopilotService.analyze_job(
        user=request.user,
        job=job,
        title=serializer.validated_data.get("title", ""),
        description=serializer.validated_data.get("description", ""),
    )
    return Response(AIRecruiterReportSerializer(report).data, status=status.HTTP_201_CREATED)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
@throttle_classes([AIRateThrottle])
def recruiter_interview_plan(request):
    serializer = AIRecruiterInterviewPlanRequestSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    organization = _organization_for_user(request.user, serializer.validated_data.get("organization_id"))
    job = _job_for_recruiter(request.user, serializer.validated_data.get("job_id"))
    candidate = get_object_or_404(User, id=serializer.validated_data["candidate_id"])
    report = AIRecruiterCopilotService.interview_plan(user=request.user, candidate=candidate, organization=organization or getattr(job, "organization", None), job=job)
    return Response(AIRecruiterReportSerializer(report).data, status=status.HTTP_201_CREATED)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
@throttle_classes([AIRateThrottle])
def recruiter_pipeline_insights(request):
    serializer = AIRecruiterPipelineInsightsRequestSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    organization = _organization_for_user(request.user, serializer.validated_data["organization_id"])
    job = _job_for_recruiter(request.user, serializer.validated_data.get("job_id"))
    report = AIRecruiterCopilotService.pipeline_insights(user=request.user, organization=organization, job=job)
    return Response(AIRecruiterReportSerializer(report).data, status=status.HTTP_201_CREATED)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def recruiter_history(request):
    reports = AIRecruiterCopilotService.history(user=request.user)
    return Response(AIRecruiterReportSerializer(reports, many=True).data)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def recruiter_analytics(request):
    return Response(AIRecruiterCopilotService.analytics(user=request.user))


@api_view(["POST"])
@permission_classes([IsAuthenticated])
@throttle_classes([AIRateThrottle])
def learning_recommendations(request):
    return _feature_endpoint(request, AIFeature.LEARNING_RECOMMENDATIONS)


def _course_for_learning(course_id):
    return get_object_or_404(Course.objects.select_related("instructor").prefetch_related("lessons"), id=course_id, deleted_at=None)


def _lesson_for_learning(course, lesson_id):
    if not lesson_id:
        return None
    return get_object_or_404(Lesson.objects.select_related("course"), id=lesson_id, course=course, deleted_at=None)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
@throttle_classes([AIRateThrottle])
def learning_course_tutor(request):
    serializer = AICourseTutorRequestSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    course = _course_for_learning(serializer.validated_data["course_id"])
    lesson = _lesson_for_learning(course, serializer.validated_data.get("lesson_id"))
    session = AILearningTutorService.tutor(
        user=request.user,
        course=course,
        lesson=lesson,
        question=serializer.validated_data.get("question", ""),
        mode=serializer.validated_data["mode"],
    )
    return Response(AILearningTutorSessionSerializer(session).data, status=status.HTTP_201_CREATED)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
@throttle_classes([AIRateThrottle])
def learning_lesson_summary(request):
    serializer = AILessonIntelligenceRequestSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    course = _course_for_learning(serializer.validated_data["course_id"])
    lesson = _lesson_for_learning(course, serializer.validated_data["lesson_id"])
    report = AILearningTutorService.lesson_intelligence(user=request.user, lesson=lesson, regenerate=serializer.validated_data["regenerate"])
    return Response(AILessonIntelligenceSerializer(report).data, status=status.HTTP_201_CREATED)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
@throttle_classes([AIRateThrottle])
def learning_study_plan(request):
    serializer = AIStudyPlanRequestSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    goal = _career_goal_for_user(request.user, serializer.validated_data.get("career_goal_id"))
    plan = AILearningTutorService.study_plan(user=request.user, career_goal=goal, **{key: value for key, value in serializer.validated_data.items() if key != "career_goal_id"})
    return Response(AIStudyPlanSerializer(plan).data, status=status.HTTP_201_CREATED)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
@throttle_classes([AIRateThrottle])
def learning_quiz_generation(request):
    serializer = AIGeneratedQuizRequestSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    course = _course_for_learning(serializer.validated_data["course_id"])
    lesson = _lesson_for_learning(course, serializer.validated_data.get("lesson_id"))
    quiz = AILearningTutorService.generate_quiz(
        user=request.user,
        course=course,
        lesson=lesson,
        difficulty=serializer.validated_data["difficulty"],
        number_of_questions=serializer.validated_data["number_of_questions"],
        learning_objectives=serializer.validated_data["learning_objectives"],
        include_coding_foundation=serializer.validated_data["include_coding_foundation"],
    )
    return Response(AIGeneratedQuizSerializer(quiz).data, status=status.HTTP_201_CREATED)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
@throttle_classes([AIRateThrottle])
def learning_quiz_feedback(request):
    serializer = AIQuizFeedbackRequestSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    course = _course_for_learning(serializer.validated_data["course_id"])
    attempt = None
    if serializer.validated_data.get("attempt_id"):
        attempt = get_object_or_404(QuizAttempt.objects.select_related("enrollment", "enrollment__course", "enrollment__user"), id=serializer.validated_data["attempt_id"], enrollment__course=course)
    feedback = AILearningTutorService.quiz_feedback(user=request.user, course=course, attempt=attempt)
    return Response(AIQuizFeedbackSerializer(feedback).data, status=status.HTTP_201_CREATED)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
@throttle_classes([AIRateThrottle])
def learning_instructor_tools(request):
    serializer = AIInstructorToolRequestSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    course = _course_for_learning(serializer.validated_data["course_id"])
    lesson = _lesson_for_learning(course, serializer.validated_data.get("lesson_id"))
    result = AILearningTutorService.instructor_tool(
        user=request.user,
        course=course,
        lesson=lesson,
        tool=serializer.validated_data["tool"],
        difficulty=serializer.validated_data["difficulty"],
        number_of_questions=serializer.validated_data["number_of_questions"],
    )
    if "quiz" in result:
        return Response({"quiz": AIGeneratedQuizSerializer(result["quiz"]).data}, status=status.HTTP_201_CREATED)
    if "lesson_intelligence" in result:
        return Response({"lesson_intelligence": AILessonIntelligenceSerializer(result["lesson_intelligence"]).data}, status=status.HTTP_201_CREATED)
    return Response(result, status=status.HTTP_201_CREATED)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def learning_history(request):
    records = AILearningTutorService.history(user=request.user)
    return Response({
        "tutor_sessions": AILearningTutorSessionSerializer(records["tutor_sessions"], many=True).data,
        "study_plans": AIStudyPlanSerializer(records["study_plans"], many=True).data,
        "quiz_feedback": AIQuizFeedbackSerializer(records["quiz_feedback"], many=True).data,
    })


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def learning_analytics(request):
    return Response(AILearningTutorService.analytics(user=request.user))


@api_view(["POST"])
@permission_classes([IsAuthenticated])
@throttle_classes([AIRateThrottle])
def job_matching(request):
    return _feature_endpoint(request, AIFeature.JOB_MATCHING)


@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
@throttle_classes([AIRateThrottle])
def interview_sessions(request):
    if request.method == "GET":
        sessions = AIInterviewSession.objects.filter(user=request.user).select_related("organization", "provider", "model_configuration").order_by("-created_at")[:100]
        return Response(AIInterviewSessionSerializer(sessions, many=True).data)
    serializer = AIInterviewSessionCreateSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    organization = _organization_for_user(request.user, serializer.validated_data.get("organization_id"))
    payload = {**serializer.validated_data, "organization": organization}
    session = AIInterviewCoachService.start_session(user=request.user, payload=payload)
    return Response(AIInterviewSessionSerializer(session).data, status=status.HTTP_201_CREATED)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def interview_session_detail(request, session_id):
    return Response(AIInterviewSessionSerializer(_get_interview_session(request.user, session_id)).data)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
@throttle_classes([AIRateThrottle])
def interview_next_question(request, session_id):
    session = _get_interview_session(request.user, session_id)
    if request.query_params.get("stream") == "true" or request.data.get("stream") is True:
        def event_stream():
            question = AIInterviewCoachService.next_question(user=request.user, session=session)
            yield f"data: {json.dumps({'event': 'question', 'question': AIInterviewQuestionSerializer(question).data})}\n\n"
            yield f"data: {json.dumps({'event': 'done', 'session_id': str(session.id)})}\n\n"

        response = StreamingHttpResponse(event_stream(), content_type="text/event-stream")
        response["Cache-Control"] = "no-cache"
        response["X-Accel-Buffering"] = "no"
        return response
    question = AIInterviewCoachService.next_question(user=request.user, session=session)
    return Response(AIInterviewQuestionSerializer(question).data, status=status.HTTP_201_CREATED)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
@throttle_classes([AIRateThrottle])
def interview_submit_answer(request, session_id):
    session = _get_interview_session(request.user, session_id)
    serializer = AIInterviewAnswerSubmitSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    question = get_object_or_404(AIInterviewQuestion, id=serializer.validated_data["question_id"], session=session)
    evaluation = AIInterviewCoachService.submit_answer(user=request.user, question=question, answer_text=serializer.validated_data["answer_text"])
    return Response(AIInterviewAnswerEvaluationSerializer(evaluation).data, status=status.HTTP_201_CREATED)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
@throttle_classes([AIRateThrottle])
def interview_evaluate_answer(request, session_id):
    return interview_submit_answer(request, session_id)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def interview_pause(request, session_id):
    session = AIInterviewCoachService.set_status(user=request.user, session=_get_interview_session(request.user, session_id), status_value="paused")
    return Response(AIInterviewSessionSerializer(session).data)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def interview_resume(request, session_id):
    session = AIInterviewCoachService.set_status(user=request.user, session=_get_interview_session(request.user, session_id), status_value="active")
    return Response(AIInterviewSessionSerializer(session).data)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def interview_cancel(request, session_id):
    session = AIInterviewCoachService.set_status(user=request.user, session=_get_interview_session(request.user, session_id), status_value="cancelled")
    return Response(AIInterviewSessionSerializer(session).data)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
@throttle_classes([AIRateThrottle])
def interview_finish(request, session_id):
    session = AIInterviewCoachService.finish_session(user=request.user, session=_get_interview_session(request.user, session_id))
    return Response(AIInterviewSessionSerializer(session).data)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def interview_analytics(request):
    organization = _organization_for_user(request.user, request.query_params.get("organization_id"))
    return Response(AIInterviewCoachService.analytics(user=request.user, organization=organization))


@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def interview_templates(request):
    organization = _organization_for_user(request.user, request.data.get("organization_id") if request.method == "POST" else request.query_params.get("organization_id"))
    if request.method == "GET":
        templates = AIInterviewTemplate.objects.filter(is_active=True)
        if organization:
            templates = templates.filter(organization=organization)
        else:
            templates = templates.filter(organization__isnull=True)
        return Response(AIInterviewTemplateSerializer(templates.order_by("title"), many=True).data)
    serializer = AIInterviewTemplateCreateSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    organization = _organization_for_user(request.user, serializer.validated_data.get("organization_id"))
    payload = {key: value for key, value in serializer.validated_data.items() if key != "organization_id"}
    template = AIInterviewCoachService.create_template(user=request.user, organization=organization, payload=payload)
    return Response(AIInterviewTemplateSerializer(template).data, status=status.HTTP_201_CREATED)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def history(request):
    requests = AIRequest.objects.filter(user=request.user).select_related("provider").order_by("-created_at")[:100]
    return Response(AIRequestSerializer(requests, many=True).data)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def conversations(request):
    items = AIConversation.objects.filter(user=request.user).order_by("-updated_at")[:50]
    return Response(AIConversationSerializer(items, many=True).data)


@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def jobs(request):
    if request.method == "GET":
        items = AIJob.objects.filter(user=request.user).order_by("-created_at")[:50]
        return Response(AIJobSerializer(items, many=True).data)
    serializer = AIJobCreateSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    organization = _organization_for_user(request.user, serializer.validated_data.get("organization_id"))
    job = AIService.create_job(
        user=request.user,
        organization=organization,
        feature=serializer.validated_data["feature"],
        input_payload=serializer.validated_data["input_payload"],
    )
    return Response(AIJobSerializer(job).data, status=status.HTTP_202_ACCEPTED)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def settings_view(request):
    providers = AIProvider.objects.filter(is_active=True).order_by("priority")
    models = AIModelConfiguration.objects.filter(is_active=True).select_related("provider")
    return Response({
        "providers": AIProviderSerializer(providers, many=True).data,
        "models": AIModelConfigurationSerializer(models, many=True).data,
        "features": [choice[0] for choice in AIFeature.choices],
    })


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def provider_status(request):
    providers = AIProvider.objects.order_by("priority", "name")
    return Response({
        "providers": AIProviderSerializer(providers, many=True).data,
        "comparison": list(
            AIRequest.objects.values("provider__provider_type")
            .annotate(total=Count("id"), avg_latency_ms=Avg("latency_ms"))
            .order_by("provider__provider_type")
        ),
    })


@api_view(["POST"])
@permission_classes([IsAuthenticated])
@throttle_classes([AIRateThrottle])
def moderate(request):
    serializer = ModerationSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    organization = _organization_for_user(request.user, serializer.validated_data.get("organization_id"))
    result = AIModerationService.moderate_text(text=serializer.validated_data["text"], stage=serializer.validated_data["stage"], user=request.user, organization=organization)
    return Response(AIModerationResultSerializer(result).data)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def vector_index(request):
    serializer = VectorIndexSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    organization = _organization_for_user(request.user, serializer.validated_data.get("organization_id"))
    collection = AIVectorService.get_collection(serializer.validated_data["collection"], organization=organization)
    document = AIVectorService.index_document(
        collection=collection,
        document_type=serializer.validated_data["document_type"],
        object_id=serializer.validated_data["object_id"],
        title=serializer.validated_data["title"],
        content=serializer.validated_data["content"],
    )
    return Response({"id": str(document.id), "collection": collection.name, "document_type": document.document_type, "title": document.title})


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def vector_search(request):
    serializer = VectorSearchSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    organization = _organization_for_user(request.user, serializer.validated_data.get("organization_id"))
    collection = get_object_or_404(VectorCollection, name=serializer.validated_data["collection"], organization=organization)
    results = AIVectorService.search(
        collection=collection,
        query=serializer.validated_data["query"],
        document_type=serializer.validated_data["document_type"],
        limit=serializer.validated_data["limit"],
    )
    return Response([
        {
            "score": item["score"],
            "document": {
                "id": str(item["document"].id),
                "document_type": item["document"].document_type,
                "object_id": item["document"].object_id,
                "title": item["document"].title,
                "content": item["document"].redacted_content,
            },
        }
        for item in results
    ])


@api_view(["POST"])
@permission_classes([IsAuthenticated])
@throttle_classes([AIRateThrottle])
def knowledge_search(request):
    serializer = KnowledgeSearchSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    organization = _organization_for_user(request.user, serializer.validated_data.get("organization_id"))
    result = RetrievalService.search(
        user=request.user,
        query=serializer.validated_data["query"],
        feature=serializer.validated_data["feature"],
        organization=organization,
        collection_types=serializer.validated_data.get("collection_types") or [],
        search_type=serializer.validated_data["search_type"],
        limit=serializer.validated_data["limit"],
        include_private=serializer.validated_data["include_private"],
        metadata=serializer.validated_data.get("metadata") or {},
    )
    return Response(result)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def knowledge_reindex(request):
    serializer = KnowledgeReindexSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    organization = _organization_for_user(request.user, serializer.validated_data.get("organization_id"))
    if organization and not PermissionService.can_manage_organization(request.user, organization):
        raise PermissionError("You cannot reindex this organization's knowledge.")
    if not organization and not PermissionService.is_platform_admin(request.user):
        raise PermissionError("Knowledge reindexing requires platform admin access.")
    documents = KnowledgeIndexingService.reindex_from_payload(payload=serializer.validated_data, user=request.user, organization=organization)
    return Response({"indexed": KnowledgeDocumentSerializer(documents, many=True).data}, status=status.HTTP_201_CREATED)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def knowledge_retrieval(request):
    serializer = KnowledgeSearchSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    organization = _organization_for_user(request.user, serializer.validated_data.get("organization_id"))
    context = AIContextBuilder.build(
        user=request.user,
        feature=serializer.validated_data["feature"],
        input_text=serializer.validated_data["query"],
        organization=organization,
        metadata={
            "collection_types": serializer.validated_data.get("collection_types") or [],
            "search_type": serializer.validated_data["search_type"],
            "context_limit": serializer.validated_data["limit"],
            "include_private_context": serializer.validated_data["include_private"],
            **(serializer.validated_data.get("metadata") or {}),
        },
    )
    return Response(context)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def knowledge_citation_preview(request):
    serializer = KnowledgeSearchSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    organization = _organization_for_user(request.user, serializer.validated_data.get("organization_id"))
    result = RetrievalService.search(
        user=request.user,
        query=serializer.validated_data["query"],
        feature=serializer.validated_data["feature"],
        organization=organization,
        collection_types=serializer.validated_data.get("collection_types") or [],
        search_type=serializer.validated_data["search_type"],
        limit=serializer.validated_data["limit"],
        include_private=serializer.validated_data["include_private"],
    )
    return Response({"citations": result["citations"], "confidence": result["confidence"], "missing_knowledge": result["missing_knowledge"]})


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def knowledge_index_status(request):
    serializer = KnowledgeStatusSerializer(data=request.query_params)
    serializer.is_valid(raise_exception=True)
    organization = _organization_for_user(request.user, serializer.validated_data.get("organization_id"))
    collections = KnowledgeCollection.objects.annotate(document_count=Count("documents"), chunk_count=Count("documents__chunks")).order_by("collection_type", "name")
    if organization:
        collections = collections.filter(organization=organization)
    elif not PermissionService.is_platform_admin(request.user):
        collections = collections.filter(organization__isnull=True)
    if serializer.validated_data.get("collection_type"):
        collections = collections.filter(collection_type=serializer.validated_data["collection_type"])
    documents = KnowledgeDocument.objects.all()
    if organization:
        documents = documents.filter(organization=organization)
    elif not PermissionService.is_platform_admin(request.user):
        documents = documents.filter(organization__isnull=True)
    status_counts = list(documents.values("index_status").annotate(total=Count("id")).order_by("index_status"))
    stale_documents = KnowledgeDocumentSerializer(documents.filter(index_status=KnowledgeIndexStatus.STALE).order_by("-updated_at")[:20], many=True).data
    failed_documents = KnowledgeDocumentSerializer(documents.filter(index_status=KnowledgeIndexStatus.FAILED).order_by("-updated_at")[:20], many=True).data
    freshness = documents.aggregate(avg_freshness=Avg("freshness_score"), stale=Count("id", filter=Q(index_status=KnowledgeIndexStatus.STALE)), failed=Count("id", filter=Q(index_status=KnowledgeIndexStatus.FAILED)))
    privacy_summary = {
        "public_documents": documents.filter(visibility="public").count(),
        "organization_documents": documents.filter(visibility="organization").count(),
        "private_documents": documents.filter(visibility="private").count(),
        "private_without_owner": documents.filter(visibility="private", owner__isnull=True).count(),
        "organization_scope_missing": documents.filter(visibility="organization", organization__isnull=True).count(),
        "safe": not documents.filter(Q(visibility="private", owner__isnull=True) | Q(visibility="organization", organization__isnull=True)).exists(),
    }
    return Response({
        "collections": KnowledgeCollectionSerializer(collections, many=True).data,
        "status_counts": status_counts,
        "freshness": freshness,
        "privacy_summary": privacy_summary,
        "stale_documents": stale_documents,
        "failed_documents": failed_documents,
        "vector_backend": VectorBackendRegistry.health_check(),
    })


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def knowledge_embedding_status(request):
    serializer = KnowledgeStatusSerializer(data=request.query_params)
    serializer.is_valid(raise_exception=True)
    organization = _organization_for_user(request.user, serializer.validated_data.get("organization_id"))
    documents = KnowledgeDocument.objects.all()
    if organization:
        documents = documents.filter(organization=organization)
    elif not PermissionService.is_platform_admin(request.user):
        documents = documents.filter(organization__isnull=True)
    by_version = list(documents.values("embedding_version", "index_status").annotate(total=Count("id")).order_by("embedding_version", "index_status"))
    recent_events = RetrievalEvent.objects.order_by("-created_at")[:20]
    return Response({"embedding_versions": by_version, "recent_retrievals": RetrievalEventSerializer(recent_events, many=True).data})


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def knowledge_vector_health(request):
    _require_ai_admin(request.user)
    backend = request.query_params.get("backend", "")
    return Response(VectorBackendRegistry.health_check(backend))


@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def retrieval_evaluation_datasets(request):
    _require_ai_admin(request.user)
    if request.method == "GET":
        datasets = RetrievalEvaluationDataset.objects.order_by("name")
        return Response(RetrievalEvaluationDatasetSerializer(datasets, many=True).data)
    serializer = RetrievalEvaluationDatasetSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    dataset = serializer.save()
    return Response(RetrievalEvaluationDatasetSerializer(dataset).data, status=status.HTTP_201_CREATED)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def run_retrieval_evaluation(request):
    _require_ai_admin(request.user)
    serializer = RetrievalEvaluationRunRequestSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    dataset = get_object_or_404(RetrievalEvaluationDataset, id=serializer.validated_data["dataset_id"])
    result = RetrievalEvaluationService.run_dataset(dataset=dataset, user=request.user)
    return Response({"run": RetrievalEvaluationRunSerializer(result["run"]).data, "passed": result["passed"]})


@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def feature_flags(request):
    _require_ai_admin(request.user)
    if request.method == "GET":
        return Response(AIFeatureFlagSerializer(AIFeatureFlag.objects.order_by("feature", "-created_at"), many=True).data)
    serializer = AIFeatureFlagSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    flag = serializer.save()
    return Response(AIFeatureFlagSerializer(flag).data, status=status.HTTP_201_CREATED)


@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def evaluations(request):
    _require_ai_admin(request.user)
    if request.method == "GET":
        return Response({
            "datasets": AIEvaluationDatasetSerializer(AIEvaluationDataset.objects.order_by("name"), many=True).data,
            "runs": AIEvaluationRunSerializer(AIEvaluationRun.objects.select_related("dataset", "provider", "model_configuration").order_by("-created_at")[:50], many=True).data,
        })
    serializer = AIEvaluationDatasetSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    dataset = serializer.save()
    return Response(AIEvaluationDatasetSerializer(dataset).data, status=status.HTTP_201_CREATED)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def run_evaluations_filtered(request):
    _require_ai_admin(request.user)
    serializer = EvaluationRunFilterSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    result = AIEvaluationOpsService.run_scheduled(
        actor=request.user,
        dataset_type=serializer.validated_data["dataset_type"],
        feature=serializer.validated_data["feature"],
        provider_type=serializer.validated_data["provider"],
        prompt_version=serializer.validated_data["prompt_version"],
        limit=serializer.validated_data["limit"],
        dry_run=serializer.validated_data["dry_run"],
        budget=serializer.validated_data["budget"],
    )
    return Response({
        "dry_run": result["dry_run"],
        "dataset_count": result["dataset_count"],
        "datasets": result.get("datasets", []),
        "runs": AIEvaluationRunSerializer(result.get("runs", []), many=True).data,
        "budget_estimate": result.get("budget_estimate", {}),
        "budget_violations": result.get("budget_violations", []),
    }, status=status.HTTP_202_ACCEPTED)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def reviewer_queue(request):
    serializer = AIEvaluationReviewFilterSerializer(data=request.query_params)
    serializer.is_valid(raise_exception=True)
    queue = AIEvaluationOpsService.reviewer_console(actor=request.user, filters=serializer.validated_data)
    return Response({
        "assigned": AIEvaluationReviewSerializer(queue["assigned"], many=True).data,
        "unassigned": AIEvaluationReviewSerializer(queue["unassigned"], many=True).data,
        "workload": queue["workload"],
    })


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def reviewer_bulk_assign(request):
    serializer = AIEvaluationReviewBulkAssignSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    reviewer = get_object_or_404(User, id=serializer.validated_data["assigned_to"])
    reviews = AIEvaluationOpsService.bulk_assign_reviews(actor=request.user, review_ids=serializer.validated_data["review_ids"], reviewer=reviewer)
    return Response(AIEvaluationReviewSerializer(reviews, many=True).data)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def reviewer_bulk_approve(request):
    serializer = AIEvaluationReviewBulkApproveSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    reviews = AIEvaluationOpsService.bulk_approve_reviews(actor=request.user, review_ids=serializer.validated_data["review_ids"], notes=serializer.validated_data["notes"])
    return Response(AIEvaluationReviewSerializer(reviews, many=True).data)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def reviewer_action(request, result_id):
    _require_ai_admin(request.user)
    result = get_object_or_404(AIEvaluationResult, id=result_id)
    serializer = AIEvaluationReviewActionSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    assigned_to = None
    if serializer.validated_data.get("assigned_to"):
        assigned_to = get_object_or_404(User, id=serializer.validated_data["assigned_to"])
    review = AIEvaluationOpsService.assign_review(actor=request.user, result=result, reviewer=assigned_to or request.user)
    if serializer.validated_data["status"] != "pending" or serializer.validated_data.get("manual_score") is not None:
        review = AIEvaluationOpsService.submit_review(
            actor=request.user,
            review=review,
            status_value=serializer.validated_data["status"],
            manual_score=serializer.validated_data.get("manual_score"),
            notes=serializer.validated_data["notes"],
            hallucination=serializer.validated_data["hallucination_flag"],
            bias=serializer.validated_data["bias_flag"],
            unsafe=serializer.validated_data["unsafe_flag"],
            request_prompt_revision=serializer.validated_data["request_prompt_revision"],
        )
    return Response(AIEvaluationReviewSerializer(review).data)


@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def red_team_suites(request):
    _require_ai_admin(request.user)
    if request.method == "GET":
        suites = AIRedTeamSuite.objects.order_by("name")
        return Response(AIRedTeamSuiteSerializer(suites, many=True).data)
    serializer = AIRedTeamSuiteSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    suite = serializer.save()
    return Response(AIRedTeamSuiteSerializer(suite).data, status=status.HTTP_201_CREATED)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def red_team_run(request):
    _require_ai_admin(request.user)
    serializer = AIRedTeamRunSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    suite = get_object_or_404(AIRedTeamSuite, id=serializer.validated_data["suite_id"])
    results = AIEvaluationOpsService.run_red_team_suite(actor=request.user, suite=suite, provider_type=serializer.validated_data["provider"])
    return Response(AIRedTeamResultSerializer(results, many=True).data, status=status.HTTP_202_ACCEPTED)


@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def comparison_reports(request):
    _require_ai_admin(request.user)
    if request.method == "GET":
        reports = AIComparisonReport.objects.order_by("-created_at")[:100]
        return Response(AIComparisonReportSerializer(reports, many=True).data)
    serializer = AIComparisonCreateSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    report = AIEvaluationOpsService.comparison_report(actor=request.user, **serializer.validated_data)
    return Response(AIComparisonReportSerializer(report).data, status=status.HTTP_201_CREATED)


@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def audit_exports(request):
    _require_ai_admin(request.user)
    if request.method == "GET":
        exports = AIAuditExport.objects.order_by("-created_at")[:100]
        return Response(AIAuditExportSerializer(exports, many=True).data)
    serializer = AIAuditExportCreateSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    export = AIEvaluationOpsService.create_export(actor=request.user, **serializer.validated_data)
    return Response(AIAuditExportSerializer(export).data, status=status.HTTP_202_ACCEPTED)


@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def release_gates(request):
    _require_ai_admin(request.user)
    if request.method == "GET":
        gates = AIReleaseGate.objects.select_related("evaluation_run", "requested_by", "reviewed_by").order_by("-created_at")[:100]
        return Response(AIReleaseGateSerializer(gates, many=True).data)
    serializer = AIReleaseGateCreateSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    evaluation_run = None
    if serializer.validated_data.get("evaluation_run_id"):
        evaluation_run = get_object_or_404(AIEvaluationRun, id=serializer.validated_data["evaluation_run_id"])
    gate = AIReleaseGateService.create_gate(
        actor=request.user,
        change_type=serializer.validated_data["change_type"],
        target_id=serializer.validated_data["target_id"],
        feature=serializer.validated_data["feature"],
        previous_version=serializer.validated_data["previous_version"],
        new_version=serializer.validated_data["new_version"],
        evaluation_run=evaluation_run,
        thresholds=serializer.validated_data["thresholds"],
    )
    return Response(AIReleaseGateSerializer(gate).data, status=status.HTTP_201_CREATED)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def release_gate_action(request, gate_id):
    gate = get_object_or_404(AIReleaseGate, id=gate_id)
    serializer = AIReleaseGateActionSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    if serializer.validated_data["action"] == "promote":
        gate = AIReleaseGateService.promote(actor=request.user, gate=gate)
    else:
        gate = AIReleaseGateService.rollback(actor=request.user, gate=gate, reason=serializer.validated_data["reason"])
    return Response(AIReleaseGateSerializer(gate).data)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def change_history(request):
    _require_ai_admin(request.user)
    history = AIChangeHistory.objects.select_related("gate", "changed_by", "evaluation_run").order_by("-created_at")[:100]
    return Response(AIChangeHistorySerializer(history, many=True).data)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def launch_checklist(request):
    _require_ai_admin(request.user)
    return Response(AIReleaseGateService.launch_checklist())


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def run_evaluation(request):
    _require_ai_admin(request.user)
    from apps.ai_platform.serializers import EvaluationRunCreateSerializer

    serializer = EvaluationRunCreateSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    dataset = get_object_or_404(AIEvaluationDataset, id=serializer.validated_data["dataset_id"])
    run = AIEvaluationService.run_dataset(
        dataset=dataset,
        user=request.user,
        provider_type=serializer.validated_data["provider_type"],
        model_name=serializer.validated_data["model_name"],
    )
    return Response(AIEvaluationRunSerializer(run).data, status=status.HTTP_202_ACCEPTED)


@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def cost_summary(request):
    _require_ai_admin(request.user)
    if request.method == "POST":
        serializer = CostReconciliationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        ai_request = get_object_or_404(AIRequest, id=serializer.validated_data["request_id"])
        usage = AIService.reconcile_costs(
            request=ai_request,
            actual_cost=serializer.validated_data.get("actual_cost"),
            provider_input_tokens=serializer.validated_data.get("provider_input_tokens"),
            provider_output_tokens=serializer.validated_data.get("provider_output_tokens"),
        )
        return Response({"request_id": str(ai_request.id), "actual_cost": str(usage.actual_cost), "variance": str(usage.cost_variance)})
    usage = AIUsage.objects.all()
    return Response({
        "estimated_cost": str(usage.aggregate(total=Sum("estimated_cost"))["total"] or 0),
        "tokens": usage.aggregate(total=Sum("total_tokens"))["total"] or 0,
        "by_feature": list(usage.values("feature").annotate(estimated_cost=Sum("estimated_cost"), tokens=Sum("total_tokens")).order_by("feature")),
        "by_provider": list(usage.values("provider__provider_type").annotate(estimated_cost=Sum("estimated_cost"), tokens=Sum("total_tokens")).order_by("provider__provider_type")),
    })


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def quality_dashboard(request):
    return Response(AIQualityDashboardService.summary(user=request.user))


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def provider_comparison(request):
    _require_ai_admin(request.user)
    return Response({"providers": AIQualityDashboardService.provider_comparison()})


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def cache_statistics(request):
    _require_ai_admin(request.user)
    recent = AICacheSerializer(AIResponseCache.objects.select_related("provider", "organization").order_by("-updated_at")[:50], many=True).data
    return Response({"stats": AICacheService.stats(), "recent": recent})


@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def feedback(request):
    if request.method == "GET":
        items = AIFeedback.objects.filter(user=request.user).select_related("request", "provider").order_by("-created_at")[:100]
        return Response(AIFeedbackSerializer(items, many=True).data)
    serializer = AIFeedbackCreateSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    ai_request = None
    if serializer.validated_data.get("request_id"):
        ai_request = get_object_or_404(AIRequest, id=serializer.validated_data["request_id"])
        if ai_request.user_id != request.user.id and not PermissionService.is_platform_admin(request.user):
            raise PermissionError("You cannot rate this AI response.")
    organization = _organization_for_user(request.user, serializer.validated_data.get("organization_id"))
    item = AIFeedbackService.record(
        user=request.user,
        request=ai_request,
        feature=serializer.validated_data["feature"],
        rating=serializer.validated_data["rating"],
        comment=serializer.validated_data["comment"],
        organization=organization,
        metadata=serializer.validated_data["metadata"],
    )
    return Response(AIFeedbackSerializer(item).data, status=status.HTTP_201_CREATED)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
@throttle_classes([AIRateThrottle])
def bias_report(request):
    serializer = AIBiasReportRequestSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    organization = _organization_for_user(request.user, serializer.validated_data.get("organization_id"))
    report = AIFairnessService.evaluate_text(text=serializer.validated_data["text"], feature=serializer.validated_data["feature"], organization=organization)
    return Response(AIFairnessReportSerializer(report).data, status=status.HTTP_201_CREATED)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
@throttle_classes([AIRateThrottle])
def privacy_report(request):
    serializer = AIPrivacyReportRequestSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    organization = _organization_for_user(request.user, serializer.validated_data.get("organization_id"))
    report = AIPrivacyService.create_report(text=serializer.validated_data["text"], feature=serializer.validated_data["feature"], organization=organization)
    return Response(AIPrivacyReportSerializer(report).data, status=status.HTTP_201_CREATED)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def explain_score(request):
    serializer = AIExplainScoreSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    ai_request = None
    if serializer.validated_data.get("request_id"):
        ai_request = get_object_or_404(AIRequest, id=serializer.validated_data["request_id"])
        if ai_request.user_id != request.user.id and not PermissionService.is_platform_admin(request.user):
            raise PermissionError("You cannot explain this AI score.")
    report = AICalibrationService.explain_score(
        request=ai_request,
        feature=serializer.validated_data["feature"],
        score_name=serializer.validated_data["score_name"],
        score=serializer.validated_data["score"],
        evidence=serializer.validated_data["evidence"],
        breakdown=serializer.validated_data["score_breakdown"],
        weighting=serializer.validated_data["weighting"],
    )
    return Response(AICalibrationReportSerializer(report).data, status=status.HTTP_201_CREATED)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def admin_overview(request):
    _require_ai_admin(request.user)
    requests = AIRequest.objects.all()
    usage = AIUsage.objects.all()
    return Response({
        "providers": AIProviderSerializer(AIProvider.objects.all(), many=True).data,
        "models": AIModelConfigurationSerializer(AIModelConfiguration.objects.select_related("provider"), many=True).data,
        "prompt_templates": AIPromptTemplateSerializer(AIPromptTemplate.objects.order_by("key", "-version")[:100], many=True).data,
        "budgets": AIBudgetPolicySerializer(AIBudgetPolicy.objects.order_by("-created_at")[:100], many=True).data,
        "usage": AIUsageSerializer(usage.order_by("-period_date")[:100], many=True).data,
        "analytics": {
            "request_count": requests.count(),
            "success_rate": round((requests.filter(status="completed").count() / requests.count()) * 100, 2) if requests.exists() else 0,
            "failure_rate": round((requests.filter(status="failed").count() / requests.count()) * 100, 2) if requests.exists() else 0,
            "avg_latency_ms": requests.aggregate(avg=Avg("latency_ms"))["avg"] or 0,
            "feature_usage": list(requests.values("feature").annotate(total=Count("id")).order_by("-total")),
            "provider_usage": list(requests.values("provider__provider_type").annotate(total=Count("id")).order_by("-total")),
            "estimated_cost": str(usage.aggregate(total=Sum("estimated_cost"))["total"] or 0),
            "tokens": usage.aggregate(total=Sum("total_tokens"))["total"] or 0,
        },
    })
