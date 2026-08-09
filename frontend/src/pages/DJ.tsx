import { useState } from "react";
import { adminCall } from "../api";
import { Card, Empty, ErrorBox, LangBadge, Spinner, StatTile, Td, Th } from "../components/ui";
import { fmtAgo, langName } from "../format";
import { useApi } from "../hooks";

// The Personal Study DJ panel (slices 1-2): what the observer saw in the
// last pulled AnkiWeb snapshot, the owner's per-language time budgets
// (the page's only mutation, via /admin/dj-budgets), and today's session
// plan with its arithmetic spelled out per line.

const DJ_LANGS = ["de", "es", "fr", "it", "pt", "zh"];

interface SecsPerRep {
  secs: number;
  n_obs: number;
  source: "observed" | "prior";
}

interface LangObservations {
  due: Record<string, number>;
  new_reservoir: Record<string, number>;
  secs_per_rep: Record<string, SecsPerRep>;
  last7: Record<string, { reps: number; minutes: number }>;
}

interface Observations {
  computed_at: string;
  langs: Record<string, LangObservations>;
  unclassified_cards: number;
}

interface MixLine {
  population: string;
  weight: number;
  cards: number;
  est_minutes: number;
  secs_per_new_card: number;
  reservoir: number;
  search: string;
  order: string;
  reasoning: string;
}

interface PlanLanguage {
  lang: string;
  anki_root: string;
  deck_name: string;
  budget_min: number;
  due: {
    cards: number;
    est_minutes: number;
    overflow: boolean;
    overflow_minutes: number;
    by_population: Record<string, { cards: number; est_minutes: number }>;
    search: string;
    limit: number;
    order: string;
  };
  new: { minutes_available: number; mix: MixLine[] };
  notes: string[];
}

interface Plan {
  schema: number;
  for_day: string;
  generated_at: string;
  observations_at: string | null;
  budgets_min: Record<string, number>;
  languages: PlanLanguage[];
  totals: {
    est_minutes: number;
    due_cards: number;
    new_cards: number;
    langs_overflowing: string[];
  };
}

interface DJOverview {
  enabled: boolean;
  interval_hours: number;
  ankiweb_configured: boolean;
  budgets: Record<string, number>;
  default_budgets: Record<string, number>;
  new_mix_weights: Record<string, number>;
  new_card_time_factor: number;
  observations: Observations | null;
  last_run: {
    ran_at: string;
    pull: string | null;
    plan_day: string | null;
    notes: string[];
    errors: string[];
  } | null;
  plan: {
    day: string;
    schema_version: number;
    generated_at: string;
    plan: Plan;
  } | null;
}

const POP_LABELS: Record<string, string> = {
  expressions: "Expressions",
  grammar: "Grammar",
  tenses: "Tenses",
  exercises: "Exercises",
  translation: "Translation",
  my_errors: "My Errors",
  rescue: "Rescue",
  pimsleur: "Pimsleur",
  podcast_lesson: "Podcast lessons",
  other: "Other",
};

function popLabel(pop: string): string {
  return POP_LABELS[pop] ?? pop;
}

export default function DJ() {
  const [refreshKey, setRefreshKey] = useState(0);
  const { data, error, loading } = useApi<DJOverview>(
    "/dj/overview",
    { v: refreshKey },
    30000,
  );
  const [edits, setEdits] = useState<Record<string, string>>({});
  const [busy, setBusy] = useState<string | null>(null);
  const [actionError, setActionError] = useState<unknown>(null);
  const [runStarted, setRunStarted] = useState(false);

  if (loading && !data) return <Spinner />;
  if (error) return <ErrorBox error={error} />;
  if (!data) return null;

  const plan = data.plan?.plan ?? null;
  const obs = data.observations;

  const budgetValue = (lang: string): string =>
    edits[lang] ?? String(data.budgets[lang] ?? 0);
  const dirty = DJ_LANGS.some(
    (l) => edits[l] !== undefined && edits[l] !== String(data.budgets[l] ?? 0),
  );

  const saveBudgets = async () => {
    setBusy("budgets");
    setActionError(null);
    try {
      const budgets: Record<string, number> = {};
      for (const lang of DJ_LANGS) budgets[lang] = Number(budgetValue(lang));
      await adminCall("/admin/dj-budgets", { body: { budgets } });
      setEdits({});
      setRefreshKey((k) => k + 1);
    } catch (e) {
      setActionError(e);
    } finally {
      setBusy(null);
    }
  };

  const recompute = async () => {
    setBusy("run");
    setActionError(null);
    try {
      await adminCall("/admin/dj-run");
      setRunStarted(true);
      // the run pulls from AnkiWeb in the background; the 30 s
      // auto-refresh picks the new plan up when it lands
    } catch (e) {
      setActionError(e);
    } finally {
      setBusy(null);
    }
  };

  return (
    <div className="flex flex-col gap-4">
      <div className="flex items-baseline justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold">Study DJ</h1>
          <div className="text-xs text-muted">
            daily session plans from synced revlogs · pull every {data.interval_hours} h
            {!data.enabled && " · DISABLED (dj_enabled)"}
          </div>
        </div>
        <button
          onClick={recompute}
          disabled={busy !== null}
          className="rounded-md border border-edge bg-surface-2 px-3 py-1.5 text-sm hover:text-ink disabled:opacity-50"
        >
          {busy === "run" ? "starting…" : "Recompute now"}
        </button>
      </div>

      {actionError != null && <ErrorBox error={actionError} />}
      {runStarted && (
        <div className="rounded-md border border-edge bg-surface px-3 py-2 text-xs text-ink-2">
          Run started — it pulls the collection from AnkiWeb in the background;
          this page refreshes itself every 30 s.
        </div>
      )}
      {!data.ankiweb_configured && (
        <div className="rounded-md border border-edge bg-surface px-3 py-2 text-xs text-warning">
          ANKIWEB_HKEY is not configured — no pulls happen; plans build from
          cached observations only.
        </div>
      )}
      {data.last_run && (
        <div className="text-xs text-muted">
          last run {fmtAgo(data.last_run.ran_at)} · pull{" "}
          {data.last_run.pull ?? "—"} · plan {data.last_run.plan_day ?? "—"}
          {data.last_run.errors.map((e) => (
            <span key={e} className="ml-2 text-critical">
              {e}
            </span>
          ))}
          {data.last_run.notes.map((n) => (
            <span key={n} className="ml-2">
              {n}
            </span>
          ))}
        </div>
      )}

      {plan && (
        <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
          <StatTile
            label={`Planned minutes (${plan.for_day})`}
            value={<span className="tnum">{plan.totals.est_minutes}</span>}
            sub={`generated ${fmtAgo(plan.generated_at)}`}
          />
          <StatTile
            label="Due reviews"
            value={<span className="tnum">{plan.totals.due_cards}</span>}
            sub="always first, never dropped"
          />
          <StatTile
            label="New cards"
            value={<span className="tnum">{plan.totals.new_cards}</span>}
            sub="weighted curriculum-forward mix"
          />
          <StatTile
            label="Overflowing"
            value={
              plan.totals.langs_overflowing.length ? (
                <span className="tnum">{plan.totals.langs_overflowing.join(" ")}</span>
              ) : (
                "none"
              )
            }
            tone={plan.totals.langs_overflowing.length ? "warning" : "good"}
            sub="dues alone exceed the budget"
          />
        </div>
      )}

      <Card
        title="Daily time budgets"
        aside="minutes per language · 0 pauses a language · saved via /admin/dj-budgets"
      >
        <div className="flex flex-wrap items-end gap-4">
          {DJ_LANGS.map((lang) => (
            <label key={lang} className="flex flex-col gap-1 text-xs text-muted">
              <span>
                {langName(lang)}
                {data.default_budgets[lang] !== undefined &&
                  Number(budgetValue(lang)) !== data.default_budgets[lang] && (
                    <span className="ml-1 text-muted">
                      (default {data.default_budgets[lang]})
                    </span>
                  )}
              </span>
              <input
                type="number"
                min={0}
                max={180}
                value={budgetValue(lang)}
                onChange={(e) => setEdits((p) => ({ ...p, [lang]: e.target.value }))}
                className="w-20 rounded-md border border-edge bg-surface-2 px-2 py-1 text-sm text-ink tnum"
              />
            </label>
          ))}
          <button
            onClick={saveBudgets}
            disabled={busy !== null || !dirty}
            className="rounded-md border border-edge bg-surface-2 px-3 py-1.5 text-sm hover:text-ink disabled:opacity-50"
          >
            {busy === "budgets" ? "saving…" : "Save budgets"}
          </button>
        </div>
      </Card>

      {!plan && (
        <Card title="Session plan">
          <Empty>
            No plan stored yet — hit “Recompute now” (needs ANKIWEB_HKEY on the
            server) or wait for the daily run.
          </Empty>
        </Card>
      )}

      {plan?.languages.map((lg) => (
        <Card
          key={lg.lang}
          title={
            <span className="flex items-center gap-2">
              <LangBadge lang={lg.lang} />
              {langName(lg.lang)}
              {lg.due.overflow && (
                <span className="text-xs font-normal text-warning">
                  overflow +{lg.due.overflow_minutes} min
                </span>
              )}
            </span>
          }
          aside={`${lg.budget_min} min budget → ${lg.deck_name}`}
        >
          <div className="mb-3 text-xs text-ink-2">
            <span className="font-semibold text-ink">
              Due first: {lg.due.cards} cards ≈ {lg.due.est_minutes} min
            </span>
            {Object.entries(lg.due.by_population).map(([pop, d]) => (
              <span key={pop} className="ml-3">
                {popLabel(pop)} {d.cards} ({d.est_minutes} min)
              </span>
            ))}
            <div className="mt-1 font-mono text-[11px] text-muted">
              {lg.due.search} · limit {lg.due.limit} · order {lg.due.order}
            </div>
          </div>

          {lg.new.mix.length > 0 ? (
            <div className="overflow-x-auto">
              <div className="mb-1 text-xs text-ink-2">
                New cards: {lg.new.minutes_available} min remaining after dues
              </div>
              <table className="w-full border-collapse">
                <thead>
                  <tr>
                    <Th>Population</Th>
                    <Th className="text-right">Weight</Th>
                    <Th className="text-right">Cards</Th>
                    <Th className="text-right">≈ min</Th>
                    <Th className="text-right">Reservoir</Th>
                    <Th>Why</Th>
                  </tr>
                </thead>
                <tbody>
                  {lg.new.mix.map((m) => (
                    <tr key={m.population} className="hover:bg-surface-2">
                      <Td>
                        {popLabel(m.population)}
                        <div className="font-mono text-[11px] text-muted">
                          {m.search}
                        </div>
                      </Td>
                      <Td className="tnum text-right text-xs">
                        {(m.weight * 100).toFixed(0)}%
                      </Td>
                      <Td className="tnum text-right text-xs">{m.cards}</Td>
                      <Td className="tnum text-right text-xs">{m.est_minutes}</Td>
                      <Td className="tnum text-right text-xs">{m.reservoir}</Td>
                      <Td className="text-xs text-ink-2">{m.reasoning}</Td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <div className="text-xs text-muted">
              no new cards today{lg.due.overflow ? " (budget consumed by dues)" : ""}
            </div>
          )}

          {lg.notes.length > 0 && (
            <ul className="mt-2 list-inside list-disc text-xs text-warning">
              {lg.notes.map((n) => (
                <li key={n}>{n}</li>
              ))}
            </ul>
          )}
        </Card>
      ))}

      <Card
        title="Observations"
        aside={
          obs
            ? `snapshot ${fmtAgo(obs.computed_at)} · ${obs.unclassified_cards} cards outside the estate roots`
            : undefined
        }
      >
        {!obs ? (
          <Empty>No pulled snapshot yet.</Empty>
        ) : (
          <div className="flex flex-col gap-4">
            {DJ_LANGS.filter((l) => obs.langs[l]).map((lang) => {
              const L = obs.langs[lang];
              const pops = Array.from(
                new Set([
                  ...Object.keys(L.due),
                  ...Object.keys(L.new_reservoir),
                  ...Object.keys(L.last7),
                ]),
              ).sort();
              return (
                <div key={lang}>
                  <div className="mb-1 flex items-center gap-2 text-sm font-semibold">
                    <LangBadge lang={lang} /> {langName(lang)}
                  </div>
                  <div className="overflow-x-auto">
                    <table className="w-full border-collapse">
                      <thead>
                        <tr>
                          <Th>Population</Th>
                          <Th className="text-right">Due</Th>
                          <Th className="text-right">New reservoir</Th>
                          <Th className="text-right">secs/rep</Th>
                          <Th className="text-right">7d reps</Th>
                          <Th className="text-right">7d minutes</Th>
                        </tr>
                      </thead>
                      <tbody>
                        {pops.map((pop) => {
                          const spr = L.secs_per_rep[pop];
                          return (
                            <tr key={pop} className="hover:bg-surface-2">
                              <Td className="text-xs">{popLabel(pop)}</Td>
                              <Td className="tnum text-right text-xs">
                                {L.due[pop] ?? 0}
                              </Td>
                              <Td className="tnum text-right text-xs">
                                {L.new_reservoir[pop] ?? 0}
                              </Td>
                              <Td className="tnum text-right text-xs">
                                {spr ? (
                                  <>
                                    {spr.secs}
                                    <span
                                      className={
                                        spr.source === "prior"
                                          ? "ml-1 text-warning"
                                          : "ml-1 text-muted"
                                      }
                                    >
                                      {spr.source === "prior"
                                        ? "prior"
                                        : `n=${spr.n_obs}`}
                                    </span>
                                  </>
                                ) : (
                                  "—"
                                )}
                              </Td>
                              <Td className="tnum text-right text-xs">
                                {L.last7[pop]?.reps ?? 0}
                              </Td>
                              <Td className="tnum text-right text-xs">
                                {L.last7[pop]?.minutes ?? 0}
                              </Td>
                            </tr>
                          );
                        })}
                      </tbody>
                    </table>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </Card>
    </div>
  );
}
