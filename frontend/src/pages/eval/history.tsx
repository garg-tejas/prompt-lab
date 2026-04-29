import { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import { api } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import type { EvalRunResponse } from "@/types/eval";
import { Play, Clock, CheckCircle, XCircle, Loader2 } from "lucide-react";

export function EvalHistoryPage() {
  const [runs, setRuns] = useState<EvalRunResponse[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchRuns = async () => {
    setLoading(true);
    try {
      const res = await api.get("/api/v1/eval-runs");
      setRuns(res.data);
    } catch (err) {
      console.error("Failed to fetch eval runs", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchRuns();
  }, []);

  const statusIcon = (status: string) => {
    switch (status) {
      case "completed":
        return <CheckCircle className="h-4 w-4 text-green-500" />;
      case "failed":
        return <XCircle className="h-4 w-4 text-red-500" />;
      case "running":
        return <Loader2 className="h-4 w-4 text-amber-500 animate-spin" />;
      default:
        return <Clock className="h-4 w-4 text-muted-foreground" />;
    }
  };

  return (
    <div className="container py-8">
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Eval Runs</h1>
          <p className="text-muted-foreground mt-1">
            History of all evaluation runs.
          </p>
        </div>
        <Button className="gap-2" asChild>
          <Link to="/runs/new">
            <Play className="h-4 w-4" />
            New Eval
          </Link>
        </Button>
      </div>

      {loading ? (
        <div className="text-sm text-muted-foreground font-mono animate-pulse">
          Loading runs...
        </div>
      ) : runs.length === 0 ? (
        <div className="text-sm text-muted-foreground">
          No eval runs yet. Start your first evaluation.
        </div>
      ) : (
        <div className="grid gap-4">
          {runs.map((run) => (
            <Card
              key={run.id}
              className="border-border hover:bg-card/80 transition-colors"
            >
              <CardContent className="p-5">
                <div className="flex items-center justify-between">
                  <div className="space-y-1">
                    <div className="flex items-center gap-2">
                      {statusIcon(run.status)}
                      <Link
                        to={`/runs/${run.id}`}
                        className="font-semibold text-base hover:text-primary transition-colors"
                      >
                        {run.name}
                      </Link>
                    </div>
                    <div className="text-xs text-muted-foreground font-mono">
                      {new Date(run.created_at).toLocaleString()}
                    </div>
                  </div>
                  <div className="text-right">
                    {run.results_summary && run.results_summary.metrics && (
                      <div className="flex items-center gap-3 text-xs font-mono">
                        {Object.entries(run.results_summary.metrics).map(
                          ([name, stats]: [string, any]) => (
                            <div key={name} className="text-muted-foreground">
                              <span className="capitalize">{name.replace("_", " ")}:</span>{" "}
                              <span className="text-foreground font-semibold">
                                {typeof stats === "object" ? stats.mean.toFixed(2) : stats}
                              </span>
                            </div>
                          )
                        )}
                      </div>
                    )}
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
