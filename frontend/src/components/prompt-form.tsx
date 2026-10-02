import { useState } from "react";
import { api } from "@/lib/api";
import { notify } from "@/components/notice";
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
  const [messagesText, setMessagesText] = useState("[]");
  const [systemContent, setSystemContent] = useState("");
  const [content, setContent] = useState(initialContent);
  const [commitMessage, setCommitMessage] = useState("");
  const [tags, setTags] = useState(initialTags);
  const [submitting, setSubmitting] = useState(false);

  const variables = Array.from(
    new Set(
      `${systemContent}\n${messagesText}\n${content}`.match(/\{\{\s*([a-zA-Z0-9_]+)\s*\}\}/g) || []
    )
  );

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    let messages: { role: string; content: string }[] = [];
    try {
      const parsed = JSON.parse(messagesText || "[]");
      if (!Array.isArray(parsed)) throw new Error("messages must be a list");
      messages = parsed;
    } catch {
      notify("Few-shot messages must be a JSON list of {role, content}.");
      setSubmitting(false);
      return;
    }
    try {
      await api.post("/api/v1/prompts", {
        name,
        description: description || null,
        content,
        system_content: systemContent || null,
        messages,
        commit_message: commitMessage || "Initial version",
        tags: tags
          .split(",")
          .map((t) => t.trim())
          .filter(Boolean),
      });
      onSuccess();
    } catch (err) {
      console.error("Failed to create prompt", err);
      notify("Failed to create prompt");
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
        <label className="text-sm font-medium">System prompt</label>
        <Textarea
          value={systemContent}
          onChange={(e) => setSystemContent(e.target.value)}
          placeholder="Optional. Instructions that stay separate from the user turn. {{variable}} works here too."
          rows={4}
          className="font-mono text-sm"
        />
      </div>

      <div className="space-y-2">
        <label className="text-sm font-medium">Few-shot turns</label>
        <Textarea
          value={messagesText}
          onChange={(e) => setMessagesText(e.target.value)}
          placeholder='[{"role":"user","content":"Example"},{"role":"assistant","content":"Reply"}]'
          rows={3}
          className="font-mono text-sm"
        />
      </div>

      <div className="space-y-2">
        <label className="text-sm font-medium">User prompt</label>
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
