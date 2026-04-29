import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent } from "@/components/ui/card";
import { ArrowLeft, Plus } from "lucide-react";

export function ModelCreatePage() {
  const navigate = useNavigate();
  const [name, setName] = useState("");
  const [modelName, setModelName] = useState("");
  const [provider, setProvider] = useState("openai");
  const [baseUrl, setBaseUrl] = useState("https://api.openai.com/v1");
  const [apiKey, setApiKey] = useState("");
  const [contextWindow, setContextWindow] = useState("");
  const [costIn, setCostIn] = useState("");
  const [costOut, setCostOut] = useState("");
  const [isJudge, setIsJudge] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    try {
      await api.post("/api/v1/models", {
        name,
        model_name: modelName,
        provider,
        base_url: baseUrl,
        api_key: apiKey,
        context_window: contextWindow ? parseInt(contextWindow) : null,
        cost_per_1k_input: costIn ? parseFloat(costIn) : null,
        cost_per_1k_output: costOut ? parseFloat(costOut) : null,
        is_judge: isJudge,
      });
      navigate("/models");
    } catch (err) {
      console.error("Failed to create model", err);
      alert("Failed to create model endpoint");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="container py-8 max-w-2xl mx-auto">
      <div className="flex items-center gap-4 mb-8">
        <Button
          variant="outline"
          size="sm"
          className="gap-1"
          onClick={() => navigate("/models")}
        >
          <ArrowLeft className="h-4 w-4" />
          Back
        </Button>
      </div>

      <h1 className="text-3xl font-bold tracking-tight mb-2">Add Model</h1>
      <p className="text-muted-foreground mb-8">
        Register an OpenAI-compatible LLM endpoint.
      </p>

      <form onSubmit={handleSubmit} className="space-y-6">
        <Card className="border-border">
          <CardContent className="p-5 space-y-4">
            <div className="grid gap-4 md:grid-cols-2">
              <div className="space-y-2">
                <label className="text-sm font-medium">Display Name</label>
                <Input
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="e.g., GPT-4 Production"
                  required
                />
              </div>
              <div className="space-y-2">
                <label className="text-sm font-medium">Model Name</label>
                <Input
                  value={modelName}
                  onChange={(e) => setModelName(e.target.value)}
                  placeholder="e.g., gpt-4"
                  required
                />
              </div>
            </div>
            <div className="grid gap-4 md:grid-cols-2">
              <div className="space-y-2">
                <label className="text-sm font-medium">Provider</label>
                <Input
                  value={provider}
                  onChange={(e) => setProvider(e.target.value)}
                  placeholder="e.g., openai"
                  required
                />
              </div>
              <div className="space-y-2">
                <label className="text-sm font-medium">Base URL</label>
                <Input
                  value={baseUrl}
                  onChange={(e) => setBaseUrl(e.target.value)}
                  placeholder="https://api.openai.com/v1"
                  required
                />
              </div>
            </div>
            <div className="space-y-2">
              <label className="text-sm font-medium">API Key</label>
              <Input
                type="password"
                value={apiKey}
                onChange={(e) => setApiKey(e.target.value)}
                placeholder="sk-..."
                required
              />
            </div>
            <div className="grid gap-4 md:grid-cols-3">
              <div className="space-y-2">
                <label className="text-sm font-medium">Context Window</label>
                <Input
                  type="number"
                  value={contextWindow}
                  onChange={(e) => setContextWindow(e.target.value)}
                  placeholder="8192"
                />
              </div>
              <div className="space-y-2">
                <label className="text-sm font-medium">Cost / 1k Input</label>
                <Input
                  type="number"
                  step="0.0001"
                  value={costIn}
                  onChange={(e) => setCostIn(e.target.value)}
                  placeholder="0.03"
                />
              </div>
              <div className="space-y-2">
                <label className="text-sm font-medium">Cost / 1k Output</label>
                <Input
                  type="number"
                  step="0.0001"
                  value={costOut}
                  onChange={(e) => setCostOut(e.target.value)}
                  placeholder="0.06"
                />
              </div>
            </div>
            <div className="flex items-center gap-2">
              <input
                type="checkbox"
                id="is-judge"
                checked={isJudge}
                onChange={(e) => setIsJudge(e.target.checked)}
                className="h-4 w-4 rounded border-border"
              />
              <label htmlFor="is-judge" className="text-sm">
                Use as judge model
              </label>
            </div>
          </CardContent>
        </Card>

        <div className="flex items-center gap-2">
          <Button type="submit" disabled={submitting} className="gap-2">
            <Plus className="h-4 w-4" />
            {submitting ? "Saving..." : "Add Model"}
          </Button>
        </div>
      </form>
    </div>
  );
}
