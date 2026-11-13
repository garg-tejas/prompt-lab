import { useState } from "react";
import { Link } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { PromptForm } from "@/components/prompt-form";
import { PageHeading, RegistrySearch, RegistryState } from "@/components/workbench";
import { useRegistry } from "@/hooks/useRegistry";
import type { Prompt } from "@/types";
import { Plus, ArrowUpRight } from "lucide-react";

export function PromptListPage() {
  const registry = useRegistry<Prompt & { status?: string }>("/api/v1/prompts");
  return <PromptRegistryView {...registry} />;
}

export function PromptRegistryView({ rows: prompts, loading, error, refresh, isSignedIn }: {
  rows: Prompt[]; loading: boolean; error: boolean; refresh: () => void; isSignedIn?: boolean;
}) {
  const [showForm, setShowForm] = useState(false);
  const [query, setQuery] = useState("");
  const filtered = prompts.filter((prompt) => `${prompt.name} ${prompt.description ?? ""} ${prompt.tags.map((tag) => tag.name).join(" ")}`.toLowerCase().includes(query.toLowerCase()));
  return (
    <div className="container">
      <PageHeading index="01 / Build" title="Prompt registry" description="A working record of your prompts. Keep versions together, inspect changes, and put each iteration to the test." action={isSignedIn && <Button className="gap-2" onClick={() => setShowForm(true)}><Plus size={15} />New prompt</Button>} />
      {showForm && <Card className="mb-8"><CardHeader><CardTitle className="text-base">Create a prompt</CardTitle></CardHeader><CardContent><PromptForm onSuccess={() => { setShowForm(false); refresh(); }} onCancel={() => setShowForm(false)} /></CardContent></Card>}
      <RegistrySearch value={query} onChange={setQuery} placeholder="Find a prompt or tag…"><span className="lab-count">{loading ? "Loading registry" : `${filtered.length} / ${prompts.length} prompts`}</span></RegistrySearch>
      {!isSignedIn ? <RegistryState title="Your workspace starts here">Sign in to access your prompt versions and evaluation history.<br /><Link to="/sign-in" className="text-primary underline">Sign in to PromptLab</Link></RegistryState>
        : loading ? <RegistryState title="Loading the registry…">Retrieving your prompts and version metadata.</RegistryState>
        : error ? <RegistryState title="The registry could not be loaded" error onRetry={refresh}>Your prompts may still be available. Check the connection and try again.</RegistryState>
        : !prompts.length ? <RegistryState title="Give your first prompt a home">Create a prompt, save a version, then evaluate it against a dataset. The registry will keep the iterations together.</RegistryState>
        : !filtered.length ? <RegistryState title="No matching prompts">Try a different name or tag.</RegistryState>
        : <div className="lab-table-wrap" tabIndex={0} role="region" aria-label="Prompt registry table"><table className="lab-table"><thead><tr><th scope="col">Prompt / purpose</th><th scope="col">Versions</th><th scope="col">Latest revision</th><th scope="col">Explore</th></tr></thead><tbody>{filtered.map((prompt) => <tr key={prompt.id}><td><Link className="lab-table-name" to={`/prompts/${prompt.id}`}>{prompt.name}</Link><p className="lab-table-description">{prompt.description || "No description added."}</p><div className="mt-2">{prompt.tags.map((tag) => <span className="lab-tag" key={tag.id}>{tag.name}</span>)}{prompt.production_version && <span className="lab-tag text-primary">Production version set</span>}</div></td><td className="lab-table-meta">{prompt.version_count} saved</td><td className="lab-table-meta">{prompt.latest_version?.version_hash ?? "No version yet"}</td><td><Link to={`/trends/${prompt.id}`} className="inline-flex items-center gap-1 text-xs text-primary">Trends <ArrowUpRight size={13} /></Link></td></tr>)}</tbody></table></div>}
      <p className="lab-footnote">Registry → Version → Evaluation → Comparison. Production labels track your selection; they do not certify quality.</p>
    </div>
  );
}
