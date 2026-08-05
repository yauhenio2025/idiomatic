import { useEffect, useState } from "react";
import { assetFileUrl } from "../api";

// ---- shared Rescue Lab types (mirror /ui/api/rescue/*) ---------------------

export type RescueStatus = "candidate" | "active" | "retired";
export type AssetStatus = "draft" | "approved" | "rejected";

export interface StruggleSnapshot {
  fails_today?: number;
  fails_14d?: number;
  failed_sentences?: string[];
}

export interface RescueItemRow {
  id: number;
  lang: string;
  idiom: string;
  gloss: string | null;
  anchor: string | null;
  status: RescueStatus;
  strike: number;
  glyph_asset_id: number | null;
  struggle_snapshot: StruggleSnapshot | null;
  created_at: string;
  updated_at: string;
  n_assets: number;
  n_approved: number;
  n_draft: number;
  n_senses: number;
  spend: number;
}

export interface RescueSense {
  id?: number;
  label: string;
  gloss: string;
  example_tl: string;
  example_en: string;
  ord?: number;
}

export interface RescueAsset {
  id: number;
  item_id: number;
  format: string;
  provider: string | null;
  model: string | null;
  prompt: string | null;
  file_path: string | null;
  mime: string | null;
  cost_usd: number;
  status: AssetStatus;
  verdict_note: string | null;
  created_at: string;
}

export interface RescueItemDetail {
  item: RescueItemRow & { spend: number };
  senses: RescueSense[];
  assets: RescueAsset[];
  prompts: Record<string, { prompt?: string; error?: string }>;
}

export interface FormatSpec {
  key: string;
  name: string;
  kind: "image" | "manual";
  when_to_use: string;
  rules: string[];
  template: string | null;
  placeholders: Record<string, string>;
}

export interface ProviderSpec {
  key: string;
  api: string;
  model: string;
  label: string;
  usd_per_image: number;
}

export interface RescueFormatsResponse {
  formats: FormatSpec[];
  providers: ProviderSpec[];
  image_formats: string[];
}

export interface CostsResponse {
  this_month: number;
  all_time: number;
  n_calls: number;
  by_day: { day: string; usd: number; n: number }[];
  by_provider: {
    provider: string;
    model: string;
    usd: number;
    usd_month: number | null;
    n: number;
  }[];
  by_format: { format: string; usd: number; n: number }[];
}

// ---- small shared UI ------------------------------------------------------

const ITEM_STATUS_CLS: Record<RescueStatus, string> = {
  candidate: "text-ink-2",
  active: "text-good",
  retired: "text-muted",
};

export function ItemStatusChip({ status }: { status: RescueStatus }) {
  return (
    <span className={`inline-flex items-center gap-1.5 text-xs ${ITEM_STATUS_CLS[status]}`}>
      <span
        className={`h-1.5 w-1.5 rounded-full ${
          status === "active" ? "bg-good" : status === "candidate" ? "bg-ink-2" : "bg-muted"
        }`}
      />
      {status}
    </span>
  );
}

const ASSET_STATUS_CLS: Record<AssetStatus, string> = {
  draft: "text-warning",
  approved: "text-good",
  rejected: "text-critical",
};

export function AssetStatusChip({ status }: { status: AssetStatus }) {
  const icon = status === "approved" ? "✓" : status === "rejected" ? "✕" : "◌";
  return (
    <span className={`inline-flex items-center gap-1 text-xs ${ASSET_STATUS_CLS[status]}`}>
      <span>{icon}</span>
      {status}
    </span>
  );
}

export function StrikeDots({ strike }: { strike: number }) {
  return (
    <span className="tnum text-xs text-ink-2" title={`escalation strike ${strike} of 3`}>
      {"●".repeat(strike)}
      <span className="text-muted">{"○".repeat(Math.max(0, 3 - strike))}</span>
    </span>
  );
}

// Authed blob fetch (image elements can't send headers), cached per asset.
export function AssetImage({ assetId, alt }: { assetId: number; alt: string }) {
  const [url, setUrl] = useState<string | null>(null);
  const [failed, setFailed] = useState(false);

  useEffect(() => {
    let alive = true;
    assetFileUrl(assetId)
      .then((u) => alive && setUrl(u))
      .catch(() => alive && setFailed(true));
    return () => {
      alive = false;
    };
  }, [assetId]);

  if (failed) {
    return (
      <div className="flex h-40 items-center justify-center rounded border border-edge text-xs text-critical">
        ✕ couldn't load asset
      </div>
    );
  }
  if (!url) {
    return (
      <div className="flex h-40 items-center justify-center rounded border border-edge text-xs text-muted">
        loading…
      </div>
    );
  }
  return (
    <img
      src={url}
      alt={alt}
      title="open full size"
      className="max-h-72 w-full cursor-zoom-in rounded border border-edge object-contain"
      onClick={() => window.open(url, "_blank")}
    />
  );
}
