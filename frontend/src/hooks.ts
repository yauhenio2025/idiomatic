import { useEffect, useRef, useState } from "react";
import { api } from "./api";

export function useApi<T>(
  path: string,
  params?: Record<string, string | number | boolean | undefined | null>,
  refreshMs?: number,
) {
  const [data, setData] = useState<T | null>(null);
  const [error, setError] = useState<unknown>(null);
  const [loading, setLoading] = useState(true);
  const key = JSON.stringify([path, params]);
  const alive = useRef(true);

  useEffect(() => {
    alive.current = true;
    let timer: number | undefined;
    const load = (initial: boolean) => {
      if (initial) setLoading(true);
      api<T>(path, params)
        .then((d) => {
          if (!alive.current) return;
          setData(d);
          setError(null);
        })
        .catch((e) => {
          if (!alive.current) return;
          // keep stale data on background refresh errors
          if (initial) setError(e);
        })
        .finally(() => alive.current && setLoading(false));
    };
    load(true);
    if (refreshMs) timer = window.setInterval(() => load(false), refreshMs);
    return () => {
      alive.current = false;
      if (timer) window.clearInterval(timer);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [key, refreshMs]);

  return { data, error, loading };
}

export function useDebounced<T>(value: T, ms = 250): T {
  const [v, setV] = useState(value);
  useEffect(() => {
    const t = window.setTimeout(() => setV(value), ms);
    return () => window.clearTimeout(t);
  }, [value, ms]);
  return v;
}
