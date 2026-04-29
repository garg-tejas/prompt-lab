import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { EvalRunResponse } from "@/types/eval";
import { ArrowLeft, GitCompare } from "lucide-react";

export function ABTestCreatePage() {
  const navigate = useNavigate();
  const [runs, setRuns] = useState<EvalRunResponse[]>([]);
  const [selectedA, setSelectedA] = useState<EvalRunResponse | null>(null);
  const [selectedB, setSelectedB] = useState<EvalRunResponse | null>(null);
  const [name, setName] = useState("");
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    api.get("/api/v1/eval-runs").then((r) => {
      setRuns(r.data.filter((run: EvalRunResponse) => run.status === "completed"));
    });
  }, []);

  const handleSubmit = async () => {
    if (!selectedA || !selectedB) return;
    setSubmitting(true);
    try {
      const res = await api.post("/api/v1/ab-tests", {
        name: name || `${selectedA.name} vs ${selectedB.name}`,
        eval_run_a_id: selectedA.id,
        eval_run_b_id: selectedB.id,
      });
      navigate(`/ab-tests/${res.data.id}`);
    } catch (err) {
      console.error("Failed to create AB test", err);
      alert("Failed to create A/B test");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="container py-8 max-w-3xl mx-auto">
      <div className="flex items-center gap-4 mb-8">
        <Button
          variant="outline"
          size="sm"
          className="gap-1"
          onClick={() => navigate("/ab-tests")}
        >
          <ArrowLeft className="h-4 w-4" />
          Back
        </Button>
      </div>

      <h1 className="text-3xl font-bold tracking-tight mb-2">New A/B Test</h1>
      <p className="text-muted-foreground mb-8">
        Pick two completed eval runs to compare.
      </p>

      <div className="space-y-6">
        <Card className="border-border">
          <CardHeader className="pb-2">
            <CardTitle className="text-base">Select Run A</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid gap-2 max-h-64 overflow-y-auto">
              {runs.map((run) => (
                <button
                  key={run.id}
                  onClick={() => setSelectedA(run)}
                  disabled={selectedB?.id === run.id}
                  className={`text-left rounded-lg border p-3 transition-colors disabled:opacity-40 ${
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
              {runs.length === 0 && (
                <div className="text-sm text-muted-foreground">
                  No completed eval runs available. Run an evaluation first.
                </div>
              )}
            </div>
          </CardContent>
        </Card>

        <Card className="border-border">
          <CardHeader className="pb-2">
            <CardTitle className="text-base">Select Run B</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid gap-2 max-h-64 overflow-y-auto">
              {runs.map((run) => (
                <button
                  key={run.id}
                  onClick={() => setSelectedB(run)}
                  disabled={selectedA?.id === run.id}
                  className={`text-left rounded-lg border p-3 transition-colors disabled:opacity-40 ${
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
            </div>
          </CardContent>
        </Card>

        <Card className="border-border">
          <CardHeader className="pb-2">
            <CardTitle className="text-base">Configuration</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              <label className="text-sm font-medium">Test Name</label>
              <Input
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="e.g., v1.0 vs v1.1 faithfulness"
              />
            </div>
          </CardContent>
        </Card>

        <div className="flex items-center gap-2">
          <Button
            disabled={!selectedA || !selectedB || submitting}
            onClick={handleSubmit}
            className="gap-2"
          >
            <GitCompare className="h-4 w-4" />
            {submitting ? "Starting..." : "Run Comparison"}
          </Button>
        </div>
      </div>
    </div>
  );
}
