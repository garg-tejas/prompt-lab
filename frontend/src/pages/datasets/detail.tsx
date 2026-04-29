import { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { api } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { Dataset } from "@/types/eval";
import { ArrowLeft, Database } from "lucide-react";

export function DatasetDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [dataset, setDataset] = useState<Dataset | null>(null);
  const [loading, setLoading] = useState(true);

  const fetchDataset = async () => {
    if (!id) return;
    setLoading(true);
    try {
      const res = await api.get(`/api/v1/datasets/${id}`);
      setDataset(res.data);
    } catch (err) {
      console.error("Failed to fetch dataset", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDataset();
  }, [id]);

  if (loading) {
    return (
      <div className="container py-8 text-sm text-muted-foreground font-mono animate-pulse">
        Loading dataset...
      </div>
    );
  }

  if (!dataset) {
    return (
      <div className="container py-8 text-sm text-muted-foreground">
        Dataset not found.
      </div>
    );
  }

  return (
    <div className="container py-8 space-y-6">
      <div className="flex items-center gap-4">
        <Button
          variant="outline"
          size="sm"
          className="gap-1"
          onClick={() => navigate("/datasets")}
        >
          <ArrowLeft className="h-4 w-4" />
          Back
        </Button>
      </div>

      <div className="space-y-1">
        <div className="flex items-center gap-3">
          <Database className="h-5 w-5 text-primary" />
          <h1 className="text-3xl font-bold tracking-tight">{dataset.name}</h1>
        </div>
        {dataset.description && (
          <p className="text-muted-foreground">{dataset.description}</p>
        )}
        <div className="text-xs text-muted-foreground font-mono">
          {dataset.row_count} rows
        </div>
      </div>

      <Card className="border-border">
        <CardHeader className="pb-2">
          <CardTitle className="text-base">Preview</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-border text-left text-muted-foreground">
                  <th className="pb-2 pr-4 font-medium">#</th>
                  <th className="pb-2 pr-4 font-medium">Question</th>
                  <th className="pb-2 pr-4 font-medium">Context</th>
                  <th className="pb-2 font-medium">Expected Answer</th>
                </tr>
              </thead>
              <tbody>
                {dataset.rows?.slice(0, 50).map((row, idx) => (
                  <tr
                    key={row.id}
                    className="border-b border-border/50 last:border-0"
                  >
                    <td className="py-2 pr-4 font-mono text-muted-foreground">
                      {idx + 1}
                    </td>
                    <td className="py-2 pr-4 max-w-xs truncate">
                      {row.question}
                    </td>
                    <td className="py-2 pr-4 max-w-xs truncate">
                      {row.context}
                    </td>
                    <td className="py-2 max-w-xs truncate">
                      {row.expected_answer || "—"}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          {(dataset.rows?.length || 0) > 50 && (
            <div className="mt-2 text-xs text-muted-foreground">
              Showing first 50 of {dataset.row_count} rows.
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
