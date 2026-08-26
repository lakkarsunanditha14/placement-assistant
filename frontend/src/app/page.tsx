"use client";

import { useEffect, useState } from "react";
import {
  approvePreparation,
  approveSubmission,
  getApplications,
  getEligibility,
  getOpportunities,
  getReadiness,
  startApplication,
  type Application,
  type Eligibility,
  type Opportunity,
} from "@/lib/api";

const VERDICT_STYLE: Record<string, string> = {
  eligible: "bg-green-100 text-green-800 border-green-300",
  not_eligible: "bg-red-100 text-red-800 border-red-300",
  needs_review: "bg-amber-100 text-amber-800 border-amber-300",
};

const OUTCOME_MARK: Record<string, string> = {
  pass: "✓",
  fail: "✗",
  unknown: "?",
};

export default function Home() {
  const [opportunities, setOpportunities] = useState<Opportunity[]>([]);
  const [applications, setApplications] = useState<Application[]>([]);
  const [dbOk, setDbOk] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const load = () =>
    Promise.all([getOpportunities(), getApplications(), getReadiness()])
      .then(([o, a, r]) => {
        setOpportunities(o);
        setApplications(a);
        setDbOk(r.database === "ok");
        setError(null);
      })
      .catch((e: Error) => setError(e.message));

  useEffect(() => {
    load();
  }, []);

  return (
    <main className="min-h-screen bg-slate-50 p-8 text-slate-900">
      <header className="mb-8 flex items-baseline justify-between">
        <div>
          <h1 className="text-2xl font-semibold">Placement Assistant</h1>
          <p className="mt-1 text-sm text-slate-500">
            {opportunities.length} opportunit
            {opportunities.length === 1 ? "y" : "ies"} tracked
          </p>
        </div>
        <span className="flex items-center gap-2 text-xs text-slate-500">
          <span
            className={`h-2 w-2 rounded-full ${dbOk ? "bg-green-500" : "bg-slate-300"}`}
          />
          {dbOk ? "connected" : "backend unreachable"}
        </span>
      </header>

      {error && (
        <div className="mb-6 rounded-md border border-red-300 bg-red-50 p-4 text-sm text-red-800">
          {error}
        </div>
      )}

      {opportunities.length === 0 && !error && (
        <p className="text-sm text-slate-500">
          No opportunities yet. Create one with a POST to /opportunities.
        </p>
      )}

      <div className="grid max-w-3xl gap-4">
        {opportunities.map((opportunity) => (
          <Card
            key={opportunity.id}
            opportunity={opportunity}
            application={applications.find(
              (a) => a.opportunity_id === opportunity.id,
            )}
            onChange={load}
          />
        ))}
      </div>
    </main>
  );
}

function Card({
  opportunity,
  application,
  onChange,
}: {
  opportunity: Opportunity;
  application?: Application;
  onChange: () => void;
}) {
  const [open, setOpen] = useState(false);
  const [eligibility, setEligibility] = useState<Eligibility | null>(null);
  const [problem, setProblem] = useState<string | null>(null);

  useEffect(() => {
    if (!open || eligibility) return;
    getEligibility(opportunity.id)
      .then(setEligibility)
      .catch((e: Error) => setProblem(e.message));
  }, [open, eligibility, opportunity.id]);

  const act = (fn: () => Promise<unknown>) => () => {
    setProblem(null);
    fn()
      .then(onChange)
      .catch((e: Error) => setProblem(e.message));
  };

  return (
    <section className="rounded-lg border border-slate-200 bg-white">
      <button
        onClick={() => setOpen(!open)}
        className="flex w-full items-start justify-between p-4 text-left"
      >
        <span>
          <span className="block font-medium">{opportunity.company}</span>
          <span className="block text-sm text-slate-500">
            {opportunity.role}
            {opportunity.package && ` · ${opportunity.package}`}
          </span>
        </span>
        <span className="flex items-center gap-3">
          {eligibility && (
            <span
              className={`rounded border px-2 py-0.5 text-xs ${VERDICT_STYLE[eligibility.verdict]
                }`}
            >
              {eligibility.verdict.replace("_", " ")}
            </span>
          )}
          <span className="text-slate-400">{open ? "−" : "+"}</span>
        </span>
      </button>

      {open && (
        <div className="border-t border-slate-100 p-4 text-sm">
          {opportunity.deadline && (
            <p className="mb-3 text-slate-600">
              Deadline: {new Date(opportunity.deadline).toLocaleString()}
            </p>
          )}

          {problem && <p className="mb-3 text-red-700">{problem}</p>}

          {eligibility && (
            <ul className="mb-4 space-y-1">
              {eligibility.rules.map((rule) => (
                <li key={rule.rule} className="flex gap-2 text-slate-700">
                  <span className="w-4 text-slate-400">
                    {OUTCOME_MARK[rule.outcome]}
                  </span>
                  {rule.explanation}
                </li>
              ))}
              {eligibility.rules.length === 0 && (
                <li className="text-slate-500">
                  This posting stated no eligibility requirements.
                </li>
              )}
            </ul>
          )}

          <Gates
            application={application}
            onStart={act(() => startApplication(opportunity.id))}
            onGateOne={act(() => approvePreparation(application!.id))}
            onGateTwo={act(() => approveSubmission(application!.id))}
          />
        </div>
      )}
    </section>
  );
}

function Gates({
  application,
  onStart,
  onGateOne,
  onGateTwo,
}: {
  application?: Application;
  onStart: () => void;
  onGateOne: () => void;
  onGateTwo: () => void;
}) {
  if (!application) {
    return <Button onClick={onStart} label="Track this opportunity" />;
  }

  if (application.state === "waiting_for_preparation_approval") {
    return (
      <div>
        <p className="mb-2 text-slate-600">
          Nothing has been opened or filled. Preparation needs your explicit
          approval.
        </p>
        <Button onClick={onGateOne} label="Approve preparation — Gate 1" />
      </div>
    );
  }

  if (application.state === "waiting_for_submission_approval") {
    return (
      <div>
        <p className="mb-2 text-slate-600">
          The form is filled but nothing has been sent.
        </p>
        <Button onClick={onGateTwo} label="Approve submission — Gate 2" />
      </div>
    );
  }

  return (
    <p className="text-slate-600">
      State: <span className="font-medium">{application.state.replace(/_/g, " ")}</span>
    </p>
  );
}

function Button({ onClick, label }: { onClick: () => void; label: string }) {
  return (
    <button
      onClick={onClick}
      className="rounded-md bg-slate-900 px-3 py-1.5 text-sm font-medium text-white hover:bg-slate-700"
    >
      {label}
    </button>
  );
}