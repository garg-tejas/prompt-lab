export interface ABTestResponse {
  id: string;
  name: string;
  eval_run_a_id: string;
  eval_run_b_id: string;
  dataset_id: string;
  status: string;
  results_summary: {
    metrics: Record<string, {
      mean_diff: number | null;
      std_dev: number | null;
      std_error: number | null;
      t_stat?: number | null;
      p_value?: number | null;
      n: number;
      significant: boolean;
      winner: "a" | "b" | "tie";
      ci_95: [number, number] | null;
      direction?: "higher" | "lower" | null;
      excluded_row_ids?: string[];
      coverage_status?: "complete" | "incomplete" | "unknown";
      expected_eligible?: number | null;
      missing_score_row_ids?: string[] | null;
      not_applicable_row_ids?: string[] | null;
    }>;
    overall_winner: "a" | "b" | "tie";
    a_wins: number;
    b_wins: number;
    total_samples: number;
    decision_note?: string;
    dataset_snapshot_status?: "matching" | "different" | "unknown";
    coverage?: {
      observed_a: number;
      observed_b: number;
      expected_a: number | null;
      expected_b: number | null;
      missing_results_a: number | null;
      missing_results_b: number | null;
      only_a_row_ids: string[];
      only_b_row_ids: string[];
      complete: boolean;
      metric_coverage?: "complete" | "incomplete" | "unknown";
    };
  } | null;
  created_by: string;
  created_at: string;
  completed_at: string | null;
}

export interface ABTestDetailResponse extends ABTestResponse {
  per_sample_breakdown: {
    dataset_row_id: string;
    wins: { a: number; b: number; tie: number };
    excluded_metrics?: string[];
    not_applicable_metrics?: string[];
  }[] | null;
}
