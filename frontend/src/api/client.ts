import type { SessionDetail, SessionOut } from "../types";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE_URL}${path}`, {
    headers: init?.body instanceof FormData ? undefined : { "Content-Type": "application/json" },
    ...init,
  });
  if (!res.ok) {
    const body = await res.text();
    throw new Error(`${res.status} ${res.statusText}: ${body}`);
  }
  return res.json() as Promise<T>;
}

export function createSession(payload: {
  patient_pseudonym: string;
  clinician_name: string;
  language: string;
}): Promise<SessionOut> {
  return request<SessionOut>("/api/sessions", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function listSessions(): Promise<SessionOut[]> {
  return request<SessionOut[]>("/api/sessions");
}

export function getSessionDetail(sessionId: string): Promise<SessionDetail> {
  return request<SessionDetail>(`/api/sessions/${sessionId}`);
}

export function ingestTextTranscript(sessionId: string, text: string): Promise<SessionDetail> {
  return request<SessionDetail>(`/api/sessions/${sessionId}/transcript`, {
    method: "POST",
    body: JSON.stringify({ text }),
  });
}

export function ingestAudio(sessionId: string, audioBlob: Blob): Promise<SessionDetail> {
  const formData = new FormData();
  formData.append("file", audioBlob, "recording.webm");
  return request<SessionDetail>(`/api/sessions/${sessionId}/audio`, {
    method: "POST",
    body: formData,
  });
}

export function reviewNote(
  sessionId: string,
  decision: "approve" | "reject",
): Promise<SessionDetail> {
  return request<SessionDetail>(`/api/sessions/${sessionId}/review`, {
    method: "POST",
    body: JSON.stringify({ decision }),
  });
}
