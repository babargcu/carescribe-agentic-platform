import { useCallback, useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { getSessionDetail, ingestAudio, ingestTextTranscript, reviewNote } from "../api/client";
import { AgentTimeline } from "../components/AgentTimeline";
import { AudioRecorder } from "../components/AudioRecorder";
import { ReviewActions } from "../components/ReviewActions";
import { StructuredNotePanel } from "../components/StructuredNotePanel";
import { TextIngestForm } from "../components/TextIngestForm";
import { TranscriptPanel } from "../components/TranscriptPanel";
import type { SessionDetail } from "../types";

export function SessionPage() {
  const { sessionId } = useParams<{ sessionId: string }>();
  const [detail, setDetail] = useState<SessionDetail | null>(null);
  const [processing, setProcessing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    if (!sessionId) return;
    setDetail(await getSessionDetail(sessionId));
  }, [sessionId]);

  useEffect(() => {
    refresh().catch((err) => setError(String(err)));
  }, [refresh]);

  async function handleTextSubmit(text: string) {
    if (!sessionId) return;
    setProcessing(true);
    setError(null);
    try {
      setDetail(await ingestTextTranscript(sessionId, text));
    } catch (err) {
      setError(String(err));
    } finally {
      setProcessing(false);
    }
  }

  async function handleAudioSubmit(blob: Blob) {
    if (!sessionId) return;
    setProcessing(true);
    setError(null);
    try {
      setDetail(await ingestAudio(sessionId, blob));
    } catch (err) {
      setError(String(err));
    } finally {
      setProcessing(false);
    }
  }

  async function handleReview(decision: "approve" | "reject") {
    if (!sessionId) return;
    setError(null);
    try {
      setDetail(await reviewNote(sessionId, decision));
    } catch (err) {
      setError(String(err));
    }
  }

  if (!detail) {
    return (
      <div className="page">
        <Link to="/">&larr; Back</Link>
        <p className="muted">Loading session…</p>
      </div>
    );
  }

  return (
    <div className="page">
      <Link to="/">&larr; Back to sessions</Link>
      <header className="page-header">
        <h1>Session: {detail.session.patient_pseudonym}</h1>
        <p className="subtitle">
          Clinician {detail.session.clinician_name} · status{" "}
          <span className={`pill pill-status-${detail.session.status}`}>{detail.session.status}</span>
        </p>
      </header>

      {error && <p className="field-error">{error}</p>}

      {!detail.transcript && (
        <section className="card">
          <h3>Capture encounter</h3>
          <AudioRecorder onRecordingComplete={handleAudioSubmit} disabled={processing} />
          <p className="muted">— or —</p>
          <TextIngestForm onSubmit={handleTextSubmit} disabled={processing} />
        </section>
      )}

      {processing && <p className="muted">Running agent pipeline…</p>}

      {detail.transcript && detail.note && (
        <>
          <TranscriptPanel transcript={detail.transcript} entities={detail.note.entities} />
          <StructuredNotePanel note={detail.note} />
          <AgentTimeline traces={detail.traces} />
          <ReviewActions note={detail.note} onReview={handleReview} />
        </>
      )}
    </div>
  );
}
