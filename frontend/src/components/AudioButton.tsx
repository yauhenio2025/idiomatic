import { useEffect, useRef, useState } from "react";
import { audioUrl } from "../api";

// One shared element so only one clip plays at a time.
let current: HTMLAudioElement | null = null;
let currentStop: (() => void) | null = null;

export default function AudioButton({
  path,
  label,
}: {
  path: string | null | undefined;
  label: string;
}) {
  const [state, setState] = useState<"idle" | "loading" | "playing" | "error">("idle");
  const mounted = useRef(true);
  useEffect(() => {
    mounted.current = true;
    return () => {
      mounted.current = false;
    };
  }, []);

  if (!path) return null;

  const play = async () => {
    if (state === "playing") {
      current?.pause();
      currentStop?.();
      return;
    }
    setState("loading");
    try {
      const url = await audioUrl(path);
      current?.pause();
      currentStop?.();
      const el = new Audio(url);
      current = el;
      currentStop = () => mounted.current && setState("idle");
      el.onended = () => currentStop?.();
      el.onerror = () => mounted.current && setState("error");
      await el.play();
      if (mounted.current) setState("playing");
    } catch {
      if (mounted.current) setState("error");
    }
  };

  const icon =
    state === "playing" ? "◼" : state === "loading" ? "…" : state === "error" ? "✕" : "▶";

  return (
    <button
      onClick={play}
      title={state === "error" ? `couldn't load ${label}` : label}
      className={`inline-flex items-center gap-1.5 rounded-full border border-edge px-2.5 py-1 text-xs transition-colors hover:bg-surface-2 ${
        state === "error" ? "text-critical" : state === "playing" ? "text-accent" : "text-ink-2"
      }`}
    >
      <span className="w-3 text-center">{icon}</span>
      {label}
    </button>
  );
}
