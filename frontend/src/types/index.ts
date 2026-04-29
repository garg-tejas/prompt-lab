export interface PromptTag {
  id: string;
  name: string;
}

export interface PromptVersion {
  id: string;
  prompt_id: string;
  version_hash: string;
  commit_message: string;
  content: string;
  variables: string[];
  tag: string | null;
  created_at: string;
}

export interface Prompt {
  id: string;
  name: string;
  description: string | null;
  owner_id: string;
  tags: PromptTag[];
  created_at: string;
  updated_at: string;
  version_count: number;
  latest_version: PromptVersion | null;
  production_version: PromptVersion | null;
  versions?: PromptVersion[];
}
