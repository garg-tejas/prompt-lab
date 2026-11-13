import { useState } from "react";
import { Link } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { PageHeading, RegistrySearch, RegistryState, StatusLabel, StatusFilter } from "@/components/workbench";
import { useRegistry } from "@/hooks/useRegistry";
import type { ABTestResponse } from "@/types/ab_test";
import { Plus } from "lucide-react";

export function ABTestListPage() {
  const registry = useRegistry<ABTestResponse>("/api/v1/ab-tests", true);
  return <ComparisonRegisterView {...registry} />;
}

export function ComparisonRegisterView({ rows: tests, loading, error, refresh, isSignedIn }: {
  rows: ABTestResponse[]; loading: boolean; error: boolean; refresh: () => void; isSignedIn?: boolean;
}) {
  const [query, setQuery] = useState("");
  const [status, setStatus] = useState("all");
  const filtered = tests.filter((test) => (status === "all" || test.status === status) && `${test.name} ${test.id}`.toLowerCase().includes(query.toLowerCase()));
  return <div className="container">
    <PageHeading index="03 / Compare" title="Comparison register" description="Two runs. Paired inputs. Inspect the change in quality and cost alongside the evidence that supports it." action={isSignedIn && <Button asChild className="gap-2"><Link to="/ab-tests/new"><Plus size={15} />New comparison</Link></Button>} />
    <RegistrySearch value={query} onChange={setQuery} placeholder="Find a comparison…"><StatusFilter value={status} onChange={setStatus} /><span className="lab-count">{filtered.length} / {tests.length} comparisons</span></RegistrySearch>
    {!isSignedIn ? <RegistryState title="Sign in to inspect comparisons"><Link to="/sign-in" className="text-primary underline">Sign in to PromptLab</Link></RegistryState>
      : loading ? <RegistryState title="Loading comparisons…">Retrieving paired-run summaries.</RegistryState>
      : error ? <RegistryState title="Comparisons could not be loaded" error onRetry={refresh}>Check the connection and retry.</RegistryState>
      : !tests.length ? <RegistryState title="A comparison begins with two completed runs">Evaluate two versions on matching inputs, then inspect paired differences. Coverage and dataset provenance remain part of the decision.</RegistryState>
      : !filtered.length ? <RegistryState title="No matching comparisons">Change the search or selected status.</RegistryState>
      : <div className="lab-table-wrap" tabIndex={0} role="region" aria-label="A/B comparisons table"><table className="lab-table"><thead><tr><th scope="col">Comparison / paired runs</th><th scope="col">Status</th><th scope="col">Input evidence</th><th scope="col">Observed preference</th></tr></thead><tbody>{filtered.map((test) => { const summary = test.status === "completed" ? test.results_summary : null; return <tr key={test.id}><td><Link to={`/ab-tests/${test.id}`} className="lab-table-name">{test.name}</Link><div className="lab-table-meta">A {test.eval_run_a_id.slice(0, 8)} <span aria-hidden="true">↔</span> B {test.eval_run_b_id.slice(0, 8)}</div><div className="lab-table-meta">{new Date(test.created_at).toLocaleDateString()}</div></td><td><StatusLabel status={test.status} /></td><td className="lab-table-meta">{summary ? <>{summary.total_samples} paired rows<div>{summary.dataset_snapshot_status === "matching" ? "Matching input fingerprints" : summary.dataset_snapshot_status === "different" ? "Different input fingerprints" : "Input fingerprints unverified"}</div><div>{summary.coverage?.complete ? "Result rows complete" : "Result rows incomplete / unknown"}</div></> : "Available after completion"}</td><td>{summary ? <><span className="lab-tag">{summary.overall_winner === "a" ? "Quality metrics favor A" : summary.overall_winner === "b" ? "Quality metrics favor B" : "No overall preference"}</span><p className="lab-table-description">Inspect metric coverage before deciding.</p></> : <span className="lab-table-meta">Not available</span>}</td></tr>; })}</tbody></table></div>}
    <p className="lab-footnote">Paired differences describe these recorded samples. They are not an automatic release decision or a claim of general superiority.</p>
  </div>;
}
