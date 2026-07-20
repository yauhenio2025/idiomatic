import { useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { LANG_ORDER } from "../api";
import { Card, ErrorBox, LangBadge, Pager, Spinner, StatusBadge, Td, Th } from "../components/ui";
import { fmtDate, fmtDuration, langName } from "../format";
import { useApi, useDebounced } from "../hooks";

interface VideoRow {
  id: number;
  youtube_id: string;
  title: string | null;
  lang: string;
  duration_sec: number | null;
  status: string;
  status_msg: string | null;
  reason_class: string;
  first_seen: string;
  processing_seconds: number | null;
  channel_id: number | null;
  channel_name: string | null;
  curated: boolean;
  apkg_id: number | null;
  apkg_built_at: string | null;
  n_idioms: number | null;
  delivered_at: string | null;
  n_extracted: number;
  n_fresh: number;
  n_duplicates: number;
}

const STATUSES = ["queued", "processing", "done", "skipped", "failed"];
const LIMIT = 50;

export default function Videos() {
  const [sp, setSp] = useSearchParams();
  const [q, setQ] = useState(sp.get("q") ?? "");
  const dq = useDebounced(q);
  const lang = sp.get("lang") ?? "";
  const status = sp.get("status") ?? "";
  const curated = sp.get("curated") ?? "";
  const channelId = sp.get("channel_id") ?? "";
  const offset = Number(sp.get("offset") ?? 0);

  const setParam = (k: string, v: string) => {
    const next = new URLSearchParams(sp);
    if (v) next.set(k, v);
    else next.delete(k);
    if (k !== "offset") next.delete("offset");
    setSp(next, { replace: true });
  };

  const { data, error, loading } = useApi<{ total: number; rows: VideoRow[] }>(
    "/videos",
    {
      lang,
      status,
      q: dq,
      curated: curated || undefined,
      channel_id: channelId || undefined,
      limit: LIMIT,
      offset,
    },
    15000,
  );

  return (
    <div className="flex flex-col gap-4">
      <h1 className="text-xl font-bold">Videos</h1>

      <div className="flex flex-wrap items-center gap-2">
        <input
          value={q}
          onChange={(e) => {
            setQ(e.target.value);
            setParam("q", e.target.value);
          }}
          placeholder="search titles…"
          className="w-56 rounded-md border border-edge bg-surface px-3 py-1.5 text-sm outline-none placeholder:text-muted focus:border-accent"
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
          value={status}
          onChange={(e) => setParam("status", e.target.value)}
          className="rounded-md border border-edge bg-surface px-2 py-1.5 text-sm"
        >
          <option value="">all statuses</option>
          {STATUSES.map((s) => (
            <option key={s} value={s}>
              {s}
            </option>
          ))}
        </select>
        <select
          value={curated}
          onChange={(e) => setParam("curated", e.target.value)}
          className="rounded-md border border-edge bg-surface px-2 py-1.5 text-sm"
        >
          <option value="">curated + RSS</option>
          <option value="true">curated only</option>
          <option value="false">RSS only</option>
        </select>
        {channelId && (
          <button
            onClick={() => setParam("channel_id", "")}
            className="rounded-md border border-edge px-2 py-1.5 text-xs text-ink-2 hover:bg-surface-2"
          >
            channel #{channelId} ✕
          </button>
        )}
      </div>

      {error ? (
        <ErrorBox error={error} />
      ) : loading && !data ? (
        <Spinner />
      ) : data ? (
        <Card>
          <div className="overflow-x-auto">
            <table className="w-full border-collapse">
              <thead>
                <tr>
                  <Th>Video</Th>
                  <Th>Channel</Th>
                  <Th className="text-right">Length</Th>
                  <Th>Status</Th>
                  <Th className="text-right">Idioms fresh/dup</Th>
                  <Th className="text-right">Deck</Th>
                  <Th className="text-right">Delivered</Th>
                  <Th className="text-right">Seen</Th>
                </tr>
              </thead>
              <tbody>
                {data.rows.map((v) => (
                  <tr key={v.id} className="hover:bg-surface-2">
                    <Td className="max-w-96">
                      <Link to={`/videos/${v.id}`} className="block truncate text-ink hover:underline" title={v.title ?? undefined}>
                        {v.title ?? v.youtube_id}
                      </Link>
                      <LangBadge lang={v.lang} />
                    </Td>
                    <Td className="max-w-40">
                      <span className="block truncate text-xs text-ink-2" title={v.channel_name ?? undefined}>
                        {v.curated && <span title="curated bucket">★ </span>}
                        {v.channel_name ?? "—"}
                      </span>
                    </Td>
                    <Td className="tnum text-right text-xs">{fmtDuration(v.duration_sec)}</Td>
                    <Td>
                      <StatusBadge status={v.status} />
                      {v.status_msg && (
                        <div className="max-w-48 truncate text-xs text-muted" title={v.status_msg}>
                          {v.reason_class !== "none" ? v.reason_class : v.status_msg}
                        </div>
                      )}
                    </Td>
                    <Td className="tnum text-right text-xs">
                      {v.n_extracted > 0 ? (
                        <>
                          <span className="text-good">{v.n_fresh}</span>
                          {" / "}
                          <span className="text-warning">{v.n_duplicates}</span>
                        </>
                      ) : v.status === "done" && v.n_idioms != null ? (
                        <span title="processed before the extraction log existed">
                          {v.n_idioms} <span className="text-muted">(pre-log)</span>
                        </span>
                      ) : (
                        "—"
                      )}
                    </Td>
                    <Td className="tnum text-right text-xs">
                      {v.apkg_built_at ? fmtDate(v.apkg_built_at) : "—"}
                    </Td>
                    <Td className="tnum text-right text-xs">
                      {v.delivered_at ? (
                        <span className="text-good">✓ {fmtDate(v.delivered_at)}</span>
                      ) : v.apkg_id ? (
                        <span className="text-warning">pending</span>
                      ) : (
                        "—"
                      )}
                    </Td>
                    <Td className="tnum text-right text-xs text-muted">{fmtDate(v.first_seen)}</Td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <Pager total={data.total} limit={LIMIT} offset={offset} onPage={(o) => setParam("offset", String(o))} />
        </Card>
      ) : null}
    </div>
  );
}
