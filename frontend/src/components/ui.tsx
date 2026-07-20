import { ReactNode } from "react";
import { langColor } from "../api";
import { langName } from "../format";

export function Card({
  title,
  children,
  aside,
  className = "",
}: {
  title?: ReactNode;
  aside?: ReactNode;
  children: ReactNode;
  className?: string;
}) {
  return (
    <section
      className={`rounded-lg border border-edge bg-surface p-4 ${className}`}
    >
      {(title || aside) && (
        <div className="mb-3 flex items-baseline justify-between gap-3">
          {title && <h2 className="text-sm font-semibold text-ink">{title}</h2>}
          {aside && <div className="text-xs text-muted">{aside}</div>}
        </div>
      )}
      {children}
    </section>
  );
}

export function StatTile({
  label,
  value,
  sub,
  tone,
}: {
  label: string;
  value: ReactNode;
  sub?: ReactNode;
  tone?: "good" | "warning" | "critical";
}) {
  const toneClass =
    tone === "critical"
      ? "text-critical"
      : tone === "warning"
        ? "text-warning"
        : tone === "good"
          ? "text-good"
          : "text-ink";
  return (
    <div className="rounded-lg border border-edge bg-surface px-4 py-3">
      <div className="text-xs text-muted">{label}</div>
      <div className={`mt-1 text-2xl font-semibold ${toneClass}`}>{value}</div>
      {sub && <div className="mt-0.5 text-xs text-ink-2">{sub}</div>}
    </div>
  );
}

export function LangBadge({ lang }: { lang: string }) {
  return (
    <span className="inline-flex items-center gap-1.5 text-xs text-ink-2">
      <span
        className="inline-block h-2.5 w-2.5 rounded-[3px]"
        style={{ background: langColor(lang) }}
      />
      {langName(lang)}
    </span>
  );
}

const STATUS_META: Record<string, { icon: string; cls: string }> = {
  done: { icon: "✓", cls: "text-good" },
  queued: { icon: "•", cls: "text-ink-2" },
  processing: { icon: "▸", cls: "text-accent" },
  skipped: { icon: "–", cls: "text-muted" },
  failed: { icon: "✕", cls: "text-critical" },
  ok: { icon: "✓", cls: "text-good" },
};

export function StatusBadge({ status, label }: { status: string; label?: string }) {
  const meta = STATUS_META[status] ?? { icon: "•", cls: "text-muted" };
  return (
    <span className={`inline-flex items-center gap-1 text-xs ${meta.cls}`}>
      <span>{meta.icon}</span>
      {label ?? status}
    </span>
  );
}

export function Spinner({ label = "loading…" }: { label?: string }) {
  return <div className="py-10 text-center text-sm text-muted">{label}</div>;
}

export function ErrorBox({ error }: { error: unknown }) {
  return (
    <div className="rounded-md border border-critical/40 bg-surface px-4 py-3 text-sm text-critical">
      ✕ {String(error)}
    </div>
  );
}

export function Empty({ children }: { children: ReactNode }) {
  return <div className="py-8 text-center text-sm text-muted">{children}</div>;
}

export function Pager({
  total,
  limit,
  offset,
  onPage,
}: {
  total: number;
  limit: number;
  offset: number;
  onPage: (offset: number) => void;
}) {
  if (total <= limit) return null;
  const page = Math.floor(offset / limit) + 1;
  const pages = Math.ceil(total / limit);
  return (
    <div className="mt-3 flex items-center justify-between text-xs text-muted">
      <span className="tnum">
        {offset + 1}–{Math.min(offset + limit, total)} of {total}
      </span>
      <div className="flex gap-1">
        <button
          disabled={page <= 1}
          onClick={() => onPage(offset - limit)}
          className="rounded border border-edge px-2 py-1 text-ink-2 transition-colors hover:bg-surface-2 disabled:opacity-40"
        >
          ← prev
        </button>
        <button
          disabled={page >= pages}
          onClick={() => onPage(offset + limit)}
          className="rounded border border-edge px-2 py-1 text-ink-2 transition-colors hover:bg-surface-2 disabled:opacity-40"
        >
          next →
        </button>
      </div>
    </div>
  );
}

export function Th({ children, className = "" }: { children?: ReactNode; className?: string }) {
  return (
    <th
      className={`border-b border-baseline px-2 py-1.5 text-left text-xs font-medium text-muted ${className}`}
    >
      {children}
    </th>
  );
}

export function Td({ children, className = "" }: { children?: ReactNode; className?: string }) {
  return (
    <td className={`border-b border-grid px-2 py-1.5 align-top text-sm ${className}`}>
      {children}
    </td>
  );
}

export function YouTubeLink({ youtubeId, title }: { youtubeId: string; title?: string | null }) {
  return (
    <a
      href={`https://www.youtube.com/watch?v=${youtubeId}`}
      target="_blank"
      rel="noreferrer"
      className="text-ink underline decoration-baseline underline-offset-2 transition-colors hover:decoration-ink"
      title="open on YouTube"
    >
      {title || youtubeId}
    </a>
  );
}
