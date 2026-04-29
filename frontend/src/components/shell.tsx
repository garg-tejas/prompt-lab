import { Outlet, Link } from "react-router-dom";
import { useAuth, UserButton } from "@clerk/clerk-react";
import { FlaskConical } from "lucide-react";

export function Shell() {
  const { isSignedIn } = useAuth();

  return (
    <div className="flex min-h-screen flex-col bg-background">
      {/* Top bar */}
      <header className="sticky top-0 z-50 w-full border-b border-border bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
        <div className="container flex h-14 items-center">
          <div className="flex items-center gap-2 mr-8">
            <FlaskConical className="h-5 w-5 text-primary" />
            <span className="font-bold text-lg tracking-tight">
              PromptLab
            </span>
          </div>

          {isSignedIn && (
            <nav className="flex items-center gap-6 text-sm font-medium">
              <Link
                to="/"
                className="transition-colors hover:text-primary text-muted-foreground"
              >
                Prompts
              </Link>
              <Link
                to="/datasets"
                className="transition-colors hover:text-primary text-muted-foreground"
              >
                Datasets
              </Link>
              <Link
                to="/models"
                className="transition-colors hover:text-primary text-muted-foreground"
              >
                Models
              </Link>
              <Link
                to="/runs"
                className="transition-colors hover:text-primary text-muted-foreground"
              >
                Runs
              </Link>
            </nav>
          )}

          <div className="ml-auto flex items-center gap-4">
            {isSignedIn ? (
              <UserButton afterSignOutUrl="/sign-in" />
            ) : (
              <Link
                to="/sign-in"
                className="text-sm font-medium text-primary hover:underline"
              >
                Sign In
              </Link>
            )}
          </div>
        </div>
      </header>

      {/* Main content */}
      <main className="flex-1">
        <Outlet />
      </main>

      {/* Footer */}
      <footer className="border-t border-border py-4">
        <div className="container flex items-center justify-between text-xs text-muted-foreground">
          <span>PromptLab v0.1.0</span>
          <span className="font-mono">Built for rigorous eval</span>
        </div>
      </footer>
    </div>
  );
}
