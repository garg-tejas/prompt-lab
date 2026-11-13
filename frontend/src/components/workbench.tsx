import type { ReactNode } from "react";
import { AlertCircle, Search } from "lucide-react";
import { Button } from "@/components/ui/button";
export function PageHeading({ index, title, description, action }: { index: string; title: string; description: string; action?: ReactNode }) {
  return <header className="lab-page-heading"><div><p className="lab-eyebrow">{index}</p><h1>{title}</h1><p className="lab-description">{description}</p></div>{action}</header>;
}
export function RegistrySearch({ value, onChange, placeholder, children }: { value: string; onChange: (value: string) => void; placeholder: string; children?: ReactNode }) {
  return <div className="lab-toolbar"><label className="lab-search"><Search size={16} aria-hidden="true" /><span className="sr-only">{placeholder}</span><input value={value} onChange={(event) => onChange(event.target.value)} placeholder={placeholder} type="search" /></label>{children}</div>;
}
export function RegistryState({ title, children, error, onRetry }: { title: string; children?: ReactNode; error?: boolean; onRetry?: () => void }) {
  return <div className={`lab-empty ${error ? "lab-empty-error" : ""}`} role={error ? "alert" : "status"}>{error && <AlertCircle size={22} />}<h2>{title}</h2><p>{children}</p>{onRetry && <Button variant="outline" onClick={onRetry}>Try again</Button>}</div>;
}
export function StatusLabel({ status }: { status: string }) {
  return <span className={`lab-status lab-status-${status}`}><span aria-hidden="true" />{status}</span>;
}
export function StatusFilter({ value, onChange }: { value: string; onChange: (value: string) => void }) {
  return <label className="lab-filter"><span>Status</span><select value={value} onChange={(event) => onChange(event.target.value)}><option value="all">All statuses</option>{["completed", "running", "pending", "failed"].map((status) => <option key={status} value={status}>{status}</option>)}</select></label>;
}
