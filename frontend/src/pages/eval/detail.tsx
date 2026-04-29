import { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { api } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { EvalRunDetailResponse } from "@/types/eval";
import { ArrowLeft, RefreshCw, Loader2, Download } from "lucide-react";

export function EvalDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [run, setRun] = useState<EvalRunDetailResponse | null>(null);
  const [loading, setLoading] = useState(true);

  const fetchRun = async () => {
    if (!id) return;
    setLoading(true);
    try {
      const res = await api.get(`/api/v1/eval-runs/${id}`);
      setRun(res.data);
    } catch (err) {
      console.error("Failed to fetch eval run", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchRun();
  }, [id]);

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

  const handleExport = (format: "json" | "csv") => {
    if (!id) return;
    const url = `/api/v1/eval-runs/${id}/export/${format}`;
    window.open(url, "_blank");
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
            onClick={fetchRun}
          >
            <RefreshCw className="h-4 w-4" />
            Refresh
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

      {run.results_summary && run.results_summary.metrics && (
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
                            <span
                              key={score.id}
                              className="inline-flex items-center rounded bg-secondary px-1.5 py-0.5 text-xs text-secondary-foreground"
                              title={score.explanation || ""}
                            >
                              {score.metric_name}: {score.score.toFixed(2)}
                            </span>
                          ))}
                        </div>
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
          Evaluation in progress... refresh to see updates.
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
  };
  return (
    <span
      className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${styles[status] || styles.pending}`}
    >
      {status}
    </span>
  );
}
