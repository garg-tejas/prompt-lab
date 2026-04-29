import { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import { api } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import type { ModelEndpoint } from "@/types/eval";
import { Cpu, Plus, Trash2, CheckCircle } from "lucide-react";

export function ModelListPage() {
  const [models, setModels] = useState<ModelEndpoint[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchModels = async () => {
    setLoading(true);
    try {
      const res = await api.get("/api/v1/models");
      setModels(res.data);
    } catch (err) {
      console.error("Failed to fetch models", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchModels();
  }, []);

  const handleDelete = async (id: string) => {
    if (!confirm("Delete this model endpoint?")) return;
    try {
      await api.delete(`/api/v1/models/${id}`);
      fetchModels();
    } catch (err) {
      console.error("Failed to delete model", err);
    }
  };

  return (
    <div className="container py-8">
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Models</h1>
          <p className="text-muted-foreground mt-1">
            Register target and judge LLM endpoints.
          </p>
        </div>
        <Button className="gap-2" asChild>
          <Link to="/models/new">
            <Plus className="h-4 w-4" />
            Add Model
          </Link>
        </Button>
      </div>

      {loading ? (
        <div className="text-sm text-muted-foreground font-mono animate-pulse">
          Loading models...
        </div>
      ) : models.length === 0 ? (
        <div className="text-sm text-muted-foreground">
          No models registered yet. Add your first endpoint.
        </div>
      ) : (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {models.map((model) => (
            <Card
              key={model.id}
              className="border-border hover:bg-card/80 transition-colors"
            >
              <CardContent className="p-5">
                <div className="flex items-start justify-between">
                  <div className="space-y-2">
                    <div className="flex items-center gap-2">
                      <Cpu className="h-4 w-4 text-primary" />
                      <h3 className="font-semibold text-base">{model.name}</h3>
                      {model.is_judge && (
                        <span className="inline-flex items-center gap-1 rounded-full bg-primary/10 px-2 py-0.5 text-xs font-medium text-primary">
                          <CheckCircle className="h-3 w-3" />
                          Judge
                        </span>
                      )}
                    </div>
                    <div className="text-xs text-muted-foreground font-mono">
                      {model.model_name} · {model.provider}
                    </div>
                    <div className="text-xs text-muted-foreground">
                      {model.base_url}
                    </div>
                    <div className="flex items-center gap-3 text-xs font-mono">
                      {model.context_window && (
                        <span>{model.context_window.toLocaleString()} ctx</span>
                      )}
                      {model.cost_per_1k_input && (
                        <span>${model.cost_per_1k_input}/1k in</span>
                      )}
                      {model.cost_per_1k_output && (
                        <span>${model.cost_per_1k_output}/1k out</span>
                      )}
                    </div>
                  </div>
                  <Button
                    variant="ghost"
                    size="sm"
                    className="text-destructive hover:text-destructive"
                    onClick={() => handleDelete(model.id)}
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
