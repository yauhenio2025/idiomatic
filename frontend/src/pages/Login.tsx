import { FormEvent, useState } from "react";
import { api, setToken } from "../api";

export default function Login({ onAuthed }: { onAuthed: () => void }) {
  const [token, setTokenInput] = useState("");
  const [err, setErr] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const submit = async (e: FormEvent) => {
    e.preventDefault();
    setBusy(true);
    setErr(null);
    setToken(token.trim());
    try {
      await api("/auth/check");
      onAuthed();
    } catch {
      setErr("That token was rejected.");
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center px-4">
      <form
        onSubmit={submit}
        className="w-full max-w-sm rounded-xl border border-edge bg-surface p-6"
      >
        <h1 className="text-lg font-bold">idiomatic</h1>
        <p className="mb-5 mt-1 text-sm text-muted">
          Paste the admin token to open the dashboard.
        </p>
        <input
          type="password"
          value={token}
          onChange={(e) => setTokenInput(e.target.value)}
          placeholder="admin token"
          autoFocus
          className="w-full rounded-md border border-edge bg-surface-2 px-3 py-2 text-sm outline-none placeholder:text-muted focus:border-accent"
        />
        {err && <div className="mt-2 text-xs text-critical">✕ {err}</div>}
        <button
          type="submit"
          disabled={busy || !token.trim()}
          className="mt-4 w-full rounded-md bg-accent px-3 py-2 text-sm font-semibold text-white transition-opacity hover:opacity-90 disabled:opacity-40"
        >
          {busy ? "checking…" : "Enter"}
        </button>
      </form>
    </div>
  );
}
