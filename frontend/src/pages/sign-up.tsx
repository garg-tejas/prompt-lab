import { SignUp } from "@clerk/clerk-react";

export function SignUpPage() {
  return (
    <div className="flex min-h-[calc(100vh-3.5rem)] items-center justify-center px-4">
      <SignUp
        routing="path"
        path="/sign-up"
        signInUrl="/sign-in"
        appearance={{
          elements: {
            card: "bg-card border border-border shadow-lg",
            headerTitle: "text-foreground",
            headerSubtitle: "text-muted-foreground",
            socialButtonsBlockButton:
              "border-border text-foreground hover:bg-secondary",
            socialButtonsBlockButtonText: "text-foreground",
            dividerLine: "bg-border",
            dividerText: "text-muted-foreground",
            formFieldLabel: "text-foreground",
            formFieldInput:
              "bg-background border-border text-foreground focus:ring-primary",
            footerActionText: "text-muted-foreground",
            footerActionLink: "text-primary hover:text-primary/80",
            formButtonPrimary: "bg-primary text-primary-foreground hover:bg-primary/90",
          },
        }}
      />
    </div>
  );
}
