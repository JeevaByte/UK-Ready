/**
 * Typed API client for the UKReady backend.
 *
 * All backend calls go through this module. The base URL is proxied via
 * Next.js rewrites (/api/* → backend), so no CORS issues in development.
 *
 * Both functions throw on network errors or non-2xx responses.
 */

// ---------------------------------------------------------------------------
// Types (mirroring the backend Pydantic models)
// ---------------------------------------------------------------------------

export type VisaType = "GRADUATE" | "SKILLED_WORKER" | "STUDENT" | "ILR";

export const VISA_DISPLAY_NAMES: Record<VisaType, string> = {
  GRADUATE: "Graduate Visa",
  SKILLED_WORKER: "Skilled Worker Visa",
  STUDENT: "Student Visa",
  ILR: "Indefinite Leave to Remain (ILR)",
};

export const VISA_DESCRIPTIONS: Record<VisaType, string> = {
  GRADUATE:
    "2 years post-study work. Any job, any employer. No sponsorship needed.",
  SKILLED_WORKER:
    "Employer-sponsored. Tied to specific job + salary threshold.",
  STUDENT:
    "20 hrs/week during term-time. Full-time in official holidays.",
  ILR: "Permanent residence. No work restrictions. Path to citizenship.",
};

export interface ChatRequest {
  visa_type: VisaType;
  message: string;
  conversation_id?: string;
}

export interface Source {
  url: string;
  title: string;
  last_updated: string;
}

export interface ChatResponse {
  answer: string;
  confidence: "HIGH" | "MEDIUM" | "LOW";
  sources: Source[];
  conversation_id: string;
  disclaimer: string;
}

export interface HealthResponse {
  status: "ok" | "degraded";
  vector_store: "ok" | "degraded" | "empty";
  ai_provider: string;
  documents_indexed: number;
}

// ---------------------------------------------------------------------------
// API client functions
// ---------------------------------------------------------------------------

const API_BASE = "/api";

/**
 * Send a chat message and receive a visa-aware response.
 *
 * @param request - The chat request with visa type and message.
 * @returns The structured chat response from the RAG pipeline.
 * @throws Error if the API call fails or returns a non-2xx status.
 */
export async function chatAPI(request: ChatRequest): Promise<ChatResponse> {
  const response = await fetch(`${API_BASE}/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(request),
  });

  if (!response.ok) {
    const errorText = await response.text().catch(() => "Unknown error");
    throw new Error(
      `Chat API error ${response.status}: ${errorText}`
    );
  }

  return response.json() as Promise<ChatResponse>;
}

/**
 * Check the health of the UKReady backend.
 *
 * @returns Health status including vector store and AI provider status.
 * @throws Error if the health endpoint is unreachable.
 */
export async function healthAPI(): Promise<HealthResponse> {
  const response = await fetch(`${API_BASE}/health`);

  if (!response.ok) {
    throw new Error(`Health check failed: ${response.status}`);
  }

  return response.json() as Promise<HealthResponse>;
}
