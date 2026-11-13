import { useState } from "react";
import { Link } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { PageHeading, RegistrySearch, RegistryState, StatusLabel, StatusFilter } from "@/components/workbench";
import { useRegistry } from "@/hooks/useRegistry";
import type { EvalRunResponse } from "@/types/eval";
import { Plus } from "lucide-react";

function metricValue(value: unknown) {
  const numeric = value !== null && typeof value === "object" && "mean" in value ? (value as { mean: unknown }).mean : value;
  return typeof numeric === "number" && Number.isFinite(numeric) ? numeric.toFixed(2) : "Unavailable";
}

export function EvalHistoryPage() {
  const registry = useRegistry<EvalRunResponse>("/api/v1/eval-runs", true);
  return <RunLedgerView {...registry} />;
}

export function RunLedgerView({ rows: runs, loading, error, refresh, isSignedIn }: {
  rows: EvalRunResponse[]; loading: boolean; error: boolean; refresh: () => void; isSignedIn?: boolean;
}) {
  const [query, setQuery] = useState("");
  const [status, setStatus] = useState("all");
  const filtered = runs.filter((run) => (status === "all" || run.status === status) && `${run.name} ${run.id}`.toLowerCase().includes(query.toLowerCase()));
  return <div className="container">
    <PageHeading index="02 / Evaluate" title="Run ledger" description="Inspect what ran, which inputs were used, and how it scored. Open a run to review individual outputs and human overrides." action={isSignedIn && <Button asChild className="gap-2"><Link to="/runs/new"><Plus size={15} />Configure evaluation</Link></Button>} />
    <RegistrySearch value={query} onChange={setQuery} placeholder="Find a run by name or ID…"><StatusFilter value={status} onChange={setStatus} /><span className="lab-count">{filtered.length} / {runs.length} runs</span></RegistrySearch>
    {!isSignedIn ? <RegistryState title="Sign in to inspect your runs"><Link to="/sign-in" className="text-primary underline">Sign in to PromptLab</Link></RegistryState>
      : loading ? <RegistryState title="Loading evaluation runs…">Retrieving the run ledger.</RegistryState>
      : error ? <RegistryState title="Runs could not be refreshed" error onRetry={refresh}>Check the connection and retry. No result is inferred from an unavailable run.</RegistryState>
      : !runs.length ? <RegistryState title="No experiments recorded yet">Configure an evaluation with a saved prompt version, dataset, and model endpoint. Launching a run uses your configured model provider.</RegistryState>
      : !filtered.length ? <RegistryState title="No runs match these filters">Change the search or status to see more of the ledger.</RegistryState>
      : <div className="lab-table-wrap" tabIndex={0} role="region" aria-label="Evaluation runs table"><table className="lab-table"><thead><tr><th scope="col">Evaluation / run ID</th><th scope="col">Status</th><th scope="col">Recorded metrics</th><th scope="col">Created</th></tr></thead><tbody>{filtered.map((run) => <tr key={run.id}><td><Link to={`/runs/${run.id}`} className="lab-table-name">{run.name}</Link><div className="lab-table-meta" title={run.id}>{run.id.slice(0, 12)}</div></td><td><StatusLabel status={run.status} /></td><td>{run.results_summary?.metrics && Object.keys(run.results_summary.metrics).length ? <div className="space-y-1">{Object.entries(run.results_summary.metrics).map(([name, value]) => <div className="lab-table-meta" key={name}><span>{name.replace(/_/g, " ")}</span><strong className="ml-3 font-medium text-foreground">{metricValue(value)}</strong></div>)}</div> : <span className="lab-table-meta">No metrics recorded</span>}</td><td className="lab-table-meta">{new Date(run.created_at).toLocaleDateString(undefined, { month: "short", day: "numeric", year: "numeric" })}<div>{new Date(run.created_at).toLocaleTimeString(undefined, { hour: "2-digit", minute: "2-digit" })}</div></td></tr>)}</tbody></table></div>}
    <p className="lab-footnote">Pending and running evaluations refresh every 3 seconds. Metric values are recorded means; inspect coverage and individual examples before drawing conclusions.</p>
  </div>;
}
