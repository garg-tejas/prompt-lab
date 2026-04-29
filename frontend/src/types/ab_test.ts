export interface ABTestResponse {
  id: string;
  name: string;
  eval_run_a_id: string;
  eval_run_b_id: string;
  dataset_id: string;
  status: string;
  results_summary: {
    metrics: Record<string, {
      mean_diff: number;
      std_dev: number;
      std_error: number;
      n: number;
      significant: boolean;
      winner: "a" | "b" | "tie";
      ci_95: [number, number];
    }>;
    overall_winner: "a" | "b" | "tie";
    a_wins: number;
    b_wins: number;
    total_samples: number;
  } | null;
  created_by: string;
  created_at: string;
  completed_at: string | null;
}

export interface ABTestDetailResponse extends ABTestResponse {
  per_sample_breakdown: {
    dataset_row_id: string;
    wins: { a: number; b: number; tie: number };
  }[] | null;
}
