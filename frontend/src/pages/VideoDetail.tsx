import { Link, useParams } from "react-router-dom";
import { EXPL_LABELS, Example } from "../api";
import AudioButton from "../components/AudioButton";
import { Card, Empty, ErrorBox, LangBadge, Spinner, StatusBadge, YouTubeLink } from "../components/ui";
import { fmtDateTime, fmtDuration } from "../format";
import { useApi } from "../hooks";

interface Detail {
  video: {
    id: number;
    youtube_id: string;
    title: string | null;
    lang: string;
    duration_sec: number | null;
    status: string;
    status_msg: string | null;
    reason_class: string;
    attempts: number;
    first_seen: string;
    picked_at: string | null;
    finished_at: string | null;
    processing_seconds: number | null;
    channel_name: string | null;
    curated: boolean;
    apkg_id: number | null;
    apkg_built_at: string | null;
    apkg_size_bytes: number | null;
    n_idioms: number | null;
    delivered_at: string | null;
  };
  idioms: {
    id: number;
    expression_id: number;
    idiom_text: string;
    english_gloss: string;
    source_phrase_target: string | null;
    source_phrase_en: string | null;
    explanation_en: string | null;
    structured: Record<string, string> | null;
    audio_idiom_tgt: string | null;
    audio_idiom_en: string | null;
    audio_explanation: string | null;
    examples: Example[];
  }[];
  extraction_log: {
    id: number;
    phrase: string;
    english: string | null;
    verdict: string;
    duplicate_of: number | null;
    duplicate_text: string | null;
    first_video_id: number | null;
    first_video_title: string | null;
  }[];
}

export default function VideoDetail() {
  const { id } = useParams();
  const { data, error, loading } = useApi<Detail>(`/videos/${id}`);
  if (loading && !data) return <Spinner />;
  if (error) return <ErrorBox error={error} />;
  if (!data) return null;
  const v = data.video;
  const dups = data.extraction_log.filter((e) => e.verdict === "duplicate");
  const freshLog = data.extraction_log.filter((e) => e.verdict === "fresh");

  return (
    <div className="flex flex-col gap-4">
      <div>
        <Link to="/videos" className="text-xs text-muted hover:text-ink-2">
          ← videos
        </Link>
        <h1 className="mt-1 text-xl font-bold leading-snug">
          <YouTubeLink youtubeId={v.youtube_id} title={v.title} />
        </h1>
        <div className="mt-1.5 flex flex-wrap items-center gap-3 text-sm text-ink-2">
          <LangBadge lang={v.lang} />
          <span>
            {v.curated && "★ "}
            {v.channel_name}
          </span>
          <span className="tnum">{fmtDuration(v.duration_sec)}</span>
          <StatusBadge status={v.status} />
          {v.processing_seconds != null && (
            <span className="text-xs text-muted">processed in {fmtDuration(v.processing_seconds)}</span>
          )}
        </div>
        {v.status_msg && <div className="mt-1 text-xs text-muted">{v.status_msg}</div>}
      </div>

      <div className="grid grid-cols-2 gap-3 text-sm lg:grid-cols-4">
        <Card title="Seen">{fmtDateTime(v.first_seen)}</Card>
        <Card title="Finished">{fmtDateTime(v.finished_at)}</Card>
        <Card title="Deck built">
          {v.apkg_built_at ? (
            <>
              {fmtDateTime(v.apkg_built_at)}
              <div className="text-xs text-muted">{v.n_idioms} idioms</div>
            </>
          ) : (
            "—"
          )}
        </Card>
        <Card title="Delivered to Anki">
          {v.delivered_at ? (
            <span className="text-good">✓ {fmtDateTime(v.delivered_at)}</span>
          ) : v.apkg_id ? (
            <span className="text-warning">pending</span>
          ) : (
            "—"
          )}
        </Card>
      </div>

      <Card
        title={`Harvested expressions (${data.idioms.length})`}
        aside="what this video contributed to the library"
      >
        {data.idioms.length === 0 ? (
          <Empty>
            Nothing harvested{v.status === "done" ? " (all extractions were duplicates?)" : ""}.
          </Empty>
        ) : (
          <div className="flex flex-col gap-4">
            {data.idioms.map((i) => (
              <div key={i.id} className="rounded-md border border-edge bg-surface-2 p-3">
                <div className="flex flex-wrap items-baseline gap-x-3 gap-y-1">
                  <Link to={`/expressions/${i.id}`} className="text-base font-semibold hover:underline">
                    {i.idiom_text}
                  </Link>
                  <span className="text-sm text-ink-2">{i.english_gloss}</span>
                  <div className="ml-auto flex gap-1.5">
                    <AudioButton path={i.audio_idiom_tgt} label="idiom" />
                    <AudioButton path={i.audio_idiom_en} label="EN" />
                    <AudioButton path={i.audio_explanation} label="explainer" />
                  </div>
                </div>
                {i.source_phrase_target && (
                  <blockquote className="mt-2 border-l-2 border-baseline pl-2.5 text-sm italic text-ink-2">
                    “{i.source_phrase_target}”
                    {i.source_phrase_en && (
                      <span className="block not-italic text-xs text-muted">— {i.source_phrase_en}</span>
                    )}
                  </blockquote>
                )}
                {i.explanation_en && <p className="mt-2 text-sm text-ink-2">{i.explanation_en}</p>}
                {i.structured && Object.values(i.structured).some(Boolean) && (
                  <div className="mt-2 grid gap-1 text-xs sm:grid-cols-2">
                    {Object.entries(i.structured)
                      .filter(([, val]) => val)
                      .map(([k, val]) => (
                        <div key={k}>
                          <span className="text-muted">{EXPL_LABELS[k] ?? k}: </span>
                          <span className="text-ink-2">{val}</span>
                        </div>
                      ))}
                  </div>
                )}
                {i.examples.length > 0 && (
                  <details className="mt-2">
                    <summary className="cursor-pointer text-xs text-muted hover:text-ink-2">
                      {i.examples.length} example pairs
                    </summary>
                    <div className="mt-1.5 flex flex-col gap-1.5">
                      {i.examples.map((ex) => (
                        <div key={ex.ord} className="flex flex-wrap items-center gap-2 text-sm">
                          <span className="tnum w-4 text-xs text-muted">{ex.ord}.</span>
                          <span className="text-ink">{ex.target_text}</span>
                          <span className="text-xs text-muted">{ex.en_text}</span>
                          <span className="ml-auto flex gap-1">
                            <AudioButton path={ex.audio_target} label="tgt" />
                            <AudioButton path={ex.audio_en} label="en" />
                          </span>
                        </div>
                      ))}
                    </div>
                  </details>
                )}
              </div>
            ))}
          </div>
        )}
      </Card>

      <Card
        title={`Rejected as already known (${dups.length})`}
        aside="dedup verdicts from the extraction log"
      >
        {data.extraction_log.length === 0 ? (
          <Empty>
            No extraction log for this video — it was processed before the log
            existed (recording started at deploy on 20 Jul 2026).
          </Empty>
        ) : dups.length === 0 ? (
          <Empty>Every extracted phrase was fresh — nothing rejected.</Empty>
        ) : (
          <div className="flex flex-col gap-1.5">
            {dups.map((d) => (
              <div key={d.id} className="flex flex-wrap items-baseline gap-2 text-sm">
                <span className="font-medium">{d.phrase}</span>
                {d.english && <span className="text-xs text-ink-2">{d.english}</span>}
                <span className="ml-auto text-xs text-muted">
                  first seen in{" "}
                  {d.first_video_id ? (
                    <Link to={`/videos/${d.first_video_id}`} className="underline hover:text-ink-2">
                      {d.first_video_title ?? `#${d.first_video_id}`}
                    </Link>
                  ) : (
                    "an earlier video"
                  )}
                </span>
              </div>
            ))}
          </div>
        )}
        {freshLog.length > 0 && (
          <div className="mt-3 border-t border-grid pt-2 text-xs text-muted">
            {freshLog.length} phrases passed dedup as fresh.
          </div>
        )}
      </Card>
    </div>
  );
}
