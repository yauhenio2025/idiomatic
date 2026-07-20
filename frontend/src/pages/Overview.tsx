import { Link } from "react-router-dom";
import { LANG_ORDER, langColor } from "../api";
import { DayStack, GrowthPoint, HBars, MultiLine, StackedBars } from "../components/charts";
import { Card, ErrorBox, LangBadge, Spinner, StatTile } from "../components/ui";
import { fmtAgo, fmtDate } from "../format";
import { useApi } from "../hooks";

interface Overview {
  health: {
    queued_videos: number;
    processing: {
      id: number;
      youtube_id: string;
      title: string | null;
      lang: string;
      picked_at: string;
      channel_name: string | null;
    }[];
    latest_apkg_age_hours: number | null;
    stalled: boolean;
    status_counts: Record<string, number>;
    daily_cap: number;
    builds_today: { lang: string; built: number }[];
  };
  throughput_30d: { day: string; lang: string; n: number }[];
  library_growth: { day: string; lang: string; total: number }[];
  funnel_7d: { status: string; reason_class: string; n: number }[];
  dedup_7d: { fresh?: number; duplicates?: number };
  extraction_log_since: string | null;
  expressions_by_lang: { lang: string; n: number }[];
}

function lastNDays(n: number): string[] {
  const out: string[] = [];
  const d = new Date();
  for (let i = n - 1; i >= 0; i--) {
    const dd = new Date(d.getTime() - i * 86400000);
    out.push(dd.toISOString().slice(0, 10));
  }
  return out;
}

const SKIP_LABELS: Record<string, string> = {
  "duration-pre-filter": "too short/long (RSS pre-filter)",
  "duration-post-check": "too short/long (after download)",
  "oxylabs-permanent": "undownloadable (Oxylabs)",
  "wrong-channel": "wrong channel",
  "all-duplicates": "every idiom already known",
  "no-idioms": "no idioms extracted",
  other: "other",
};

export default function OverviewPage() {
  const { data, error, loading } = useApi<Overview>("/overview", undefined, 30000);
  if (loading && !data) return <Spinner />;
  if (error) return <ErrorBox error={error} />;
  if (!data) return null;

  const h = data.health;

  const activeLangs = LANG_ORDER.filter(
    (l) =>
      data.throughput_30d.some((r) => r.lang === l) ||
      data.library_growth.some((r) => r.lang === l),
  );

  const days30 = lastNDays(30);
  const throughput: DayStack[] = days30.map((day) => ({
    day,
    counts: Object.fromEntries(
      data.throughput_30d
        .filter((r) => r.day.slice(0, 10) === day)
        .map((r) => [r.lang, Number(r.n)]),
    ),
  }));

  // forward-fill cumulative totals per language across the union of days
  const growthDays = [...new Set(data.library_growth.map((r) => r.day.slice(0, 10)))].sort();
  const running: Record<string, number> = {};
  const growth: GrowthPoint[] = growthDays.map((day) => {
    for (const r of data.library_growth) {
      if (r.day.slice(0, 10) === day) running[r.lang] = Number(r.total);
    }
    return { day, totals: { ...running } };
  });

  // funnel: discovered -> enqueued -> outcomes
  const f = data.funnel_7d;
  const sum = (pred: (r: Overview["funnel_7d"][0]) => boolean) =>
    f.filter(pred).reduce((s, r) => s + Number(r.n), 0);
  const discovered = sum(() => true);
  const preFiltered = sum((r) => r.reason_class === "duration-pre-filter");
  const enqueued = discovered - preFiltered;
  const done = sum((r) => r.status === "done");
  const failed = sum((r) => r.status === "failed");
  const inFlight = sum((r) => r.status === "queued" || r.status === "processing");
  const skipReasons = Object.entries(
    f
      .filter((r) => r.status === "skipped" && r.reason_class !== "duration-pre-filter")
      .reduce<Record<string, number>>((acc, r) => {
        acc[r.reason_class] = (acc[r.reason_class] ?? 0) + Number(r.n);
        return acc;
      }, {}),
  ).sort((a, b) => b[1] - a[1]);

  const capBadges = LANG_ORDER.map((l) => ({
    lang: l,
    built: Number(h.builds_today.find((b) => b.lang === l)?.built ?? 0),
  }));

  const totalExpressions = data.expressions_by_lang.reduce((s, r) => s + Number(r.n), 0);

  return (
    <div className="flex flex-col gap-4">
      <div className="flex items-baseline justify-between">
        <h1 className="text-xl font-bold">Overview</h1>
        <span className="text-xs text-muted">refreshes every 30s</span>
      </div>

      {/* health strip */}
      <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
        <StatTile
          label="Worker"
          value={
            h.stalled ? "⚠ stalled" : h.processing.length > 0 ? "▸ processing" : "✓ idle"
          }
          tone={h.stalled ? "critical" : h.processing.length > 0 ? undefined : "good"}
          sub={
            h.latest_apkg_age_hours != null
              ? `last deck ${h.latest_apkg_age_hours}h ago`
              : "no decks yet"
          }
        />
        <StatTile label="Queued videos" value={<span className="tnum">{h.queued_videos}</span>} sub={`${h.status_counts.failed ?? 0} failed total`} />
        <StatTile
          label="Expression library"
          value={<span className="tnum">{totalExpressions}</span>}
          sub={data.expressions_by_lang.map((r) => `${r.lang} ${r.n}`).join(" · ")}
        />
        <div className="rounded-lg border border-edge bg-surface px-4 py-3">
          <div className="text-xs text-muted">Today's builds vs cap ({h.daily_cap}/lang)</div>
          <div className="mt-2 flex flex-col gap-1">
            {capBadges.map((b) => (
              <div key={b.lang} className="flex items-center gap-2">
                <LangBadge lang={b.lang} />
                <div className="ml-auto flex gap-1">
                  {Array.from({ length: h.daily_cap }, (_, i) => (
                    <span
                      key={i}
                      className="inline-block h-2 w-4 rounded-[3px]"
                      style={{
                        background: i < b.built ? langColor(b.lang) : "var(--grid)",
                      }}
                    />
                  ))}
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {h.processing.length > 0 && (
        <Card title="Processing right now">
          {h.processing.map((p) => (
            <div key={p.id} className="flex items-center gap-3 text-sm">
              <LangBadge lang={p.lang} />
              <Link to={`/videos/${p.id}`} className="truncate text-ink hover:underline">
                {p.title ?? p.youtube_id}
              </Link>
              <span className="ml-auto shrink-0 text-xs text-muted">
                {p.channel_name} · started {fmtAgo(p.picked_at)}
              </span>
            </div>
          ))}
        </Card>
      )}

      <div className="grid gap-4 xl:grid-cols-2">
        <Card title="Decks built per day" aside="last 30 days · stacked by language">
          <StackedBars data={throughput} langs={activeLangs} />
        </Card>
        <Card title="Expression library growth" aside="cumulative unique expressions">
          <MultiLine data={growth} langs={activeLangs} />
        </Card>
      </div>

      <div className="grid gap-4 xl:grid-cols-2">
        <Card title="Last 7 days: from RSS to Anki" aside="the funnel">
          <HBars
            rows={[
              { label: "videos discovered", value: discovered, color: "var(--baseline)" },
              { label: "pre-filtered out", value: preFiltered, color: "var(--grid)" },
              { label: "enqueued", value: enqueued, color: "var(--accent)" },
              { label: "✓ decks built", value: done, color: "var(--status-good)" },
              { label: "queued / in flight", value: inFlight, color: "var(--lang-de)" },
              { label: "✕ failed", value: failed, color: "var(--status-critical)" },
            ]}
          />
          {skipReasons.length > 0 && (
            <>
              <div className="mb-1.5 mt-4 text-xs font-medium text-muted">
                skipped after enqueue, by reason
              </div>
              <HBars
                rows={skipReasons.map(([cls, n]) => ({
                  label: SKIP_LABELS[cls] ?? cls,
                  value: n,
                  color: "var(--status-serious)",
                }))}
              />
            </>
          )}
        </Card>
        <Card
          title="Dedup — what we already knew"
          aside={
            data.extraction_log_since
              ? `logged since ${fmtDate(data.extraction_log_since)}`
              : "no data yet"
          }
        >
          {!data.extraction_log_since ? (
            <p className="text-sm text-muted">
              The extraction log starts recording at first deploy — duplicate
              rejections were never persisted before, so older videos show no
              dedup data (that history is unrecoverable, not zero).
            </p>
          ) : (
            <>
              <HBars
                rows={[
                  {
                    label: "fresh expressions",
                    value: Number(data.dedup_7d.fresh ?? 0),
                    color: "var(--status-good)",
                  },
                  {
                    label: "already in library",
                    value: Number(data.dedup_7d.duplicates ?? 0),
                    color: "var(--status-warning)",
                  },
                ]}
              />
              <p className="mt-3 text-xs text-muted">
                Last 7 days of Gemini extractions, split by dedup verdict.
                Recording began {fmtAgo(data.extraction_log_since)} — earlier
                videos predate the log. Per-video detail on each{" "}
                <Link to="/videos" className="underline">
                  video page
                </Link>
                ; per-expression re-encounters on the{" "}
                <Link to="/expressions" className="underline">
                  expression cards
                </Link>
                .
              </p>
            </>
          )}
        </Card>
      </div>

      <div className="text-center text-xs text-muted">
        {h.status_counts.done ?? 0} videos done all-time · {h.status_counts.skipped ?? 0}{" "}
        skipped · {h.status_counts.failed ?? 0} failed
      </div>
    </div>
  );
}
