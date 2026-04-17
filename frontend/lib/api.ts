import type { UploadResponse, QueryResponse, ComplianceReport } from "@/types";

function resolveBaseUrl(): string {
  const configured = process.env.NEXT_PUBLIC_API_URL;
  if (configured) return configured;

  if (typeof window !== "undefined") {
    const { hostname } = window.location;
    if (hostname !== "localhost" && hostname !== "127.0.0.1") {
      throw new Error(
        "Frontend is missing NEXT_PUBLIC_API_URL. Set it to the backend URL before using uploads."
      );
    }
  }

  return "http://localhost:8000";
}

async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  try {
    const res = await fetch(`${resolveBaseUrl()}${path}`, init);
    if (!res.ok) {
      const body = await res.json().catch(() => ({}));
      throw new Error(body.detail ?? `API error ${res.status}`);
    }
    return res.json() as Promise<T>;
  } catch (error) {
    if (error instanceof Error) {
      if (error.message === "Failed to fetch") {
        throw new Error(
          "Failed to reach the backend. Check NEXT_PUBLIC_API_URL, backend health, CORS, and upload size."
        );
      }
      throw error;
    }
    throw new Error(
      "Failed to reach the backend. Check NEXT_PUBLIC_API_URL, backend health, CORS, and upload size."
    );
  }
}

export async function uploadDocument(file: File): Promise<UploadResponse> {
  const form = new FormData();
  form.append("file", file);
  return apiFetch<UploadResponse>("/upload", { method: "POST", body: form });
}

export async function queryDocument(
  documentId: string,
  question: string
): Promise<QueryResponse> {
  return apiFetch<QueryResponse>("/query", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ document_id: documentId, question }),
  });
}

export async function generateReport(documentId: string): Promise<ComplianceReport> {
  return apiFetch<ComplianceReport>(`/report?document_id=${documentId}`, {
    method: "POST",
  });
}

export async function getMetrics(): Promise<{ session_total_cost_usd: number; total_tokens: Record<string, number> }> {
  return apiFetch("/metrics");
}

export async function clearSession(): Promise<{ message: string }> {
  return apiFetch("/session", { method: "DELETE" });
}
