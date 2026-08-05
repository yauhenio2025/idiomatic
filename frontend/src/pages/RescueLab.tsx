import { useState } from "react";
import { Link } from "react-router-dom";
import { LANG_ORDER } from "../api";
import {
  CostsResponse,
  ItemStatusChip,
  RescueItemRow,
  StrikeDots,
} from "../components/rescue";
import { Card, Empty, ErrorBox, LangBadge, Spinner, StatTile, Td, Th } from "../components/ui";
import { fmtAgo, fmtUsd } from "../format";
import { useApi } from "../hooks";

export default function RescueLab() {
  const [lang, setLang] = useState("");
  const [status, setStatus] = useState("");
  const { data, error, loading } = useApi<{ rows: RescueItemRow[] }>("/rescue/items", {
    lang,
    status,
  });
  const costs = useApi<CostsResponse>("/rescue/costs");

  if (loading && !data) return <Spinner />;
  if (error) return <ErrorBox error={error} />;
  if (!data) return null;

  const c = costs.data;
  const topProvider = c?.by_provider[0];

  return (
    <div className="flex flex-col gap-4">
      <div className="flex flex-wrap items-baseline gap-3">
        <h1 className="text-xl font-bold">Rescue Lab</h1>
        <span className="text-xs text-muted">
          struggle idioms → rescue assets, with full cost accounting
        </span>
        <Link
          to="/rescue/formats"
          className="ml-auto rounded border border-edge px-2.5 py-1 text-xs text-ink-2 transition-colors hover:bg-surface-2"
        >
          Format taxonomy →
        </Link>
      </div>

      <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
        <StatTile
          label="Spend this month"
          value={fmtUsd(c?.this_month)}
          sub={`${c?.n_calls ?? "—"} paid calls all-time`}
        />
        <StatTile label="Spend all-time" value={fmtUsd(c?.all_time)} />
        <StatTile
          label="Top provider"
          value={topProvider ? topProvider.provider : "—"}
          sub={topProvider ? `${fmtUsd(topProvider.usd)} · ${topProvider.n} calls` : "no spend yet"}
        />
        <StatTile
          label="Items"
          value={data.rows.length}
          sub={`${data.rows.filter((r) => r.status === "active").length} active`}
        />
      </div>

      {c && (c.by_provider.length > 0 || c.by_format.length > 0) && (
        <div className="grid gap-3 lg:grid-cols-2">
          <Card title="Spend by provider">
            {c.by_provider.length === 0 ? (
              <Empty>No paid calls yet.</Empty>
            ) : (
              <table className="w-full border-collapse">
                <thead>
                  <tr>
                    <Th>Provider</Th>
                    <Th>Model</Th>
                    <Th className="text-right">Calls</Th>
                    <Th className="text-right">This month</Th>
                    <Th className="text-right">All-time</Th>
                  </tr>
                </thead>
                <tbody>
                  {c.by_provider.map((p) => (
                    <tr key={`${p.provider}:${p.model}`}>
                      <Td>{p.provider}</Td>
                      <Td className="font-mono text-xs text-muted">{p.model}</Td>
                      <Td className="tnum text-right">{p.n}</Td>
                      <Td className="tnum text-right">{fmtUsd(p.usd_month ?? 0)}</Td>
                      <Td className="tnum text-right">{fmtUsd(p.usd)}</Td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </Card>
          <Card title="Spend by format">
            {c.by_format.length === 0 ? (
              <Empty>No paid calls yet.</Empty>
            ) : (
              <table className="w-full border-collapse">
                <thead>
                  <tr>
                    <Th>Format</Th>
                    <Th className="text-right">Calls</Th>
                    <Th className="text-right">All-time</Th>
                  </tr>
                </thead>
                <tbody>
                  {c.by_format.map((f) => (
                    <tr key={f.format}>
                      <Td>{f.format}</Td>
                      <Td className="tnum text-right">{f.n}</Td>
                      <Td className="tnum text-right">{fmtUsd(f.usd)}</Td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </Card>
        </div>
      )}

      <Card
        title="Struggle items"
        aside={
          <div className="flex gap-2">
            <select
              value={lang}
              onChange={(e) => setLang(e.target.value)}
              className="rounded border border-edge bg-surface-2 px-2 py-1 text-xs text-ink"
            >
              <option value="">all languages</option>
              {LANG_ORDER.map((l) => (
                <option key={l} value={l}>
                  {l}
                </option>
              ))}
            </select>
            <select
              value={status}
              onChange={(e) => setStatus(e.target.value)}
              className="rounded border border-edge bg-surface-2 px-2 py-1 text-xs text-ink"
            >
              <option value="">all statuses</option>
              <option value="candidate">candidate</option>
              <option value="active">active</option>
              <option value="retired">retired</option>
            </select>
          </div>
        }
      >
        {data.rows.length === 0 ? (
          <Empty>
            No struggle items yet — upload a snapshot via POST /admin/rescue/struggles.
          </Empty>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full border-collapse">
              <thead>
                <tr>
                  <Th>Lang</Th>
                  <Th>Idiom</Th>
                  <Th className="text-right">Fails (today/14d)</Th>
                  <Th>Strike</Th>
                  <Th>Status</Th>
                  <Th className="text-right">Senses</Th>
                  <Th className="text-right">Assets ✓/all</Th>
                  <Th className="text-right">Spend</Th>
                  <Th className="text-right">Updated</Th>
                </tr>
              </thead>
              <tbody>
                {data.rows.map((r) => (
                  <tr key={r.id} className="hover:bg-surface-2">
                    <Td>
                      <LangBadge lang={r.lang} />
                    </Td>
                    <Td className="min-w-48">
                      <Link
                        to={`/rescue/item/${r.id}`}
                        className="font-medium text-ink hover:underline"
                      >
                        {r.glyph_asset_id != null && (
                          <span className="mr-1.5 text-accent" title="glyph minted">
                            ◈
                          </span>
                        )}
                        {r.idiom}
                      </Link>
                      {r.gloss && (
                        <div className="mt-0.5 text-xs text-muted">{r.gloss}</div>
                      )}
                    </Td>
                    <Td className="tnum text-right text-xs">
                      {r.struggle_snapshot
                        ? `${r.struggle_snapshot.fails_today ?? 0} / ${
                            r.struggle_snapshot.fails_14d ?? 0
                          }`
                        : "—"}
                    </Td>
                    <Td>
                      <StrikeDots strike={r.strike} />
                    </Td>
                    <Td>
                      <ItemStatusChip status={r.status} />
                    </Td>
                    <Td className="tnum text-right text-xs">{r.n_senses}</Td>
                    <Td className="tnum text-right text-xs">
                      <span className="text-good">{r.n_approved}</span>
                      <span className="text-muted"> / {r.n_assets}</span>
                    </Td>
                    <Td className="tnum text-right text-xs">{fmtUsd(r.spend)}</Td>
                    <Td className="tnum text-right text-xs text-muted">
                      {fmtAgo(r.updated_at)}
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
