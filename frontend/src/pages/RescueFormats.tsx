import { Link } from "react-router-dom";
import { RescueFormatsResponse } from "../components/rescue";
import { Card, ErrorBox, Spinner, Td, Th } from "../components/ui";
import { fmtUsd } from "../format";
import { useApi } from "../hooks";

export default function RescueFormats() {
  const { data, error, loading } = useApi<RescueFormatsResponse>("/rescue/formats");

  if (loading && !data) return <Spinner />;
  if (error) return <ErrorBox error={error} />;
  if (!data) return null;

  return (
    <div className="flex flex-col gap-4">
      <div>
        <Link to="/rescue" className="text-xs text-muted hover:text-ink">
          ← Rescue Lab
        </Link>
        <div className="mt-1 flex flex-wrap items-baseline gap-3">
          <h1 className="text-xl font-bold">Rescue formats</h1>
          <span className="text-xs text-muted">
            the taxonomy behind the Generate panel — video is not, and will never be, on
            this list
          </span>
        </div>
      </div>

      <Card title="Image providers">
        <table className="w-full border-collapse">
          <thead>
            <tr>
              <Th>Key</Th>
              <Th>Model</Th>
              <Th>API family</Th>
              <Th className="text-right">Cost / image</Th>
            </tr>
          </thead>
          <tbody>
            {data.providers.map((p) => (
              <tr key={p.key}>
                <Td className="font-medium">{p.key}</Td>
                <Td className="font-mono text-xs">{p.model}</Td>
                <Td className="text-xs text-muted">{p.api}</Td>
                <Td className="tnum text-right">{fmtUsd(p.usd_per_image)}</Td>
              </tr>
            ))}
          </tbody>
        </table>
        <div className="mt-2 text-xs text-muted">
          Prices verified against the official pricing docs (1K output, standard tier);
          the registry in <span className="font-mono">idiomatic/genmedia.py</span> is the
          single source of truth and stamps gen_ledger at call time.
        </div>
      </Card>

      {data.formats.map((f) => (
        <Card
          key={f.key}
          title={
            <>
              {f.name} <span className="font-mono text-xs font-normal text-muted">{f.key}</span>
            </>
          }
          aside={
            f.kind === "image" ? (
              <span className="text-xs text-accent">generated</span>
            ) : (
              <span className="text-xs text-muted">authored manually</span>
            )
          }
        >
          <div className="flex flex-col gap-3 text-sm">
            <div>
              <span className="text-xs font-semibold uppercase tracking-wide text-muted">
                When to use
              </span>
              <p className="mt-1 text-ink-2">{f.when_to_use}</p>
            </div>
            <div>
              <span className="text-xs font-semibold uppercase tracking-wide text-muted">
                Design rules
              </span>
              <ul className="mt-1 list-disc pl-5 text-ink-2">
                {f.rules.map((r, i) => (
                  <li key={i}>{r}</li>
                ))}
              </ul>
            </div>
            {f.template && (
              <div>
                <span className="text-xs font-semibold uppercase tracking-wide text-muted">
                  Template prompt
                </span>
                <pre className="mt-1 whitespace-pre-wrap rounded border border-edge bg-surface-2 p-3 font-mono text-xs text-ink-2">
                  {f.template}
                </pre>
                {Object.keys(f.placeholders).length > 0 && (
                  <div className="mt-2 text-xs text-muted">
                    {Object.entries(f.placeholders).map(([k, v]) => (
                      <div key={k}>
                        <span className="font-mono text-accent">{"{" + k + "}"}</span> — {v}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}
          </div>
        </Card>
      ))}
    </div>
  );
}
