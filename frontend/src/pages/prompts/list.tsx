import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "@clerk/clerk-react";
import { api } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { PromptForm } from "@/components/prompt-form";
import type { Prompt } from "@/types";
import { GitBranch, Plus, Tag, TrendingUp } from "lucide-react";

export function PromptListPage() {
  const [prompts, setPrompts] = useState<Prompt[]>([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const navigate = useNavigate();
  const { isSignedIn } = useAuth();

  const fetchPrompts = async () => {
    setLoading(true);
    try {
      const res = await api.get("/api/v1/prompts");
      setPrompts(res.data);
    } catch (err) {
      console.error("Failed to fetch prompts", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (isSignedIn) {
      fetchPrompts();
    }
  }, [isSignedIn]);

  return (
    <div className="container py-8">
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Prompts</h1>
          <p className="text-muted-foreground mt-1">
            Version, evaluate, and ship prompts with confidence.
          </p>
        </div>
        <Button className="gap-2" onClick={() => setShowForm(true)}>
          <Plus className="h-4 w-4" />
          New Prompt
        </Button>
      </div>

      {showForm && (
        <Card className="mb-8 border-border">
          <CardHeader className="pb-2">
            <CardTitle className="text-base">Create New Prompt</CardTitle>
          </CardHeader>
          <CardContent>
            <PromptForm
              onSuccess={() => {
                setShowForm(false);
                fetchPrompts();
              }}
              onCancel={() => setShowForm(false)}
            />
          </CardContent>
        </Card>
      )}

      {loading ? (
        <div className="text-sm text-muted-foreground font-mono animate-pulse">
          Loading prompts...
        </div>
      ) : prompts.length === 0 ? (
        <div className="text-sm text-muted-foreground">
          No prompts yet. Create your first one above.
        </div>
      ) : (
        <div className="grid gap-4">
          {prompts.map((prompt) => (
            <Card
              key={prompt.id}
              className="border-border cursor-pointer hover:bg-card/80 transition-colors"
              onClick={() => navigate(`/prompts/${prompt.id}`)}
            >
              <CardContent className="p-5">
                <div className="flex items-start justify-between">
                  <div className="space-y-1">
                    <div className="flex items-center gap-2">
                      <h3 className="font-semibold text-base">{prompt.name}</h3>
                      {prompt.production_version && (
                        <span className="inline-flex items-center rounded-full bg-primary/10 px-2 py-0.5 text-xs font-medium text-primary">
                          production
                        </span>
                      )}
                    </div>
                    {prompt.description && (
                      <p className="text-sm text-muted-foreground">
                        {prompt.description}
                      </p>
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
                  <div className="flex items-center gap-4 text-xs text-muted-foreground font-mono">
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        navigate(`/trends/${prompt.id}`);
                      }}
                      className="flex items-center gap-1 text-primary hover:underline"
                    >
                      <TrendingUp className="h-3.5 w-3.5" />
                      Trends
                    </button>
                    <div className="flex items-center gap-1">
                      <GitBranch className="h-3.5 w-3.5" />
                      {prompt.version_count} versions
                    </div>
                    {prompt.latest_version && (
                      <span className="text-amber-500">
                        {prompt.latest_version.version_hash}
                      </span>
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
