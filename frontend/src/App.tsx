import { Suspense } from "react";
import { Routes, Route } from "react-router-dom";
import { useAuth } from "@clerk/clerk-react";
import { Shell } from "@/components/shell";
import { AuthSync } from "@/components/auth-sync";
import { PromptListPage } from "@/pages/prompts/list";
import { PromptDetailPage } from "@/pages/prompts/detail";
import { EvalWizardPage } from "@/pages/eval/wizard";
import { EvalHistoryPage } from "@/pages/eval/history";
import { EvalDetailPage } from "@/pages/eval/detail";
import { SignInPage } from "@/pages/sign-in";
import { SignUpPage } from "@/pages/sign-up";

function App() {
  const { isLoaded } = useAuth();

  if (!isLoaded) {
    return (
      <div className="flex h-screen w-screen items-center justify-center bg-background">
        <div className="font-mono text-sm text-muted-foreground animate-pulse">
          Loading PromptLab...
        </div>
      </div>
    );
  }

  return (
    <>
      <AuthSync />
      <Suspense
        fallback={
          <div className="flex h-screen w-screen items-center justify-center bg-background">
            <div className="font-mono text-sm text-muted-foreground animate-pulse">
              Loading...
            </div>
          </div>
        }
      >
        <Routes>
          <Route path="/sign-in/*" element={<SignInPage />} />
          <Route path="/sign-up/*" element={<SignUpPage />} />
          <Route path="/*" element={<Shell />}>
            <Route index element={<PromptListPage />} />
            <Route path="prompts/:id" element={<PromptDetailPage />} />
            <Route path="runs" element={<EvalHistoryPage />} />
            <Route path="runs/new" element={<EvalWizardPage />} />
            <Route path="runs/:id" element={<EvalDetailPage />} />
          </Route>
        </Routes>
      </Suspense>
    </>
  );
}

export default App;
