# Tenant-Isolation Route Matrix

This matrix tracks sensitive route coverage for staging and Version 1.0 readiness. Add the exact automated test name when a route is covered.

| Domain | Endpoint pattern | Method | Auth | Allowed roles | Organization scope | Ownership rule | Admin override | Audit event | Positive test | Negative tests required | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Organizations | `/api/v1/organizations/` | GET/POST | Required | organization admin, platform admin | Membership scoped | User must belong to organization for list detail | platform_admin | organization viewed/created | `apps.organizations.tests.test_views` | ID guessing, list leakage | Partial |
| Organization members | `/api/v1/organizations/{id}/members/` | GET/POST/PATCH/DELETE | Required | company_admin, university_admin, platform_admin | Organization scoped | Admin role in same organization | platform_admin | member invited/changed/removed | `apps.organizations.tests.test_enterprise_platform` | Cross-tenant member mutation | Partial |
| Invitations | `/api/v1/organizations/invitations/accept/` | POST | Required | invited user, platform_admin | Invitation organization | Email must match unless platform admin | platform_admin | invitation accepted | `apps.organizations.tests.test_views` | Token replay, wrong email, expired token | Partial |
| Jobs | `/api/v1/jobs/organizations/{org_id}/...` | GET/POST/PATCH | Required | recruiter, company_admin, platform_admin | Organization scoped | Recruiter must belong to organization | platform_admin | job created/published/archived | `apps.jobs.tests.test_recruiter_jobs` | Cross-tenant job edit, list leakage | Partial |
| Applications | `/api/v1/jobs/applications/...` | GET/PATCH/POST | Required | applicant, recruiter, company_admin, platform_admin | Job organization | Applicant owns own application; recruiter owns org job | platform_admin | application changed | `apps.jobs.tests.test_revenue_pass2` | ID guessing, aggregate leakage | Partial |
| Candidate search | `/api/v1/careers/candidates/search/` | GET | Required | recruiter, company_admin, platform_admin | Recruiter organization | CandidateVisibilityService controls exposure | platform_admin | candidate searched/viewed | `apps.careers.tests.test_recruiter_candidate_visibility` | Private profile leak, locked resume leak | Partial |
| Resume downloads | `/api/v1/careers/resumes/{id}/download/` | GET | Required | owner, unlocked recruiter, platform_admin | Candidate/recruiter organization | Owner or unlocked recruiter only | platform_admin | resume downloaded | `common.tests.test_platform_hardening` | File URL guessing, locked recruiter denial | Partial |
| Portfolio media | `/api/v1/profiles/...` | GET/POST/PATCH | Mixed | owner, authorized recruiter, platform_admin | Candidate/recruiter organization | Visibility rules by public/private media | platform_admin | portfolio visibility changed | `apps.careers.tests.test_student_career_pass2` | Private media URL access | Partial |
| Notifications | `/api/v1/notifications/` | GET/PATCH | Required | owner, platform_admin | User scoped | User sees only own notifications | platform_admin | preference changed | `apps.notifications.tests.test_notification_preferences` | User notification leakage | Partial |
| Email webhooks | `/api/v1/notifications/email/webhooks/...` | POST | Provider signed | provider only | Delivery/user scoped | Valid provider signature required | none | bounce/complaint/webhook rejected | `apps.notifications.tests.test_email_delivery_service` | Invalid signature, replay | Partial |
| Data exports | `/api/v1/organizations/{id}/exports/` | GET/POST | Required | export_manager, report_viewer, platform_admin | Organization scoped | Export permission in same organization | platform_admin | export created/downloaded | `apps.organizations.tests.test_enterprise_platform` | Cross-tenant export, audit export role | Partial |
| Audit logs | `/api/v1/platform/audit/` | GET | Required | platform_admin | Platform scoped | Platform admin only | platform_admin | audit viewed | `common.tests.test_platform_operations` | Tenant admin denial | Partial |
| AI recruiter | `/api/v1/ai/recruiter/...` | POST/GET | Required | recruiter, company_admin, platform_admin | Recruiter organization | CandidateVisibilityService and EntitlementService | platform_admin | ai recruiter action | `apps.ai_platform.tests.test_ai_recruiter_copilot` | Hidden candidate leakage | Partial |
| RAG retrieval | `/api/v1/ai/knowledge/retrieval/` | POST | Required | feature authorized user | Knowledge collection scoped | RetrievalService filters by permissions | platform_admin | retrieval used | `apps.ai_platform.tests.test_ai_knowledge_rag` | Private resume/portfolio/org document leak | Partial |
| Payments/webhooks | `/api/v1/payments/...` | POST | Mixed | authenticated user or provider signed | User/org entitlement | Valid signature for provider callbacks | platform_admin | entitlement changed | `apps.payments.tests` | Duplicate webhook, invalid signature | Needs review |

## Staging Closure Criteria

- Every `Partial` row must name a positive automated test and at least one cross-tenant negative test.
- File access routes must include URL-guessing denial.
- List and analytics routes must include aggregate-count leakage checks.
- AI and RAG routes must prove private documents are not retrieved across organizations.
- Export and audit routes must prove report-only roles cannot mutate records.
