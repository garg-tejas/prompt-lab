import { useState } from "react";
import { api } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";

interface PromptFormProps {
  initialName?: string;
  initialDescription?: string;
  initialContent?: string;
  initialTags?: string;
  onSuccess: () => void;
  onCancel: () => void;
}

export function PromptForm({
  initialName = "",
  initialDescription = "",
  initialContent = "",
  initialTags = "",
  onSuccess,
  onCancel,
}: PromptFormProps) {
  const [name, setName] = useState(initialName);
  const [description, setDescription] = useState(initialDescription);
  const [content, setContent] = useState(initialContent);
  const [commitMessage, setCommitMessage] = useState("");
  const [tags, setTags] = useState(initialTags);
  const [submitting, setSubmitting] = useState(false);

  const variables = Array.from(
    new Set((content.match(/\{\{\s*([a-zA-Z0-9_]+)\s*\}\}/g) || []))
  );

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    try {
      await api.post("/api/v1/prompts", {
        name,
        description: description || null,
        content,
        commit_message: commitMessage || "Initial version",
        tags: tags
          .split(",")
          .map((t) => t.trim())
          .filter(Boolean),
      });
      onSuccess();
    } catch (err) {
      console.error("Failed to create prompt", err);
      alert("Failed to create prompt");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div className="grid gap-4 md:grid-cols-2">
        <div className="space-y-2">
          <label className="text-sm font-medium">Name</label>
          <Input
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="e.g., RAG System Prompt"
            required
          />
        </div>
        <div className="space-y-2">
          <label className="text-sm font-medium">Tags (comma separated)</label>
          <Input
            value={tags}
            onChange={(e) => setTags(e.target.value)}
            placeholder="rag, summarization"
          />
        </div>
      </div>

      <div className="space-y-2">
        <label className="text-sm font-medium">Description</label>
        <Input
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          placeholder="What does this prompt do?"
        />
      </div>

      <div className="space-y-2">
        <label className="text-sm font-medium">Prompt Content</label>
        <Textarea
          value={content}
          onChange={(e) => setContent(e.target.value)}
          placeholder="You are a helpful assistant... Use {{variable}} for placeholders."
          rows={8}
          className="font-mono text-sm"
          required
        />
        {variables.length > 0 && (
          <div className="flex items-center gap-2 text-xs text-muted-foreground">
            <span>Detected variables:</span>
            {variables.map((v) => (
              <span
                key={v}
                className="rounded bg-secondary px-1.5 py-0.5 font-mono text-secondary-foreground"
              >
                {v}
              </span>
            ))}
          </div>
        )}
      </div>

      <div className="space-y-2">
        <label className="text-sm font-medium">Commit Message</label>
        <Input
          value={commitMessage}
          onChange={(e) => setCommitMessage(e.target.value)}
          placeholder="e.g., Initial version"
          required
        />
      </div>

      <div className="flex items-center gap-2 pt-2">
        <Button type="submit" disabled={submitting}>
          {submitting ? "Saving..." : "Save Prompt"}
        </Button>
        <Button type="button" variant="outline" onClick={onCancel}>
          Cancel
        </Button>
      </div>
    </form>
  );
}
