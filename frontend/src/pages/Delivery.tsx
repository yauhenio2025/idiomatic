import { useState } from "react";
import { Link } from "react-router-dom";
import { Card, ErrorBox, LangBadge, Pager, Spinner, StatTile, Td, Th } from "../components/ui";
import { fmtAgo, fmtBytes, fmtDateTime } from "../format";
import { useApi } from "../hooks";

interface ApkgRow {
  id: number;
  lang: string;
  kind: string;
  filename: string;
  size_bytes: number | null;
  n_idioms: number | null;
  created_at: string;
  video_id: number | null;
  video_title: string | null;
  youtube_id: string | null;
  ack_status: string | null;
  ack_attempts: number | null;
  acked_at: string | null;
  agent_name: string | null;
}

interface DeliveryData {
  total: number;
  rows: ApkgRow[];
  agents: { id: number; name: string | null; langs: string[]; last_seen: string | null }[];
  ack_retry_budget: number;
}

const KIND_LABELS: Record<string, string> = {
  video: "video deck",
  pool_idioms: "pool · idioms",
  pool_expr: "pool · expressions",
  pool_idiom_t2e: "pool · target→EN",
  pool_idiom_e2t: "pool · EN→target",
};

const LIMIT = 100;

export default function Delivery() {
  const [offset, setOffset] = useState(0);
  const { data, error, loading } = useApi<DeliveryData>(
    "/delivery",
    { limit: LIMIT, offset },
    20000,
  );
  if (loading && !data) return <Spinner />;
  if (error) return <ErrorBox error={error} />;
  if (!data) return null;

  const pending = data.rows.filter((r) => !r.ack_status);
  const failed = data.rows.filter(
    (r) => r.ack_status === "failed" && (r.ack_attempts ?? 0) < data.ack_retry_budget,
  );
  const buried = data.rows.filter(
    (r) => r.ack_status === "failed" && (r.ack_attempts ?? 0) >= data.ack_retry_budget,
  );
  const agent = data.agents[0];

  return (
    <div className="flex flex-col gap-4">
      <h1 className="text-xl font-bold">Delivery</h1>

      <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
        <StatTile
          label="Agent"
          value={agent?.name ?? "none"}
          sub={agent ? `last seen ${fmtAgo(agent.last_seen)} · ${agent.langs.join(", ")}` : undefined}
          tone={
            agent?.last_seen && Date.now() - new Date(agent.last_seen).getTime() < 15 * 60000
              ? "good"
              : "warning"
          }
        />
        <StatTile label="Awaiting pickup" value={<span className="tnum">{pending.length}</span>} sub="no ack yet (this page)" />
        <StatTile
          label="Retrying"
          value={<span className="tnum">{failed.length}</span>}
          tone={failed.length ? "warning" : undefined}
          sub={`failed but under the ${data.ack_retry_budget}-attempt budget`}
        />
        <StatTile
          label="Given up"
          value={<span className="tnum">{buried.length}</span>}
          tone={buried.length ? "critical" : undefined}
          sub="failed acks past the retry budget"
        />
      </div>

      <Card title={`Deliverables (${data.total})`} aside="newest first">
        <div className="overflow-x-auto">
          <table className="w-full border-collapse">
            <thead>
              <tr>
                <Th>Deck</Th>
                <Th>Kind</Th>
                <Th className="text-right">Idioms</Th>
                <Th className="text-right">Size</Th>
                <Th className="text-right">Built</Th>
                <Th>Delivery</Th>
              </tr>
            </thead>
            <tbody>
              {data.rows.map((r) => (
                <tr key={r.id} className="hover:bg-surface-2">
                  <Td className="max-w-96">
                    {r.video_id ? (
                      <Link to={`/videos/${r.video_id}`} className="block truncate hover:underline" title={r.video_title ?? undefined}>
                        {r.video_title ?? r.filename}
                      </Link>
                    ) : (
                      <span className="block truncate text-ink-2" title={r.filename}>
                        {r.filename.split("/").pop()}
                      </span>
                    )}
                    <LangBadge lang={r.lang} />
                  </Td>
                  <Td className="text-xs text-ink-2">{KIND_LABELS[r.kind] ?? r.kind}</Td>
                  <Td className="tnum text-right text-xs">{r.n_idioms ?? "—"}</Td>
                  <Td className="tnum text-right text-xs">{fmtBytes(r.size_bytes)}</Td>
                  <Td className="tnum text-right text-xs text-muted">{fmtDateTime(r.created_at)}</Td>
                  <Td>
                    {r.ack_status === "ok" ? (
                      <span className="text-xs text-good">✓ imported {fmtAgo(r.acked_at)}</span>
                    ) : r.ack_status === "failed" ? (
                      (r.ack_attempts ?? 0) >= data.ack_retry_budget ? (
                        <span className="text-xs text-critical">
                          ✕ gave up after {r.ack_attempts} attempts
                        </span>
                      ) : (
                        <span className="text-xs text-warning">
                          ⟳ failed ×{r.ack_attempts}, retrying
                        </span>
                      )
                    ) : (
                      <span className="text-xs text-muted">awaiting pickup</span>
                    )}
                  </Td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <Pager total={data.total} limit={LIMIT} offset={offset} onPage={setOffset} />
      </Card>
    </div>
  );
}
