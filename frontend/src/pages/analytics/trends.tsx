import { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { api } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ArrowLeft, TrendingUp } from "lucide-react";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ReferenceLine,
} from "recharts";

interface TrendPoint {
  run_id: string;
  run_name: string;
  created_at: string;
  mean_score: number;
  min_score: number;
  max_score: number;
}

const METRICS = [
  "faithfulness",
  "answer_relevance",
  "context_precision",
  "context_recall",
];

export function TrendsPage() {
  const { promptId } = useParams<{ promptId: string }>();
  const navigate = useNavigate();
  const [metric, setMetric] = useState("faithfulness");
  const [data, setData] = useState<TrendPoint[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchTrends = async () => {
    if (!promptId) return;
    setLoading(true);
    try {
      const res = await api.get(`/api/v1/analytics/prompts/${promptId}/trends`, {
        params: { metric },
      });
      setData(res.data.data);
    } catch (err) {
      console.error("Failed to fetch trends", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchTrends();
  }, [promptId, metric]);

  return (
    <div className="container py-8 space-y-6">
      <div className="flex items-center gap-4">
        <Button
          variant="outline"
          size="sm"
          className="gap-1"
          onClick={() => navigate("/")}
        >
          <ArrowLeft className="h-4 w-4" />
          Back
        </Button>
      </div>

      <div className="space-y-1">
        <div className="flex items-center gap-3">
          <TrendingUp className="h-5 w-5 text-primary" />
          <h1 className="text-3xl font-bold tracking-tight">Trends</h1>
        </div>
        <p className="text-muted-foreground">
          Metric evolution over prompt versions.
        </p>
      </div>

      <div className="flex items-center gap-2">
        {METRICS.map((m) => (
          <button
            key={m}
            onClick={() => setMetric(m)}
            className={`rounded-md border px-3 py-1 text-xs capitalize transition-colors ${
              metric === m
                ? "border-primary bg-primary/10 text-primary"
                : "border-border hover:bg-secondary/30"
            }`}
          >
            {m.replace("_", " ")}
          </button>
        ))}
      </div>

      {loading ? (
        <div className="text-sm text-muted-foreground font-mono animate-pulse">
          Loading trends...
        </div>
      ) : data.length === 0 ? (
        <div className="text-sm text-muted-foreground">
          No completed eval runs for this prompt yet.
        </div>
      ) : (
        <Card className="border-border">
          <CardHeader className="pb-2">
            <CardTitle className="text-base capitalize">
              {metric.replace("_", " ")} Over Time
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="h-[400px] w-full">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={data} margin={{ top: 5, right: 20, bottom: 5, left: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
                  <XAxis
                    dataKey="created_at"
                    tickFormatter={(v) => new Date(v).toLocaleDateString()}
                    stroke="hsl(var(--muted-foreground))"
                    fontSize={12}
                  />
                  <YAxis domain={[0, 1]} stroke="hsl(var(--muted-foreground))" fontSize={12} />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: "hsl(var(--card))",
                      borderColor: "hsl(var(--border))",
                      color: "hsl(var(--foreground))",
                    }}
                    labelFormatter={(v) => new Date(v).toLocaleString()}
                  />
                  <ReferenceLine y={0.5} stroke="hsl(var(--muted-foreground))" strokeDasharray="3 3" />
                  <Line
                    type="monotone"
                    dataKey="mean_score"
                    stroke="hsl(var(--primary))"
                    strokeWidth={2}
                    dot={{ fill: "hsl(var(--primary))", r: 4 }}
                    name="Mean Score"
                  />
                  <Line
                    type="monotone"
                    dataKey="min_score"
                    stroke="hsl(var(--muted-foreground))"
                    strokeWidth={1}
                    strokeDasharray="4 4"
                    dot={false}
                    name="Min"
                  />
                  <Line
                    type="monotone"
                    dataKey="max_score"
                    stroke="hsl(var(--muted-foreground))"
                    strokeWidth={1}
                    strokeDasharray="4 4"
                    dot={false}
                    name="Max"
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
