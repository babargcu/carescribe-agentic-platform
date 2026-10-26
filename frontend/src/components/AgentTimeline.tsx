import type { AgentTraceOut } from "../types";

interface AgentTimelineProps {
  traces: AgentTraceOut[];
}

const STATUS_ICON: Record<string, string> = {
  ok: "✅",
  flagged: "⚠️",
  error: "❌",
};

export function AgentTimeline({ traces }: AgentTimelineProps) {
  if (traces.length === 0) {
    return (
      <section className="card">
        <h3>Agent timeline</h3>
        <p className="muted">No pipeline run yet.</p>
      </section>
    );
  }

  const totalLatency = traces.reduce((sum, t) => sum + t.latency_ms, 0);

  return (
    <section className="card">
      <h3>Agent timeline</h3>
      <p className="meta-row">Total latency: {totalLatency.toFixed(0)} ms</p>
      <ol className="timeline">
        {traces.map((trace) => (
          <li key={trace.step_index} className={`timeline-step status-${trace.status}`}>
            <div className="timeline-step-header">
              <span>
                {STATUS_ICON[trace.status] ?? ""} <strong>{trace.agent_name}</strong>
              </span>
              <span className="timeline-latency">{trace.latency_ms.toFixed(1)} ms</span>
            </div>
            <p className="timeline-summary">{trace.output_summary}</p>
            {trace.confidence !== null && (
              <div className="confidence-bar">
                <div
                  className="confidence-bar-fill"
                  style={{ width: `${Math.round(trace.confidence * 100)}%` }}
                />
              </div>
            )}
          </li>
        ))}
      </ol>
    </section>
  );
}
