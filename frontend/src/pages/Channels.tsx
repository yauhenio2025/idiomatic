import { Link } from "react-router-dom";
import { Card, ErrorBox, LangBadge, Spinner, Td, Th } from "../components/ui";
import { fmtAgo, fmtDuration } from "../format";
import { useApi } from "../hooks";

interface ChannelRow {
  id: number;
  youtube_id: string;
  lang: string;
  name: string | null;
  active: boolean;
  priority: number;
  title_filter: string | null;
  min_duration_sec: number | null;
  max_duration_sec: number | null;
  videos_seen: number;
  videos_done: number;
  videos_skipped: number;
  videos_failed: number;
  videos_queued: number;
  last_video_at: string | null;
  idioms_yielded: number;
}

export default function Channels() {
  const { data, error, loading } = useApi<{ rows: ChannelRow[] }>("/channels");
  if (loading && !data) return <Spinner />;
  if (error) return <ErrorBox error={error} />;
  if (!data) return null;

  const rows = [...data.rows].sort((a, b) => b.idioms_yielded - a.idioms_yielded);
  const deadWeight = rows.filter(
    (c) => c.active && c.idioms_yielded === 0 && c.videos_seen > 10,
  );

  return (
    <div className="flex flex-col gap-4">
      <div className="flex items-baseline gap-3">
        <h1 className="text-xl font-bold">Channels</h1>
        <span className="text-sm text-muted">{rows.length} subscriptions</span>
      </div>

      {deadWeight.length > 0 && (
        <div className="rounded-md border border-warning/40 bg-surface px-4 py-2.5 text-sm text-ink-2">
          <span className="text-warning">⚠ dead weight:</span>{" "}
          {deadWeight.map((c) => c.name).join(", ")} —{" "}
          {deadWeight.length === 1 ? "has" : "have"} produced zero idioms despite
          plenty of RSS traffic.
        </div>
      )}

      <Card>
        <div className="overflow-x-auto">
          <table className="w-full border-collapse">
            <thead>
              <tr>
                <Th>Channel</Th>
                <Th>Rules</Th>
                <Th className="text-right">Seen</Th>
                <Th className="text-right">Done</Th>
                <Th className="text-right">Skipped</Th>
                <Th className="text-right">Queued</Th>
                <Th className="text-right">Idioms</Th>
                <Th className="text-right">Yield/video</Th>
                <Th className="text-right">Last video</Th>
              </tr>
            </thead>
            <tbody>
              {rows.map((c) => {
                const zero = c.active && c.idioms_yielded === 0 && c.videos_seen > 10;
                return (
                  <tr key={c.id} className={`hover:bg-surface-2 ${zero ? "opacity-70" : ""}`}>
                    <Td className="max-w-56">
                      <Link
                        to={`/videos?channel_id=${c.id}`}
                        className="block truncate font-medium text-ink hover:underline"
                        title="see this channel's videos"
                      >
                        {c.priority >= 10 && <span title="priority — bypasses the daily cap">🔥 </span>}
                        {c.name?.startsWith("Curated ·") && "★ "}
                        {c.name ?? c.youtube_id}
                      </Link>
                      <div className="flex items-center gap-2">
                        <LangBadge lang={c.lang} />
                        {!c.active && <span className="text-xs text-muted">inactive</span>}
                        {zero && <span className="text-xs text-warning">⚠ zero yield</span>}
                      </div>
                    </Td>
                    <Td className="max-w-44 text-xs text-muted">
                      {c.title_filter && (
                        <div className="truncate" title={`title filter: ${c.title_filter}`}>
                          ~ /{c.title_filter}/
                        </div>
                      )}
                      {(c.min_duration_sec || c.max_duration_sec) && (
                        <div>
                          {fmtDuration(c.min_duration_sec ?? 420)}–
                          {fmtDuration(c.max_duration_sec ?? 900)}
                        </div>
                      )}
                    </Td>
                    <Td className="tnum text-right">{c.videos_seen}</Td>
                    <Td className="tnum text-right text-good">{c.videos_done}</Td>
                    <Td className="tnum text-right text-muted">{c.videos_skipped}</Td>
                    <Td className="tnum text-right">{c.videos_queued}</Td>
                    <Td className="tnum text-right font-medium">{c.idioms_yielded}</Td>
                    <Td className="tnum text-right text-xs text-ink-2">
                      {c.videos_done > 0 ? (c.idioms_yielded / c.videos_done).toFixed(1) : "—"}
                    </Td>
                    <Td className="tnum text-right text-xs text-muted">{fmtAgo(c.last_video_at)}</Td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </Card>
    </div>
  );
}
