// Single place that knows where the backend lives.

export const API_BASE_URL =
    process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

export type Readiness = { status: string; database: string };

export type Opportunity = {
    id: number;
    company: string;
    role: string;
    package: string | null;
    deadline: string | null;
    apply_url: string | null;
    bond: string | null;
    summary: string | null;
    skills: string[];
    eligible_branches: string[] | null;
    min_cgpa: string | null;
    eligible_graduation_year: number | null;
    active_backlogs_allowed: boolean | null;
};

export type EligibilityRule = {
    rule: string;
    outcome: "pass" | "fail" | "unknown";
    explanation: string;
};

export type Eligibility = {
    opportunity_id: number;
    verdict: "eligible" | "not_eligible" | "needs_review";
    rules: EligibilityRule[];
};

export type Application = {
    id: number;
    opportunity_id: number;
    state: string;
    preparation_approved_at: string | null;
    submission_approved_at: string | null;
};

async function request<T>(path: string, init?: RequestInit): Promise<T> {
    const res = await fetch(`${API_BASE_URL}${path}`, { cache: "no-store", ...init });
    if (!res.ok) {
        const body = await res.json().catch(() => ({}));
        throw new Error(body.detail ?? `${path} -> HTTP ${res.status}`);
    }
    return (await res.json()) as T;
}

const post = <T>(path: string, body?: unknown) =>
    request<T>(path, {
        method: "POST",
        headers: body ? { "Content-Type": "application/json" } : undefined,
        body: body ? JSON.stringify(body) : undefined,
    });

export const getReadiness = () => request<Readiness>("/health/ready");
export const getOpportunities = () => request<Opportunity[]>("/opportunities");
export const getApplications = () => request<Application[]>("/applications");

// ponytail: one request per expanded card. Batch it if the list ever gets long.
export const getEligibility = (id: number) =>
    request<Eligibility>(`/opportunities/${id}/eligibility`);

export const startApplication = (opportunityId: number) =>
    post<Application>("/applications", { opportunity_id: opportunityId });

export const approvePreparation = (id: number) =>
    post<Application>(`/applications/${id}/approve-preparation`);

export const approveSubmission = (id: number) =>
    post<Application>(`/applications/${id}/approve-submission`);