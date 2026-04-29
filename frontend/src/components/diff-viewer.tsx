export function DiffViewer({ diff }: { diff: string }) {
  const lines = diff.split("\n");

  return (
    <div className="rounded-md border border-border bg-background overflow-hidden">
      <div className="flex items-center gap-2 border-b border-border bg-secondary/50 px-4 py-2 text-xs font-mono text-muted-foreground">
        <span className="text-green-500">+ additions</span>
        <span className="text-red-500">- deletions</span>
        <span className="text-amber-500">@@ context</span>
      </div>
      <pre className="overflow-x-auto p-4 text-xs font-mono leading-relaxed">
        {lines.map((line, i) => {
          let colorClass = "text-foreground";
          if (line.startsWith("+")) colorClass = "text-green-500";
          else if (line.startsWith("-")) colorClass = "text-red-500";
          else if (line.startsWith("@@")) colorClass = "text-amber-500";
          else if (line.startsWith("---") || line.startsWith("+++"))
            colorClass = "text-muted-foreground";

          return (
            <div key={i} className={colorClass}>
              {line || " "}
            </div>
          );
        })}
      </pre>
    </div>
  );
}
