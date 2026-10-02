import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

interface TokenRow {
  id: string;
  name: string;
  token_prefix: string;
  created_at: string;
  last_used_at: string | null;
}

interface WebhookRow {
  id: string;
  url: string;
  events: string[];
  created_at: string;
}

interface TraceRow {
  id: string;
  output: string;
  scores: Record<string, { score: number | null }> | null;
  status: string;
  created_at: string;
}

export function ConnectPage() {
  const [tokens, setTokens] = useState<TokenRow[]>([]);
  const [hooks, setHooks] = useState<WebhookRow[]>([]);
  const [traces, setTraces] = useState<TraceRow[]>([]);
  const [traceTotal, setTraceTotal] = useState(0);
  const [traceOffset, setTraceOffset] = useState(0);
  const [deliveries, setDeliveries] = useState<Record<string, { id: string; event: string; status: string; attempts: number; last_error: string | null }[]>>({});
  const [tokenName, setTokenName] = useState("CI");
  const [freshToken, setFreshToken] = useState<string | null>(null);
  const [hookUrl, setHookUrl] = useState("");
  const [freshSecret, setFreshSecret] = useState<string | null>(null);

  const load = async (offset = 0) => {
    const [tokenRes, hookRes, traceRes] = await Promise.all([
      api.get("/api/v1/tokens"),
      api.get("/api/v1/webhooks"),
      api.get("/api/v1/traces", { params: { offset, limit: 50 } }),
    ]);
    setTokens(tokenRes.data);
    setHooks(hookRes.data);
    setTraces(traceRes.data.items);
    setTraceTotal(traceRes.data.total);
    setTraceOffset(traceRes.data.offset);
  };

  useEffect(() => {
    load().catch((err) => console.error(err));
  }, []);

  const createToken = async () => {
    const res = await api.post("/api/v1/tokens", { name: tokenName || "token" });
    setFreshToken(res.data.token);
    setTokenName("");
    load();
  };

  const createHook = async () => {
    const res = await api.post("/api/v1/webhooks", { url: hookUrl });
    setFreshSecret(res.data.secret);
    setHookUrl("");
    load();
  };

  return (
    <div className="container py-8 space-y-8 max-w-4xl">
      <div>
        <p className="font-mono text-xs uppercase tracking-[0.18em] text-primary">Live pipeline</p>
        <h1 className="mt-2 text-4xl">Connect a running app</h1>
        <p className="mt-2 max-w-2xl text-muted-foreground">
          Send a trace from production, score it with your judge, and hear about regressions
          through a webhook. CI uses the same token as the app.
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">API token</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          <div className="flex gap-2">
            <Input
              value={tokenName}
              onChange={(e) => setTokenName(e.target.value)}
              placeholder="Token name"
            />
            <Button onClick={createToken}>Create</Button>
          </div>
          {freshToken && (
            <pre className="overflow-x-auto rounded-md border border-border bg-background p-3 text-xs font-mono text-primary">
              {freshToken}
            </pre>
          )}
          <ul className="space-y-1 text-sm text-muted-foreground">
            {tokens.map((token) => (
              <li key={token.id} className="flex items-center justify-between font-mono text-xs">
                <span>
                  {token.name} · {token.token_prefix}…
                </span>
                <button
                  className="text-destructive"
                  onClick={async () => {
                    await api.delete(`/api/v1/tokens/${token.id}`);
                    load();
                  }}
                >
                  Revoke
                </button>
              </li>
            ))}
          </ul>
          <pre className="overflow-x-auto rounded-md border border-border bg-background p-3 text-xs font-mono leading-relaxed text-muted-foreground">{`from promptlab import PromptLab

lab = PromptLab("http://localhost:8000", "pl_...")
lab.ingest(
    prompt_id="...",
    inputs={"question": "...", "context": "...", "expected_answer": "..."},
    output="...",
)`}</pre>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Webhook</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          <div className="flex gap-2">
            <Input
              value={hookUrl}
              onChange={(e) => setHookUrl(e.target.value)}
              placeholder="https://example.com/hooks/promptlab"
            />
            <Button onClick={createHook} disabled={!hookUrl}>
              Add
            </Button>
          </div>
          {freshSecret && (
            <p className="font-mono text-xs text-primary">Signing secret: {freshSecret}</p>
          )}
          <p className="text-xs text-muted-foreground">
            Events: eval.completed, eval.failed, eval.anomaly. Verify X-PromptLab-Signature as sha256 HMAC of the raw body.
          </p>
            <ul className="space-y-2 text-xs font-mono text-muted-foreground">
            {hooks.map((hook) => (
              <li key={hook.id} className="space-y-1">
                <div className="flex justify-between gap-4">
                  <span className="truncate">{hook.url}</span>
                  <span className="flex gap-3">
                    <button
                      onClick={async () => {
                        const res = await api.get(`/api/v1/webhooks/${hook.id}/deliveries`);
                        setDeliveries((current) => ({ ...current, [hook.id]: res.data }));
                      }}
                    >
                      Log
                    </button>
                    <button
                      className="text-destructive"
                      onClick={async () => {
                        await api.delete(`/api/v1/webhooks/${hook.id}`);
                        load();
                      }}
                    >
                      Remove
                    </button>
                  </span>
                </div>
                {(deliveries[hook.id] || []).map((row) => (
                  <div key={row.id}>
                    {row.event} · {row.status} · {row.attempts} tries
                    {row.last_error ? ` · ${row.last_error}` : ""}
                  </div>
                ))}
              </li>
            ))}
          </ul>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Recent traces</CardTitle>
        </CardHeader>
        <CardContent>
          {traces.length === 0 ? (
            <p className="text-sm text-muted-foreground">No traces yet.</p>
          ) : (
            <ul className="space-y-3">
              {traces.map((trace) => (
                <li key={trace.id} className="border-b border-border pb-3 last:border-0">
                  <div className="text-xs font-mono text-muted-foreground">
                    {new Date(trace.created_at).toLocaleString()} · {trace.status}
                  </div>
                  <p className="mt-1 line-clamp-2 text-sm">{trace.output}</p>
                  {trace.scores && (
                    <div className="mt-2 flex flex-wrap gap-1">
                      {Object.entries(trace.scores).map(([name, judgment]) => (
                        <span key={name} className="rounded bg-secondary px-1.5 py-0.5 text-xs font-mono">
                          {name} {judgment.score == null ? "—" : judgment.score.toFixed(2)}
                        </span>
                      ))}
                    </div>
                  )}
                </li>
              ))}
            </ul>
          )}
          {traceTotal > 50 && (
            <div className="mt-3 flex justify-between text-xs text-muted-foreground">
              <span>
                {traceOffset + 1}–{Math.min(traceOffset + 50, traceTotal)} of {traceTotal}
              </span>
              <span className="flex gap-3">
                <button type="button" disabled={traceOffset === 0} onClick={() => load(Math.max(0, traceOffset - 50))}>
                  Previous
                </button>
                <button type="button" disabled={traceOffset + 50 >= traceTotal} onClick={() => load(traceOffset + 50)}>
                  Next
                </button>
              </span>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
