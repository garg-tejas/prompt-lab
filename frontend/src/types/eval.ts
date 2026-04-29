export interface DatasetRow {
  id: string;
  dataset_id: string;
  question: string;
  context: string;
  expected_answer: string | null;
  created_at: string;
}

export interface Dataset {
  id: string;
  name: string;
  description: string | null;
  domain_tag: string | null;
  owner_id: string;
  created_at: string;
  row_count: number;
  rows?: DatasetRow[];
}

export interface ModelEndpoint {
  id: string;
  name: string;
  model_name: string;
  provider: string;
  base_url: string;
  context_window: number | null;
  cost_per_1k_input: number | null;
  cost_per_1k_output: number | null;
  is_judge: boolean;
  created_by: string;
  created_at: string;
}

export interface EvalConfig {
  sample_size?: number;
  concurrency: number;
  retry_count: number;
}

export interface EvalRunResponse {
  id: string;
  name: string;
  prompt_id: string;
  prompt_version_id: string;
  dataset_id: string;
  model_id: string;
  judge_model_id: string;
  status: string;
  config: EvalConfig;
  results_summary: Record<string, any> | null;
  created_by: string;
  created_at: string;
  completed_at: string | null;
}

export interface MetricScoreResponse {
  id: string;
  metric_name: string;
  score: number;
  explanation: string | null;
  judge_model_id: string;
  created_at: string;
}

export interface EvalResultResponse {
  id: string;
  dataset_row_id: string;
  output: string;
  latency_ms: number;
  input_tokens: number;
  output_tokens: number;
  estimated_cost: number;
  created_at: string;
  scores: MetricScoreResponse[];
}

export interface EvalRunDetailResponse extends EvalRunResponse {
  results: EvalResultResponse[];
}
