import { Link, useParams } from "react-router-dom";
import { EXPL_LABELS, IdiomDetail } from "../api";
import AudioButton from "../components/AudioButton";
import { Card, Empty, ErrorBox, LangBadge, Spinner, YouTubeLink } from "../components/ui";
import { fmtDate, fmtDateTime } from "../format";
import { useApi } from "../hooks";

export default function ExpressionDetail() {
  const { id } = useParams();
  const { data: d, error, loading } = useApi<IdiomDetail>(`/expressions/${id}`);
  if (loading && !d) return <Spinner />;
  if (error) return <ErrorBox error={error} />;
  if (!d) return null;

  const structured = Object.entries(d.structured ?? {}).filter(([, v]) => v);

  return (
    <div className="flex flex-col gap-4">
      <div>
        <Link to="/expressions" className="text-xs text-muted hover:text-ink-2">
          ← expressions
        </Link>
        <div className="mt-1 flex flex-wrap items-baseline gap-x-4 gap-y-1">
          <h1 className="text-3xl font-bold leading-tight">{d.idiom_text}</h1>
          <span className="text-lg text-ink-2">{d.english_gloss}</span>
          <LangBadge lang={d.lang} />
        </div>
        <div className="mt-2 flex flex-wrap gap-2">
          <AudioButton path={d.audio_context} label="hear it in context" />
          <AudioButton path={d.audio_idiom_tgt} label="hear the idiom" />
          <AudioButton path={d.audio_idiom_en} label="hear the English" />
          <AudioButton path={d.audio_explanation} label="hear the explainer" />
        </div>
      </div>

      {d.explanation_en && (
        <Card title="How to use it">
          <p className="text-sm leading-relaxed text-ink-2">{d.explanation_en}</p>
        </Card>
      )}

      {d.source_phrase_target && (
        <Card title="Where it was said" aside={d.video_title ?? undefined}>
          <blockquote className="border-l-2 border-baseline pl-3 text-base italic">
            “{d.source_phrase_target}”
          </blockquote>
          {d.audio_context ? (
            <div className="mt-2 pl-3">
              <AudioButton path={d.audio_context} label="play this moment from the video" />
            </div>
          ) : (
            <p className="mt-2 pl-3 text-xs text-muted">
              No context clip — this expression was harvested before
              sentence clips were kept (2026-07-20); the source audio is
              gone.
            </p>
          )}
          {d.source_phrase_en && (
            <p className="mt-1.5 pl-3 text-sm text-muted">— {d.source_phrase_en}</p>
          )}
          <div className="mt-2 pl-3 text-xs text-muted">
            {d.channel_name?.startsWith("Curated ·") ? "★ " : ""}
            {d.channel_name} ·{" "}
            {d.youtube_id && <YouTubeLink youtubeId={d.youtube_id} title={d.video_title} />} ·{" "}
            harvested {fmtDate(d.created_at)}
          </div>
        </Card>
      )}

      {structured.length > 0 && (
        <Card title="Stylebook">
          <div className="grid gap-x-6 gap-y-2 text-sm sm:grid-cols-2">
            {structured.map(([k, v]) => (
              <div key={k}>
                <div className="text-xs font-medium text-muted">{EXPL_LABELS[k] ?? k}</div>
                <div className="text-ink-2">{v}</div>
              </div>
            ))}
          </div>
        </Card>
      )}

      <Card title={`Example pairs (${d.examples.length})`} aside="1–3 teach · 4–6 drill">
        {d.examples.length === 0 ? (
          <Empty>No examples stored.</Empty>
        ) : (
          <div className="flex flex-col gap-3">
            {d.examples.map((ex) => (
              <div key={ex.ord} className="rounded-md border border-edge bg-surface-2 p-2.5">
                <div className="flex flex-wrap items-center gap-2">
                  <span className="tnum text-xs text-muted">{ex.ord}.</span>
                  <span className="text-sm font-medium">{ex.target_text}</span>
                  <span className="ml-auto flex gap-1.5">
                    <AudioButton path={ex.audio_target} label="target" />
                    <AudioButton path={ex.audio_en} label="EN" />
                  </span>
                </div>
                <div className="mt-0.5 pl-6 text-sm text-ink-2">{ex.en_text}</div>
              </div>
            ))}
          </div>
        )}
      </Card>

      <Card
        title={`Re-encountered later (${d.reencounters.length})`}
        aside="videos where this expression was extracted again and rejected as a duplicate"
      >
        {d.reencounters.length === 0 ? (
          <Empty>
            Not re-encountered since the extraction log began (20 Jul 2026).
          </Empty>
        ) : (
          <div className="flex flex-col gap-1.5">
            {d.reencounters.map((r, i) => (
              <div key={i} className="flex flex-wrap items-baseline gap-2 text-sm">
                <span className="text-xs text-muted">{fmtDateTime(r.created_at)}</span>
                <span className="italic text-ink-2">“{r.phrase}”</span>
                <span className="ml-auto text-xs">
                  in{" "}
                  <Link to={`/videos/${r.video_id}`} className="underline hover:text-ink-2">
                    {r.video_title ?? r.youtube_id}
                  </Link>
                </span>
              </div>
            ))}
          </div>
        )}
      </Card>
    </div>
  );
}
