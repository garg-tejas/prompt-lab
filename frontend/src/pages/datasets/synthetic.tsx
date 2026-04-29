import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Card, CardContent } from "@/components/ui/card";
import { ArrowLeft, Sparkles } from "lucide-react";

export function DatasetSyntheticPage() {
  const navigate = useNavigate();
  const [name, setName] = useState("");
  const [context, setContext] = useState("");
  const [numPairs, setNumPairs] = useState("5");
  const [domainTag, setDomainTag] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    try {
      await api.post("/api/v1/datasets/synthetic", {
        name: name || "Synthetic Dataset",
        context,
        num_pairs: parseInt(numPairs) || 5,
        domain_tag: domainTag,
      });
      navigate("/datasets");
    } catch (err) {
      console.error("Failed to generate dataset", err);
      alert("Failed to generate synthetic dataset");
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
          onClick={() => navigate("/datasets")}
        >
          <ArrowLeft className="h-4 w-4" />
          Back
        </Button>
      </div>

      <h1 className="text-3xl font-bold tracking-tight mb-2">Synthetic Dataset</h1>
      <p className="text-muted-foreground mb-8">
        Paste a document or context and let an LLM generate Q&A pairs automatically.
      </p>

      <form onSubmit={handleSubmit} className="space-y-6">
        <Card className="border-border">
          <CardContent className="p-5 space-y-4">
            <div className="space-y-2">
              <label className="text-sm font-medium">Dataset Name</label>
              <Input
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="e.g., Generated from Annual Report 2024"
              />
            </div>
            <div className="space-y-2">
              <label className="text-sm font-medium">Context / Document</label>
              <Textarea
                value={context}
                onChange={(e) => setContext(e.target.value)}
                placeholder="Paste your document or context here..."
                rows={10}
                required
              />
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <label className="text-sm font-medium">Number of Q&A pairs</label>
                <Input
                  type="number"
                  min={1}
                  max={50}
                  value={numPairs}
                  onChange={(e) => setNumPairs(e.target.value)}
                />
              </div>
              <div className="space-y-2">
                <label className="text-sm font-medium">Domain Tag</label>
                <Input
                  value={domainTag}
                  onChange={(e) => setDomainTag(e.target.value)}
                  placeholder="e.g., finance"
                />
              </div>
            </div>
          </CardContent>
        </Card>

        <div className="flex items-center gap-2">
          <Button
            type="submit"
            disabled={submitting || !context.trim()}
            className="gap-2"
          >
            <Sparkles className="h-4 w-4" />
            {submitting ? "Generating..." : "Generate Q&A Pairs"}
          </Button>
        </div>
      </form>
    </div>
  );
}
