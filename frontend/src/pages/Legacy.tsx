import { useMemo, useState } from "react";
import { Card, Empty, ErrorBox, Spinner, StatTile, Td, Th } from "../components/ui";
import { fmtDate, langName } from "../format";
import { useApi, useDebounced } from "../hooks";

type Verdict = "import" | "partial" | "skip" | "already-covered";

interface AuditFlag {
  code: string;
  scope?: string;
  count?: number;
  details?: string | Record<string, unknown>;
}

interface AuditOverlap {
  kind: string;
  status: string;
  scope?: string;
  count?: number;
  details?: string;
}

interface EstateRow {
  deck_path: string;
  source_deck_id: number;
  parent_path: string | null;
  depth: number;
  top_level: string;
  lang: string | null;
  direct_notes: number;
  direct_cards: number;
  direct_mature: number;
  direct_reps: number;
  direct_reviews: number;
  direct_audio_notes: number;
  direct_sound_tags: number;
  direct_last_review: string | null;
  subtree_notes: number;
  subtree_cards: number;
  note_models: { id: number; name: string }[];
  quality_flags: AuditFlag[];
  overlap: AuditOverlap[];
  proposed_verdict: Verdict;
  proposal_reason: string;
  owner_verdict: Verdict | null;
  owner_note: string | null;
  verdict: Verdict;
  verdict_source: "codex" | "owner";
}

interface EstateData {
  snapshot: { source_sha256: string | null; audited_at: string | null };
  totals: {
    deck_rows: number;
    nonempty_decks: number;
    notes: number;
    cards: number;
    mature: number;
    reps: number;
    reviews: number;
    audio_notes: number;
    last_review: string | null;
    owner_pending: number;
    verdicts: Partial<Record<Verdict, number>>;
  };
  rows: EstateRow[];
}

const VERDICT_META: Record<Verdict, { label: string; cls: string }> = {
  import: { label: "import", cls: "border-good/40 text-good" },
  partial: { label: "partial", cls: "border-warning/40 text-warning" },
  skip: { label: "skip", cls: "border-critical/40 text-critical" },
  "already-covered": {
    label: "already covered",
    cls: "border-accent/40 text-accent",
  },
};

function VerdictBadge({ verdict, source }: { verdict: Verdict; source: "codex" | "owner" }) {
  const meta = VERDICT_META[verdict];
  return (
    <span
      className={`inline-flex whitespace-nowrap rounded border px-1.5 py-0.5 text-xs ${meta.cls}`}
      title={source === "owner" ? "owner verdict" : "Codex proposal; owner verdict pending"}
    >
      {meta.label}{source === "owner" ? " · owner" : ""}
    </span>
  );
}

function compactNumber(value: number): string {
  return new Intl.NumberFormat("en", { notation: "compact", maximumFractionDigits: 1 }).format(value);
}

function flagDetails(flag: AuditFlag): string | undefined {
  if (typeof flag.details === "string") return flag.details;
  if (flag.details) {
    return Object.entries(flag.details).map(([key, value]) => `${key}: ${String(value)}`).join(" · ");
  }
  return undefined;
}

export default function Legacy() {
  const { data, error, loading } = useApi<EstateData>("/legacy");
  const [query, setQuery] = useState("");
  const [topLevel, setTopLevel] = useState("");
  const [language, setLanguage] = useState("");
  const [verdict, setVerdict] = useState("");
  const [includeEmpty, setIncludeEmpty] = useState(false);
  const debouncedQuery = useDebounced(query.trim().toLocaleLowerCase(), 150);

  const rows = useMemo(() => {
    if (!data) return [];
    return data.rows.filter((row) => {
      if (!includeEmpty && row.direct_cards === 0) return false;
      if (topLevel && row.top_level !== topLevel) return false;
      if (language && (row.lang ?? "und") !== language) return false;
      if (verdict && row.verdict !== verdict) return false;
      if (debouncedQuery && !row.deck_path.toLocaleLowerCase().includes(debouncedQuery)) {
        return false;
      }
      return true;
    });
  }, [data, debouncedQuery, includeEmpty, language, topLevel, verdict]);

  if (loading && !data) return <Spinner label="loading legacy estate…" />;
  if (error) return <ErrorBox error={error} />;
  if (!data) return null;

  const tops = [...new Set(data.rows.map((row) => row.top_level))].sort();
  const languages = [...new Set(data.rows.map((row) => row.lang ?? "und"))].sort();
  const decided = data.totals.deck_rows - data.totals.owner_pending;

  return (
    <div className="flex flex-col gap-4">
      <div>
        <h1 className="text-xl font-bold">Legacy estate</h1>
        <p className="mt-1 max-w-4xl text-sm text-muted">
          Read-only census of the +2 AnkiWeb account. Proposals are evidence for one owner
          gate; no row authorizes an import by itself.
        </p>
      </div>

      <div className="grid grid-cols-2 gap-3 lg:grid-cols-5">
        <StatTile label="Notes" value={<span className="tnum">{compactNumber(data.totals.notes)}</span>} sub={`${data.totals.deck_rows} deck rows`} />
        <StatTile label="Cards" value={<span className="tnum">{compactNumber(data.totals.cards)}</span>} sub={`${compactNumber(data.totals.mature)} mature`} />
        <StatTile label="Review history" value={<span className="tnum">{compactNumber(data.totals.reviews)}</span>} sub={`last ${fmtDate(data.totals.last_review)}`} />
        <StatTile label="Sound-tag notes" value={<span className="tnum">{compactNumber(data.totals.audio_notes)}</span>} sub="presence scan; media not downloaded" />
        <StatTile
          label="Owner verdicts"
          value={<span className="tnum">{decided}/{data.totals.deck_rows}</span>}
          sub={`${data.totals.owner_pending} proposals pending`}
          tone={data.totals.owner_pending ? "warning" : "good"}
        />
      </div>

      <Card>
        <div className="grid gap-2 md:grid-cols-5">
          <input
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            placeholder="search deck path"
            className="rounded border border-edge bg-page px-2.5 py-1.5 text-sm outline-none focus:border-accent"
          />
          <select value={topLevel} onChange={(event) => setTopLevel(event.target.value)} className="rounded border border-edge bg-page px-2.5 py-1.5 text-sm">
            <option value="">all top-level decks</option>
            {tops.map((top) => <option key={top}>{top}</option>)}
          </select>
          <select value={language} onChange={(event) => setLanguage(event.target.value)} className="rounded border border-edge bg-page px-2.5 py-1.5 text-sm">
            <option value="">all languages</option>
            {languages.map((lang) => <option key={lang} value={lang}>{lang === "und" ? "Unclassified" : langName(lang)}</option>)}
          </select>
          <select value={verdict} onChange={(event) => setVerdict(event.target.value)} className="rounded border border-edge bg-page px-2.5 py-1.5 text-sm">
            <option value="">all proposals</option>
            {(Object.keys(VERDICT_META) as Verdict[]).map((key) => <option key={key} value={key}>{VERDICT_META[key].label}</option>)}
          </select>
          <label className="flex items-center gap-2 px-1 text-sm text-ink-2">
            <input type="checkbox" checked={includeEmpty} onChange={(event) => setIncludeEmpty(event.target.checked)} />
            include containers
          </label>
        </div>
      </Card>

      <Card title={`Deck tree (${rows.length})`} aside={data.snapshot.audited_at ? `audited ${fmtDate(data.snapshot.audited_at)}` : undefined}>
        {rows.length === 0 ? (
          <Empty>No decks match these filters.</Empty>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full min-w-[1180px] border-collapse">
              <thead>
                <tr>
                  <Th>Deck</Th>
                  <Th>Lang</Th>
                  <Th className="text-right">Notes / cards</Th>
                  <Th>Study history</Th>
                  <Th>Audio</Th>
                  <Th>Quality flags</Th>
                  <Th>Overlap</Th>
                  <Th>Verdict</Th>
                </tr>
              </thead>
              <tbody>
                {rows.map((row) => {
                  const basename = row.deck_path.split("::").at(-1) ?? row.deck_path;
                  const audioPct = row.direct_notes
                    ? Math.round((100 * row.direct_audio_notes) / row.direct_notes)
                    : 0;
                  return (
                    <tr key={row.deck_path} className="hover:bg-surface-2">
                      <Td className="max-w-96">
                        <div style={{ paddingLeft: `${Math.min(row.depth, 5) * 14}px` }} title={row.deck_path}>
                          <span className="break-words text-sm">{basename}</span>
                          {row.direct_cards === 0 && <span className="ml-2 text-xs text-muted">container</span>}
                        </div>
                      </Td>
                      <Td className="whitespace-nowrap text-xs text-ink-2">{row.lang ? langName(row.lang) : "—"}</Td>
                      <Td className="tnum whitespace-nowrap text-right text-xs">
                        {row.direct_notes.toLocaleString()} / {row.direct_cards.toLocaleString()}
                      </Td>
                      <Td className="text-xs text-ink-2">
                        <div className="tnum">{row.direct_reviews.toLocaleString()} reviews · {row.direct_mature.toLocaleString()} mature</div>
                        <div className="text-muted">last {fmtDate(row.direct_last_review)}</div>
                      </Td>
                      <Td className="whitespace-nowrap text-xs">
                        <span className="tnum">{row.direct_audio_notes.toLocaleString()}</span>
                        <span className="text-muted"> · {audioPct}%</span>
                      </Td>
                      <Td className="max-w-64 text-xs">
                        {row.quality_flags.length ? row.quality_flags.map((flag) => (
                          <span key={`${flag.code}:${flag.scope ?? ""}`} className="mr-1 inline-block text-warning" title={flagDetails(flag)}>
                            {flag.code}{flag.count ? ` (${flag.count})` : ""}
                          </span>
                        )) : <span className="text-muted">—</span>}
                      </Td>
                      <Td className="max-w-64 text-xs text-ink-2">
                        {row.overlap.length ? row.overlap.map((item) => (
                          <div key={`${item.kind}:${item.status}`} title={item.details}>{item.kind} · {item.status}{item.count != null ? ` (${item.count})` : ""}</div>
                        )) : <span className="text-muted">none detected</span>}
                      </Td>
                      <Td className="max-w-72 text-xs">
                        <VerdictBadge verdict={row.verdict} source={row.verdict_source} />
                        <div className="mt-1 text-muted" title={row.proposal_reason}>{row.owner_note || row.proposal_reason}</div>
                      </Td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </Card>
    </div>
  );
}
