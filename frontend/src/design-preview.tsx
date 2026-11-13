// Isolated development entry. Not imported by main.tsx or included in production build inputs.
import React, { useState } from "react";
import { createRoot } from "react-dom/client";
import { MemoryRouter, useLocation } from "react-router-dom";
import { WorkbenchFrame } from "@/components/shell";
import { PromptRegistryView } from "@/pages/prompts/list";
import { RunLedgerView } from "@/pages/eval/history";
import { ComparisonRegisterView } from "@/pages/ab-tests/list";
import { RegistryState } from "@/components/workbench";
import { NoticeHost } from "@/components/notice";
import { api } from "@/lib/api";
import type { Prompt } from "@/types";
import type { EvalRunResponse } from "@/types/eval";
import type { ABTestResponse } from "@/types/ab_test";
import "@/index.css";

// Deny every API request from fixture interactions; no credentials, provider, or backend is used.
api.defaults.adapter = async () => { throw new Error("UI fixture: network operations are disabled."); };
const prompts: Prompt[] = ["Support answer / grounded response", "Release notes / concise summary", "Query router / intent classification"].map((name, index) => ({
  id: `fixture-prompt-${index}`, name, description: ["Answer from the supplied context and cite the relevant source.", "Turn a list of changes into a readable product update.", "Classify requests before choosing a retrieval strategy."][index], owner_id: "fixture", tags: [{ id: `tag-${index}`, name: ["retrieval", "writing", "routing"][index] }], created_at: "2026-01-01", updated_at: "2026-01-01", version_count: [4, 2, 1][index], latest_version: null, production_version: null,
}));
const runs: EvalRunResponse[] = ["completed", "running", "failed"].map((status, index) => ({
  id: `fixture-run-${index}`, name: ["Grounded answer / candidate revision", "Release notes / baseline", "Router / endpoint timeout"][index], prompt_id: "fixture-prompt", prompt_version_id: "fixture-version", dataset_id: "fixture-dataset", model_id: "fixture-model", judge_model_id: "fixture-judge", status, config: { concurrency: 1, retry_count: 0 }, results_summary: status === "completed" ? { metrics: { answer_correctness: { mean: 0.74 }, context_recall: { mean: null } } } : null, created_by: "fixture", created_at: "2026-01-01T10:30:00Z", completed_at: null,
}));
const tests: ABTestResponse[] = ["completed", "running", "completed"].map((status, index) => ({
  id: `fixture-comparison-${index}`, name: ["Grounding instructions / revision 3 vs 4", "Summary length / baseline vs candidate", "Router thresholds / historic comparison"][index], eval_run_a_id: "fixture-run-a", eval_run_b_id: "fixture-run-b", dataset_id: "fixture-dataset", status, results_summary: status === "completed" ? { metrics: {}, overall_winner: "tie", a_wins: 0, b_wins: 0, total_samples: 12, dataset_snapshot_status: index === 0 ? "matching" : "unknown" } : null, created_by: "fixture", created_at: "2026-01-01T10:30:00Z", completed_at: null,
}));

function Preview() {
  const { pathname } = useLocation();
  const [state, setState] = useState("populated");
  const shared = { loading: state === "loading", error: state === "error", isSignedIn: state !== "signed-out", refresh: () => setState("populated") };
  const longText = state === "long-text";
  return <><div className="fixture-banner"><strong>ISOLATED UI FIXTURES</strong><span>Synthetic records, not project results. Network operations disabled.</span><label>State <select value={state} onChange={(event) => setState(event.target.value)}>{["populated", "loading", "error", "empty", "long-text", "signed-out"].map((value) => <option key={value}>{value}</option>)}</select></label></div><NoticeHost /><WorkbenchFrame account={<span>UI preview</span>}>
    {pathname === "/" ? <PromptRegistryView {...shared} rows={state === "empty" ? [] : prompts.map((prompt) => longText ? { ...prompt, name: `${prompt.name} / a deliberately long title to inspect wrapping`, description: `${prompt.description} ${prompt.description} ${prompt.description}` } : prompt)} />
      : pathname === "/runs" ? <RunLedgerView {...shared} rows={state === "empty" ? [] : runs} />
      : pathname === "/ab-tests" ? <ComparisonRegisterView {...shared} rows={state === "empty" ? [] : tests} />
      : <div className="container"><RegistryState title="This screen is outside the UI fixture">Use Prompt registry, Evaluation runs, or A/B comparisons in the navigation. No backend is connected.</RegistryState></div>}
  </WorkbenchFrame></>;
}
if (import.meta.env.DEV) createRoot(document.getElementById("root")!).render(<React.StrictMode><MemoryRouter><Preview /></MemoryRouter></React.StrictMode>);
