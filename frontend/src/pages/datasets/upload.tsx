import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent } from "@/components/ui/card";
import { ArrowLeft, Upload } from "lucide-react";

export function DatasetUploadPage() {
  const navigate = useNavigate();
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [domainTag, setDomainTag] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!file) return;
    setSubmitting(true);

    const formData = new FormData();
    formData.append("file", file);
    formData.append("name", name);
    formData.append("description", description);
    formData.append("domain_tag", domainTag);

    try {
      await api.post("/api/v1/datasets/upload", formData);
      navigate("/datasets");
    } catch (err) {
      console.error("Failed to upload dataset", err);
      alert("Failed to upload dataset");
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

      <h1 className="text-3xl font-bold tracking-tight mb-2">Upload Dataset</h1>
      <p className="text-muted-foreground mb-8">
        Upload a CSV or JSON file with question, context, and optional expected_answer columns.
      </p>

      <form onSubmit={handleSubmit} className="space-y-6">
        <Card className="border-border">
          <CardContent className="p-5 space-y-4">
            <div className="space-y-2">
              <label className="text-sm font-medium">Name</label>
              <Input
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="e.g., Medical QA v1"
                required
              />
            </div>
            <div className="space-y-2">
              <label className="text-sm font-medium">Description</label>
              <Input
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                placeholder="Optional description"
              />
            </div>
            <div className="space-y-2">
              <label className="text-sm font-medium">Domain Tag</label>
              <Input
                value={domainTag}
                onChange={(e) => setDomainTag(e.target.value)}
                placeholder="e.g., medical, legal"
              />
            </div>
            <div className="space-y-2">
              <label className="text-sm font-medium">File (.csv or .json)</label>
              <Input
                type="file"
                accept=".csv,.json"
                onChange={(e) => setFile(e.target.files?.[0] || null)}
                required
              />
            </div>
          </CardContent>
        </Card>

        <div className="flex items-center gap-2">
          <Button type="submit" disabled={submitting || !file} className="gap-2">
            <Upload className="h-4 w-4" />
            {submitting ? "Uploading..." : "Upload Dataset"}
          </Button>
        </div>
      </form>
    </div>
  );
}
