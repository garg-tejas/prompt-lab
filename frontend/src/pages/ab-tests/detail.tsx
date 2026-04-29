import { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { api } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { ABTestDetailResponse } from "@/types/ab_test";
import { ArrowLeft, RefreshCw, Trophy, AlertTriangle } from "lucide-react";

export function ABTestDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [test, setTest] = useState<ABTestDetailResponse | null>(null);
  const [loading, setLoading] = useState(true);

  const fetchTest = async () => {
    if (!id) return;
    setLoading(true);
    try {
      const res = await api.get(`/api/v1/ab-tests/${id}`);
      setTest(res.data);
    } catch (err) {
      console.error("Failed to fetch AB test", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchTest();
  }, [id]);

  if (loading) {
    return (
      <div className="container py-8 text-sm text-muted-foreground font-mono animate-pulse">
        Loading A/B test...
      </div>
    );
  }

  if (!test) {
    return (
      <div className="container py-8 text-sm text-muted-foreground">
        A/B test not found.
      </div>
    );
  }

  const isRunning = test.status === "running" || test.status === "pending";
  const metrics = test.results_summary?.metrics || {};
  const overall = test.results_summary?.overall_winner;

  return (
    <div className="container py-8 space-y-6">
      <div className="flex items-center gap-4">
        <Button
          variant="outline"
          size="sm"
          className="gap-1"
          onClick={() => navigate("/ab-tests")}
        >
          <ArrowLeft className="h-4 w-4" />
          Back
        </Button>
        {isRunning && (
          <Button
            variant="outline"
            size="sm"
            className="gap-1"
            onClick={fetchTest}
          >
            <RefreshCw className="h-4 w-4" />
            Refresh
          </Button>
        )}
      </div>

      <div className="space-y-1">
        <div className="flex items-center gap-3">
          <h1 className="text-3xl font-bold tracking-tight">{test.name}</h1>
          {overall && overall !== "tie" && (
            <span className="inline-flex items-center gap-1 rounded-full bg-primary/10 px-3 py-1 text-sm font-medium text-primary">
              <Trophy className="h-4 w-4" />
              {overall === "a" ? "Run A Wins" : "Run B Wins"}
            </span>
          )}
        </div>
        <div className="text-xs text-muted-foreground font-mono">
          {test.status === "completed" && test.results_summary && (
            <>
              {test.results_summary.total_samples} paired samples ·{" "}
              {test.results_summary.a_wins} metrics favor A ·{" "}
              {test.results_summary.b_wins} metrics favor B
            </>
          )}
        </div>
      </div>

      {/* Head-to-Head Table */}
      {Object.keys(metrics).length > 0 && (
        <Card className="border-border">
          <CardHeader className="pb-2">
            <CardTitle className="text-base">Head-to-Head Comparison</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-border text-left text-muted-foreground">
                    <th className="pb-2 pr-4 font-medium">Metric</th>
                    <th className="pb-2 pr-4 font-medium">Mean Diff (A − B)</th>
                    <th className="pb-2 pr-4 font-medium">Std Dev</th>
                    <th className="pb-2 pr-4 font-medium">95% CI</th>
                    <th className="pb-2 pr-4 font-medium">Significant?</th>
                    <th className="pb-2 font-medium">Winner</th>
                  </tr>
                </thead>
                <tbody>
                  {Object.entries(metrics).map(([name, stats]: [string, any]) => (
                    <tr
                      key={name}
                      className={`border-b border-border/50 last:border-0 ${
                        stats.winner !== "tie" ? "bg-primary/5" : ""
                      }`}
                    >
                      <td className="py-3 pr-4 font-medium capitalize">
                        {name.replace("_", " ")}
                      </td>
                      <td className="py-3 pr-4 font-mono">
                        {stats.mean_diff > 0 ? "+" : ""}
                        {stats.mean_diff.toFixed(3)}
                      </td>
                      <td className="py-3 pr-4 font-mono text-muted-foreground">
                        {stats.std_dev.toFixed(3)}
                      </td>
                      <td className="py-3 pr-4 font-mono text-muted-foreground">
                        [{stats.ci_95[0].toFixed(3)}, {stats.ci_95[1].toFixed(3)}]
                      </td>
                      <td className="py-3 pr-4">
                        {stats.significant ? (
                          <span className="inline-flex items-center rounded-full bg-green-500/10 px-2 py-0.5 text-xs font-medium text-green-500">
                            Yes
                          </span>
                        ) : (
                          <span className="inline-flex items-center gap-1 rounded-full bg-amber-500/10 px-2 py-0.5 text-xs font-medium text-amber-500">
                            <AlertTriangle className="h-3 w-3" />
                            No
                          </span>
                        )}
                      </td>
                      <td className="py-3">
                        {stats.winner === "a" && (
                          <span className="text-sm font-semibold text-primary">A</span>
                        )}
                        {stats.winner === "b" && (
                          <span className="text-sm font-semibold text-destructive">B</span>
                        )}
                        {stats.winner === "tie" && (
                          <span className="text-sm text-muted-foreground">Tie</span>
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

      {/* Per-Sample Breakdown */}
      {test.per_sample_breakdown && test.per_sample_breakdown.length > 0 && (
        <Card className="border-border">
          <CardHeader className="pb-2">
            <CardTitle className="text-base">Per-Sample Breakdown</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-border text-left text-muted-foreground">
                    <th className="pb-2 pr-4 font-medium">Sample</th>
                    <th className="pb-2 pr-4 font-medium">A Wins</th>
                    <th className="pb-2 pr-4 font-medium">B Wins</th>
                    <th className="pb-2 font-medium">Ties</th>
                  </tr>
                </thead>
                <tbody>
                  {test.per_sample_breakdown.map((row, idx) => (
                    <tr
                      key={idx}
                      className="border-b border-border/50 last:border-0"
                    >
                      <td className="py-2 pr-4 font-mono text-muted-foreground">
                        {idx + 1}
                      </td>
                      <td className="py-2 pr-4">
                        {row.wins.a > 0 && (
                          <span className="rounded bg-primary/10 px-1.5 py-0.5 text-xs font-medium text-primary">
                            {row.wins.a}
                          </span>
                        )}
                      </td>
                      <td className="py-2 pr-4">
                        {row.wins.b > 0 && (
                          <span className="rounded bg-destructive/10 px-1.5 py-0.5 text-xs font-medium text-destructive">
                            {row.wins.b}
                          </span>
                        )}
                      </td>
                      <td className="py-2">
                        {row.wins.tie > 0 && (
                          <span className="rounded bg-secondary px-1.5 py-0.5 text-xs text-secondary-foreground">
                            {row.wins.tie}
                          </span>
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
        <div className="text-sm text-muted-foreground font-mono animate-pulse">
          Computing comparison... refresh to see updates.
        </div>
      )}
    </div>
  );
}
