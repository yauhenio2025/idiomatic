import { useEffect, useMemo, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { adminCall } from "../api";
import {
  AssetImage,
  AssetStatusChip,
  ItemStatusChip,
  RescueAsset,
  RescueFormatsResponse,
  RescueItemDetail,
  RescueSense,
  RescueStatus,
  StrikeDots,
} from "../components/rescue";
import { Card, Empty, ErrorBox, LangBadge, Spinner } from "../components/ui";
import { fmtDateTime, fmtUsd } from "../format";
import { useApi } from "../hooks";

const inputCls =
  "w-full rounded border border-edge bg-surface-2 px-2 py-1 text-sm text-ink " +
  "placeholder:text-muted focus:outline-none focus:ring-1 focus:ring-accent";
const btnCls =
  "rounded border border-edge px-2.5 py-1 text-xs text-ink-2 transition-colors " +
  "hover:bg-surface-2 disabled:cursor-not-allowed disabled:opacity-40";

function emptySense(): RescueSense {
  return { label: "", gloss: "", example_tl: "", example_en: "" };
}

export default function RescueItem() {
  const { id } = useParams();
  const itemId = Number(id);
  const [refreshKey, setRefreshKey] = useState(0);
  const { data, error, loading } = useApi<RescueItemDetail>(`/rescue/item/${itemId}`, {
    refresh: refreshKey,
  });
  const meta = useApi<RescueFormatsResponse>("/rescue/formats");

  // -- item head editing ----------------------------------------------------
  const [status, setStatus] = useState<RescueStatus>("candidate");
  const [strike, setStrike] = useState(1);
  const [anchor, setAnchor] = useState("");
  const [gloss, setGloss] = useState("");
  const [savingItem, setSavingItem] = useState(false);
  const [itemMsg, setItemMsg] = useState<string | null>(null);

  // -- senses editor --------------------------------------------------------
  const [senses, setSenses] = useState<RescueSense[]>([]);
  const [savingSenses, setSavingSenses] = useState(false);
  const [sensesMsg, setSensesMsg] = useState<string | null>(null);

  // -- generate panel -------------------------------------------------------
  const [genFormat, setGenFormat] = useState("comic");
  const [genProvider, setGenProvider] = useState("nano-banana");
  const [genPrompt, setGenPrompt] = useState("");
  const [generating, setGenerating] = useState(false);
  const [genError, setGenError] = useState<unknown>(null);

  // -- per-asset verdicts ---------------------------------------------------
  const [notes, setNotes] = useState<Record<number, string>>({});
  const [verdictBusy, setVerdictBusy] = useState<number | null>(null);
  const [verdictError, setVerdictError] = useState<unknown>(null);

  useEffect(() => {
    if (!data) return;
    setStatus(data.item.status);
    setStrike(data.item.strike);
    setAnchor(data.item.anchor ?? "");
    setGloss(data.item.gloss ?? "");
    setSenses(data.senses.length ? data.senses : []);
  }, [data]);

  useEffect(() => {
    if (!data) return;
    const spec = data.prompts[genFormat];
    setGenPrompt(spec?.prompt ?? "");
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [genFormat, data]);

  const assetsByFormat = useMemo(() => {
    const groups: Record<string, RescueAsset[]> = {};
    for (const a of data?.assets ?? []) (groups[a.format] ??= []).push(a);
    return groups;
  }, [data]);

  if (loading && !data) return <Spinner />;
  if (error) return <ErrorBox error={error} />;
  if (!data) return null;

  const item = data.item;
  const providers = meta.data?.providers ?? [];
  const imageFormats = meta.data?.image_formats ?? [];
  const providerSpec = providers.find((p) => p.key === genProvider);
  const promptSpec = data.prompts[genFormat];
  const snapshot = item.struggle_snapshot;

  const refresh = () => setRefreshKey((v) => v + 1);

  const saveItem = async () => {
    setSavingItem(true);
    setItemMsg(null);
    try {
      await adminCall(`/admin/rescue/item/${itemId}`, {
        body: { status, strike, anchor, gloss },
      });
      setItemMsg("saved ✓");
      refresh();
    } catch (e) {
      setItemMsg(String(e));
    } finally {
      setSavingItem(false);
    }
  };

  const saveSenses = async () => {
    setSavingSenses(true);
    setSensesMsg(null);
    try {
      await adminCall(`/admin/rescue/item/${itemId}`, {
        body: {
          senses: senses.map(({ label, gloss: g, example_tl, example_en }) => ({
            label,
            gloss: g,
            example_tl,
            example_en,
          })),
        },
      });
      setSensesMsg("saved ✓");
      refresh();
    } catch (e) {
      setSensesMsg(String(e));
    } finally {
      setSavingSenses(false);
    }
  };

  const generate = async () => {
    setGenerating(true);
    setGenError(null);
    try {
      await adminCall("/admin/rescue/generate", {
        body: {
          item_id: itemId,
          format: genFormat,
          provider: genProvider,
          prompt: genPrompt,
        },
      });
      refresh();
    } catch (e) {
      setGenError(e);
    } finally {
      setGenerating(false);
    }
  };

  const verdict = async (asset: RescueAsset, v: "approved" | "rejected") => {
    setVerdictBusy(asset.id);
    setVerdictError(null);
    try {
      await adminCall(`/admin/rescue/asset/${asset.id}/verdict`, {
        body: { status: v, note: notes[asset.id] ?? "" },
      });
      refresh();
    } catch (e) {
      setVerdictError(e);
    } finally {
      setVerdictBusy(null);
    }
  };

  return (
    <div className="flex flex-col gap-4">
      <div>
        <Link to="/rescue" className="text-xs text-muted hover:text-ink">
          ← Rescue Lab
        </Link>
        <div className="mt-1 flex flex-wrap items-center gap-3">
          <h1 className="text-xl font-bold">{item.idiom}</h1>
          <LangBadge lang={item.lang} />
          <ItemStatusChip status={item.status} />
          <StrikeDots strike={item.strike} />
          <span className="tnum text-xs text-muted">spend {fmtUsd(item.spend)}</span>
          {item.glyph_asset_id != null && (
            <span className="text-xs text-accent" title="permanent glyph pinned">
              ◈ glyph #{item.glyph_asset_id}
            </span>
          )}
        </div>
        {snapshot && (
          <div className="mt-1 text-xs text-muted">
            fails: <span className="tnum">{snapshot.fails_today ?? 0}</span> today ·{" "}
            <span className="tnum">{snapshot.fails_14d ?? 0}</span> in 14d
            {(snapshot.failed_sentences?.length ?? 0) > 0 && (
              <span> · failed on: “{snapshot.failed_sentences![0]}”</span>
            )}
          </div>
        )}
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <Card
          title="Item"
          aside={
            <div className="flex items-center gap-2">
              {itemMsg && <span className="text-xs">{itemMsg}</span>}
              <button type="button" onClick={() => void saveItem()} disabled={savingItem} className={btnCls}>
                {savingItem ? "saving…" : "Save"}
              </button>
            </div>
          }
        >
          <div className="flex flex-col gap-3">
            <div className="flex gap-3">
              <label className="flex flex-1 flex-col gap-1 text-xs text-muted">
                status
                <select
                  value={status}
                  onChange={(e) => setStatus(e.target.value as RescueStatus)}
                  className={inputCls}
                >
                  <option value="candidate">candidate</option>
                  <option value="active">active</option>
                  <option value="retired">retired</option>
                </select>
              </label>
              <label className="flex flex-1 flex-col gap-1 text-xs text-muted">
                strike (escalation ladder)
                <select
                  value={strike}
                  onChange={(e) => setStrike(Number(e.target.value))}
                  className={inputCls}
                >
                  <option value={1}>1 — comic + sentences</option>
                  <option value={2}>2 — switch encoding axis</option>
                  <option value={3}>3 — personal-max</option>
                </select>
              </label>
            </div>
            <label className="flex flex-col gap-1 text-xs text-muted">
              gloss
              <input value={gloss} onChange={(e) => setGloss(e.target.value)} className={inputCls} />
            </label>
            <label className="flex flex-col gap-1 text-xs text-muted">
              anchor (mnemonic hook — feeds the prompt templates)
              <textarea
                value={anchor}
                onChange={(e) => setAnchor(e.target.value)}
                rows={3}
                className={inputCls}
              />
            </label>
          </div>
        </Card>

        <Card
          title={
            <>
              Senses{" "}
              <span className="font-normal text-muted">
                — polysemy rule: every door needs gloss + micro-example
              </span>
            </>
          }
          aside={
            <div className="flex items-center gap-2">
              {sensesMsg && <span className="text-xs">{sensesMsg}</span>}
              <button
                type="button"
                onClick={() => setSenses((s) => [...s, emptySense()])}
                className={btnCls}
              >
                + sense
              </button>
              <button
                type="button"
                onClick={() => void saveSenses()}
                disabled={savingSenses}
                className={btnCls}
              >
                {savingSenses ? "saving…" : "Save senses"}
              </button>
            </div>
          }
        >
          {senses.length === 0 ? (
            <Empty>
              No senses. A polysemy-map asset cannot be approved until the item has ≥ 2
              fully-taught senses.
            </Empty>
          ) : (
            <div className="flex flex-col gap-3">
              {senses.map((s, i) => (
                <div key={i} className="rounded border border-edge p-2.5">
                  <div className="mb-2 flex items-center justify-between">
                    <span className="text-xs font-semibold text-muted">door {i + 1}</span>
                    <button
                      type="button"
                      onClick={() => setSenses((all) => all.filter((_, j) => j !== i))}
                      className="text-xs text-muted hover:text-critical"
                    >
                      remove
                    </button>
                  </div>
                  <div className="grid grid-cols-2 gap-2">
                    <input
                      placeholder="label (en el suelo)"
                      value={s.label}
                      onChange={(e) =>
                        setSenses((all) =>
                          all.map((x, j) => (j === i ? { ...x, label: e.target.value } : x)),
                        )
                      }
                      className={inputCls}
                    />
                    <input
                      placeholder="gloss (lying around, abandoned)"
                      value={s.gloss}
                      onChange={(e) =>
                        setSenses((all) =>
                          all.map((x, j) => (j === i ? { ...x, gloss: e.target.value } : x)),
                        )
                      }
                      className={inputCls}
                    />
                    <input
                      placeholder="micro-example (target lang)"
                      value={s.example_tl}
                      onChange={(e) =>
                        setSenses((all) =>
                          all.map((x, j) => (j === i ? { ...x, example_tl: e.target.value } : x)),
                        )
                      }
                      className={inputCls}
                    />
                    <input
                      placeholder="micro-example (English)"
                      value={s.example_en}
                      onChange={(e) =>
                        setSenses((all) =>
                          all.map((x, j) => (j === i ? { ...x, example_en: e.target.value } : x)),
                        )
                      }
                      className={inputCls}
                    />
                  </div>
                </div>
              ))}
            </div>
          )}
        </Card>
      </div>

      <Card
        title="Generate asset"
        aside={
          providerSpec && (
            <span className="tnum text-xs">
              estimated cost: <span className="text-ink">{fmtUsd(providerSpec.usd_per_image)}</span>{" "}
              per image
            </span>
          )
        }
      >
        <div className="flex flex-col gap-3">
          <div className="flex flex-wrap gap-3">
            <label className="flex flex-col gap-1 text-xs text-muted">
              format
              <select
                value={genFormat}
                onChange={(e) => setGenFormat(e.target.value)}
                className={inputCls}
              >
                {imageFormats.map((f) => (
                  <option key={f} value={f}>
                    {f}
                  </option>
                ))}
              </select>
            </label>
            <label className="flex flex-col gap-1 text-xs text-muted">
              provider / model
              <select
                value={genProvider}
                onChange={(e) => setGenProvider(e.target.value)}
                className={inputCls}
              >
                {providers.map((p) => (
                  <option key={p.key} value={p.key}>
                    {p.key} · {p.model} · {fmtUsd(p.usd_per_image)}/img
                  </option>
                ))}
              </select>
            </label>
            <div className="flex flex-1 items-end justify-end">
              <button
                type="button"
                onClick={() => void generate()}
                disabled={generating || !genPrompt.trim() || !!promptSpec?.error}
                className={btnCls}
              >
                {generating ? "generating…" : `Generate (${fmtUsd(providerSpec?.usd_per_image)})`}
              </button>
            </div>
          </div>
          {promptSpec?.error ? (
            <div className="rounded border border-warning/40 px-3 py-2 text-xs text-warning">
              {promptSpec.error}
            </div>
          ) : (
            <label className="flex flex-col gap-1 text-xs text-muted">
              prompt (prefilled from the format template + this item's fields)
              <textarea
                value={genPrompt}
                onChange={(e) => setGenPrompt(e.target.value)}
                rows={6}
                className={`${inputCls} font-mono text-xs`}
              />
            </label>
          )}
          {genError != null && <ErrorBox error={genError} />}
        </div>
      </Card>

      {verdictError != null && <ErrorBox error={verdictError} />}

      {Object.keys(assetsByFormat).length === 0 ? (
        <Card>
          <Empty>No assets yet — generate one above.</Empty>
        </Card>
      ) : (
        Object.entries(assetsByFormat).map(([format, assets]) => (
          <Card
            key={format}
            title={
              <>
                {format}{" "}
                <span className="font-normal text-muted">
                  — {assets.length} asset{assets.length === 1 ? "" : "s"}, side-by-side
                </span>
              </>
            }
          >
            <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
              {assets.map((a) => (
                <div key={a.id} className="flex flex-col gap-2 rounded border border-edge p-3">
                  <AssetImage assetId={a.id} alt={`${format} for ${item.idiom}`} />
                  <div className="flex flex-wrap items-center gap-x-3 gap-y-1 text-xs text-muted">
                    <AssetStatusChip status={a.status} />
                    <span>{a.provider}</span>
                    <span className="font-mono">{a.model}</span>
                    <span className="tnum">{fmtUsd(a.cost_usd)}</span>
                    <span className="tnum">{fmtDateTime(a.created_at)}</span>
                    {item.glyph_asset_id === a.id && (
                      <span className="text-accent" title="pinned as the permanent glyph">
                        ◈ glyph
                      </span>
                    )}
                  </div>
                  {a.verdict_note && (
                    <div className="text-xs italic text-ink-2">“{a.verdict_note}”</div>
                  )}
                  {a.prompt && (
                    <details className="text-xs text-muted">
                      <summary className="cursor-pointer hover:text-ink">prompt</summary>
                      <pre className="mt-1 whitespace-pre-wrap font-mono text-[11px]">
                        {a.prompt}
                      </pre>
                    </details>
                  )}
                  <div className="mt-auto flex items-center gap-2">
                    <input
                      placeholder="verdict note…"
                      value={notes[a.id] ?? ""}
                      onChange={(e) => setNotes((n) => ({ ...n, [a.id]: e.target.value }))}
                      className={`${inputCls} flex-1`}
                    />
                    <button
                      type="button"
                      onClick={() => void verdict(a, "approved")}
                      disabled={verdictBusy !== null || a.status === "approved"}
                      className={`${btnCls} text-good`}
                    >
                      {verdictBusy === a.id ? "…" : "✓"}
                    </button>
                    <button
                      type="button"
                      onClick={() => void verdict(a, "rejected")}
                      disabled={verdictBusy !== null || a.status === "rejected"}
                      className={`${btnCls} text-critical`}
                    >
                      {verdictBusy === a.id ? "…" : "✕"}
                    </button>
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
