import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ArrowLeft, GitCompare } from "lucide-react";
import type { EvalRunResponse } from "@/types/eval";

interface ComparisonResult {
  run_a: { id: string; name: string; status: string };
  run_b: { id: string; name: string; status: string };
  comparison: Record<string, { a: number | null; b: number | null; delta: number | null }>;
}

export function RunComparisonPage() {
  const navigate = useNavigate();
  const [runs, setRuns] = useState<EvalRunResponse[]>([]);
  const [selectedA, setSelectedA] = useState<EvalRunResponse | null>(null);
  const [selectedB, setSelectedB] = useState<EvalRunResponse | null>(null);
  const [comparison, setComparison] = useState<ComparisonResult | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    api.get("/api/v1/eval-runs").then((r) => {
      setRuns(r.data.filter((run: EvalRunResponse) => run.status === "completed"));
    });
  }, []);

  const handleCompare = async () => {
    if (!selectedA || !selectedB) return;
    setLoading(true);
    try {
      const res = await api.get(`/api/v1/analytics/runs/${selectedA.id}/compare/${selectedB.id}`);
      setComparison(res.data);
    } catch (err) {
      console.error("Failed to compare runs", err);
      alert("Failed to compare runs");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="container py-8 max-w-3xl mx-auto">
      <div className="flex items-center gap-4 mb-8">
        <Button
          variant="outline"
          size="sm"
          className="gap-1"
          onClick={() => navigate("/runs")}
        >
          <ArrowLeft className="h-4 w-4" />
          Back
        </Button>
      </div>

      <h1 className="text-3xl font-bold tracking-tight mb-2">Compare Runs</h1>
      <p className="text-muted-foreground mb-8">
        Pick two completed eval runs and see metric deltas.
      </p>

      <div className="grid gap-4 md:grid-cols-2 mb-6">
        <Card className="border-border">
          <CardHeader className="pb-2">
            <CardTitle className="text-base">Run A</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2 max-h-64 overflow-y-auto">
            {runs.map((run) => (
              <button
                key={run.id}
                onClick={() => { setSelectedA(run); setComparison(null); }}
                disabled={selectedB?.id === run.id}
                className={`w-full text-left rounded-lg border p-3 transition-colors disabled:opacity-40 ${
                  selectedA?.id === run.id
                    ? "border-primary bg-primary/5"
                    : "border-border hover:bg-secondary/30"
                }`}
              >
                <div className="font-medium text-sm">{run.name}</div>
                <div className="text-xs text-muted-foreground font-mono">
                  {new Date(run.created_at).toLocaleDateString()}
                </div>
              </button>
            ))}
          </CardContent>
        </Card>

        <Card className="border-border">
          <CardHeader className="pb-2">
            <CardTitle className="text-base">Run B</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2 max-h-64 overflow-y-auto">
            {runs.map((run) => (
              <button
                key={run.id}
                onClick={() => { setSelectedB(run); setComparison(null); }}
                disabled={selectedA?.id === run.id}
                className={`w-full text-left rounded-lg border p-3 transition-colors disabled:opacity-40 ${
                  selectedB?.id === run.id
                    ? "border-primary bg-primary/5"
                    : "border-border hover:bg-secondary/30"
                }`}
              >
                <div className="font-medium text-sm">{run.name}</div>
                <div className="text-xs text-muted-foreground font-mono">
                  {new Date(run.created_at).toLocaleDateString()}
                </div>
              </button>
            ))}
          </CardContent>
        </Card>
      </div>

      <div className="flex items-center gap-2 mb-8">
        <Button
          disabled={!selectedA || !selectedB || loading}
          onClick={handleCompare}
          className="gap-2"
        >
          <GitCompare className="h-4 w-4" />
          {loading ? "Comparing..." : "Compare"}
        </Button>
      </div>

      {comparison && (
        <Card className="border-border">
          <CardHeader className="pb-2">
            <CardTitle className="text-base">Results</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-border text-left text-muted-foreground">
                    <th className="pb-2 pr-4 font-medium">Metric</th>
                    <th className="pb-2 pr-4 font-medium">Run A</th>
                    <th className="pb-2 pr-4 font-medium">Run B</th>
                    <th className="pb-2 font-medium">Delta (A − B)</th>
                  </tr>
                </thead>
                <tbody>
                  {Object.entries(comparison.comparison).map(([name, vals]: [string, any]) => (
                    <tr key={name} className="border-b border-border/50 last:border-0">
                      <td className="py-3 pr-4 font-medium capitalize">
                        {name.replace("_", " ")}
                      </td>
                      <td className="py-3 pr-4 font-mono">
                        {vals.a !== null ? vals.a.toFixed(3) : "—"}
                      </td>
                      <td className="py-3 pr-4 font-mono">
                        {vals.b !== null ? vals.b.toFixed(3) : "—"}
                      </td>
                      <td className="py-3">
                        {vals.delta !== null ? (
                          <span
                            className={`font-mono font-semibold ${
                              vals.delta > 0
                                ? "text-green-500"
                                : vals.delta < 0
                                ? "text-red-500"
                                : "text-muted-foreground"
                            }`}
                          >
                            {vals.delta > 0 ? "+" : ""}
                            {vals.delta.toFixed(3)}
                          </span>
                        ) : (
                          "—"
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
    </div>
  );
}
