import { useCallback, useEffect, useRef, useState } from "react";
import { Link } from "react-router-dom";
import { LANG_ORDER, adminCall, langColor } from "../api";
import { Card, Empty, ErrorBox, LangBadge, Spinner, StatusBadge, Td, Th } from "../components/ui";
import { fmtAgo, fmtBytes } from "../format";
import { useApi } from "../hooks";

type UnitStatus = "active" | "maintenance" | "planned";

interface GrammarDeck {
  apkg_id: number;
  lang: string;
  size_bytes: number;
  cards: number;
  built_at: string;
  ack_status: "ok" | "failed" | null;
  ack_attempts: number;
  acked_at: string | null;
  agent_name: string | null;
}

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

interface GrammarCluster {
  cluster: string;
  units: GrammarUnitRow[];
}

interface GrammarLanguage {
  lang: string;
  deck: GrammarDeck | null;
  clusters: GrammarCluster[];
}

interface GrammarRun {
  running: boolean;
  lang?: string;
  batch?: string;
  mode?: string;
  topics_total?: number;
  topics_done?: number;
  accepted?: number;
  rejected?: number;
  errors?: string[];
  deck?: GrammarDeck;
  finished_at?: string;
}

interface GrammarOverview {
  langs: GrammarLanguage[];
  lang_names: Record<string, string>;
  run: GrammarRun;
}

interface StartResponse {
  started: boolean;
  lang?: string;
  unit?: string;
  n_requested?: number;
  reason?: string;
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

function DeckDelivery({ deck }: { deck: GrammarDeck }) {
  if (deck.ack_status === "ok") {
    return <StatusBadge status="ok" label="delivered" />;
  }
  if (deck.ack_status === "failed") {
    return <StatusBadge status="failed" label="delivery failed" />;
  }
  return <StatusBadge status="queued" label="awaiting pickup" />;
}

export default function Grammar() {
  const [refreshKey, setRefreshKey] = useState(0);
  const [run, setRun] = useState<GrammarRun | null>(null);
  const [statusError, setStatusError] = useState<unknown>(null);
  const [actionError, setActionError] = useState<unknown>(null);
  const [actionKey, setActionKey] = useState<string | null>(null);
  const [dismissedErrors, setDismissedErrors] = useState<string | null>(null);
  const wasRunning = useRef(false);
  const { data, error, loading } = useApi<GrammarOverview>(
    "/grammar/overview",
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
      setStatusError(null);
    } catch (runError) {
      setStatusError(runError);
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

  const markRunning = (lang: string, mode: string) => {
    wasRunning.current = true;
    setRun({ running: true, lang, mode });
  };

  const topUp = async (unit: GrammarUnitRow) => {
    setActionKey(`topup:${unit.key}`);
    setActionError(null);
    try {
      const result = await adminCall<StartResponse>(`/admin/grammar-topup/${unit.key}`);
      if (result.started) {
        markRunning(result.lang ?? unit.lang, "topup");
      } else if (result.reason === "at target") {
        setRefreshKey((value) => value + 1);
      } else {
        await refreshRun();
      }
    } catch (topUpError) {
      setActionError(topUpError);
    } finally {
      setActionKey(null);
    }
  };

  const rebuild = async (lang: string) => {
    setActionKey(`rebuild:${lang}`);
    setActionError(null);
    try {
      const result = await adminCall<StartResponse>("/admin/grammar-rebuild", {
        params: { lang },
      });
      if (result.started) {
        markRunning(lang, "rebuild");
      } else {
        await refreshRun();
      }
    } catch (rebuildError) {
      setActionError(rebuildError);
    } finally {
      setActionKey(null);
    }
  };

  if (loading && !data) return <Spinner />;
  if (error) return <ErrorBox error={error} />;
  if (!data) return null;

  const currentRun = run ?? data.run;
  const isRunning = currentRun.running;
  const runErrors = currentRun.errors ?? [];
  const runErrorKey = runErrors.join("\n");
  const languages = [...data.langs].sort((a, b) => {
    const ai = LANG_ORDER.indexOf(a.lang);
    const bi = LANG_ORDER.indexOf(b.lang);
    return (ai === -1 ? LANG_ORDER.length : ai) - (bi === -1 ? LANG_ORDER.length : bi);
  });

  return (
    <div className="flex flex-col gap-4">
      <div className="flex flex-wrap items-center gap-3">
        <h1 className="text-xl font-bold">Grammar</h1>
        {isRunning && (
          <div className="inline-flex items-center gap-2 text-sm text-accent">
            <span className="h-2 w-2 animate-pulse rounded-full bg-accent" />
            {currentRun.mode === "rebuild" ? (
              <span>rebuilding {currentRun.lang ?? "—"}</span>
            ) : (
              <span>
                generating {currentRun.lang ?? "—"} ·{" "}
                <span className="tnum">
                  {currentRun.topics_done ?? 0}/{currentRun.topics_total ?? 0}
                </span>{" "}
                units · <span className="tnum">{currentRun.accepted ?? 0}</span> accepted /{" "}
                <span className="tnum">{currentRun.rejected ?? 0}</span> rejected
              </span>
            )}
          </div>
        )}
      </div>

      {!isRunning && runErrors.length > 0 && dismissedErrors !== runErrorKey && (
        <div className="flex items-start gap-3 rounded-md border border-critical/40 bg-surface px-4 py-2.5 text-sm text-critical">
          <span>✕ {runErrors.join(" · ")}</span>
          <button
            type="button"
            onClick={() => setDismissedErrors(runErrorKey)}
            className="ml-auto text-xs text-muted hover:text-ink"
            aria-label="dismiss run errors"
          >
            dismiss
          </button>
        </div>
      )}

      {(actionError ?? statusError) != null && (
        <ErrorBox error={actionError ?? statusError} />
      )}

      {languages.length === 0 ? (
        <Card>
          <Empty>No grammar languages configured.</Empty>
        </Card>
      ) : (
        languages.map(({ lang, deck, clusters }) => (
          <Card
            key={lang}
            title={
              <div className="flex flex-wrap items-center gap-x-3 gap-y-1">
                <LangBadge lang={lang} />
                {deck ? (
                  <>
                    <span className="text-xs font-normal text-muted">
                      <span className="tnum">{deck.cards}</span> cards ·{" "}
                      <span className="tnum">{fmtBytes(deck.size_bytes)}</span> · built{" "}
                      {fmtAgo(deck.built_at)}
                    </span>
                    <DeckDelivery deck={deck} />
                  </>
                ) : (
                  <span className="text-xs font-normal text-muted">no deck built yet</span>
                )}
              </div>
            }
            aside={
              <button
                type="button"
                onClick={() => void rebuild(lang)}
                disabled={isRunning || actionKey !== null}
                className="rounded border border-edge px-2.5 py-1 text-xs text-ink-2 transition-colors hover:bg-surface-2 disabled:cursor-not-allowed disabled:opacity-40"
              >
                {actionKey === `rebuild:${lang}` ? "starting…" : "Rebuild deck"}
              </button>
            }
          >
            <div className="flex flex-col gap-4">
              {clusters.map((cluster) => (
                <div key={cluster.cluster}>
                  <h3 className="mb-1.5 text-xs font-semibold uppercase tracking-wide text-muted">
                    {cluster.cluster}
                  </h3>
                  <div className="overflow-x-auto">
                    <table className="w-full border-collapse">
                      <thead>
                        <tr>
                          <Th>Unit</Th>
                          <Th>Status</Th>
                          <Th>Progress</Th>
                          <Th className="text-right">Rejects</Th>
                          <Th className="text-right">Last batch</Th>
                          <Th className="text-right">Actions</Th>
                        </tr>
                      </thead>
                      <tbody>
                        {cluster.units.map((unit) => {
                          const generated = unit.verified + unit.rejected;
                          const rejectRate = generated ? unit.rejected / generated : null;
                          const progress = unit.target_size
                            ? Math.min(100, (unit.verified / unit.target_size) * 100)
                            : 0;
                          const rejectTone =
                            rejectRate !== null && rejectRate >= 0.5
                              ? "text-critical"
                              : rejectRate !== null && rejectRate >= 0.25
                                ? "text-warning"
                                : "text-muted";

                          return (
                            <tr key={unit.key} className="hover:bg-surface-2">
                              <Td className="min-w-56">
                                <Link
                                  to={`/grammar/unit/${unit.key}`}
                                  className="font-medium text-ink hover:underline"
                                >
                                  <span className="mr-2 text-accent">{unit.symbol}</span>
                                  {unit.label}
                                </Link>
                                <div className="mt-0.5 font-mono text-[10px] text-muted">
                                  {unit.key}
                                </div>
                              </Td>
                              <Td>
                                <UnitStatusChip status={unit.status} />
                              </Td>
                              <Td className="min-w-32">
                                {unit.status === "planned" ? (
                                  <span className="text-muted">—</span>
                                ) : (
                                  <>
                                    <div className="tnum text-xs text-ink-2">
                                      {unit.verified}/{unit.target_size}
                                    </div>
                                    <div className="mt-1 h-1 w-28 overflow-hidden rounded-full bg-surface-2">
                                      <div
                                        className="h-full rounded-full"
                                        style={{
                                          width: `${progress}%`,
                                          background: langColor(lang),
                                        }}
                                      />
                                    </div>
                                  </>
                                )}
                              </Td>
                              <Td className={`tnum text-right text-xs ${rejectTone}`}>
                                {rejectRate === null
                                  ? "—"
                                  : `${unit.rejected} · ${Math.round(rejectRate * 100)}%`}
                              </Td>
                              <Td className="tnum text-right text-xs text-muted">
                                <span title={unit.last_batch ?? undefined}>
                                  {fmtAgo(unit.last_item_at)}
                                </span>
                              </Td>
                              <Td className="text-right">
                                {unit.status === "planned" ? (
                                  <span className="text-xs text-muted">
                                    planned — no generator yet
                                  </span>
                                ) : unit.status === "active" &&
                                  unit.verified < unit.target_size ? (
                                  <button
                                    type="button"
                                    onClick={() => void topUp(unit)}
                                    disabled={isRunning || actionKey !== null}
                                    className="rounded border border-edge px-2 py-1 text-xs text-ink-2 transition-colors hover:bg-surface-2 disabled:cursor-not-allowed disabled:opacity-40"
                                  >
                                    {actionKey === `topup:${unit.key}` ? "starting…" : "Top up"}
                                  </button>
                                ) : (
                                  <span className="text-xs text-muted">
                                    {unit.status === "maintenance" ? "maintenance" : "at target"}
                                  </span>
                                )}
                              </Td>
                            </tr>
                          );
                        })}
                      </tbody>
                    </table>
                  </div>
                </div>
              ))}
            </div>
          </Card>
        ))
      )}
    </div>
  );
}
