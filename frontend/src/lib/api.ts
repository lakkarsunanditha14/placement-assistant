// Single place that knows where the backend lives.
// Every later phase adds functions here instead of hard-coding URLs in components.

export const API_BASE_URL =
    process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

export type Liveness = { status: string; app: string; env: string };
export type Readiness = { status: string; database: string };

async function getJson<T>(path: string): Promise<T> {
    const res = await fetch(`${API_BASE_URL}${path}`, { cache: "no-store" });
    if (!res.ok) {
        throw new Error(`${path} -> HTTP ${res.status}`);
    }
    return (await res.json()) as T;
}

export const getLiveness = () => getJson<Liveness>("/health/live");
export const getReadiness = () => getJson<Readiness>("/health/ready");