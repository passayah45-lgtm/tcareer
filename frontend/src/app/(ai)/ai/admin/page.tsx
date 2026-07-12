"use client";

import { useEffect, useState } from "react";
import { actOnAIReleaseGate, createAIAuditExport, createAIComparison, createAIReleaseGate, getAIAdminOverview, getAICostSummary, getAIEvaluations, getAIFeatureFlags, getAIProviderStatus, getAIQualityDashboard, getAIReleaseGates, getKnowledgeEmbeddingStatus, getKnowledgeIndexStatus, reindexKnowledge, runFilteredEvaluations, searchKnowledge } from "@/lib/api/ai.api";
import type { AIAdminOverview, AICostSummary, AIEvaluationSummary, AIFeatureFlag, AIKnowledgeEmbeddingStatus, AIKnowledgeIndexStatus, AIKnowledgeSearchResult, AIProviderStatus, AIQualityDashboard, AIReleaseGate } from "@/types/ai.types";

export default function AIAdminPage() {
  const [overview, setOverview] = useState<AIAdminOverview | null>(null);
  const [providerStatus, setProviderStatus] = useState<AIProviderStatus | null>(null);
  const [costs, setCosts] = useState<AICostSummary | null>(null);
  const [evaluations, setEvaluations] = useState<AIEvaluationSummary | null>(null);
  const [quality, setQuality] = useState<AIQualityDashboard | null>(null);
  const [releaseGates, setReleaseGates] = useState<AIReleaseGate[]>([]);
  const [knowledgeStatus, setKnowledgeStatus] = useState<AIKnowledgeIndexStatus | null>(null);
  const [embeddingStatus, setEmbeddingStatus] = useState<AIKnowledgeEmbeddingStatus | null>(null);
  const [knowledgeResult, setKnowledgeResult] = useState<AIKnowledgeSearchResult | null>(null);
  const [knowledgeQuery, setKnowledgeQuery] = useState("Django career skills");
  const [flags, setFlags] = useState<AIFeatureFlag[]>([]);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const [busy, setBusy] = useState("");

  useEffect(() => {
    Promise.all([getAIAdminOverview(), getAIProviderStatus(), getAICostSummary(), getAIEvaluations(), getAIFeatureFlags(), getAIQualityDashboard(), getAIReleaseGates(), getKnowledgeIndexStatus(), getKnowledgeEmbeddingStatus()])
      .then(([admin, providers, costSummary, evaluationSummary, featureFlags, qualitySummary, gates, indexStatus, embeddings]) => {
        setOverview(admin);
        setProviderStatus(providers);
        setCosts(costSummary);
        setEvaluations(evaluationSummary);
        setFlags(featureFlags);
        setQuality(qualitySummary);
        setReleaseGates(gates);
        setKnowledgeStatus(indexStatus);
        setEmbeddingStatus(embeddings);
      })
      .catch(() => setError("AI admin requires platform admin access."));
  }, []);

  async function runEvaluations() {
    setBusy("evaluations");
    setMessage("");
    try {
      const result = await runFilteredEvaluations({ limit: 5, dry_run: false, budget: { max_requests: 50, max_estimated_cost: "2.00", max_tokens: 100000 } });
      const blocked = result.budget_violations && result.budget_violations.length > 0;
      setMessage(blocked ? `Evaluation blocked by budget: ${result.budget_violations?.join(", ")}.` : `Launched ${result.runs.length} evaluation run(s).`);
    } catch {
      setError("Unable to launch evaluations.");
    } finally {
      setBusy("");
    }
  }

  async function exportAudit() {
    setBusy("export");
    setMessage("");
    try {
      const result = await createAIAuditExport({ export_type: "evaluation_runs", file_format: "csv" });
      setMessage(`Created export ${result.file_name || result.id}.`);
    } catch {
      setError("Unable to create AI audit export.");
    } finally {
      setBusy("");
    }
  }

  async function compareProviders() {
    setBusy("comparison");
    setMessage("");
    try {
      const result = await createAIComparison({ comparison_type: "provider", feature: "chat", left_label: "mock", right_label: "openai" });
      setMessage(`Created comparison report. Winner: ${result.winner || "n/a"}.`);
    } catch {
      setError("Unable to create comparison report.");
    } finally {
      setBusy("");
    }
  }

  async function dryRunBudget() {
    setBusy("budget");
    setMessage("");
    try {
      const result = await runFilteredEvaluations({ limit: 10, dry_run: true, budget: { max_requests: 50, max_estimated_cost: "2.00", max_tokens: 100000 } });
      setMessage(`Dry run estimate: ${result.budget_estimate?.requests ?? 0} requests, ${result.budget_estimate?.tokens ?? 0} tokens, $${result.budget_estimate?.estimated_cost ?? "0"}.`);
    } catch {
      setError("Unable to estimate evaluation budget.");
    } finally {
      setBusy("");
    }
  }

  async function createGate() {
    setBusy("gate");
    setMessage("");
    try {
      const latestRun = evaluations?.runs[0];
      if (!latestRun) {
        setMessage("Create or run an evaluation before creating a release gate.");
        return;
      }
      const gate = await createAIReleaseGate({
        change_type: "prompt_template",
        target_id: "default-prompt",
        feature: "chat",
        previous_version: { version: "current" },
        new_version: { version: "candidate" },
        evaluation_run_id: latestRun.id,
      });
      setReleaseGates(await getAIReleaseGates());
      setMessage(`Created release gate with status ${gate.status}.`);
    } catch {
      setError("Unable to create release gate.");
    } finally {
      setBusy("");
    }
  }

  async function testRetrieval() {
    setBusy("knowledge-search");
    setMessage("");
    try {
      setKnowledgeResult(await searchKnowledge({ query: knowledgeQuery, feature: "course_tutor", search_type: "hybrid", limit: 5 }));
      setMessage("Knowledge retrieval completed.");
    } catch {
      setError("Unable to run knowledge retrieval.");
    } finally {
      setBusy("");
    }
  }

  async function createSampleKnowledge() {
    setBusy("knowledge-reindex");
    setMessage("");
    try {
      await reindexKnowledge({
        source_type: "document",
        collection_type: "faqs",
        title: "T-Career AI knowledge sample",
        text: "T-Career helps learners build skills, complete courses, earn certificates, improve resumes and portfolios, and connect with recruiters.",
        visibility: "public",
      });
      setKnowledgeStatus(await getKnowledgeIndexStatus());
      setEmbeddingStatus(await getKnowledgeEmbeddingStatus());
      setMessage("Sample knowledge document indexed.");
    } catch {
      setError("Unable to index sample knowledge.");
    } finally {
      setBusy("");
    }
  }

  async function actOnGate(gate: AIReleaseGate, action: "promote" | "rollback") {
    setBusy(gate.id);
    setMessage("");
    try {
      await actOnAIReleaseGate(gate.id, action, action === "rollback" ? "Rollback from AI admin console." : "");
      setReleaseGates(await getAIReleaseGates());
      setMessage(`Release gate ${action} complete.`);
    } catch {
      setError(`Unable to ${action} release gate.`);
    } finally {
      setBusy("");
    }
  }

  return (
    <main className="min-h-screen bg-background px-4 py-8">
      <div className="mx-auto max-w-6xl space-y-6">
        <header>
          <h1 className="text-2xl font-semibold">AI Admin</h1>
          <p className="text-sm text-muted-foreground">Provider health, prompts, usage, cost, and job history foundation.</p>
        </header>
        {error && <p className="text-sm text-destructive">{error}</p>}
        {message && <p className="text-sm text-primary">{message}</p>}
        <div className="grid gap-4 sm:grid-cols-4">
          <div className="stat-card"><span className="stat-value">{overview?.analytics.request_count ?? 0}</span><span className="stat-label">Requests</span></div>
          <div className="stat-card"><span className="stat-value">{overview?.analytics.success_rate ?? 0}%</span><span className="stat-label">Success</span></div>
          <div className="stat-card"><span className="stat-value">{overview?.analytics.tokens ?? 0}</span><span className="stat-label">Tokens</span></div>
          <div className="stat-card"><span className="stat-value">${costs?.estimated_cost ?? overview?.analytics.estimated_cost ?? "0"}</span><span className="stat-label">Est. cost</span></div>
        </div>
        <section className="rounded-lg border border-border bg-card p-5">
          <h2 className="font-semibold mb-3">Quality and safety</h2>
          <div className="grid gap-3 md:grid-cols-4">
            <div className="rounded-lg border border-border p-3 text-sm"><strong className="block text-xl text-primary">{quality?.bias_reports.manual_review ?? 0}</strong><span className="text-muted-foreground">Bias manual reviews</span></div>
            <div className="rounded-lg border border-border p-3 text-sm"><strong className="block text-xl text-primary">{quality?.privacy_reports.high ?? 0}</strong><span className="text-muted-foreground">High privacy reports</span></div>
            <div className="rounded-lg border border-border p-3 text-sm"><strong className="block text-xl text-primary">{quality?.feedback.total ?? 0}</strong><span className="text-muted-foreground">Feedback items</span></div>
            <div className="rounded-lg border border-border p-3 text-sm"><strong className="block text-xl text-primary">{Math.round((quality?.cache.cache_hit_ratio ?? 0) * 100)}%</strong><span className="text-muted-foreground">Cache hit ratio</span></div>
          </div>
        </section>
        <section className="rounded-lg border border-border bg-card p-5">
          <h2 className="font-semibold mb-3">Evaluation operations</h2>
          <div className="flex flex-wrap gap-3">
            <button disabled={busy !== ""} onClick={() => void runEvaluations()} className="btn-base btn-primary">{busy === "evaluations" ? "Running..." : "Launch evaluations"}</button>
            <button disabled={busy !== ""} onClick={() => void dryRunBudget()} className="btn-base btn-secondary">{busy === "budget" ? "Estimating..." : "Dry-run budget"}</button>
            <button disabled={busy !== ""} onClick={() => void compareProviders()} className="btn-base btn-secondary">{busy === "comparison" ? "Comparing..." : "Compare providers"}</button>
            <button disabled={busy !== ""} onClick={() => void exportAudit()} className="btn-base btn-secondary">{busy === "export" ? "Exporting..." : "Export audit CSV"}</button>
            <button disabled={busy !== ""} onClick={() => void createGate()} className="btn-base btn-secondary">{busy === "gate" ? "Creating..." : "Create release gate"}</button>
          </div>
        </section>
        <section className="rounded-lg border border-border bg-card p-5">
          <h2 className="mb-3 font-semibold">Knowledge and RAG</h2>
          <div className="grid gap-3 md:grid-cols-4">
            <div className="rounded-lg border border-border p-3 text-sm"><strong className="block text-xl text-primary">{knowledgeStatus?.collections.length ?? 0}</strong><span className="text-muted-foreground">Collections</span></div>
            <div className="rounded-lg border border-border p-3 text-sm"><strong className="block text-xl text-primary">{knowledgeStatus?.collections.reduce((sum, item) => sum + (item.document_count || 0), 0) ?? 0}</strong><span className="text-muted-foreground">Documents</span></div>
            <div className="rounded-lg border border-border p-3 text-sm"><strong className="block text-xl text-primary">{knowledgeStatus?.collections.reduce((sum, item) => sum + (item.chunk_count || 0), 0) ?? 0}</strong><span className="text-muted-foreground">Chunks</span></div>
            <div className="rounded-lg border border-border p-3 text-sm"><strong className="block text-xl text-primary">{Math.round(Number(knowledgeStatus?.freshness.avg_freshness ?? 0))}%</strong><span className="text-muted-foreground">Freshness</span></div>
          </div>
          <div className="mt-4 flex flex-col gap-3 md:flex-row">
            <input className="flex-1 rounded-lg border border-border bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary/30" value={knowledgeQuery} onChange={(event) => setKnowledgeQuery(event.target.value)} placeholder="Search indexed knowledge..." />
            <button disabled={busy !== "" || !knowledgeQuery.trim()} onClick={() => void testRetrieval()} className="btn-base btn-primary">{busy === "knowledge-search" ? "Searching..." : "Test retrieval"}</button>
            <button disabled={busy !== ""} onClick={() => void createSampleKnowledge()} className="btn-base btn-secondary">{busy === "knowledge-reindex" ? "Indexing..." : "Index sample"}</button>
          </div>
          <div className="mt-4 grid gap-3 md:grid-cols-2">
            <div className="rounded-lg border border-border p-3 text-sm">
              <p className="font-medium">Index status</p>
              {(knowledgeStatus?.status_counts.length ?? 0) > 0 ? knowledgeStatus?.status_counts.map((item) => (
                <p key={item.index_status} className="text-muted-foreground">{item.index_status}: {item.total}</p>
              )) : <p className="text-muted-foreground">No indexed knowledge yet.</p>}
            </div>
            <div className="rounded-lg border border-border p-3 text-sm">
              <p className="font-medium">Embedding versions</p>
              {(embeddingStatus?.embedding_versions.length ?? 0) > 0 ? embeddingStatus?.embedding_versions.map((item) => (
                <p key={`${item.embedding_version}-${item.index_status}`} className="text-muted-foreground">{item.embedding_version} / {item.index_status}: {item.total}</p>
              )) : <p className="text-muted-foreground">No embeddings recorded yet.</p>}
            </div>
            <div className="rounded-lg border border-border p-3 text-sm">
              <p className="font-medium">Vector backend</p>
              <p className="text-muted-foreground">{knowledgeStatus?.vector_backend.backend ?? "unknown"} - {knowledgeStatus?.vector_backend.status ?? "unknown"} - {knowledgeStatus?.vector_backend.dimensions ?? 0} dims</p>
              <p className="text-muted-foreground">Recent retrievals: {embeddingStatus?.recent_retrievals.length ?? 0}</p>
            </div>
            <div className="rounded-lg border border-border p-3 text-sm">
              <p className="font-medium">Freshness exceptions</p>
              <p className="text-muted-foreground">Stale: {knowledgeStatus?.freshness.stale ?? 0}</p>
              <p className="text-muted-foreground">Failed: {knowledgeStatus?.freshness.failed ?? 0}</p>
            </div>
            <div className="rounded-lg border border-border p-3 text-sm md:col-span-2">
              <p className="font-medium">Privacy test summary</p>
              <div className="mt-2 grid gap-2 md:grid-cols-5">
                <p className="text-muted-foreground">Public: {knowledgeStatus?.privacy_summary.public_documents ?? 0}</p>
                <p className="text-muted-foreground">Organization: {knowledgeStatus?.privacy_summary.organization_documents ?? 0}</p>
                <p className="text-muted-foreground">Private: {knowledgeStatus?.privacy_summary.private_documents ?? 0}</p>
                <p className="text-muted-foreground">Private missing owner: {knowledgeStatus?.privacy_summary.private_without_owner ?? 0}</p>
                <p className={knowledgeStatus?.privacy_summary.safe ? "text-primary" : "text-destructive"}>
                  {knowledgeStatus?.privacy_summary.safe ? "Safe" : "Needs review"}
                </p>
              </div>
            </div>
          </div>
          {knowledgeResult && (
            <div className="mt-4 rounded-lg border border-border p-3 text-sm">
              <p className="font-medium">Retrieval confidence {knowledgeResult.confidence}% - {knowledgeResult.latency_ms} ms</p>
              <p className="text-muted-foreground">Sources {knowledgeResult.source_count} - chunks scanned {knowledgeResult.chunk_count} - context {knowledgeResult.context_size} chars{knowledgeResult.timed_out ? " - timed out" : ""}</p>
              <div className="mt-2 space-y-2">
                {knowledgeResult.citations.map((citation) => (
                  <div key={citation.chunk_id} className="rounded-md bg-muted p-2">
                    <p className="font-medium">{citation.title || citation.source_type}</p>
                    <p className="text-muted-foreground">{citation.collection_type} - {citation.source_type}:{citation.source_id} - {citation.confidence}% - {citation.visibility} - freshness {citation.freshness_score}%</p>
                    {citation.deep_link && <p className="text-muted-foreground">{citation.deep_link}</p>}
                  </div>
                ))}
                {knowledgeResult.citations.length === 0 && <p className="text-muted-foreground">No citations found. Index course, job, or FAQ content first.</p>}
              </div>
            </div>
          )}
        </section>
        <section className="rounded-lg border border-border bg-card p-5">
          <h2 className="font-semibold mb-3">Release governance</h2>
          <div className="grid gap-3 md:grid-cols-5">
            <div className="rounded-lg border border-border p-3 text-sm"><strong className="block text-xl text-primary">{quality?.release_governance.release_gates.pending ?? 0}</strong><span className="text-muted-foreground">Pending</span></div>
            <div className="rounded-lg border border-border p-3 text-sm"><strong className="block text-xl text-primary">{quality?.release_governance.release_gates.approved ?? 0}</strong><span className="text-muted-foreground">Approved</span></div>
            <div className="rounded-lg border border-border p-3 text-sm"><strong className="block text-xl text-primary">{quality?.release_governance.release_gates.rejected ?? 0}</strong><span className="text-muted-foreground">Failed gates</span></div>
            <div className="rounded-lg border border-border p-3 text-sm"><strong className="block text-xl text-primary">{quality?.release_governance.release_gates.rolled_back ?? 0}</strong><span className="text-muted-foreground">Rollbacks</span></div>
            <div className="rounded-lg border border-border p-3 text-sm"><strong className="block text-xl text-primary">{Math.round((quality?.release_governance.red_team_pass_rate ?? 0) * 100)}%</strong><span className="text-muted-foreground">Red-team pass</span></div>
          </div>
          <div className="mt-4 grid gap-3">
            {releaseGates.slice(0, 5).map((gate) => (
              <div key={gate.id} className="rounded-lg border border-border p-3 text-sm">
                <div className="flex flex-col gap-2 md:flex-row md:items-center md:justify-between">
                  <div>
                    <p className="font-medium">{gate.change_type.replaceAll("_", " ")} - {gate.feature}</p>
                    <p className="text-muted-foreground">{gate.status} - target {gate.target_id}</p>
                  </div>
                  <div className="flex flex-wrap gap-2">
                    <button disabled={busy !== "" || gate.status !== "approved"} onClick={() => void actOnGate(gate, "promote")} className="btn-base btn-secondary">Promote</button>
                    <button disabled={busy !== ""} onClick={() => void actOnGate(gate, "rollback")} className="btn-base btn-secondary">Rollback</button>
                  </div>
                </div>
              </div>
            ))}
            {releaseGates.length === 0 && <p className="text-sm text-muted-foreground">No release gates created yet.</p>}
          </div>
        </section>
        <section className="rounded-lg border border-border bg-card p-5">
          <h2 className="font-semibold mb-3">Public AI launch checklist</h2>
          <div className="grid gap-2 md:grid-cols-3">
            {Object.entries(quality?.release_governance.launch_checklist.items ?? {}).map(([key, value]) => (
              <div key={key} className="rounded-lg border border-border p-3 text-sm">
                <p className="font-medium">{key.replaceAll("_", " ")}</p>
                <p className={value ? "text-primary" : "text-destructive"}>{value ? "Ready" : "Needs work"}</p>
              </div>
            ))}
          </div>
        </section>
        <section className="rounded-lg border border-border bg-card p-5">
          <h2 className="font-semibold mb-3">Provider status</h2>
          <div className="grid gap-3 md:grid-cols-3">
            {providerStatus?.providers.map((provider) => (
              <div key={provider.id} className="rounded-lg border border-border p-3 text-sm">
                <p className="font-medium">{provider.name}</p>
                <p className="text-muted-foreground">{provider.provider_type} - {provider.health_status}</p>
                <p className="text-muted-foreground">Priority {provider.priority} - timeout {provider.timeout_seconds}s</p>
              </div>
            ))}
          </div>
        </section>
        <section className="rounded-lg border border-border bg-card p-5">
          <h2 className="font-semibold mb-3">Feature flags</h2>
          <div className="divide-y divide-border">
            {flags.map((flag) => (
              <div key={flag.id} className="py-3 text-sm grid gap-2 md:grid-cols-[1fr_120px_1fr]">
                <span>{flag.feature.replaceAll("_", " ")}</span>
                <span>{flag.is_enabled ? "enabled" : "disabled"}</span>
                <span className="text-muted-foreground">{flag.reason || "No reason recorded"}</span>
              </div>
            ))}
            {flags.length === 0 && <p className="text-sm text-muted-foreground">No feature overrides configured.</p>}
          </div>
        </section>
        <section className="rounded-lg border border-border bg-card p-5">
          <h2 className="font-semibold mb-3">Evaluation results</h2>
          <div className="divide-y divide-border">
            {evaluations?.runs.map((run) => (
              <div key={run.id} className="py-3 text-sm grid gap-2 md:grid-cols-[1fr_120px_120px_120px]">
                <span>{run.dataset_name}</span>
                <span>{run.status}</span>
                <span>{run.average_score ?? "n/a"}</span>
                <span>{run.average_latency_ms} ms</span>
              </div>
            ))}
            {evaluations?.runs.length === 0 && <p className="text-sm text-muted-foreground">No evaluation runs yet.</p>}
          </div>
        </section>
        <section className="rounded-lg border border-border bg-card p-5">
          <h2 className="font-semibold mb-3">Prompt templates</h2>
          <div className="divide-y divide-border">
            {overview?.prompt_templates.map((template) => (
              <div key={template.id} className="py-3 text-sm grid gap-2 md:grid-cols-[1fr_160px_80px_80px]">
                <span>{template.name}</span>
                <span>{template.feature.replaceAll("_", " ")}</span>
                <span>v{template.version}</span>
                <span>{template.locale}</span>
              </div>
            ))}
          </div>
        </section>
      </div>
    </main>
  );
}
