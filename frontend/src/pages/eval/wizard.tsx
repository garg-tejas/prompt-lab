import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { Prompt, PromptVersion } from "@/types";
import type { Dataset, ModelEndpoint } from "@/types/eval";
import { ArrowLeft, Play } from "lucide-react";

export function EvalWizardPage() {
  const navigate = useNavigate();
  const [prompts, setPrompts] = useState<Prompt[]>([]);
  const [datasets, setDatasets] = useState<Dataset[]>([]);
  const [models, setModels] = useState<ModelEndpoint[]>([]);

  const [selectedPrompt, setSelectedPrompt] = useState<Prompt | null>(null);
  const [selectedVersion, setSelectedVersion] = useState<PromptVersion | null>(null);
  const [selectedDataset, setSelectedDataset] = useState<Dataset | null>(null);
  const [selectedModel, setSelectedModel] = useState<ModelEndpoint | null>(null);
  const [selectedJudge, setSelectedJudge] = useState<ModelEndpoint | null>(null);

  const [name, setName] = useState("");
  const [sampleSize, setSampleSize] = useState("");
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    api.get("/api/v1/prompts").then((r) => setPrompts(r.data));
    api.get("/api/v1/datasets").then((r) => setDatasets(r.data));
    api.get("/api/v1/models").then((r) => setModels(r.data));
  }, []);

  const handleSubmit = async () => {
    if (!selectedPrompt || !selectedVersion || !selectedDataset || !selectedModel || !selectedJudge) return;
    setSubmitting(true);
    try {
      const res = await api.post("/api/v1/eval-runs", {
        name: name || `${selectedPrompt.name} eval`,
        prompt_id: selectedPrompt.id,
        prompt_version_id: selectedVersion.id,
        dataset_id: selectedDataset.id,
        model_id: selectedModel.id,
        judge_model_id: selectedJudge.id,
        config: {
          sample_size: sampleSize ? parseInt(sampleSize) : null,
          concurrency: 1,
          retry_count: 2,
        },
      });
      navigate(`/runs/${res.data.id}`);
    } catch (err) {
      console.error("Failed to create eval run", err);
      alert("Failed to create eval run");
    } finally {
      setSubmitting(false);
    }
  };

  const canSubmit =
    selectedPrompt &&
    selectedVersion &&
    selectedDataset &&
    selectedModel &&
    selectedJudge;

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

      <h1 className="text-3xl font-bold tracking-tight mb-2">New Eval Run</h1>
      <p className="text-muted-foreground mb-8">
        Configure your evaluation pipeline step by step.
      </p>

      <div className="space-y-6">
        {/* Step 1: Prompt */}
        <Card className="border-border">
          <CardHeader className="pb-2">
            <CardTitle className="text-base">1. Select Prompt & Version</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="grid gap-2">
              {prompts.map((p) => (
                <button
                  key={p.id}
                  onClick={() => {
                    setSelectedPrompt(p);
                    setSelectedVersion(null);
                  }}
                  className={`text-left rounded-lg border p-3 transition-colors ${
                    selectedPrompt?.id === p.id
                      ? "border-primary bg-primary/5"
                      : "border-border hover:bg-secondary/30"
                  }`}
                >
                  <div className="font-medium text-sm">{p.name}</div>
                  <div className="text-xs text-muted-foreground">
                    {p.version_count} versions
                  </div>
                </button>
              ))}
            </div>

            {selectedPrompt && (
              <div className="space-y-2">
                <div className="text-sm font-medium">Select Version</div>
                <div className="flex flex-wrap gap-2">
                  {selectedPrompt.versions?.map((v) => (
                    <button
                      key={v.id}
                      onClick={() => setSelectedVersion(v)}
                      className={`rounded-md border px-2.5 py-1 text-xs font-mono transition-colors ${
                        selectedVersion?.id === v.id
                          ? "border-primary bg-primary/10 text-primary"
                          : "border-border hover:bg-secondary/30"
                      }`}
                    >
                      {v.version_hash} {v.tag ? `(${v.tag})` : ""}
                    </button>
                  ))}
                </div>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Step 2: Dataset */}
        <Card className="border-border">
          <CardHeader className="pb-2">
            <CardTitle className="text-base">2. Select Dataset</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid gap-2">
              {datasets.map((d) => (
                <button
                  key={d.id}
                  onClick={() => setSelectedDataset(d)}
                  className={`text-left rounded-lg border p-3 transition-colors ${
                    selectedDataset?.id === d.id
                      ? "border-primary bg-primary/5"
                      : "border-border hover:bg-secondary/30"
                  }`}
                >
                  <div className="font-medium text-sm">{d.name}</div>
                  <div className="text-xs text-muted-foreground">
                    {d.row_count} rows {d.domain_tag ? `· ${d.domain_tag}` : ""}
                  </div>
                </button>
              ))}
              {datasets.length === 0 && (
                <div className="text-sm text-muted-foreground">
                  No datasets available. Create one first.
                </div>
              )}
            </div>
          </CardContent>
        </Card>

        {/* Step 3: Models */}
        <Card className="border-border">
          <CardHeader className="pb-2">
            <CardTitle className="text-base">3. Select Models</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <div className="text-sm font-medium">Target Model</div>
              <div className="grid gap-2">
                {models
                  .filter((m) => !m.is_judge)
                  .map((m) => (
                    <button
                      key={m.id}
                      onClick={() => setSelectedModel(m)}
                      className={`text-left rounded-lg border p-3 transition-colors ${
                        selectedModel?.id === m.id
                          ? "border-primary bg-primary/5"
                          : "border-border hover:bg-secondary/30"
                      }`}
                    >
                      <div className="font-medium text-sm">{m.name}</div>
                      <div className="text-xs text-muted-foreground font-mono">
                        {m.model_name} · {m.provider}
                      </div>
                    </button>
                  ))}
              </div>
            </div>

            <div className="space-y-2">
              <div className="text-sm font-medium">Judge Model</div>
              <div className="grid gap-2">
                {models
                  .filter((m) => m.is_judge)
                  .map((m) => (
                    <button
                      key={m.id}
                      onClick={() => setSelectedJudge(m)}
                      className={`text-left rounded-lg border p-3 transition-colors ${
                        selectedJudge?.id === m.id
                          ? "border-primary bg-primary/5"
                          : "border-border hover:bg-secondary/30"
                      }`}
                    >
                      <div className="font-medium text-sm">{m.name}</div>
                      <div className="text-xs text-muted-foreground font-mono">
                        {m.model_name} · {m.provider}
                      </div>
                    </button>
                  ))}
                {models.filter((m) => m.is_judge).length === 0 && (
                  <div className="text-sm text-muted-foreground">
                    No judge models registered. Mark a model as judge in the model registry.
                  </div>
                )}
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Step 4: Config */}
        <Card className="border-border">
          <CardHeader className="pb-2">
            <CardTitle className="text-base">4. Configuration</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="space-y-2">
              <label className="text-sm font-medium">Run Name</label>
              <Input
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="e.g., v1.1 baseline eval"
              />
            </div>
            <div className="space-y-2">
              <label className="text-sm font-medium">Sample Size (optional)</label>
              <Input
                type="number"
                value={sampleSize}
                onChange={(e) => setSampleSize(e.target.value)}
                placeholder="Leave empty to run on full dataset"
              />
            </div>
          </CardContent>
        </Card>

        <div className="flex items-center gap-2">
          <Button
            disabled={!canSubmit || submitting}
            onClick={handleSubmit}
            className="gap-2"
          >
            <Play className="h-4 w-4" />
            {submitting ? "Starting..." : "Start Evaluation"}
          </Button>
        </div>
      </div>
    </div>
  );
}
