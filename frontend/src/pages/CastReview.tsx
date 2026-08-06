import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { adminCall, adminUpload, castAssetUrl } from "../api";
import { Card, Empty, ErrorBox, LangBadge, Spinner } from "../components/ui";
import { useApi } from "../hooks";

// Fast-forward review of Asset Factory cast sheets: sheet + ref photo side
// by side, keyboard driven (← → navigate, O = OK, R = remake). Designed to
// be reused whenever new characters are enrolled.

type CastRow = {
  slug: string;
  real_name: string | null;
  lang: string | null;
  role_key: string | null;
  famous_source: string | null;
  survival_prior: string | null;
  exclusion_checked: boolean;
  exclusion_verdict: string | null;
  status: string;
  review_flag: "ok" | "remake" | null;
  review_note: string | null;
  has_ref: boolean;
  has_sheet: boolean;
  sheet_hash: string | null;
  updated_at: string;
};

type CastResponse = {
  rows: CastRow[];
  counts: { total: number; unreviewed: number; remake: number; ok: number };
};

function AuthedImg({
  slug,
  kind,
  version,
  className,
}: {
  slug: string;
  kind: "ref" | "sheet";
  version: string;
  className?: string;
}) {
  const [url, setUrl] = useState<string | null>(null);
  const [failed, setFailed] = useState(false);
  useEffect(() => {
    let alive = true;
    setUrl(null);
    setFailed(false);
    castAssetUrl(slug, kind, version)
      .then((u) => alive && setUrl(u))
      .catch(() => alive && setFailed(true));
    return () => {
      alive = false;
    };
  }, [slug, kind, version]);
  if (failed)
    return (
      <div className="flex h-40 items-center justify-center text-xs text-muted">
        no {kind} uploaded
      </div>
    );
  if (!url) return <Spinner label={`${kind}…`} />;
  return <img src={url} className={className} alt={`${slug} ${kind}`} />;
}

export default function CastReview() {
  const [refreshKey, setRefreshKey] = useState(0);
  const { data, error, loading } = useApi<CastResponse>("/factory/cast", {
    refresh: refreshKey,
  });
  const reload = useCallback(async () => setRefreshKey((v) => v + 1), []);
  const [idx, setIdx] = useState(0);
  const [note, setNote] = useState("");
  const [busy, setBusy] = useState(false);
  const [toast, setToast] = useState<string | null>(null);
  const fileRef = useRef<HTMLInputElement>(null);
  const noteRef = useRef<HTMLTextAreaElement>(null);

  const rows = useMemo(() => data?.rows ?? [], [data]);
  const row = rows[Math.min(idx, Math.max(rows.length - 1, 0))];

  useEffect(() => {
    setNote(row?.review_note ?? "");
  }, [row?.slug]); // eslint-disable-line react-hooks/exhaustive-deps

  const flash = (msg: string) => {
    setToast(msg);
    window.setTimeout(() => setToast(null), 1500);
  };

  const verdict = useCallback(
    async (flag: "ok" | "remake" | null) => {
      if (!row || busy) return;
      setBusy(true);
      try {
        await adminCall(`/admin/factory/cast/${row.slug}/review`, {
          body: { flag, note },
        });
        flash(flag === "ok" ? "✓ OK" : flag === "remake" ? "⚑ remake" : "cleared");
        await reload();
        setIdx((i) => Math.min(i + 1, rows.length - 1));
      } finally {
        setBusy(false);
      }
    },
    [row, note, busy, reload, rows.length],
  );

  const saveNote = useCallback(async () => {
    if (!row || busy) return;
    setBusy(true);
    try {
      await adminCall(`/admin/factory/cast/${row.slug}/review`, {
        body: { note },
      });
      flash("note saved");
      await reload();
    } finally {
      setBusy(false);
    }
  }, [row, note, busy, reload]);

  const uploadRef = useCallback(
    async (file: File) => {
      if (!row) return;
      setBusy(true);
      try {
        const form = new FormData();
        form.append("ref", file);
        await adminUpload(`/admin/factory/cast/${row.slug}/ref`, form);
        // a new ref implies the sheet needs remaking
        await adminCall(`/admin/factory/cast/${row.slug}/review`, {
          body: { flag: "remake", note: note || "new ref uploaded" },
        });
        flash("ref replaced + flagged remake");
        await reload();
      } finally {
        setBusy(false);
      }
    },
    [row, note, reload],
  );

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (document.activeElement === noteRef.current) return;
      if (e.key === "ArrowRight") setIdx((i) => Math.min(i + 1, rows.length - 1));
      else if (e.key === "ArrowLeft") setIdx((i) => Math.max(i - 1, 0));
      else if (e.key === "o" || e.key === "O") void verdict("ok");
      else if (e.key === "r" || e.key === "R") void verdict("remake");
      else return;
      e.preventDefault();
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [rows.length, verdict]);

  if (loading && !data) return <Spinner />;
  if (error) return <ErrorBox error={error} />;
  if (!data || rows.length === 0)
    return <Empty>No cast enrolled yet — run the sync script on the render box.</Empty>;

  const c = data.counts;
  const version = row.sheet_hash ?? row.updated_at;

  return (
    <div className="flex flex-col gap-4">
      <div className="flex flex-wrap items-baseline gap-3">
        <h1 className="text-xl font-bold">Cast review</h1>
        <span className="text-xs text-muted">
          {idx + 1}/{c.total} · {c.unreviewed} unreviewed · {c.remake} remake ·{" "}
          {c.ok} ok — keys: ← → navigate, O = ok, R = remake
        </span>
        {toast && <span className="text-xs font-semibold">{toast}</span>}
      </div>

      <div className="flex flex-wrap items-center gap-2">
        <div className="flex flex-wrap items-baseline gap-2">
          <span className="text-lg font-semibold">
            {row.real_name ?? row.slug}
          </span>
          {row.lang && <LangBadge lang={row.lang} />}
          {row.role_key && (
            <span className="text-xs text-muted">{row.role_key}</span>
          )}
          {row.famous_source && (
            <span className="text-xs text-muted">· {row.famous_source}</span>
          )}
          {row.survival_prior && (
            <span className="text-xs text-muted">
              · survival {row.survival_prior}
            </span>
          )}
          <span className="text-xs text-muted">
            · {row.status}
            {row.review_flag ? ` · ${row.review_flag}` : " · unreviewed"}
          </span>
        </div>
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        <Card title="Sheet">
          {row.has_sheet ? (
            <AuthedImg
              slug={row.slug}
              kind="sheet"
              version={version}
              className="w-full rounded"
            />
          ) : (
            <Empty>not rendered yet</Empty>
          )}
        </Card>
        <Card title="Reference photo">
          {row.has_ref ? (
            <AuthedImg
              slug={row.slug}
              kind="ref"
              version={row.updated_at}
              className="w-full rounded"
            />
          ) : (
            <Empty>no ref on server</Empty>
          )}
          <div className="mt-2">
            <input
              ref={fileRef}
              type="file"
              accept="image/*"
              className="hidden"
              onChange={(e) => {
                const f = e.target.files?.[0];
                if (f) void uploadRef(f);
                e.target.value = "";
              }}
            />
            <button
              className="rounded border border-edge px-2 py-1 text-xs hover:bg-surface"
              disabled={busy}
              onClick={() => fileRef.current?.click()}
            >
              upload new ref photo
            </button>
          </div>
        </Card>
      </div>

      <Card title="Verdict">
        <div className="flex flex-wrap items-start gap-3">
          <button
            className="rounded bg-emerald-700 px-3 py-1.5 text-sm font-semibold text-white disabled:opacity-50"
            disabled={busy}
            onClick={() => void verdict("ok")}
          >
            OK (O)
          </button>
          <button
            className="rounded bg-amber-700 px-3 py-1.5 text-sm font-semibold text-white disabled:opacity-50"
            disabled={busy}
            onClick={() => void verdict("remake")}
          >
            Needs remake (R)
          </button>
          <button
            className="rounded border border-edge px-3 py-1.5 text-sm disabled:opacity-50"
            disabled={busy}
            onClick={() => void verdict(null)}
          >
            clear flag
          </button>
          <div className="flex min-w-64 flex-1 flex-col gap-1">
            <textarea
              ref={noteRef}
              className="w-full rounded border border-edge bg-transparent p-2 text-sm"
              rows={2}
              placeholder="quick comment (what's wrong / what to change)…"
              value={note}
              onChange={(e) => setNote(e.target.value)}
              onBlur={() => {
                if ((row.review_note ?? "") !== note) void saveNote();
              }}
            />
          </div>
        </div>
      </Card>

      <div className="flex flex-wrap gap-1">
        {rows.map((r, i) => (
          <button
            key={r.slug}
            title={`${r.real_name ?? r.slug}${r.review_flag ? ` (${r.review_flag})` : ""}`}
            onClick={() => setIdx(i)}
            className={`h-3 w-3 rounded-sm ${
              i === idx
                ? "ring-2 ring-offset-1"
                : ""
            } ${
              r.review_flag === "ok"
                ? "bg-emerald-600"
                : r.review_flag === "remake"
                  ? "bg-amber-600"
                  : "bg-edge"
            }`}
          />
        ))}
      </div>
    </div>
  );
}
