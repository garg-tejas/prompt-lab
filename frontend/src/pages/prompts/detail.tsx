import { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { api } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { DiffViewer } from "@/components/diff-viewer";
import type { Prompt, PromptVersion } from "@/types";
import {
  ArrowLeft,
  GitBranch,
  GitCommit,
  Tag,
  ChevronDown,
  ChevronUp,
  Copy,
  Check,
} from "lucide-react";

export function PromptDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [prompt, setPrompt] = useState<Prompt | null>(null);
  const [loading, setLoading] = useState(true);
  const [showNewVersion, setShowNewVersion] = useState(false);
  const [diffVersions, setDiffVersions] = useState<{
    a: string | null;
    b: string | null;
  }>({ a: null, b: null });
  const [diffResult, setDiffResult] = useState<string | null>(null);
  const [diffLoading, setDiffLoading] = useState(false);

  const fetchPrompt = async () => {
    if (!id) return;
    setLoading(true);
    try {
      const res = await api.get(`/api/v1/prompts/${id}`);
      setPrompt(res.data);
    } catch (err) {
      console.error("Failed to fetch prompt", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchPrompt();
  }, [id]);

  const handlePromote = async (versionId: string, tag: string) => {
    if (!id) return;
    try {
      await api.post(`/api/v1/prompts/${id}/versions/${versionId}/promote`, {
        tag,
      });
      fetchPrompt();
    } catch (err) {
      console.error("Failed to promote version", err);
      alert("Failed to promote version");
    }
  };

  const handleDiff = async () => {
    if (!id || !diffVersions.a || !diffVersions.b) return;
    if (diffVersions.a === diffVersions.b) {
      setDiffResult("No diff: versions are identical");
      return;
    }
    setDiffLoading(true);
    try {
      const res = await api.get(
        `/api/v1/prompts/${id}/versions/${diffVersions.a}/diff/${diffVersions.b}`
      );
      setDiffResult(res.data.diff);
    } catch (err) {
      console.error("Failed to compute diff", err);
      alert("Failed to compute diff");
    } finally {
      setDiffLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="container py-8 text-sm text-muted-foreground font-mono animate-pulse">
        Loading prompt...
      </div>
    );
  }

  if (!prompt) {
    return (
      <div className="container py-8 text-sm text-muted-foreground">
        Prompt not found.
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
          onClick={() => navigate("/")}
        >
          <ArrowLeft className="h-4 w-4" />
          Back
        </Button>
      </div>

      <div className="space-y-1">
        <div className="flex items-center gap-3">
          <h1 className="text-3xl font-bold tracking-tight">{prompt.name}</h1>
          {prompt.production_version && (
            <span className="inline-flex items-center rounded-full bg-primary/10 px-2.5 py-0.5 text-xs font-medium text-primary">
              production
            </span>
          )}
        </div>
        {prompt.description && (
          <p className="text-muted-foreground">{prompt.description}</p>
        )}
        <div className="flex items-center gap-2 pt-1">
          {prompt.tags.map((tag) => (
            <span
              key={tag.id}
              className="inline-flex items-center gap-1 rounded-md bg-secondary px-1.5 py-0.5 text-xs text-secondary-foreground"
            >
              <Tag className="h-3 w-3" />
              {tag.name}
            </span>
          ))}
        </div>
      </div>

      <Card className="border-border">
        <CardHeader className="pb-2">
          <CardTitle className="text-base flex items-center justify-between">
            <span className="flex items-center gap-2">
              <GitBranch className="h-4 w-4 text-primary" />
              Versions
            </span>
            <Button size="sm" onClick={() => setShowNewVersion(!showNewVersion)}>
              {showNewVersion ? (
                <>
                  <ChevronUp className="h-4 w-4 mr-1" /> Cancel
                </>
              ) : (
                <>
                  <ChevronDown className="h-4 w-4 mr-1" /> New Version
                </>
              )}
            </Button>
          </CardTitle>
        </CardHeader>
        <CardContent>
          {showNewVersion && id && (
            <NewVersionForm
              promptId={id}
              onSuccess={() => {
                setShowNewVersion(false);
                fetchPrompt();
              }}
            />
          )}

          <div className="space-y-3 mt-4">
            {prompt.versions?.map((version) => (
              <VersionRow
                key={version.id}
                version={version}
                isProduction={version.tag === "production"}
                onPromote={(tag) => handlePromote(version.id, tag)}
                onSelectForDiff={(selected) => {
                  if (selected) {
                    if (!diffVersions.a) {
                      setDiffVersions({ a: version.id, b: null });
                    } else if (!diffVersions.b) {
                      setDiffVersions({ a: diffVersions.a, b: version.id });
                    } else {
                      setDiffVersions({ a: version.id, b: null });
                    }
                  } else {
                    setDiffVersions({
                      a: diffVersions.a === version.id ? null : diffVersions.a,
                      b: diffVersions.b === version.id ? null : diffVersions.b,
                    });
                  }
                }}
                isSelectedForDiff={
                  diffVersions.a === version.id || diffVersions.b === version.id
                }
              />
            ))}
          </div>

          {diffVersions.a && diffVersions.b && (
            <div className="mt-4 flex items-center gap-2">
              <Button
                size="sm"
                onClick={handleDiff}
                disabled={diffLoading}
                className="gap-1"
              >
                <GitCommit className="h-4 w-4" />
                {diffLoading ? "Computing..." : "View Diff"}
              </Button>
              <Button
                size="sm"
                variant="outline"
                onClick={() => {
                  setDiffVersions({ a: null, b: null });
                  setDiffResult(null);
                }}
              >
                Clear Selection
              </Button>
            </div>
          )}

          {diffVersions.a && !diffVersions.b && (
            <div className="mt-4 text-xs text-muted-foreground">
              Select a second version to compare.
            </div>
          )}

          {diffResult && (
            <div className="mt-4">
              <DiffViewer diff={diffResult} />
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

function VersionRow({
  version,
  isProduction,
  onPromote,
  onSelectForDiff,
  isSelectedForDiff,
}: {
  version: PromptVersion;
  isProduction: boolean;
  onPromote: (tag: string) => void;
  onSelectForDiff: (selected: boolean) => void;
  isSelectedForDiff: boolean;
}) {
  const [showContent, setShowContent] = useState(false);
  const [copied, setCopied] = useState(false);

  const copyContent = () => {
    navigator.clipboard.writeText(version.content);
    setCopied(true);
    setTimeout(() => setCopied(false), 1500);
  };

  return (
    <div
      className={`rounded-lg border p-3 transition-colors ${
        isSelectedForDiff
          ? "border-primary bg-primary/5"
          : "border-border hover:bg-secondary/30"
      }`}
    >
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <button
            onClick={() => onSelectForDiff(!isSelectedForDiff)}
            className={`h-4 w-4 rounded border ${
              isSelectedForDiff
                ? "bg-primary border-primary"
                : "border-muted-foreground"
            }`}
          />
          <span className="font-mono text-sm font-semibold text-amber-500">
            {version.version_hash}
          </span>
          {isProduction && (
            <span className="inline-flex items-center rounded-full bg-primary/10 px-2 py-0.5 text-xs font-medium text-primary">
              production
            </span>
          )}
          {version.tag && version.tag !== "production" && (
            <span className="inline-flex items-center rounded-full bg-secondary px-2 py-0.5 text-xs text-secondary-foreground">
              {version.tag}
            </span>
          )}
          <span className="text-xs text-muted-foreground">
            {new Date(version.created_at).toLocaleString()}
          </span>
        </div>
        <div className="flex items-center gap-1">
          {!isProduction && (
            <Button
              size="sm"
              variant="ghost"
              className="h-7 text-xs"
              onClick={() => onPromote("production")}
            >
              Promote
            </Button>
          )}
          <Button
            size="sm"
            variant="ghost"
            className="h-7 text-xs"
            onClick={() => setShowContent(!showContent)}
          >
            {showContent ? "Hide" : "Show"}
          </Button>
        </div>
      </div>

      <div className="mt-1 text-xs text-muted-foreground">
        {version.commit_message}
      </div>

      {version.variables.length > 0 && (
        <div className="mt-1 flex items-center gap-1 text-xs">
          <span className="text-muted-foreground">Vars:</span>
          {version.variables.map((v) => (
            <span
              key={v}
              className="rounded bg-secondary px-1 py-0.5 font-mono text-secondary-foreground"
            >
              {v}
            </span>
          ))}
        </div>
      )}

      {showContent && (
        <div className="mt-3 relative">
          <button
            onClick={copyContent}
            className="absolute right-2 top-2 rounded bg-secondary p-1 text-secondary-foreground hover:bg-secondary/80"
          >
            {copied ? (
              <Check className="h-3.5 w-3.5 text-green-500" />
            ) : (
              <Copy className="h-3.5 w-3.5" />
            )}
          </button>
          <pre className="rounded-md border border-border bg-background p-3 text-xs font-mono leading-relaxed overflow-x-auto">
            {version.content}
          </pre>
        </div>
      )}
    </div>
  );
}

function NewVersionForm({
  promptId,
  onSuccess,
}: {
  promptId: string;
  onSuccess: () => void;
}) {
  const [content, setContent] = useState("");
  const [commitMessage, setCommitMessage] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    try {
      await api.post(`/api/v1/prompts/${promptId}/versions`, {
        content,
        commit_message: commitMessage,
      });
      onSuccess();
    } catch (err) {
      console.error("Failed to create version", err);
      alert("Failed to create version");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-3 border-b border-border pb-4">
      <div className="space-y-2">
        <label className="text-sm font-medium">New Content</label>
        <Textarea
          value={content}
          onChange={(e) => setContent(e.target.value)}
          placeholder="Updated prompt content..."
          rows={6}
          className="font-mono text-sm"
          required
        />
      </div>
      <div className="space-y-2">
        <label className="text-sm font-medium">Commit Message</label>
        <Input
          value={commitMessage}
          onChange={(e) => setCommitMessage(e.target.value)}
          placeholder="e.g., Added CoT prefix"
          required
        />
      </div>
      <div className="flex items-center gap-2">
        <Button type="submit" disabled={submitting} size="sm">
          {submitting ? "Saving..." : "Save Version"}
        </Button>
      </div>
    </form>
  );
}
