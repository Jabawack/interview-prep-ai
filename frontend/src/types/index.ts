export type StepType =
  | "parse"
  | "thought"
  | "action"
  | "observation"
  | "agent_start"
  | "step"
  | "error";

export type StepStatus = "active" | "complete" | "error";

export interface AgentStep {
  id: number;
  type: StepType;
  status: StepStatus;
  content: string;
  tool?: string;
  input?: Record<string, unknown>;
  output?: string;
  isError?: boolean;
  agentKey?: string;
  agentLabel?: string;
  taskId?: string;
}

export type RunSeverity = "ok" | "warning" | "error";

export interface UsageData {
  model: string;
  prompt_tokens: number;
  completion_tokens: number;
  total_tokens: number;
  llm_calls: number;
  cost_usd: number;
}

export interface ModelInfo {
  id: string;
  input_cost_per_token: number;
  output_cost_per_token: number;
}

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  steps?: AgentStep[];
  isStreaming?: boolean;
  error?: string | null;
  usage?: UsageData;
  output?: AgentOutput;
}

export interface AgentOutput {
  intent?: string;
  entities?: Record<string, unknown>;
  results?: {
    jobs?: JobResult[];
    company_profile?: Record<string, unknown>;
    [key: string]: unknown;
  };
  summary?: string;
  follow_up_suggestions?: string[];
  error?: string | null;
}

export interface JobResult {
  title: string;
  company: string;
  location?: string;
  url?: string;
  salary?: string | null;
  description?: string;
  date_posted?: string;
  site?: string;
}

export interface JobPosting {
  id: string;
  title: string;
  company: string;
  location: string | null;
  url: string | null;
  salary_range: string | null;
  parsed_data: Record<string, unknown>;
  created_at: string;
}

export interface CompanyProfile {
  id: string;
  name: string;
  industry: string | null;
  interview_rounds: unknown[];
  common_questions: unknown[];
  glassdoor_rating: number | null;
  culture_notes: string | null;
  updated_at: string;
}
