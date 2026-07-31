import { FormEvent, useCallback, useEffect, useRef, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { adminCall } from "../api";
import AudioButton from "../components/AudioButton";
import { Card, Empty, ErrorBox, LangBadge, Spinner, Td, Th } from "../components/ui";
import { fmtDate, langName } from "../format";
import { useApi } from "../hooks";

type UnitStatus = "active" | "maintenance" | "planned";

interface GrammarUnitRow {
  key: string;
  lang: string;
  cluster: string;
  label: string;
  symbol: string;
  status: UnitStatus;
  target_size: number;
  sort_order: number;
  notes: string | null;
  updated_at: string;
  verified: number;
  rejected: number;
  retired: number;
  last_item_at: string | null;
  last_batch: string | null;
}

interface GrammarItem {
  id: number;
  infinitive: string | null;
  person: string | null;
  sentence: string;
  answer: string;
  gloss_en: string;
  why_en: string;
  batch: string;
  created_at: string;
  audio: string | null;
}

interface GrammarReject {
  id: number;
  topic: string;
  infinitive: string | null;
  person: string | null;
  sentence: string;
  answer: string;
  reject_reason: string;
  batch: string;
  created_at: string;
}

interface GrammarUnitData {
  unit: GrammarUnitRow;
  guidance: string | null;
  deck_name: string;
  items: GrammarItem[];
  rejects: GrammarReject[];
}

interface GrammarRun {
  running: boolean;
  lang?: string;
  mode?: string;
  errors?: string[];
}

interface StartResponse {
  started: boolean;
  lang?: string;
  unit?: string;
  n_requested?: number;
  reason?: string;
}

interface UpdateResponse {
  ok: true;
  unit: GrammarUnitRow;
}

interface RetireResponse {
  ok: true;
  id: number;
  lang: string;
  topic: string;
}

function UnitStatusChip({ status }: { status: UnitStatus }) {
  if (status === "active") {
    return (
      <span className="inline-flex items-center gap-1.5 text-xs text-good">
        <span className="h-1.5 w-1.5 rounded-full bg-good" />
        active
      </span>
    );
  }
  if (status === "planned") {
    return (
      <span className="inline-flex rounded border border-dashed border-muted/60 px-1.5 py-0.5 text-xs text-muted">
        planned
      </span>
    );
  }
  return <span className="text-xs text-muted">maintenance</span>;
}

function SentenceWithBlank({
  sentence,
  infinitive,
}: {
  sentence: string;
  infinitive: string | null;
}) {
  const blankAt = sentence.indexOf("___");
  if (blankAt === -1) return <>{sentence}</>;

  const before = sentence.slice(0, blankAt);
  let after = sentence.slice(blankAt + 3);
  // Closed-class units (clitics, por/para…) have no infinitive hint.
  const marker = infinitive ? ` (${infinitive})` : "";
  if (marker && after.startsWith(marker)) after = after.slice(marker.length);

  return (
    <>
      {before}
      <span className="font-medium text-accent">___{marker}</span>
      {after}
    </>
  );
}

interface LingqTerm {
  term: string;
  gloss: string | null;
  status: number | null;
}

// The learner's LingQ vocabulary rides along inside generation prompts
// ("we study vocabulary even as we study grammar") — this panel shows a
// sample of what the generator draws from for this language.
function VocabPanel({ lang }: { lang: string }) {
  const [terms, setTerms] = useState<LingqTerm[] | null>(null);
  const [state, setState] = useState<"idle" | "loading" | "error" | "empty">("idle");

  const load = useCallback(async () => {
    setState("loading");
    try {
      const r = await adminCall<{ terms: LingqTerm[] }>("/admin/lingq-sample", {
        method: "GET",
        params: { lang, n: 18 },
      });
      setTerms(r.terms);
      setState(r.terms.length ? "idle" : "empty");
    } catch {
      setState("error");
    }
  }, [lang]);

  useEffect(() => {
    void load();
  }, [load]);

  if (state === "empty") return null; // mirror not filled for this lang yet
  return (
    <Card
      title="Vocabulary woven into generation"
      aside={
        <button
          type="button"
          onClick={() => void load()}
          className="text-xs text-muted transition-colors hover:text-ink-2"
        >
          {state === "loading" ? "sampling…" : "resample ↻"}
        </button>
      }
    >
      {state === "error" ? (
        <div className="text-xs text-muted">
          LingQ sample unavailable (mirror still syncing?)
        </div>
      ) : (
        <div className="flex flex-wrap gap-1.5">
          {(terms ?? []).map((t) => (
            <span
              key={t.term}
              title={t.gloss ?? undefined}
              className="rounded-full border border-edge bg-surface-2 px-2.5 py-1 text-xs text-ink-2"
            >
              {t.term}
            </span>
          ))}
        </div>
      )}
      <p className="mt-2 text-[11px] text-muted">
        Random sample of still-learning LingQ terms for {langName(lang)} — the
        generator weaves several of these into each new batch of drill sentences.
      </p>
    </Card>
  );
}

export default function GrammarUnit() {
  const { key } = useParams();
  const [refreshKey, setRefreshKey] = useState(0);
  const [targetSize, setTargetSize] = useState("1");
  const [status, setStatus] = useState<UnitStatus>("planned");
  const [notes, setNotes] = useState("");
  const [saving, setSaving] = useState(false);
  const [saveMessage, setSaveMessage] = useState<{
    tone: "good" | "critical";
    text: string;
  } | null>(null);
  const [revealed, setRevealed] = useState<Record<number, boolean>>({});
  const [retiringId, setRetiringId] = useState<number | null>(null);
  const [retireError, setRetireError] = useState<unknown>(null);
  const [topUpPending, setTopUpPending] = useState(false);
  const [topUpError, setTopUpError] = useState<unknown>(null);
  const [run, setRun] = useState<GrammarRun | null>(null);
  const wasRunning = useRef(false);
  const { data, error, loading } = useApi<GrammarUnitData>(
    `/grammar/units/${key ?? ""}`,
    { refresh: refreshKey },
  );

  const refreshRun = useCallback(async () => {
    try {
      const next = await adminCall<GrammarRun>("/admin/grammar-status", { method: "GET" });
      if (wasRunning.current && !next.running) {
        setRefreshKey((value) => value + 1);
      }
      wasRunning.current = next.running;
      setRun(next);
    } catch {
      // Unit data remains usable even if the background run-status check fails.
    }
  }, []);

  useEffect(() => {
    void refreshRun();
  }, [refreshRun]);

  useEffect(() => {
    if (!run?.running) return;
    const timer = window.setInterval(() => void refreshRun(), 3000);
    return () => window.clearInterval(timer);
  }, [refreshRun, run?.running]);

  useEffect(() => {
    if (!data) return;
    setTargetSize(String(data.unit.target_size));
    setStatus(data.unit.status);
    setNotes(data.unit.notes ?? "");
  }, [
    data?.unit.key,
    data?.unit.notes,
    data?.unit.status,
    data?.unit.target_size,
    data?.unit.updated_at,
  ]);

  useEffect(() => {
    if (saveMessage?.tone !== "good") return;
    const timer = window.setTimeout(() => setSaveMessage(null), 2000);
    return () => window.clearTimeout(timer);
  }, [saveMessage]);

  const save = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!data) return;

    const parsedTarget = Number(targetSize);
    if (!Number.isInteger(parsedTarget) || parsedTarget < 1 || parsedTarget > 100) {
      setSaveMessage({ tone: "critical", text: "target size must be an integer from 1 to 100" });
      return;
    }

    const body: {
      target_size?: number;
      status?: UnitStatus;
      notes?: string;
    } = {};
    if (parsedTarget !== data.unit.target_size) body.target_size = parsedTarget;
    if (status !== data.unit.status) body.status = status;
    // Send "" (not null) to clear — the server treats null as "unchanged".
    if (notes !== (data.unit.notes ?? "")) body.notes = notes;

    setSaving(true);
    setSaveMessage(null);
    try {
      const result = await adminCall<UpdateResponse>(
        `/admin/grammar-unit/${data.unit.key}`,
        { body },
      );
      setTargetSize(String(result.unit.target_size));
      setStatus(result.unit.status);
      setNotes(result.unit.notes ?? "");
      setSaveMessage({ tone: "good", text: "saved ✓" });
      setRefreshKey((value) => value + 1);
    } catch (saveError) {
      setSaveMessage({ tone: "critical", text: String(saveError) });
    } finally {
      setSaving(false);
    }
  };

  const topUp = async () => {
    if (!data) return;
    setTopUpPending(true);
    setTopUpError(null);
    try {
      const result = await adminCall<StartResponse>(
        `/admin/grammar-topup/${data.unit.key}`,
      );
      if (result.started) {
        wasRunning.current = true;
        setRun({ running: true, lang: result.lang ?? data.unit.lang, mode: "topup" });
      } else if (result.reason === "at target") {
        setRefreshKey((value) => value + 1);
      } else {
        await refreshRun();
      }
    } catch (actionError) {
      setTopUpError(actionError);
    } finally {
      setTopUpPending(false);
    }
  };

  const retire = async (id: number) => {
    const confirmed = window.confirm(
      "Retire this card? It is dropped from the deck at the next rebuild; the note stays in Anki until a cleanup purge.",
    );
    if (!confirmed) return;

    setRetiringId(id);
    setRetireError(null);
    try {
      await adminCall<RetireResponse>(`/admin/grammar-retire-item/${id}`);
      setRefreshKey((value) => value + 1);
    } catch (actionError) {
      setRetireError(actionError);
    } finally {
      setRetiringId(null);
    }
  };

  if (loading && !data) return <Spinner />;
  if (error) return <ErrorBox error={error} />;
  if (!data) return null;

  const unit = data.unit;
  const topUpN = Math.max(0, unit.target_size - unit.verified);
  const canTopUp = unit.status === "active" && topUpN > 0;

  return (
    <div className="flex flex-col gap-4">
      <div>
        <Link to="/grammar" className="text-xs text-muted hover:text-ink-2">
          ← Grammar
        </Link>
        <div className="mt-1 flex flex-wrap items-baseline gap-x-3 gap-y-1">
          <h1 className="text-2xl font-bold leading-tight">
            <span className="mr-2 text-accent">{unit.symbol}</span>
            {unit.label}
          </h1>
          <LangBadge lang={unit.lang} />
          <UnitStatusChip status={unit.status} />
        </div>
        <div className="mt-1 flex flex-wrap gap-x-3 gap-y-1 font-mono text-xs text-muted">
          <span>{data.deck_name}</span>
          <span>{unit.key}</span>
        </div>
      </div>

      <Card title="Unit settings">
        <form onSubmit={save} className="flex flex-col gap-3">
          <div className="grid gap-3 md:grid-cols-[9rem_12rem_minmax(0,1fr)]">
            <label className="text-xs text-muted">
              Target size
              <input
                type="number"
                min={1}
                max={100}
                required
                value={targetSize}
                onChange={(event) => setTargetSize(event.target.value)}
                className="mt-1 w-full rounded border border-edge bg-surface-2 px-2.5 py-2 text-sm text-ink outline-none focus:border-accent"
              />
            </label>
            <label className="text-xs text-muted">
              Status
              <select
                value={status}
                onChange={(event) => setStatus(event.target.value as UnitStatus)}
                className="mt-1 w-full rounded border border-edge bg-surface-2 px-2.5 py-2 text-sm text-ink outline-none focus:border-accent"
              >
                <option value="active">active</option>
                <option value="maintenance">maintenance</option>
                <option value="planned">planned</option>
              </select>
            </label>
            <label className="text-xs text-muted">
              Notes
              <textarea
                rows={2}
                value={notes}
                onChange={(event) => setNotes(event.target.value)}
                className="mt-1 w-full resize-y rounded border border-edge bg-surface-2 px-2.5 py-2 text-sm text-ink outline-none focus:border-accent"
              />
            </label>
          </div>
          <div className="flex flex-wrap items-center gap-2">
            <button
              type="submit"
              disabled={saving}
              className="rounded border border-edge px-3 py-1.5 text-xs font-medium text-ink-2 transition-colors hover:bg-surface-2 disabled:cursor-not-allowed disabled:opacity-40"
            >
              {saving ? "saving…" : "Save"}
            </button>
            {canTopUp && (
              <button
                type="button"
                onClick={() => void topUp()}
                disabled={topUpPending || run?.running === true}
                className="rounded border border-edge px-3 py-1.5 text-xs font-medium text-ink-2 transition-colors hover:bg-surface-2 disabled:cursor-not-allowed disabled:opacity-40"
              >
                {topUpPending ? "starting…" : `Top up +${topUpN}`}
              </button>
            )}
            {unit.status === "planned" && (
              <span className="text-xs text-muted">planned — no generator yet</span>
            )}
            {unit.status === "maintenance" && (
              <span className="text-xs text-muted">maintenance</span>
            )}
            {unit.status === "active" && topUpN === 0 && (
              <span className="text-xs text-muted">at target</span>
            )}
            {saveMessage && (
              <span
                className={`text-xs ${
                  saveMessage.tone === "good" ? "text-good" : "text-critical"
                }`}
              >
                {saveMessage.text}
              </span>
            )}
          </div>
          {topUpError != null && <ErrorBox error={topUpError} />}
        </form>
      </Card>

      {data.guidance && (
        <Card title="Generation guidance">
          <p className="text-sm italic leading-relaxed text-muted">{data.guidance}</p>
        </Card>
      )}

      <VocabPanel lang={unit.lang} />

      <Card title={`Verified cards · ${data.items.length}`}>
        {retireError != null && (
          <div className="mb-3">
            <ErrorBox error={retireError} />
          </div>
        )}
        {data.items.length === 0 ? (
          <Empty>No verified cards for this unit.</Empty>
        ) : (
          <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
            {data.items.map((item) => {
              const isRevealed = Boolean(revealed[item.id]);
              return (
                <article
                  key={item.id}
                  className="flex min-h-48 flex-col rounded-md border border-edge bg-surface-2 p-3"
                >
                  <div className="flex items-start gap-2">
                    <span className="text-accent">{unit.symbol}</span>
                    <p className="text-sm leading-relaxed text-ink">
                      <SentenceWithBlank
                        sentence={item.sentence}
                        infinitive={item.infinitive}
                      />
                    </p>
                  </div>
                  <button
                    type="button"
                    onClick={() =>
                      setRevealed((current) => ({
                        ...current,
                        [item.id]: !current[item.id],
                      }))
                    }
                    className="mt-3 self-start text-xs text-muted hover:text-ink"
                    aria-expanded={isRevealed}
                  >
                    {isRevealed ? "hide answer" : "reveal"}
                  </button>
                  {isRevealed && (
                    <div className="mt-2 border-l-2 border-accent/50 pl-3">
                      <div className="font-bold text-accent">{item.answer}</div>
                      <div className="mt-1 text-sm italic text-muted">{item.gloss_en}</div>
                      {item.why_en && (
                        <div className="mt-1 text-xs leading-relaxed text-ink-2">
                          {item.why_en}
                        </div>
                      )}
                    </div>
                  )}
                  <div className="mt-auto flex flex-wrap items-center gap-2 pt-4">
                    {item.audio && <AudioButton path={item.audio} label="audio" />}
                    <span className="font-mono text-[10px] text-muted">{item.batch}</span>
                    <button
                      type="button"
                      onClick={() => void retire(item.id)}
                      disabled={retiringId !== null}
                      className="ml-auto rounded border border-critical/50 px-2 py-1 text-[10px] text-critical transition-colors hover:bg-critical/10 disabled:cursor-not-allowed disabled:opacity-40"
                    >
                      {retiringId === item.id ? "retiring…" : "retire"}
                    </button>
                  </div>
                </article>
              );
            })}
          </div>
        )}
      </Card>

      <Card title={`Rejects · ${data.rejects.length} — verifier diagnostics`}>
        {data.rejects.length === 0 ? (
          <Empty>no rejects for this unit</Empty>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full border-collapse">
              <thead>
                <tr>
                  <Th>Sentence</Th>
                  <Th>Rejected answer</Th>
                  <Th>Reason</Th>
                  <Th>Infinitive / person</Th>
                  <Th>Batch</Th>
                  <Th className="text-right">Created</Th>
                </tr>
              </thead>
              <tbody>
                {data.rejects.map((reject) => (
                  <tr key={reject.id} className="hover:bg-surface-2">
                    <Td className="min-w-64">{reject.sentence}</Td>
                    <Td className="font-medium text-ink-2">{reject.answer}</Td>
                    <Td className="min-w-56 whitespace-normal text-warning">
                      {reject.reject_reason}
                    </Td>
                    <Td className="whitespace-nowrap text-xs text-muted">
                      {reject.infinitive ?? "—"} / {reject.person ?? "—"}
                    </Td>
                    <Td className="font-mono text-[10px] text-muted">{reject.batch}</Td>
                    <Td className="tnum whitespace-nowrap text-right text-xs text-muted">
                      {fmtDate(reject.created_at)}
                    </Td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>
    </div>
  );
}
