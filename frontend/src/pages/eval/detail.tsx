import { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { api } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { EvalRunDetailResponse } from "@/types/eval";
import { ArrowLeft, Loader2, Download } from "lucide-react";

export function EvalDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [run, setRun] = useState<EvalRunDetailResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [cancelling, setCancelling] = useState(false);
  const [reviewId, setReviewId] = useState<string | null>(null);
  const [reviewScore, setReviewScore] = useState("");
  const [reviewNote, setReviewNote] = useState("");

  useEffect(() => {
    if (!id) return;
    let timer = 0;
    let active = true;

    const tick = async () => {
      try {
        const res = await api.get(`/api/v1/eval-runs/${id}`);
        if (!active) return;
        setRun(res.data);
        const status = res.data.status as string;
        if (status === "pending" || status === "running") {
          timer = window.setTimeout(tick, 2000);
        }
      } catch (err) {
        console.error("Failed to fetch eval run", err);
      } finally {
        if (active) setLoading(false);
      }
    };

    tick();
    return () => {
      active = false;
      window.clearTimeout(timer);
    };
  }, [id]);

  const cancelRun = async () => {
    if (!id) return;
    setCancelling(true);
    try {
      const res = await api.post(`/api/v1/eval-runs/${id}/cancel`);
      setRun((current) => (current ? { ...current, ...res.data, results: current.results } : current));
    } catch (err) {
      console.error("Failed to cancel eval run", err);
    } finally {
      setCancelling(false);
    }
  };

  if (loading) {
    return (
      <div className="container py-8 text-sm text-muted-foreground font-mono animate-pulse">
        Loading eval run...
      </div>
    );
  }

  if (!run) {
    return (
      <div className="container py-8 text-sm text-muted-foreground">
        Eval run not found.
      </div>
    );
  }

  const isRunning = run.status === "running" || run.status === "pending";

  const handleExport = async (format: "json" | "csv") => {
    if (!id) return;
    const res = await api.get(`/api/v1/eval-runs/${id}/export/${format}`, {
      responseType: "blob",
    });
    const href = URL.createObjectURL(res.data);
    const link = document.createElement("a");
    link.href = href;
    link.download = `run-${id}.${format}`;
    link.click();
    URL.revokeObjectURL(href);
  };

  return (
    <div className="container py-8 space-y-6">
      <div className="flex items-center gap-4">
        <Button
          variant="outline"
          size="sm"
          className="gap-1"
          onClick={() => navigate("/runs")}
        >
          <ArrowLeft className="h-4 w-4" />
          Back
        </Button>
        {isRunning && (
          <Button
            variant="outline"
            size="sm"
            className="gap-1"
            disabled={cancelling}
            onClick={cancelRun}
          >
            {cancelling ? "Stopping..." : "Stop"}
          </Button>
        )}
        {run.status === "completed" && (
          <>
            <Button
              variant="outline"
              size="sm"
              className="gap-1"
              onClick={() => handleExport("json")}
            >
              <Download className="h-4 w-4" />
              JSON
            </Button>
            <Button
              variant="outline"
              size="sm"
              className="gap-1"
              onClick={() => handleExport("csv")}
            >
              <Download className="h-4 w-4" />
              CSV
            </Button>
          </>
        )}
      </div>

      <div className="space-y-1">
        <div className="flex items-center gap-3">
          <h1 className="text-3xl font-bold tracking-tight">{run.name}</h1>
          <StatusBadge status={run.status} />
        </div>
        <div className="text-xs text-muted-foreground font-mono">
          Created: {new Date(run.created_at).toLocaleString()}
          {run.completed_at &&
            ` | Completed: ${new Date(run.completed_at).toLocaleString()}`}
        </div>
      </div>

      {run.results_summary?.anomaly && (
        <div className="rounded-lg border border-amber-500/40 bg-amber-500/10 px-4 py-3 text-sm">
          <div className="font-medium text-amber-400">Regression against the previous run</div>
          <ul className="mt-2 space-y-1 font-mono text-xs text-amber-100/80">
            {run.results_summary.anomaly.drops.map((drop: { metric: string; previous: number; current: number; drop: number }) => (
              <li key={drop.metric}>
                {drop.metric}: {drop.previous.toFixed(2)} → {drop.current.toFixed(2)} (Δ {drop.drop.toFixed(2)})
              </li>
            ))}
          </ul>
        </div>
      )}

      {isRunning && run.results_summary?.progress && (
        <div className="space-y-2">
          <div className="flex justify-between text-xs font-mono text-muted-foreground">
            <span>Scoring rows</span>
            <span>
              {run.results_summary.progress.completed} / {run.results_summary.progress.total}
            </span>
          </div>
          <div className="h-1.5 overflow-hidden rounded-full bg-secondary">
            <div
              className="h-full bg-primary transition-all"
              style={{
                width: `${Math.min(
                  100,
                  (run.results_summary.progress.completed / Math.max(run.results_summary.progress.total, 1)) * 100
                )}%`,
              }}
            />
          </div>
        </div>
      )}

      {run.results_summary && run.results_summary.metrics && Object.keys(run.results_summary.metrics).length > 0 && (
        <Card className="border-border">
          <CardHeader className="pb-2">
            <CardTitle className="text-base">Metrics Summary</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
              {Object.entries(run.results_summary.metrics).map(
                ([name, stats]: [string, any]) => (
                  <div
                    key={name}
                    className="rounded-lg border border-border p-3"
                  >
                    <div className="text-xs text-muted-foreground capitalize">
                      {name.replace("_", " ")}
                    </div>
                    <div className="text-2xl font-bold text-foreground">
                      {typeof stats === "object" ? stats.mean.toFixed(2) : stats}
                    </div>
                    {typeof stats === "object" && (
                      <div className="text-xs text-muted-foreground font-mono mt-1">
                        min {stats.min.toFixed(2)} / max {stats.max.toFixed(2)}
                      </div>
                    )}
                  </div>
                )
              )}
            </div>
          </CardContent>
        </Card>
      )}

      {run.results && run.results.length > 0 && (
        <Card className="border-border">
          <CardHeader className="pb-2">
            <CardTitle className="text-base">Per-Sample Results</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-border text-left text-muted-foreground">
                    <th className="pb-2 pr-4 font-medium">#</th>
                    <th className="pb-2 pr-4 font-medium">Output</th>
                    <th className="pb-2 pr-4 font-medium">Latency</th>
                    <th className="pb-2 pr-4 font-medium">Tokens</th>
                    <th className="pb-2 pr-4 font-medium">Cost</th>
                    <th className="pb-2 font-medium">Scores</th>
                  </tr>
                </thead>
                <tbody>
                  {run.results.map((result, idx) => (
                    <tr
                      key={result.id}
                      className="border-b border-border/50 last:border-0"
                    >
                      <td className="py-3 pr-4 font-mono text-muted-foreground">
                        {idx + 1}
                      </td>
                      <td className="py-3 pr-4 max-w-xs truncate">
                        {result.output}
                      </td>
                      <td className="py-3 pr-4 font-mono text-muted-foreground">
                        {result.latency_ms.toFixed(0)}ms
                      </td>
                      <td className="py-3 pr-4 font-mono text-muted-foreground">
                        {result.input_tokens}+{result.output_tokens}
                      </td>
                      <td className="py-3 pr-4 font-mono text-muted-foreground">
                        ${result.estimated_cost.toFixed(4)}
                      </td>
                      <td className="py-3">
                        <div className="flex flex-wrap gap-1">
                          {result.scores.map((score) => (
                            <button
                              key={score.id}
                              type="button"
                              className="inline-flex items-center gap-1 rounded bg-secondary px-1.5 py-0.5 text-xs text-secondary-foreground"
                              title={score.human_note || score.explanation || ""}
                              onClick={() => {
                                setReviewId(score.id);
                                setReviewScore(
                                  score.human_score != null ? String(score.human_score) : ""
                                );
                                setReviewNote(score.human_note || "");
                              }}
                            >
                              {score.metric_name}:{" "}
                              {score.human_score ?? score.score ?? "—"}
                              {score.human_score != null ? " human" : ""}
                            </button>
                          ))}
                        </div>
                        {result.scores.some((score) => score.id === reviewId) && (
                          <form
                            className="mt-2 flex flex-wrap items-center gap-2"
                            onSubmit={async (event) => {
                              event.preventDefault();
                              if (!reviewId) return;
                              const parsed = Number(reviewScore);
                              if (Number.isNaN(parsed)) return;
                              await api.post(`/api/v1/eval-runs/scores/${reviewId}/review`, {
                                score: parsed,
                                note: reviewNote || null,
                              });
                              setRun((current) => {
                                if (!current) return current;
                                return {
                                  ...current,
                                  results: current.results.map((row) => ({
                                    ...row,
                                    scores: row.scores.map((item) =>
                                      item.id === reviewId
                                        ? { ...item, human_score: parsed, human_note: reviewNote || null }
                                        : item
                                    ),
                                  })),
                                };
                              });
                              setReviewId(null);
                            }}
                          >
                            <input
                              aria-label="Human score"
                              className="w-16 rounded border border-border bg-background px-1 font-mono text-xs"
                              value={reviewScore}
                              onChange={(event) => setReviewScore(event.target.value)}
                              placeholder="0-1"
                            />
                            <input
                              aria-label="Review note"
                              className="w-40 rounded border border-border bg-background px-1 text-xs"
                              value={reviewNote}
                              onChange={(event) => setReviewNote(event.target.value)}
                              placeholder="Note"
                            />
                            <button className="font-mono text-xs" type="submit">
                              Save review
                            </button>
                          </form>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>
      )}

      {isRunning && (
        <div className="flex items-center gap-2 text-sm text-muted-foreground">
          <Loader2 className="h-4 w-4 animate-spin" />
          Evaluation in progress. This page updates on its own.
        </div>
      )}
    </div>
  );
}

function StatusBadge({ status }: { status: string }) {
  const styles: Record<string, string> = {
    pending: "bg-muted text-muted-foreground",
    running: "bg-amber-500/10 text-amber-500",
    completed: "bg-green-500/10 text-green-500",
    failed: "bg-red-500/10 text-red-500",
    cancelled: "bg-muted text-muted-foreground",
  };
  return (
    <span
      className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${styles[status] || styles.pending}`}
    >
      {status}
    </span>
  );
}
