import { useCallback, useState } from "react";
import { adminCall } from "../api";
import { Empty, ErrorBox, Spinner } from "../components/ui";
import { useApi } from "../hooks";

// Owner-facing verdict surface for CODEX_LINGQ_CONSOLE.md. This page stores
// decisions only; the coordinator commissions any build in a separate step.

type Verdict =
  | "greenlight-pilot"
  | "interested-later"
  | "not-for-me"
  | "defer";

type SizingFact = {
  value: string;
  label: string;
};

type LingqRow = {
  concept_key: string;
  concept_id: string;
  name: string;
  pitch: string;
  sizing: SizingFact[];
  study_minutes_per_day: number;
  study_impact: string;
  proposal_rank: number;
  proposal_score: number;
  recommended: boolean;
  recommendation_reason: string | null;
  owner_verdict: Verdict | null;
  owner_note: string | null;
  verdicted_at: string | null;
  seeded_at: string;
};

type LingqResponse = {
  rows: LingqRow[];
  summary: {
    total: number;
    verdicted: number;
    remaining: number;
    verdict_counts: Record<string, number>;
  };
  meta: {
    applies_changes: boolean;
    coordinator_note: string;
  };
};

const VERDICT_BUTTONS: {
  key: Verdict;
  label: string;
  selected: string;
}[] = [
  {
    key: "greenlight-pilot",
    label: "Greenlight pilot",
    selected: "border-emerald-600 bg-emerald-700 text-white",
  },
  {
    key: "interested-later",
    label: "Interested later",
    selected: "border-sky-600 bg-sky-700 text-white",
  },
  {
    key: "not-for-me",
    label: "Not for me",
    selected: "border-slate-500 bg-slate-600 text-white",
  },
  {
    key: "defer",
    label: "Defer",
    selected: "border-edge bg-surface-2 text-ink",
  },
];

function NoteField({
  row,
  busy,
  onSave,
}: {
  row: LingqRow;
  busy: boolean;
  onSave: (note: string) => Promise<void>;
}) {
  const [open, setOpen] = useState(Boolean(row.owner_note));
  const [text, setText] = useState(row.owner_note ?? "");

  if (!open) {
    return (
      <button
        type="button"
        className="min-h-11 rounded border border-edge px-3 py-2 text-sm text-muted hover:bg-surface-2 hover:text-ink"
        disabled={busy}
        onClick={() => setOpen(true)}
      >
        + note
      </button>
    );
  }

  return (
    <textarea
      className="min-h-11 min-w-56 flex-1 rounded border border-edge bg-page/40 px-3 py-2 text-sm text-ink placeholder:text-muted"
      rows={2}
      autoFocus={!row.owner_note}
      placeholder="Optional owner note…"
      value={text}
      disabled={busy}
      onChange={(event) => setText(event.target.value)}
      onBlur={() => {
        if (text !== (row.owner_note ?? "")) void onSave(text);
      }}
    />
  );
}

function ConceptCard({
  row,
  busy,
  onVerdict,
  onNote,
}: {
  row: LingqRow;
  busy: boolean;
  onVerdict: (row: LingqRow, verdict: Verdict) => Promise<void>;
  onNote: (row: LingqRow, note: string) => Promise<void>;
}) {
  return (
    <article
      className={`rounded-xl border p-4 ${
        row.recommended
          ? "border-accent bg-surface shadow-[0_0_0_1px_rgba(57,135,229,0.2)]"
          : "border-edge bg-surface"
      }`}
    >
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <div className="flex flex-wrap items-center gap-2">
            <span className="rounded bg-surface-2 px-2 py-1 text-xs font-bold text-muted">
              {row.concept_id}
            </span>
            <h2 className="text-lg font-bold">{row.name}</h2>
            {row.recommended && (
              <span className="rounded-full border border-accent/60 bg-accent/15 px-2 py-1 text-[11px] font-bold uppercase tracking-wide text-sky-300">
                Recommended pilot
              </span>
            )}
            {row.owner_verdict && (
              <span className="text-xs font-semibold text-good">
                ✓ {row.owner_verdict}
              </span>
            )}
          </div>
          <div className="mt-1 text-xs text-muted tnum">
            proposal rank #{row.proposal_rank} · score {row.proposal_score}/20
          </div>
        </div>
        <div className="rounded-lg border border-edge bg-page/40 px-3 py-2 text-right">
          <div className="text-[10px] uppercase tracking-wide text-muted">
            Study impact
          </div>
          <div className="text-sm font-semibold text-ink-2">
            {row.study_impact}
          </div>
        </div>
      </div>

      <p className="mt-3 max-w-5xl text-sm leading-relaxed text-ink-2">
        {row.pitch}
      </p>

      <div className="mt-3 flex flex-wrap gap-2">
        {row.sizing.map((fact) => (
          <div
            key={`${fact.value}-${fact.label}`}
            className="rounded-md border border-edge bg-page/30 px-2.5 py-1.5"
          >
            <span className="text-xs font-bold text-ink tnum">{fact.value}</span>{" "}
            <span className="text-xs text-muted">{fact.label}</span>
          </div>
        ))}
      </div>

      {row.recommended && row.recommendation_reason && (
        <div className="mt-3 rounded-lg border border-accent/40 bg-accent/10 p-3 text-sm leading-relaxed text-ink-2">
          <span className="font-semibold text-sky-300">Why this pilot:</span>{" "}
          {row.recommendation_reason}
        </div>
      )}

      <div className="mt-4 flex flex-wrap items-stretch gap-2">
        {VERDICT_BUTTONS.map((definition) => {
          const selected = row.owner_verdict === definition.key;
          return (
            <button
              key={definition.key}
              type="button"
              disabled={busy}
              onClick={() => void onVerdict(row, definition.key)}
              className={`min-h-11 rounded border px-3 py-2 text-sm font-semibold disabled:opacity-50 ${
                selected
                  ? definition.selected
                  : "border-edge text-ink-2 hover:bg-surface-2 hover:text-ink"
              }`}
            >
              {definition.label}
            </button>
          );
        })}
        <NoteField
          key={`${row.concept_key}-${row.owner_note ?? ""}`}
          row={row}
          busy={busy}
          onSave={(note) => onNote(row, note)}
        />
      </div>
    </article>
  );
}

export default function Lingq() {
  const [refreshKey, setRefreshKey] = useState(0);
  const { data, error, loading } = useApi<LingqResponse>("/lingq", {
    refresh: refreshKey,
  });
  const [busy, setBusy] = useState(false);
  const [actionError, setActionError] = useState<unknown>(null);
  const [toast, setToast] = useState<string | null>(null);

  const reload = useCallback(() => {
    setRefreshKey((value) => value + 1);
  }, []);

  const flash = (message: string) => {
    setToast(message);
    window.setTimeout(() => setToast(null), 1600);
  };

  const saveVerdict = useCallback(
    async (row: LingqRow, verdict: Verdict) => {
      if (busy) return;
      setBusy(true);
      setActionError(null);
      try {
        await adminCall("/admin/lingq-verdict", {
          body: { concept_key: row.concept_key, verdict },
        });
        flash(`✓ ${row.concept_id}: ${verdict}`);
        reload();
      } catch (requestError) {
        setActionError(requestError);
      } finally {
        setBusy(false);
      }
    },
    [busy, reload],
  );

  const saveNote = useCallback(
    async (row: LingqRow, note: string) => {
      setBusy(true);
      setActionError(null);
      try {
        await adminCall("/admin/lingq-verdict", {
          body: { concept_key: row.concept_key, note },
        });
        flash("note saved");
        reload();
      } catch (requestError) {
        setActionError(requestError);
      } finally {
        setBusy(false);
      }
    },
    [reload],
  );

  if (loading && !data) return <Spinner />;
  if (error) return <ErrorBox error={error} />;
  if (!data || data.rows.length === 0) {
    return <Empty>No LingQ concepts have been seeded yet.</Empty>;
  }

  const progress =
    data.summary.total === 0
      ? 0
      : (data.summary.verdicted / data.summary.total) * 100;

  return (
    <div className="flex flex-col gap-4">
      <div className="sticky top-0 z-20 -mx-8 border-b border-edge bg-page/95 px-8 py-2 backdrop-blur">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <div className="text-sm font-semibold tnum">
            {data.summary.verdicted}/{data.summary.total} concepts decided
            <span className="ml-2 text-xs font-normal text-muted">
              {data.summary.remaining} remaining
            </span>
          </div>
          {toast && <span className="text-xs font-semibold text-good">{toast}</span>}
        </div>
        <div className="mt-2 h-1.5 overflow-hidden rounded-full bg-surface-2">
          <div
            className="h-full rounded-full bg-accent transition-[width] duration-300"
            style={{ width: `${progress}%` }}
          />
        </div>
      </div>

      <div>
        <h1 className="text-xl font-bold">LingQ — dormant value</h1>
        <p className="mt-1 max-w-4xl text-sm text-muted">
          Seven product directions distilled from the technical inventory and
          ranked proposal. Decide each concept here; the research documents stay
          source material, not the verdict surface.
        </p>
      </div>

      <div className="grid grid-cols-2 gap-px overflow-hidden rounded-xl border border-edge bg-edge sm:grid-cols-4">
        {[
          ["51,826", "terms"],
          ["95%", "status-0 encounter log"],
          ["5,455", "never-drilled multiword expressions in active langs"],
          ["~18k", "pre-clozed fragments"],
        ].map(([value, label]) => (
          <div key={label} className="bg-surface p-3">
            <div className="text-lg font-bold tnum">{value}</div>
            <div className="mt-0.5 text-xs leading-snug text-muted">{label}</div>
          </div>
        ))}
      </div>

      <div className="rounded-lg border border-warning/50 bg-surface p-3 text-sm text-ink-2">
        <span className="font-semibold text-warning">Decisions only.</span>{" "}
        {data.meta.coordinator_note} Nothing on this page builds cards, spends
        money, or changes an Anki collection.
      </div>

      {actionError != null && <ErrorBox error={actionError} />}

      <div className="flex flex-col gap-3">
        {data.rows.map((row) => (
          <ConceptCard
            key={row.concept_key}
            row={row}
            busy={busy}
            onVerdict={saveVerdict}
            onNote={saveNote}
          />
        ))}
      </div>
    </div>
  );
}
