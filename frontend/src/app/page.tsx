"use client";

import { useEffect, useState } from "react";
import { getLiveness, getReadiness, type Liveness, type Readiness } from "@/lib/api";

export default function Home() {
  const [live, setLive] = useState<Liveness | null>(null);
  const [ready, setReady] = useState<Readiness | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    Promise.all([getLiveness(), getReadiness()])
      .then(([l, r]) => {
        setLive(l);
        setReady(r);
      })
      .catch((e: Error) => setError(e.message));
  }, []);

  const ok = (v?: string) => v === "ok";

  return (
    <main className="min-h-screen bg-slate-50 p-10 text-slate-900">
      <h1 className="text-2xl font-semibold">Placement Assistant</h1>
      <p className="mt-1 text-sm text-slate-500">Phase 1 — local setup check</p>

      {error && (
        <div className="mt-6 rounded-md border border-red-300 bg-red-50 p-4 text-sm text-red-800">
          Cannot reach the backend: {error}
          <br />
          Is <code>uvicorn app.main:app --reload</code> running on port 8000?
        </div>
      )}

      <div className="mt-6 grid max-w-xl gap-3">
        <Row label="Backend (FastAPI)" ok={ok(live?.status)} detail={live?.app ?? "…"} />
        <Row
          label="Database (PostgreSQL)"
          ok={ok(ready?.database)}
          detail={ready?.database ?? "…"}
        />
      </div>
    </main>
  );
}

function Row({ label, ok, detail }: { label: string; ok: boolean; detail: string }) {
  return (
    <div className="flex items-center justify-between rounded-md border border-slate-200 bg-white px-4 py-3">
      <span className="font-medium">{label}</span>
      <span className="flex items-center gap-2 text-sm">
        <span className={`h-2.5 w-2.5 rounded-full ${ok ? "bg-green-500" : "bg-slate-300"}`} />
        <span className="text-slate-600">{detail}</span>
      </span>
    </div>
  );
}