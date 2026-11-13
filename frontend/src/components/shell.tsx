import type { ReactNode } from "react";
import { Outlet, NavLink, Link, useLocation } from "react-router-dom";
import { useAuth, UserButton } from "@clerk/clerk-react";
import { FlaskConical, GitBranch, Database, Cpu, ListChecks, GitCompare, Plug, ArrowUpRight } from "lucide-react";

const navigation = [
  { to: "/", label: "Prompt registry", icon: GitBranch, section: "Build", end: true },
  { to: "/datasets", label: "Datasets", icon: Database, section: "Build" },
  { to: "/models", label: "Model endpoints", icon: Cpu, section: "Build" },
  { to: "/runs", label: "Evaluation runs", icon: ListChecks, section: "Evaluate" },
  { to: "/ab-tests", label: "A/B comparisons", icon: GitCompare, section: "Evaluate" },
  { to: "/connect", label: "Integrations", icon: Plug, section: "Connect" },
];

export function WorkbenchFrame({ children, account }: { children: ReactNode; account?: ReactNode }) {
  const { pathname } = useLocation();
  const current = pathname === "/compare" ? "Run comparison" : pathname.startsWith("/trends/") ? "Prompt trends" : [...navigation].reverse().find((item) => item.to !== "/" && pathname.startsWith(item.to))?.label ?? "Prompt registry";
  return (
    <div className="lab-layout">
      <a href="#workspace" className="skip-link">Skip to workspace</a>
      <aside className="lab-rail">
        <Link to="/" className="lab-brand"><span className="lab-mark"><FlaskConical size={21} /></span><span>PromptLab<small>EVALUATION WORKBENCH</small></span></Link>
        <nav aria-label="Workspace navigation" className="lab-navigation">
          {["Build", "Evaluate", "Connect"].map((section) => (
            <div className="lab-nav-group" key={section}>
              <p className="lab-nav-label">{section}</p>
              {navigation.filter((item) => item.section === section).map(({ to, label, icon: Icon, end }) => (
                <NavLink key={to} to={to} end={end} className={({ isActive }) => `lab-nav-link ${isActive ? "is-active" : ""}`}>
                  <Icon size={16} aria-hidden="true" /><span>{label}</span>
                </NavLink>
              ))}
            </div>
          ))}
        </nav>
        <div className="lab-rail-note"><span className="lab-nav-label">The evaluation loop</span><p>Version a prompt.<br />Test on fixed inputs.<br />Inspect the difference.</p><Link to="/runs/new">Configure an evaluation <ArrowUpRight size={14} /></Link></div>
        <div className="lab-account">{account}<span className="font-mono text-xs">PromptLab / v0.1</span></div>
      </aside>
      <div className="lab-workspace">
        <header className="lab-topbar"><span>Workspace <span aria-hidden="true">/</span> <strong>{current}</strong></span><Link to="/compare">Compare runs <ArrowUpRight size={14} /></Link></header>
        <main id="workspace" tabIndex={-1}>{children}</main>
        <footer className="lab-footer"><span>Observe. Review. Iterate.</span><span>Evaluation is evidence, not a release decision.</span></footer>
      </div>
    </div>
  );
}

export function Shell() {
  const { isSignedIn } = useAuth();
  return <WorkbenchFrame account={isSignedIn ? <UserButton afterSignOutUrl="/sign-in" /> : <Link to="/sign-in">Sign in →</Link>}><Outlet /></WorkbenchFrame>;
}
