import { SignedIn, SignedOut, RedirectToSignIn } from "@clerk/clerk-react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { GitBranch, Plus, TestTube } from "lucide-react";

export function HomePage() {
  return (
    <>
      <SignedIn>
        <div className="container py-8">
          <div className="flex items-center justify-between mb-8">
            <div>
              <h1 className="text-3xl font-bold tracking-tight">Prompts</h1>
              <p className="text-muted-foreground mt-1">
                Version, evaluate, and ship prompts with confidence.
              </p>
            </div>
            <Button className="gap-2">
              <Plus className="h-4 w-4" />
              New Prompt
            </Button>
          </div>

          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            <Card className="border-dashed border-2 border-border bg-transparent hover:bg-card/50 transition-colors cursor-pointer">
              <CardHeader className="pb-2">
                <CardTitle className="text-base font-medium flex items-center gap-2">
                  <GitBranch className="h-4 w-4 text-primary" />
                  Prompt Registry
                </CardTitle>
                <CardDescription>
                  Create prompts with git-like versioning and diffing.
                </CardDescription>
              </CardHeader>
              <CardContent>
                <p className="text-xs text-muted-foreground font-mono">
                  v1.0 &rarr; v1.1 &rarr; production
                </p>
              </CardContent>
            </Card>

            <Card className="border-dashed border-2 border-border bg-transparent hover:bg-card/50 transition-colors cursor-pointer">
              <CardHeader className="pb-2">
                <CardTitle className="text-base font-medium flex items-center gap-2">
                  <TestTube className="h-4 w-4 text-primary" />
                  Eval Engine
                </CardTitle>
                <CardDescription>
                  Run faithfulness, relevance, and precision metrics.
                </CardDescription>
              </CardHeader>
              <CardContent>
                <p className="text-xs text-muted-foreground font-mono">
                  LLM-as-judge + cost tracking
                </p>
              </CardContent>
            </Card>
          </div>
        </div>
      </SignedIn>

      <SignedOut>
        <RedirectToSignIn />
      </SignedOut>
    </>
  );
}
