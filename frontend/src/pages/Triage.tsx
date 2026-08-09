import { useCallback, useMemo, useState } from "react";
import { adminCall } from "../api";
import { Empty, ErrorBox, Spinner } from "../components/ui";
import { useApi } from "../hooks";

// DJ-C2 curation-triage console (CODEX_DJ_C2_CURATION_TRIAGE.md): the owner
// walks every studyable subtree and records a disposition verdict. Phone-
// first: large touch targets, one-tap verdicts, sticky projection bar.
// This page NEVER applies anything to a collection — verdicts are stored
// server-side; the executor lane applies them owner-present, later.

type Disposition =
  | "keep-active"
  | "suspend-reference"
  | "sample-hardest"
  | "owner-review";

type Verdict =
  | "accept-proposal"
  | "keep-active"
  | "suspend-reference"
  | "sample-hardest"
  | "defer";

type TriageRow = {
  subtree: string;
  language: string;
  lane: string;
  scope_kind: "lane" | "first_level_subdeck" | "dormant_summary";
  parent_subtree: string | null;
  applied_scope: boolean;
  card_count: number;
  due_now: number;
  new_reservoir: number;
  suspended_cards: number;
  provenance_dominant: string | null;
  reps: number;
  distinct_studied_cards: number;
  recent_reps: number;
  last_touch_date: string | null;
  easy_rate_pct: number | null;
  again_rate_pct: number | null;
  median_ivl_mature_days: number | null;
  due_minutes_before: number;
  due_cards_before: number;
  due_minutes_after_proposal: number;
  due_cards_after_proposal: number;
  proposal_disposition: Disposition;
  sample_n: number | null;
  rationale: string;
  owner_verdict: Verdict | null;
  owner_note: string | null;
  verdicted_at: string | null;
  source_as_of: string;
};

type LangProjection = {
  language: string;
  before_minutes: number;
  before_due_cards: number;
  current_minutes: number;
  current_due_cards: number;
  proposal_minutes: number;
  proposal_due_cards: number;
  applied_scopes: number;
  undecided_scopes: number;
};

type TriageResponse = {
  rows: TriageRow[];
  summary: {
    total: number;
    verdicted: number;
    remaining: number;
    verdict_counts: Record<string, number>;
    languages: LangProjection[];
  };
  meta: {
    source_as_of: string | null;
    applies_dispositions: boolean;
    executor_note: string;
  };
};

const VERDICT_BUTTONS: {
  key: Verdict;
  label: string;
  selectedCls: string;
  proposedCls: string;
}[] = [
  {
    key: "accept-proposal",
    label: "Accept",
    selectedCls: "bg-sky-700 text-white",
    proposedCls: "border-sky-600",
  },
  {
    key: "keep-active",
    label: "Keep",
    selectedCls: "bg-emerald-700 text-white",
    proposedCls: "border-emerald-600",
  },
  {
    key: "suspend-reference",
    label: "Suspend",
    selectedCls: "bg-slate-600 text-white",
    proposedCls: "border-slate-400",
  },
  {
    key: "sample-hardest",
    label: "Sample",
    selectedCls: "bg-amber-700 text-white",
    proposedCls: "border-amber-600",
  },
  {
    key: "defer",
    label: "Defer",
    selectedCls: "bg-surface-2 text-ink ring-1 ring-edge",
    proposedCls: "border-edge",
  },
];

const PROPOSAL_SHORT: Record<Disposition, string> = {
  "keep-active": "keep",
  "suspend-reference": "suspend",
  "sample-hardest": "sample hardest",
  "owner-review": "your call",
};

const PROVENANCE_SHORT: Record<string, string> = {
  "pipeline-minted": "pipeline",
  "batch-imported": "batch",
  "hand-made": "hand-made",
};

function fmtMin(v: number): string {
  return v >= 10 ? String(Math.round(v)) : v.toFixed(1);
}

function rowName(row: TriageRow): string {
  if (row.scope_kind === "lane") return row.lane;
  const parts = row.subtree.split("::");
  return parts[parts.length - 1];
}

function Chip({
  children,
  tone = "muted",
}: {
  children: React.ReactNode;
  tone?: "muted" | "warning" | "good";
}) {
  const cls =
    tone === "warning"
      ? "text-warning border-warning/40"
      : tone === "good"
        ? "text-good border-good/40"
        : "text-muted border-edge";
  return (
    <span
      className={`inline-flex items-center rounded border px-1.5 py-0.5 text-[11px] tnum ${cls}`}
    >
      {children}
    </span>
  );
}

function EvidenceChips({ row }: { row: TriageRow }) {
  const studied = row.reps > 0;
  return (
    <div className="flex flex-wrap gap-1">
      <Chip tone={row.due_now > 0 ? "warning" : "muted"}>
        due {row.due_now.toLocaleString()}
      </Chip>
      <Chip>{row.card_count.toLocaleString()} cards</Chip>
      <Chip>new {row.new_reservoir.toLocaleString()}</Chip>
      {studied && row.easy_rate_pct != null && (
        <Chip>easy {row.easy_rate_pct.toFixed(0)}%</Chip>
      )}
      {studied && row.again_rate_pct != null && (
        <Chip>again {row.again_rate_pct.toFixed(0)}%</Chip>
      )}
      <Chip>{studied ? `last ${row.last_touch_date ?? "?"}` : "never studied"}</Chip>
      {row.provenance_dominant && (
        <Chip>{PROVENANCE_SHORT[row.provenance_dominant] ?? row.provenance_dominant}</Chip>
      )}
      {row.due_cards_before > 0 && (
        <Chip
          tone={
            row.due_minutes_after_proposal < row.due_minutes_before
              ? "good"
              : "muted"
          }
        >
          {fmtMin(row.due_minutes_before)}→
          {fmtMin(row.due_minutes_after_proposal)} min
        </Chip>
      )}
    </div>
  );
}

function NoteField({
  row,
  busy,
  onSave,
}: {
  row: TriageRow;
  busy: boolean;
  onSave: (note: string) => Promise<void>;
}) {
  const [open, setOpen] = useState(Boolean(row.owner_note));
  const [text, setText] = useState(row.owner_note ?? "");
  if (!open)
    return (
      <button
        className="min-h-11 rounded border border-edge px-3 py-2 text-sm text-muted hover:text-ink"
        onClick={() => setOpen(true)}
      >
        + note
      </button>
    );
  return (
    <textarea
      className="min-h-11 w-full min-w-52 flex-1 rounded border border-edge bg-transparent p-2 text-sm"
      rows={1}
      autoFocus={!row.owner_note}
      placeholder="note (voice-dictation friendly)…"
      value={text}
      disabled={busy}
      onChange={(e) => setText(e.target.value)}
      onBlur={() => {
        if (text !== (row.owner_note ?? "")) void onSave(text);
      }}
    />
  );
}

function RowCard({
  row,
  busy,
  onVerdict,
  onNote,
}: {
  row: TriageRow;
  busy: boolean;
  onVerdict: (row: TriageRow, verdict: Verdict) => Promise<void>;
  onNote: (row: TriageRow, note: string) => Promise<void>;
}) {
  const isLane = row.scope_kind === "lane";
  return (
    <div
      className={`rounded-lg border bg-surface p-3 ${
        row.owner_verdict ? "border-edge opacity-90" : "border-edge"
      } ${isLane ? "" : "ml-3 sm:ml-6"}`}
    >
      <div className="flex flex-wrap items-baseline gap-x-2 gap-y-1">
        <span className={`font-semibold ${isLane ? "text-base" : "text-sm"}`}>
          {rowName(row)}
        </span>
        <span className="text-[11px] text-muted">
          proposed: {PROPOSAL_SHORT[row.proposal_disposition]}
          {row.proposal_disposition === "sample-hardest" &&
            ` (N=${row.sample_n ?? 50})`}
        </span>
        {row.owner_verdict && (
          <span className="text-[11px] font-semibold text-sky-400">
            ✓ {row.owner_verdict}
          </span>
        )}
      </div>
      <p className="mt-1 text-xs leading-snug text-ink-2">{row.rationale}</p>
      <div className="mt-2">
        <EvidenceChips row={row} />
      </div>
      <div className="mt-2 flex flex-wrap items-stretch gap-1.5">
        {VERDICT_BUTTONS.map((def) => {
          const selected = row.owner_verdict === def.key;
          const proposed =
            !row.owner_verdict && def.key === row.proposal_disposition;
          const acceptHint =
            def.key === "accept-proposal" && !row.owner_verdict
              ? ` (${PROPOSAL_SHORT[row.proposal_disposition]})`
              : "";
          return (
            <button
              key={def.key}
              disabled={busy}
              onClick={() => void onVerdict(row, def.key)}
              className={`min-h-11 rounded px-3 py-2 text-sm font-medium disabled:opacity-50 ${
                selected
                  ? def.selectedCls
                  : proposed
                    ? `border-2 border-dashed ${def.proposedCls} text-ink`
                    : "border border-edge text-ink-2 hover:bg-surface-2"
              }`}
              title={
                proposed ? "census-proposed disposition" : undefined
              }
            >
              {def.label}
              {acceptHint}
              {proposed && " ◦"}
            </button>
          );
        })}
        <NoteField
          row={row}
          busy={busy}
          onSave={(note) => onNote(row, note)}
        />
      </div>
    </div>
  );
}

type LaneGroup = { lane: string; header: TriageRow | null; rows: TriageRow[] };
type LangGroup = { language: string; lanes: LaneGroup[] };

export default function Triage() {
  const [refreshKey, setRefreshKey] = useState(0);
  const { data, error, loading } = useApi<TriageResponse>("/triage", {
    refresh: refreshKey,
  });
  const reload = useCallback(async () => setRefreshKey((v) => v + 1), []);
  const [busy, setBusy] = useState(false);
  const [toast, setToast] = useState<string | null>(null);

  const flash = (msg: string) => {
    setToast(msg);
    window.setTimeout(() => setToast(null), 1500);
  };

  const verdict = useCallback(
    async (row: TriageRow, v: Verdict) => {
      if (busy) return;
      setBusy(true);
      try {
        await adminCall("/admin/triage-verdict", {
          body: { subtree_id: row.subtree, verdict: v },
        });
        flash(`✓ ${rowName(row)}: ${v}`);
        await reload();
      } finally {
        setBusy(false);
      }
    },
    [busy, reload],
  );

  const saveNote = useCallback(
    async (row: TriageRow, note: string) => {
      setBusy(true);
      try {
        await adminCall("/admin/triage-verdict", {
          body: { subtree_id: row.subtree, note },
        });
        flash("note saved");
        await reload();
      } finally {
        setBusy(false);
      }
    },
    [reload],
  );

  const acceptAll = useCallback(async () => {
    if (busy || !data) return;
    const remaining = data.summary.remaining;
    if (
      !window.confirm(
        `Record accept-proposal on all ${remaining} unverdicted subtrees? ` +
          "You can still override any row afterwards. Nothing is applied " +
          "to any collection.",
      )
    )
      return;
    setBusy(true);
    try {
      const res = await adminCall<{ updated: number }>(
        "/admin/triage-verdict-bulk",
        { body: { verdict: "accept-proposal", scope: "all-unverdicted" } },
      );
      flash(`accepted ${res.updated} proposals`);
      await reload();
    } finally {
      setBusy(false);
    }
  }, [busy, data, reload]);

  const groups = useMemo<LangGroup[]>(() => {
    const langs: LangGroup[] = [];
    const langIdx = new Map<string, number>();
    const laneIdx = new Map<string, number>();
    for (const row of data?.rows ?? []) {
      let li = langIdx.get(row.language);
      if (li === undefined) {
        li = langs.length;
        langIdx.set(row.language, li);
        langs.push({ language: row.language, lanes: [] });
      }
      const lang = langs[li];
      const laneKey = `${row.language}::${row.lane}`;
      let gi = laneIdx.get(laneKey);
      if (gi === undefined) {
        gi = lang.lanes.length;
        laneIdx.set(laneKey, gi);
        lang.lanes.push({ lane: row.lane, header: null, rows: [] });
      }
      const group = lang.lanes[gi];
      if (row.scope_kind === "lane") group.header = row;
      else group.rows.push(row);
    }
    return langs;
  }, [data]);

  if (loading && !data) return <Spinner />;
  if (error) return <ErrorBox error={error} />;
  if (!data || data.rows.length === 0)
    return <Empty>No triage evidence seeded yet.</Empty>;

  const { summary, meta } = data;
  const projections = new Map(
    summary.languages.map((l) => [l.language, l]),
  );
  const deferred = summary.verdict_counts["defer"] ?? 0;

  return (
    <div className="flex flex-col gap-4">
      {/* sticky progress + projection bar */}
      <div className="sticky top-0 z-20 -mx-8 border-b border-edge bg-page/95 px-8 py-2 backdrop-blur">
        <div className="flex flex-wrap items-center gap-x-3 gap-y-1">
          <span className="text-sm font-semibold tnum">
            {summary.verdicted}/{summary.total} verdicted
          </span>
          <span className="text-xs text-muted tnum">
            {summary.remaining} remaining
            {deferred > 0 && ` · ${deferred} deferred`}
          </span>
          {summary.remaining > 0 && (
            <button
              className="min-h-9 rounded bg-sky-700 px-3 py-1.5 text-xs font-semibold text-white disabled:opacity-50"
              disabled={busy}
              onClick={() => void acceptAll()}
            >
              Accept all proposals
            </button>
          )}
          {toast && <span className="text-xs font-semibold">{toast}</span>}
        </div>
        <div className="mt-1 flex flex-wrap gap-x-4 gap-y-0.5">
          {summary.languages.map((l) => (
            <a
              key={l.language}
              href={`#lang-${l.language.split(" ")[0]}`}
              className="text-xs tnum text-ink-2 hover:text-ink"
            >
              <span className="font-semibold">{l.language.split(" ")[0]}</span>{" "}
              {fmtMin(l.before_minutes)}→
              <span
                className={
                  l.current_minutes < l.before_minutes ? "text-good" : ""
                }
              >
                {fmtMin(l.current_minutes)}
              </span>
              m
            </a>
          ))}
        </div>
      </div>

      <div className="flex flex-wrap items-baseline gap-3">
        <h1 className="text-xl font-bold">Curation triage</h1>
        <span className="text-xs text-muted">
          DJ-C2 census as of {meta.source_as_of?.slice(0, 10)} · verdict every
          subtree, or accept all and override
        </span>
      </div>

      {/* executor-lane banner: this page decides, it never applies */}
      <div className="rounded-lg border border-warning/50 bg-surface p-3 text-sm text-ink-2">
        <span className="font-semibold text-warning">Decisions only.</span>{" "}
        {meta.executor_note} Suspension proposals are reversible; nothing is
        ever deleted.
      </div>

      {groups.map((lang) => {
        const projection = projections.get(lang.language);
        const dormant = lang.language === "zz Dormant";
        return (
          <section
            key={lang.language}
            id={`lang-${lang.language.split(" ")[0]}`}
            className="flex scroll-mt-20 flex-col gap-2"
          >
            <div className="mt-2 flex flex-wrap items-baseline gap-3">
              <h2 className="text-lg font-bold">{lang.language}</h2>
              {projection && (
                <span className="text-xs text-muted tnum">
                  due load {fmtMin(projection.before_minutes)} →{" "}
                  <span
                    className={
                      projection.current_minutes < projection.before_minutes
                        ? "text-good"
                        : ""
                    }
                  >
                    {fmtMin(projection.current_minutes)} min
                  </span>{" "}
                  under current verdicts ({projection.before_due_cards}→
                  {projection.current_due_cards} cards
                  {projection.undecided_scopes > 0 &&
                    `, ${projection.undecided_scopes} scopes undecided`}
                  )
                </span>
              )}
              {dormant && (
                <span className="text-xs text-muted">
                  already retired — listed for completeness
                </span>
              )}
            </div>
            {lang.lanes.map((lane) => (
              <div key={lane.lane} className="flex flex-col gap-1.5">
                {lane.header && (
                  <RowCard
                    row={lane.header}
                    busy={busy}
                    onVerdict={verdict}
                    onNote={saveNote}
                  />
                )}
                {lane.rows.map((row) => (
                  <RowCard
                    key={row.subtree}
                    row={row}
                    busy={busy}
                    onVerdict={verdict}
                    onNote={saveNote}
                  />
                ))}
              </div>
            ))}
          </section>
        );
      })}
    </div>
  );
}
