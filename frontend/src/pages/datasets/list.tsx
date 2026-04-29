import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import type { Dataset } from "@/types/eval";
import { Database, Plus, Tag, Trash2 } from "lucide-react";

export function DatasetListPage() {
  const [datasets, setDatasets] = useState<Dataset[]>([]);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  const fetchDatasets = async () => {
    setLoading(true);
    try {
      const res = await api.get("/api/v1/datasets");
      setDatasets(res.data);
    } catch (err) {
      console.error("Failed to fetch datasets", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDatasets();
  }, []);

  const handleDelete = async (id: string) => {
    if (!confirm("Delete this dataset?")) return;
    try {
      await api.delete(`/api/v1/datasets/${id}`);
      fetchDatasets();
    } catch (err) {
      console.error("Failed to delete dataset", err);
    }
  };

  return (
    <div className="container py-8">
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Datasets</h1>
          <p className="text-muted-foreground mt-1">
            Upload and manage evaluation datasets.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="outline" className="gap-2" asChild>
            <a href="/datasets/synthetic">Synthetic</a>
          </Button>
          <Button className="gap-2" asChild>
            <a href="/datasets/upload">
              <Plus className="h-4 w-4" />
              Upload
            </a>
          </Button>
        </div>
      </div>

      {loading ? (
        <div className="text-sm text-muted-foreground font-mono animate-pulse">
          Loading datasets...
        </div>
      ) : datasets.length === 0 ? (
        <div className="text-sm text-muted-foreground">
          No datasets yet. Upload a CSV/JSON or generate synthetic data.
        </div>
      ) : (
        <div className="grid gap-4">
          {datasets.map((dataset) => (
            <Card
              key={dataset.id}
              className="border-border hover:bg-card/80 transition-colors"
            >
              <CardContent className="p-5">
                <div className="flex items-center justify-between">
                  <div
                    className="space-y-1 cursor-pointer"
                    onClick={() => navigate(`/datasets/${dataset.id}`)}
                  >
                    <div className="flex items-center gap-2">
                      <Database className="h-4 w-4 text-primary" />
                      <h3 className="font-semibold text-base">{dataset.name}</h3>
                      {dataset.domain_tag && (
                        <span className="inline-flex items-center gap-1 rounded-md bg-secondary px-1.5 py-0.5 text-xs text-secondary-foreground">
                          <Tag className="h-3 w-3" />
                          {dataset.domain_tag}
                        </span>
                      )}
                    </div>
                    {dataset.description && (
                      <p className="text-sm text-muted-foreground">
                        {dataset.description}
                      </p>
                    )}
                    <div className="text-xs text-muted-foreground font-mono">
                      {dataset.row_count} rows
                    </div>
                  </div>
                  <Button
                    variant="ghost"
                    size="sm"
                    className="text-destructive hover:text-destructive"
                    onClick={() => handleDelete(dataset.id)}
                  >
                    <Trash2 className="h-4 w-4" />
                  </Button>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
