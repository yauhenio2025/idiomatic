// Thin fetch client. The admin token lives in localStorage and rides on
// every /ui/api call as X-Admin-Token; a 401 anywhere kicks back to login.

const TOKEN_KEY = "idiomatic_admin_token";

export function getToken(): string | null {
  return localStorage.getItem(TOKEN_KEY);
}

export function setToken(token: string) {
  localStorage.setItem(TOKEN_KEY, token);
}

export function clearToken() {
  localStorage.removeItem(TOKEN_KEY);
}

export class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

let onUnauthorized: (() => void) | null = null;
export function setUnauthorizedHandler(fn: () => void) {
  onUnauthorized = fn;
}

export async function api<T>(
  path: string,
  params?: Record<string, string | number | boolean | undefined | null>,
): Promise<T> {
  const url = new URL(`/ui/api${path}`, window.location.origin);
  if (params) {
    for (const [k, v] of Object.entries(params)) {
      if (v !== undefined && v !== null && v !== "") url.searchParams.set(k, String(v));
    }
  }
  const res = await fetch(url, {
    headers: { "X-Admin-Token": getToken() ?? "" },
  });
  if (res.status === 401) {
    onUnauthorized?.();
    throw new ApiError(401, "unauthorized");
  }
  if (!res.ok) {
    throw new ApiError(res.status, `${res.status} ${await res.text()}`);
  }
  return res.json();
}

// Admin actions (grammar generate/rebuild/top-up/unit edits) live under
// /admin/*, not /ui/api/* — same token, different prefix. The dashboard
// is read-only EXCEPT the grammar section (commission 2026-07-31).
export async function adminCall<T>(
  path: string,
  opts?: {
    method?: "GET" | "POST";
    params?: Record<string, string | number | boolean | undefined | null>;
    body?: unknown;
  },
): Promise<T> {
  const url = new URL(path, window.location.origin);
  if (opts?.params) {
    for (const [k, v] of Object.entries(opts.params)) {
      if (v !== undefined && v !== null && v !== "") url.searchParams.set(k, String(v));
    }
  }
  const res = await fetch(url, {
    method: opts?.method ?? "POST",
    headers: {
      "X-Admin-Token": getToken() ?? "",
      ...(opts?.body !== undefined ? { "Content-Type": "application/json" } : {}),
    },
    ...(opts?.body !== undefined ? { body: JSON.stringify(opts.body) } : {}),
  });
  if (res.status === 401) {
    onUnauthorized?.();
    throw new ApiError(401, "unauthorized");
  }
  if (!res.ok) {
    throw new ApiError(res.status, `${res.status} ${await res.text()}`);
  }
  return res.json();
}

// Audio is fetched as a blob (the <audio> element can't send headers) and
// cached as object URLs per path for the session.
const audioCache = new Map<string, string>();

export async function audioUrl(relPath: string): Promise<string> {
  const cached = audioCache.get(relPath);
  if (cached) return cached;
  const res = await fetch(`/ui/api/audio/${relPath}`, {
    headers: { "X-Admin-Token": getToken() ?? "" },
  });
  if (!res.ok) throw new ApiError(res.status, "audio fetch failed");
  const url = URL.createObjectURL(await res.blob());
  audioCache.set(relPath, url);
  return url;
}

// Rescue asset images ride the same authed-blob pattern (an <img> can't
// send the token header), cached per asset id for the session.
const assetCache = new Map<number, string>();

export async function assetFileUrl(assetId: number): Promise<string> {
  const cached = assetCache.get(assetId);
  if (cached) return cached;
  const res = await fetch(`/ui/api/rescue/asset-file/${assetId}`, {
    headers: { "X-Admin-Token": getToken() ?? "" },
  });
  if (!res.ok) throw new ApiError(res.status, "asset fetch failed");
  const url = URL.createObjectURL(await res.blob());
  assetCache.set(assetId, url);
  return url;
}

// Factory cast images: same authed-blob pattern, keyed by slug/kind plus a
// version salt (sheet_hash / updated_at) so re-uploads bust the cache.
const castAssetCache = new Map<string, string>();

export async function castAssetUrl(
  slug: string,
  kind: "ref" | "sheet",
  version: string,
): Promise<string> {
  const key = `${slug}/${kind}/${version}`;
  const cached = castAssetCache.get(key);
  if (cached) return cached;
  const res = await fetch(`/ui/api/factory/cast-asset/${slug}/${kind}`, {
    headers: { "X-Admin-Token": getToken() ?? "" },
  });
  if (!res.ok) throw new ApiError(res.status, "asset fetch failed");
  const url = URL.createObjectURL(await res.blob());
  castAssetCache.set(key, url);
  return url;
}

// Multipart admin upload (Cast Review ref replacement). No Content-Type
// header — the browser sets the multipart boundary itself.
export async function adminUpload<T>(path: string, form: FormData): Promise<T> {
  const res = await fetch(path, {
    method: "POST",
    headers: { "X-Admin-Token": getToken() ?? "" },
    body: form,
  });
  if (res.status === 401) {
    onUnauthorized?.();
    throw new ApiError(401, "unauthorized");
  }
  if (!res.ok) throw new ApiError(res.status, `${res.status} ${await res.text()}`);
  return res.json();
}

// ---- shared types ---------------------------------------------------------

export const LANG_COLORS: Record<string, string> = {
  de: "var(--lang-de)",
  es: "var(--lang-es)",
  fr: "var(--lang-fr)",
  it: "var(--lang-it)",
  pt: "var(--lang-pt)",
};

export const LANG_ORDER = ["de", "es", "fr", "it", "pt"];

export function langColor(lang: string): string {
  return LANG_COLORS[lang] ?? "var(--lang-other)";
}

export interface Example {
  ord: number;
  en_text: string;
  target_text: string;
  audio_en: string | null;
  audio_target: string | null;
}

export interface IdiomDetail {
  id: number;
  expression_id: number;
  lang: string;
  idiom_text: string;
  english_gloss: string;
  source_phrase_target: string | null;
  source_phrase_en: string | null;
  explanation_en: string | null;
  structured: Record<string, string> | null;
  audio_idiom_tgt: string | null;
  audio_idiom_en: string | null;
  audio_explanation: string | null;
  audio_context: string | null;
  created_at: string;
  youtube_id: string | null;
  video_title: string | null;
  video_id?: number;
  channel_id: number | null;
  channel_name: string | null;
  first_seen_at?: string;
  examples: Example[];
  reencounters: {
    created_at: string;
    phrase: string;
    video_id: number;
    video_title: string;
    youtube_id: string;
  }[];
}

// Labels for the structured JSONB sections (mirrors EXPL_LABELS in
// pipeline/apkg.py).
export const EXPL_LABELS: Record<string, string> = {
  usage: "Usage",
  collocations: "Typical collocations",
  synonyms_formal: "More formal alternative",
  synonyms_neutral: "Close synonym",
  synonyms_colloquial: "More casually",
  antonyms: "Opposite",
  register_note: "Register",
  metaphor: "Image / etymology",
  pitfall: "Grammatical pitfall",
  false_friend: "False-friend warning",
};
