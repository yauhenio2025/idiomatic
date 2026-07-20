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
