import { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import { api } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import type { ABTestResponse } from "@/types/ab_test";
import { GitCompare, Plus, Loader2, CheckCircle, XCircle, Clock } from "lucide-react";

export function ABTestListPage() {
  const [tests, setTests] = useState<ABTestResponse[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchTests = async () => {
    setLoading(true);
    try {
      const res = await api.get("/api/v1/ab-tests");
      setTests(res.data);
    } catch (err) {
      console.error("Failed to fetch AB tests", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchTests();
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

  const winnerBadge = (winner: string | undefined) => {
    if (!winner || winner === "tie") {
      return (
        <span className="inline-flex items-center rounded-full bg-secondary px-2 py-0.5 text-xs text-secondary-foreground">
          Tie
        </span>
      );
    }
    return (
      <span className="inline-flex items-center rounded-full bg-primary/10 px-2 py-0.5 text-xs font-medium text-primary">
        {winner === "a" ? "A wins" : "B wins"}
      </span>
    );
  };

  return (
    <div className="container py-8">
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">A/B Tests</h1>
          <p className="text-muted-foreground mt-1">
            Compare prompts or models head-to-head.
          </p>
        </div>
        <Button className="gap-2" asChild>
          <Link to="/ab-tests/new">
            <Plus className="h-4 w-4" />
            New A/B Test
          </Link>
        </Button>
      </div>

      {loading ? (
        <div className="text-sm text-muted-foreground font-mono animate-pulse">
          Loading A/B tests...
        </div>
      ) : tests.length === 0 ? (
        <div className="text-sm text-muted-foreground">
          No A/B tests yet. Create your first comparison.
        </div>
      ) : (
        <div className="grid gap-4">
          {tests.map((test) => (
            <Card
              key={test.id}
              className="border-border hover:bg-card/80 transition-colors"
            >
              <CardContent className="p-5">
                <div className="flex items-center justify-between">
                  <div className="space-y-1">
                    <div className="flex items-center gap-2">
                      {statusIcon(test.status)}
                      <Link
                        to={`/ab-tests/${test.id}`}
                        className="font-semibold text-base hover:text-primary transition-colors"
                      >
                        {test.name}
                      </Link>
                    </div>
                    <div className="text-xs text-muted-foreground font-mono">
                      {new Date(test.created_at).toLocaleString()}
                    </div>
                  </div>
                  <div className="flex items-center gap-3">
                    {test.status === "completed" && test.results_summary && (
                      <>
                        <div className="flex items-center gap-1 text-xs font-mono text-muted-foreground">
                          <GitCompare className="h-3.5 w-3.5" />
                          {test.results_summary.total_samples} samples
                        </div>
                        {winnerBadge(test.results_summary.overall_winner)}
                      </>
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
