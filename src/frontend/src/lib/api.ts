const BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
const V1 = `${BASE}/api/v1`;

export const API = {
  chatStream: `${V1}/chat/stream`,
  jobs: `${V1}/jobs`,
  companies: `${V1}/companies`,
  conversations: `${V1}/conversations`,
} as const;
