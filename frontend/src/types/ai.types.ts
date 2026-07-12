export interface AIUsageSummary {
  input_tokens: number;
  output_tokens: number;
  total_tokens: number;
  estimated_cost: string;
  latency_ms: number;
}

export interface AIRequest {
  id: string;
  feature: string;
  operation: string;
  status: string;
  redacted_input: string;
  safety_flags: string[];
  latency_ms: number;
  error_message: string;
  response_text: string;
  created_at: string;
}

export interface AIConversation {
  id: string;
  title: string;
  feature: string;
  locale: string;
  is_archived: boolean;
  metadata: Record<string, unknown>;
  created_at: string;
  updated_at: string;
}

export interface AIChatResponse {
  request: AIRequest;
  conversation: AIConversation | null;
  text: string;
  usage: AIUsageSummary;
  retrieval?: AIRetrievalMetadata;
}

export interface AICitation {
  document_id: string;
  chunk_id: string;
  collection_type: string;
  source_type: string;
  source_id: string;
  title: string;
  visibility: string;
  freshness_score: string;
  last_indexed_at: string | null;
  source_updated_at: string | null;
  deep_link: string;
  score: number;
  confidence: number;
}

export interface AIRetrievalMetadata {
  citations: AICitation[];
  confidence: number;
  event_id?: string;
}

export interface AIKnowledgeCollection {
  id: string;
  name: string;
  collection_type: string;
  organization: string | null;
  embedding_version: string;
  vector_backend: string;
  vector_dimensions: number;
  health_status: string;
  last_health_check_at: string | null;
  last_health_error: string;
  is_active: boolean;
  document_count: number;
  chunk_count: number;
  created_at: string;
  updated_at: string;
}

export interface AIKnowledgeSearchResult {
  query: string;
  search_type: string;
  results: Array<{ score: number; text: string; citation: AICitation }>;
  citations: AICitation[];
  confidence: number;
  latency_ms: number;
  source_count: number;
  chunk_count: number;
  context_size: number;
  timed_out: boolean;
  cache_hit: boolean;
  missing_knowledge: Array<Record<string, unknown>>;
  event_id: string;
}

export interface AIKnowledgeIndexStatus {
  collections: AIKnowledgeCollection[];
  status_counts: Array<{ index_status: string; total: number }>;
  freshness: { avg_freshness: string | null; stale: number; failed: number };
  privacy_summary: {
    public_documents: number;
    organization_documents: number;
    private_documents: number;
    private_without_owner: number;
    organization_scope_missing: number;
    safe: boolean;
  };
  stale_documents: Array<Record<string, unknown>>;
  failed_documents: Array<Record<string, unknown>>;
  vector_backend: { backend: string; status: string; dimensions: number; provider_ready?: boolean };
}

export interface AIKnowledgeEmbeddingStatus {
  embedding_versions: Array<{ embedding_version: string; index_status: string; total: number }>;
  recent_retrievals: Array<Record<string, unknown>>;
}

export interface AIProvider {
  id: string;
  name: string;
  provider_type: string;
  is_active: boolean;
  is_default: boolean;
  priority: number;
  timeout_seconds: number;
  max_retries: number;
  metadata: Record<string, unknown>;
  health_status: string;
  last_health_check_at: string | null;
  last_error: string;
  created_at: string;
}

export interface AIModelConfiguration {
  id: string;
  provider: string;
  provider_name: string;
  model_name: string;
  display_name: string;
  is_active: boolean;
  is_default: boolean;
  max_tokens: number;
  temperature: string;
  timeout_seconds: number;
  max_retries: number;
  created_at: string;
}

export interface AISettings {
  providers: AIProvider[];
  models: AIModelConfiguration[];
  features: string[];
}

export interface AIOverview {
  providers_configured: number;
  requests: number;
  conversations: number;
  usage: { requests: number; tokens: number; estimated_cost: string };
  features: string[];
}

export interface AIAdminOverview {
  providers: AIProvider[];
  models: AIModelConfiguration[];
  prompt_templates: Array<{ id: string; key: string; name: string; feature: string; version: number; locale: string; is_active: boolean }>;
  budgets: Array<Record<string, unknown>>;
  usage: Array<Record<string, unknown>>;
  analytics: {
    request_count: number;
    success_rate: number;
    failure_rate: number;
    avg_latency_ms: number;
    feature_usage: Array<{ feature: string; total: number }>;
    provider_usage: Array<{ provider__provider_type: string; total: number }>;
    estimated_cost: string;
    tokens: number;
  };
}

export interface AIProviderStatus {
  providers: AIProvider[];
  comparison: Array<{ provider__provider_type: string | null; total: number; avg_latency_ms: number | null }>;
}

export interface AICostSummary {
  estimated_cost: string;
  tokens: number;
  by_feature: Array<{ feature: string; estimated_cost: string; tokens: number }>;
  by_provider: Array<{ provider__provider_type: string | null; estimated_cost: string; tokens: number }>;
}

export interface AIEvaluationSummary {
  datasets: Array<{ id: string; name: string; feature: string; examples: Array<Record<string, string>>; created_at: string }>;
  runs: Array<{ id: string; dataset_name: string; status: string; average_score: string | null; average_latency_ms: number; estimated_cost: string; created_at: string }>;
}

export interface AIFeatureFlag {
  id: string;
  feature: string;
  is_enabled: boolean;
  organization: string | null;
  user: string | null;
  reason: string;
  created_at: string;
}

export interface AIStreamEvent {
  event: "token" | "done" | "error" | "cancelled";
  chunk?: string;
  request_id?: string;
  error?: string;
  usage?: { total_tokens: number; estimated_cost: string; latency_ms: number };
}

export type AIInterviewSessionType = "behavioral" | "technical" | "system_design" | "coding" | "hr" | "leadership" | "language_interview" | "custom";
export type AIInterviewDifficulty = "beginner" | "intermediate" | "advanced" | "expert";
export type AIInterviewStatus = "active" | "paused" | "completed" | "cancelled";

export interface AIInterviewQuestion {
  id: string;
  sequence: number;
  question_text: string;
  skill_area: string;
  follow_up_to: string | null;
  metadata: Record<string, unknown>;
  created_at: string;
}

export interface AIInterviewEvaluation {
  id: string;
  question: string;
  question_text: string;
  answer_text: string;
  clarity: number;
  confidence: number;
  technical_quality: number;
  communication: number;
  structure: number;
  problem_solving: number;
  accuracy: number;
  professionalism: number;
  overall_score: number;
  strengths: string[];
  weaknesses: string[];
  better_answer: string;
  tips: string[];
  next_practice_goal: string;
  metadata: Record<string, unknown>;
  created_at: string;
}

export interface AIInterviewSession {
  id: string;
  organization: string | null;
  organization_name: string;
  session_type: AIInterviewSessionType;
  difficulty: AIInterviewDifficulty;
  status: AIInterviewStatus;
  job_title: string;
  industry: string;
  experience_level: string;
  company_type: string;
  language: string;
  skills: string[];
  history: Array<Record<string, unknown>>;
  summary: string;
  feedback: {
    question_reviews?: Array<{ question: string; score: number; weaknesses: string[] }>;
    improvement_roadmap?: string[];
    recommended_learning?: string[];
  };
  overall_score: number;
  confidence_trend: number[];
  communication_trend: number[];
  technical_trend: number[];
  estimated_cost: string;
  input_tokens: number;
  output_tokens: number;
  total_tokens: number;
  started_at: string;
  finished_at: string | null;
  duration_seconds: number;
  metadata: Record<string, unknown>;
  questions: AIInterviewQuestion[];
  evaluations: AIInterviewEvaluation[];
  created_at: string;
  updated_at: string;
}

export interface AIInterviewStartPayload {
  organization_id?: string;
  session_type: AIInterviewSessionType;
  difficulty: AIInterviewDifficulty;
  job_title?: string;
  industry?: string;
  experience_level?: string;
  company_type?: string;
  language?: string;
  skills?: string[];
  resume_context?: string;
  portfolio_context?: string;
}

export interface AIInterviewAnalytics {
  sessions: number;
  completed: number;
  average_score: number;
  average_duration_seconds: number;
  practice_frequency: Array<{ day: string; total: number }>;
  weak_areas: Array<{ area: string; score: number }>;
  strong_areas: Array<{ area: string; score: number }>;
  ai_cost: string;
  organization_usage: Array<{ organization__name: string | null; total: number; avg_score: number | null }>;
}

export interface AIInterviewTemplate {
  id: string;
  organization: string | null;
  organization_name: string;
  title: string;
  session_type: AIInterviewSessionType;
  difficulty: AIInterviewDifficulty;
  job_title: string;
  industry: string;
  skills: string[];
  question_count: number;
  is_active: boolean;
  metadata: Record<string, unknown>;
  created_at: string;
  updated_at: string;
}

export interface AIQualityDashboard {
  request_count: number;
  failure_rate: number;
  blocked_rate: number;
  estimated_cost: string;
  token_usage: number;
  avg_latency_ms: number;
  evaluation_history: Array<{
    id: string;
    dataset__name: string;
    dataset__feature: string;
    status: string;
    average_score: string | null;
    confidence_score: string | null;
    average_latency_ms: number;
    estimated_cost: string;
    created_at: string;
  }>;
  feature_quality: Array<{ dataset__feature: string; avg_score: string | null; avg_confidence: string | null; runs: number }>;
  bias_reports: { total: number; manual_review: number; by_feature: Array<{ feature: string; total: number }> };
  privacy_reports: { total: number; high: number; by_feature: Array<{ feature: string; total: number; redactions: number | null }> };
  feedback: { total: number; by_rating: Array<{ rating: string; total: number }> };
  provider_comparison: Array<{ provider__provider_type: string | null; model_configuration__model_name: string | null; total: number; avg_latency_ms: number | null }>;
  cache: { entries: number; hits: number; cache_hit_ratio: number; by_feature: Array<{ feature: string; entries: number; hits: number | null }> };
  confidence_trends: Array<{ feature: string; score_name: string; avg_confidence: string | null; total: number }>;
  reviewer_queue: {
    pending: number;
    manual_review: number;
    recent: Array<{ id: string; status: string; manual_score: string | null; hallucination_flag: boolean; bias_flag: boolean; unsafe_flag: boolean; created_at: string }>;
  };
  red_team: {
    suites: number;
    results: number;
    failed: number;
    high_risk: number;
    recent: Array<{ id: string; suite__name: string; case_name: string; risk_severity: string; passed: boolean; risk_flags: string[]; created_at: string }>;
  };
  comparisons: Array<{ id: string; comparison_type: string; feature: string; left_label: string; right_label: string; winner: string; created_at: string }>;
  audit_exports: Array<{ id: string; export_type: string; file_format: string; status: string; row_count: number; file_name: string; created_at: string }>;
  release_governance: AIReleaseGovernanceSummary;
}

export interface AIFeedback {
  id: string;
  request: string | null;
  feature: string;
  rating: "helpful" | "not_helpful" | "incorrect" | "hallucination" | "unsafe" | "biased" | "incomplete";
  comment: string;
  provider: string | null;
  model_name: string;
  prompt_version: string;
  created_at: string;
}

export interface AIEvaluationRunResponse {
  dry_run: boolean;
  dataset_count: number;
  datasets: string[];
  runs: Array<{ id: string; dataset_name: string; status: string; average_score: string | null; confidence_score: string | null; duration_seconds: number; failure_reason: string }>;
  budget_estimate?: { requests?: number; tokens?: number; estimated_cost?: string };
  budget_violations?: string[];
}

export interface AIEvaluationReview {
  id: string;
  result: string;
  dataset_name: string;
  assigned_to: string | null;
  reviewed_by: string | null;
  status: string;
  manual_score: string | null;
  hallucination_flag: boolean;
  bias_flag: boolean;
  unsafe_flag: boolean;
  request_prompt_revision: boolean;
  notes: string;
  assigned_at: string | null;
  reviewed_at: string | null;
  created_at: string;
}

export interface AIReviewerQueue {
  assigned: AIEvaluationReview[];
  unassigned: AIEvaluationReview[];
  workload: Array<{ assigned_to__email: string | null; total: number; pending: number }>;
}

export interface AIRedTeamSuite {
  id: string;
  name: string;
  suite_type: string;
  feature: string;
  severity: string;
  expected_safe_behavior: string;
  cases: Array<Record<string, unknown>>;
  is_active: boolean;
  created_at: string;
}

export interface AIReleaseGovernanceSummary {
  release_gates: {
    total: number;
    pending: number;
    approved: number;
    rejected: number;
    promoted: number;
    rolled_back: number;
    recent_promotions: Array<Record<string, unknown>>;
    rollback_history: Array<Record<string, unknown>>;
  };
  red_team_pass_rate: number;
  launch_checklist: { ready: boolean; items: Record<string, boolean> };
}

export interface AIReleaseGate {
  id: string;
  change_type: string;
  target_id: string;
  feature: string;
  status: string;
  previous_version: Record<string, unknown>;
  new_version: Record<string, unknown>;
  thresholds: Record<string, unknown>;
  gate_results: Record<string, unknown>;
  evaluation_run: string | null;
  evaluation_run_status: string | null;
  requested_by_email: string;
  reviewed_by_email: string;
  promoted_at: string | null;
  rolled_back_at: string | null;
  rollback_reason: string;
  created_at: string;
}

export interface AICareerGoal {
  id: string;
  title: string;
  target_role: string;
  target_industry: string;
  target_country: string;
  status: "active" | "paused" | "completed" | "archived";
  progress_percentage: number;
  milestones: Array<Record<string, unknown>>;
  completed_milestones: Array<Record<string, unknown>>;
  coaching_history: Array<Record<string, unknown>>;
  created_at: string;
  updated_at: string;
}

export interface AICareerAssessment {
  id: string;
  goal: string | null;
  goal_title: string;
  readiness_score: string;
  confidence_score: string;
  strengths: string[];
  weaknesses: string[];
  growth_opportunities: string[];
  recommendations: string[];
  assessment: Record<string, unknown>;
  estimated_cost: string;
  created_at: string;
}

export interface AICareerRoadmap {
  id: string;
  goal: string | null;
  goal_title: string;
  horizon: "3_months" | "6_months" | "12_months" | "24_months";
  title: string;
  roadmap: Record<string, unknown>;
  milestones: Array<{ title?: string; due?: string; status?: string }>;
  recommended_courses: Array<Record<string, unknown>>;
  recommended_projects: Array<Record<string, unknown>>;
  progress_percentage: number;
  created_at: string;
}

export interface AICareerSkillGap {
  id: string;
  goal: string | null;
  comparison_type: string;
  target: string;
  missing_skills: string[];
  priority_skills: string[];
  estimated_learning_time: Record<string, string>;
  recommended_courses: Array<Record<string, unknown>>;
  recommended_projects: Array<Record<string, unknown>>;
  confidence_score: string;
  report: Record<string, unknown>;
  created_at: string;
}

export interface AICareerCoachingSummary {
  id: string;
  goal: string | null;
  week_start: string;
  summary: string;
  achievements: string[];
  missed_goals: string[];
  recommended_actions: string[];
  upcoming_priorities: string[];
  motivation_summary: string;
  confidence_score: string;
  created_at: string;
}

export interface AICareerHistory {
  assessments: AICareerAssessment[];
  roadmaps: AICareerRoadmap[];
  skill_gaps: AICareerSkillGap[];
  coaching: AICareerCoachingSummary[];
}

export interface AICareerAnalytics {
  goal_completion: number;
  active_goals: number;
  roadmap_completion: number;
  latest_readiness_score: string;
  career_confidence_trend: Array<Record<string, unknown>>;
  roadmaps: number;
  weekly_coaching_count: number;
}

export interface AIRecruiterReport {
  id: string;
  organization: string | null;
  organization_name: string;
  job: string | null;
  job_title: string;
  candidate: string | null;
  candidate_name: string;
  report_type: "candidate_analysis" | "candidate_ranking" | "candidate_comparison" | "job_analysis" | "interview_plan" | "pipeline_insights";
  title: string;
  score: string;
  confidence_score: string;
  candidate_ids: string[];
  report: Record<string, unknown>;
  fairness_notes: string;
  disclaimer: string;
  model_name: string;
  estimated_cost: string;
  created_at: string;
}

export interface AIRecruiterAnalytics {
  reports: number;
  estimated_cost: string;
  average_score: string;
  average_confidence: string;
  by_type: Array<{ report_type: string; total: number }>;
  recent: Array<{ id: string; report_type: string; title: string; score: string; confidence_score: string; created_at: string }>;
}

export interface AILearningTutorSession {
  id: string;
  course: string;
  course_title: string;
  lesson: string | null;
  lesson_title: string;
  question: string;
  answer: string;
  mode: string;
  concepts: string[];
  confidence_score: string;
  model_name: string;
  estimated_cost: string;
  context: { retrieval?: AIRetrievalMetadata } & Record<string, unknown>;
  created_at: string;
}

export interface AILessonIntelligence {
  id: string;
  lesson: string;
  lesson_title: string;
  course: string;
  course_title: string;
  summary: string;
  key_concepts: string[];
  glossary: Record<string, string>;
  important_formulas: string[];
  common_mistakes: string[];
  prerequisites: string[];
  learning_objectives: string[];
  estimated_study_time_minutes: number;
  is_current: boolean;
  model_name: string;
  estimated_cost: string;
  created_at: string;
}

export interface AIStudyPlan {
  id: string;
  cadence: "daily" | "weekly" | "monthly";
  pace: "relaxed" | "balanced" | "intensive";
  available_minutes_per_day: number;
  deadline: string | null;
  title: string;
  plan: Record<string, unknown>;
  milestones: Array<Record<string, unknown>>;
  weak_concepts: string[];
  recommended_lessons: Array<Record<string, unknown>>;
  confidence_score: string;
  model_name: string;
  estimated_cost: string;
  created_at: string;
}

export interface AIGeneratedQuiz {
  id: string;
  course: string;
  course_title: string;
  lesson: string | null;
  lesson_title: string;
  title: string;
  difficulty: "beginner" | "intermediate" | "advanced";
  question_count: number;
  learning_objectives: string[];
  questions: Array<Record<string, unknown>>;
  is_instructor_reviewed: boolean;
  is_published_to_students: boolean;
  model_name: string;
  estimated_cost: string;
  created_at: string;
}

export interface AIQuizFeedback {
  id: string;
  course: string;
  course_title: string;
  quiz_attempt: string | null;
  explanation: string;
  correct_reasoning: string[];
  weak_topics: string[];
  recommended_lessons: Array<Record<string, unknown>>;
  next_actions: string[];
  confidence_score: string;
  model_name: string;
  estimated_cost: string;
  created_at: string;
}

export interface AILearningHistory {
  tutor_sessions: AILearningTutorSession[];
  study_plans: AIStudyPlan[];
  quiz_feedback: AIQuizFeedback[];
}

export interface AILearningAnalytics {
  tutor_sessions: number;
  questions_asked: number;
  concepts_mastered: number;
  weak_concepts: string[][];
  learning_streak: number;
  study_time_minutes: number;
  quiz_improvement: string;
  ai_usage: number;
  cost: string;
  confidence: string;
}

export interface AIComparisonReport {
  id: string;
  comparison_type: string;
  feature: string;
  left_label: string;
  right_label: string;
  metrics: Record<string, unknown>;
  winner: string;
  created_at: string;
}

export interface AIAuditExport {
  id: string;
  export_type: string;
  file_format: string;
  status: string;
  file: string | null;
  file_name: string;
  row_count: number;
  failure_reason: string;
  created_at: string;
}
