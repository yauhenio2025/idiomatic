// Hand-rolled SVG charts following the dataviz mark specs: thin marks,
// 2px surface gaps between stacked segments, 4px rounded data-ends,
// hairline grid, recessive axes, hover tooltips, legend for >=2 series.
// Series color follows the language (fixed slots), never the rank.

import { ReactNode, useMemo, useRef, useState } from "react";
import { langColor } from "../api";
import { langName } from "../format";

// ---- tooltip plumbing -------------------------------------------------------

interface TipState {
  x: number;
  y: number;
  body: ReactNode;
}

function useTip() {
  const [tip, setTip] = useState<TipState | null>(null);
  const ref = useRef<HTMLDivElement>(null);
  const show = (e: React.MouseEvent, body: ReactNode) => {
    const rect = ref.current?.getBoundingClientRect();
    if (!rect) return;
    setTip({ x: e.clientX - rect.left, y: e.clientY - rect.top, body });
  };
  const hide = () => setTip(null);
  return { tip, ref, show, hide };
}

function TipBox({ tip }: { tip: TipState | null }) {
  if (!tip) return null;
  return (
    <div
      className="pointer-events-none absolute z-10 max-w-64 rounded-md border border-edge bg-surface-2 px-2.5 py-1.5 text-xs shadow-lg"
      style={{
        left: Math.min(tip.x + 12, 9999),
        top: tip.y + 12,
      }}
    >
      {tip.body}
    </div>
  );
}

export function Legend({ langs }: { langs: string[] }) {
  return (
    <div className="mt-2 flex flex-wrap gap-x-4 gap-y-1">
      {langs.map((l) => (
        <span key={l} className="inline-flex items-center gap-1.5 text-xs text-ink-2">
          <span
            className="inline-block h-2.5 w-2.5 rounded-[3px]"
            style={{ background: langColor(l) }}
          />
          {langName(l)}
        </span>
      ))}
    </div>
  );
}

// ---- stacked daily bars -----------------------------------------------------

export interface DayStack {
  day: string; // ISO date
  counts: Record<string, number>; // lang -> n
}

export function StackedBars({
  data,
  langs,
  height = 180,
  unit = "decks",
}: {
  data: DayStack[];
  langs: string[];
  height?: number;
  unit?: string;
}) {
  const { tip, ref, show, hide } = useTip();
  const W = 720;
  const P = { l: 28, r: 8, t: 8, b: 20 };
  const innerW = W - P.l - P.r;
  const innerH = height - P.t - P.b;
  const max = Math.max(1, ...data.map((d) => langs.reduce((s, l) => s + (d.counts[l] ?? 0), 0)));
  const slot = innerW / Math.max(1, data.length);
  const barW = Math.max(3, Math.min(18, slot - 2));
  const yTicks = max <= 4 ? max : 4;

  return (
    <div ref={ref} className="relative">
      <svg viewBox={`0 0 ${W} ${height}`} className="w-full" role="img">
        {Array.from({ length: yTicks + 1 }, (_, i) => {
          const v = (max / yTicks) * i;
          const y = P.t + innerH - (v / max) * innerH;
          return (
            <g key={i}>
              <line x1={P.l} x2={W - P.r} y1={y} y2={y} stroke="var(--grid)" strokeWidth={1} />
              <text x={P.l - 6} y={y + 3} textAnchor="end" fontSize={9} fill="var(--ink-muted)" className="tnum">
                {Math.round(v)}
              </text>
            </g>
          );
        })}
        {data.map((d, i) => {
          const x = P.l + i * slot + (slot - barW) / 2;
          let yCursor = P.t + innerH;
          const total = langs.reduce((s, l) => s + (d.counts[l] ?? 0), 0);
          const segs = langs
            .filter((l) => (d.counts[l] ?? 0) > 0)
            .map((l) => {
              const h = ((d.counts[l] ?? 0) / max) * innerH;
              yCursor -= h;
              return { lang: l, y: yCursor, h };
            });
          return (
            <g
              key={d.day}
              onMouseMove={(e) =>
                show(
                  e,
                  <div>
                    <div className="mb-0.5 font-medium text-ink">{d.day.slice(5)}</div>
                    {segs.length === 0 && <div className="text-muted">no {unit}</div>}
                    {segs.map((s) => (
                      <div key={s.lang} className="flex items-center gap-1.5">
                        <span className="inline-block h-2 w-2 rounded-[2px]" style={{ background: langColor(s.lang) }} />
                        <span className="text-ink-2">{langName(s.lang)}</span>
                        <span className="tnum ml-auto pl-3 text-ink">{d.counts[s.lang]}</span>
                      </div>
                    ))}
                    {segs.length > 1 && (
                      <div className="mt-0.5 border-t border-edge pt-0.5 text-ink-2">
                        total <span className="tnum text-ink">{total}</span>
                      </div>
                    )}
                  </div>,
                )
              }
              onMouseLeave={hide}
            >
              {/* invisible hit target wider than the mark */}
              <rect x={P.l + i * slot} y={P.t} width={slot} height={innerH} fill="transparent" />
              {segs.map((s, j) => {
                const isTop = j === segs.length - 1;
                const gap = j > 0 ? 1 : 0; // 2px total gap between segments (1px each side)
                return (
                  <rect
                    key={s.lang}
                    x={x}
                    y={s.y + gap}
                    width={barW}
                    height={Math.max(1, s.h - gap)}
                    rx={isTop ? 2.5 : 0}
                    fill={langColor(s.lang)}
                  />
                );
              })}
            </g>
          );
        })}
        <line x1={P.l} x2={W - P.r} y1={P.t + innerH} y2={P.t + innerH} stroke="var(--baseline)" strokeWidth={1} />
        {data.map((d, i) =>
          i % Math.ceil(data.length / 8) === 0 ? (
            <text
              key={d.day}
              x={P.l + i * slot + slot / 2}
              y={height - 6}
              textAnchor="middle"
              fontSize={9}
              fill="var(--ink-muted)"
            >
              {d.day.slice(5)}
            </text>
          ) : null,
        )}
      </svg>
      <TipBox tip={tip} />
      <Legend langs={langs} />
    </div>
  );
}

// ---- cumulative multi-line --------------------------------------------------

export interface GrowthPoint {
  day: string;
  totals: Record<string, number>; // lang -> cumulative
}

export function MultiLine({
  data,
  langs,
  height = 200,
}: {
  data: GrowthPoint[];
  langs: string[];
  height?: number;
}) {
  const { tip, ref, show, hide } = useTip();
  const [hoverI, setHoverI] = useState<number | null>(null);
  const W = 720;
  const P = { l: 34, r: 46, t: 8, b: 20 };
  const innerW = W - P.l - P.r;
  const innerH = height - P.t - P.b;
  const max = Math.max(1, ...data.flatMap((d) => langs.map((l) => d.totals[l] ?? 0)));
  const x = (i: number) => P.l + (data.length <= 1 ? 0 : (i / (data.length - 1)) * innerW);
  const y = (v: number) => P.t + innerH - (v / max) * innerH;

  const paths = useMemo(
    () =>
      langs.map((l) => ({
        lang: l,
        d: data
          .map((pt, i) => `${i === 0 ? "M" : "L"}${x(i).toFixed(1)},${y(pt.totals[l] ?? 0).toFixed(1)}`)
          .join(" "),
        last: data.length ? (data[data.length - 1].totals[l] ?? 0) : 0,
      })),
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [data, langs, max],
  );

  const onMove = (e: React.MouseEvent<SVGSVGElement>) => {
    const svg = e.currentTarget;
    const rect = svg.getBoundingClientRect();
    const px = ((e.clientX - rect.left) / rect.width) * W;
    const i = Math.round(((px - P.l) / innerW) * (data.length - 1));
    if (i < 0 || i >= data.length) {
      setHoverI(null);
      hide();
      return;
    }
    setHoverI(i);
    const pt = data[i];
    show(
      e,
      <div>
        <div className="mb-0.5 font-medium text-ink">{pt.day.slice(5)}</div>
        {langs.map((l) => (
          <div key={l} className="flex items-center gap-1.5">
            <span className="inline-block h-2 w-2 rounded-[2px]" style={{ background: langColor(l) }} />
            <span className="text-ink-2">{langName(l)}</span>
            <span className="tnum ml-auto pl-3 text-ink">{pt.totals[l] ?? 0}</span>
          </div>
        ))}
      </div>,
    );
  };

  return (
    <div ref={ref} className="relative">
      <svg
        viewBox={`0 0 ${W} ${height}`}
        className="w-full"
        role="img"
        onMouseMove={onMove}
        onMouseLeave={() => {
          setHoverI(null);
          hide();
        }}
      >
        {Array.from({ length: 5 }, (_, i) => {
          const v = (max / 4) * i;
          const yy = y(v);
          return (
            <g key={i}>
              <line x1={P.l} x2={W - P.r} y1={yy} y2={yy} stroke="var(--grid)" strokeWidth={1} />
              <text x={P.l - 6} y={yy + 3} textAnchor="end" fontSize={9} fill="var(--ink-muted)" className="tnum">
                {Math.round(v)}
              </text>
            </g>
          );
        })}
        {hoverI !== null && (
          <line x1={x(hoverI)} x2={x(hoverI)} y1={P.t} y2={P.t + innerH} stroke="var(--baseline)" strokeWidth={1} />
        )}
        {paths.map((p) => (
          <path key={p.lang} d={p.d} fill="none" stroke={langColor(p.lang)} strokeWidth={2} strokeLinejoin="round" />
        ))}
        {hoverI !== null &&
          langs.map((l) => (
            <circle
              key={l}
              cx={x(hoverI)}
              cy={y(data[hoverI].totals[l] ?? 0)}
              r={4}
              fill={langColor(l)}
              stroke="var(--surface)"
              strokeWidth={2}
            />
          ))}
        {/* direct labels at line ends — text in ink, identity via the dot */}
        {paths.map((p, i) => {
          const yy = y(p.last);
          // naive collision nudge
          const overlaps = paths.filter((q, j) => j < i && Math.abs(y(q.last) - yy) < 11).length;
          return (
            <g key={p.lang}>
              <circle cx={W - P.r + 6} cy={yy + overlaps * 11} r={3} fill={langColor(p.lang)} />
              <text x={W - P.r + 12} y={yy + overlaps * 11 + 3} fontSize={9} fill="var(--ink-2)" className="tnum">
                {p.last}
              </text>
            </g>
          );
        })}
        <line x1={P.l} x2={W - P.r} y1={P.t + innerH} y2={P.t + innerH} stroke="var(--baseline)" strokeWidth={1} />
        {data.map((d, i) =>
          data.length > 0 && i % Math.ceil(data.length / 8) === 0 ? (
            <text key={d.day} x={x(i)} y={height - 6} textAnchor="middle" fontSize={9} fill="var(--ink-muted)">
              {d.day.slice(5)}
            </text>
          ) : null,
        )}
      </svg>
      <TipBox tip={tip} />
      <Legend langs={langs} />
    </div>
  );
}

// ---- horizontal funnel / reason bars ---------------------------------------

export interface FunnelRow {
  label: string;
  value: number;
  color?: string; // defaults to sequential accent
  sub?: string;
}

export function HBars({ rows }: { rows: FunnelRow[] }) {
  const max = Math.max(1, ...rows.map((r) => r.value));
  return (
    <div className="flex flex-col gap-1.5">
      {rows.map((r) => (
        <div key={r.label} className="grid grid-cols-[9.5rem_1fr_3.5rem] items-center gap-2">
          <div className="truncate text-xs text-ink-2" title={r.sub ?? r.label}>
            {r.label}
          </div>
          <div className="h-4 rounded-r-[4px]" style={{ width: "100%" }}>
            <div
              className="h-4 rounded-r-[4px]"
              style={{
                width: `${Math.max(0.5, (r.value / max) * 100)}%`,
                background: r.color ?? "var(--accent)",
                minWidth: r.value > 0 ? 3 : 0,
              }}
            />
          </div>
          <div className="tnum text-right text-xs text-ink">{r.value}</div>
        </div>
      ))}
    </div>
  );
}
