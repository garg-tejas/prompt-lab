# PromptLab interface verification

The application uses a navy navigation rail and pale-paper evaluation workspace. Prompt registry, run ledger, and comparison register are searchable tables with loading, error/retry, empty, signed-out, and populated states. The shared vocabulary is consistent with the portfolio; PromptLab is organized as an evaluation workbench.

## Credential-free design preview

Run `pnpm dev --host 127.0.0.1 --port 4181`, then open `http://127.0.0.1:4181/design-preview.html`.

This is a separate Vite development entry using the actual `WorkbenchFrame`, `PromptRegistryView`, `RunLedgerView`, and `ComparisonRegisterView` components. The yellow fixture banner labels all displayed records as synthetic. Switch states with the banner control; use the sidebar to inspect the three registers. Search and status filters operate on fixture records. Other destination screens show an explicit unavailable-fixture state.

No Clerk provider is mounted. The fixture never invokes the authenticated data hooks. Every Axios request is rejected by a fixture adapter, including accidental form submissions. It does not connect to a backend, model provider, or database. This verifies rendering and local interactions only; it does not verify authentication or backend integration.

`design-preview.html` is not a production Vite build input, and `src/design-preview.tsx` is not imported by the application entry. Its mount is also guarded by `import.meta.env.DEV`. The application continues using Clerk and its authenticated API connection.
