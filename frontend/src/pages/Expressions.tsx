import { useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { LANG_ORDER } from "../api";
import AudioButton from "../components/AudioButton";
import { Card, Empty, ErrorBox, LangBadge, Pager, Spinner } from "../components/ui";
import { fmtDate, langName } from "../format";
import { useApi, useDebounced } from "../hooks";

interface ExprRow {
  id: number;
  expression_id: number;
  lang: string;
  idiom_text: string;
  english_gloss: string;
  explanation_en: string | null;
  audio_idiom_tgt: string | null;
  audio_idiom_en: string | null;
  created_at: string;
  video_id: number | null;
  youtube_id: string | null;
  video_title: string | null;
  channel_id: number | null;
  channel_name: string | null;
  n_reencounters: number;
}

interface ChannelRow {
  id: number;
  name: string | null;
  lang: string;
}

const LIMIT = 30;

export default function Expressions() {
  const [sp, setSp] = useSearchParams();
  const [q, setQ] = useState(sp.get("q") ?? "");
  const dq = useDebounced(q);
  const lang = sp.get("lang") ?? "";
  const channelId = sp.get("channel_id") ?? "";
  const offset = Number(sp.get("offset") ?? 0);

  const setParam = (k: string, v: string) => {
    const next = new URLSearchParams(sp);
    if (v) next.set(k, v);
    else next.delete(k);
    if (k !== "offset") next.delete("offset");
    setSp(next, { replace: true });
  };

  const { data: channels } = useApi<{ rows: ChannelRow[] }>("/channels");
  const { data, error, loading } = useApi<{ total: number; rows: ExprRow[] }>("/expressions", {
    lang,
    q: dq,
    channel_id: channelId || undefined,
    limit: LIMIT,
    offset,
  });

  // People/person buckets are channels — curated ones get top billing.
  const channelOpts = (channels?.rows ?? [])
    .filter((c) => !lang || c.lang === lang)
    .sort((a, b) => {
      const ac = a.name?.startsWith("Curated ·") ? 0 : 1;
      const bc = b.name?.startsWith("Curated ·") ? 0 : 1;
      return ac - bc || (a.name ?? "").localeCompare(b.name ?? "");
    });

  return (
    <div className="flex flex-col gap-4">
      <div className="flex items-baseline gap-3">
        <h1 className="text-xl font-bold">Expressions</h1>
        {data && <span className="tnum text-sm text-muted">{data.total} in view</span>}
      </div>

      <div className="flex flex-wrap items-center gap-2">
        <input
          value={q}
          onChange={(e) => {
            setQ(e.target.value);
            setParam("q", e.target.value);
          }}
          placeholder="search idioms, glosses, explanations…"
          autoFocus
          className="w-80 rounded-md border border-edge bg-surface px-3 py-1.5 text-sm outline-none placeholder:text-muted focus:border-accent"
        />
        <select
          value={lang}
          onChange={(e) => setParam("lang", e.target.value)}
          className="rounded-md border border-edge bg-surface px-2 py-1.5 text-sm"
        >
          <option value="">all languages</option>
          {LANG_ORDER.map((l) => (
            <option key={l} value={l}>
              {langName(l)}
            </option>
          ))}
        </select>
        <select
          value={channelId}
          onChange={(e) => setParam("channel_id", e.target.value)}
          className="max-w-64 rounded-md border border-edge bg-surface px-2 py-1.5 text-sm"
        >
          <option value="">anyone / any channel</option>
          {channelOpts.map((c) => (
            <option key={c.id} value={c.id}>
              {c.name?.startsWith("Curated ·") ? `★ ${c.name.slice(10)}` : c.name} ({c.lang})
            </option>
          ))}
        </select>
      </div>

      {error ? (
        <ErrorBox error={error} />
      ) : loading && !data ? (
        <Spinner />
      ) : data && data.rows.length === 0 ? (
        <Empty>Nothing matches.</Empty>
      ) : data ? (
        <>
          <div className="grid gap-3 xl:grid-cols-2">
            {data.rows.map((r) => (
              <Card key={r.id} className="flex flex-col gap-2">
                <div className="flex flex-wrap items-baseline gap-x-3 gap-y-0.5">
                  <Link
                    to={`/expressions/${r.id}`}
                    className="text-lg font-semibold leading-snug hover:underline"
                  >
                    {r.idiom_text}
                  </Link>
                  <span className="text-sm text-ink-2">{r.english_gloss}</span>
                </div>
                {r.explanation_en && (
                  <p className="line-clamp-2 text-sm text-ink-2">{r.explanation_en}</p>
                )}
                <div className="mt-auto flex flex-wrap items-center gap-2 pt-1">
                  <AudioButton path={r.audio_idiom_tgt} label="idiom" />
                  <AudioButton path={r.audio_idiom_en} label="EN" />
                  <span className="ml-auto flex items-center gap-2 text-xs text-muted">
                    <LangBadge lang={r.lang} />
                    {r.n_reencounters > 0 && (
                      <span
                        className="text-warning"
                        title="times re-encountered in later videos"
                      >
                        ↻ {r.n_reencounters}
                      </span>
                    )}
                    <span>{fmtDate(r.created_at)}</span>
                  </span>
                </div>
                <div className="truncate text-xs text-muted">
                  {r.channel_name?.startsWith("Curated ·") ? "★ " : ""}
                  {r.channel_name} ·{" "}
                  {r.video_id ? (
                    <Link to={`/videos/${r.video_id}`} className="hover:underline">
                      {r.video_title}
                    </Link>
                  ) : (
                    r.video_title
                  )}
                </div>
              </Card>
            ))}
          </div>
          <Pager total={data.total} limit={LIMIT} offset={offset} onPage={(o) => setParam("offset", String(o))} />
        </>
      ) : null}
    </div>
  );
}
