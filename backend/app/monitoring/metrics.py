from prometheus_client import Counter, Histogram

PIPELINE_RUNS = Counter(
    "carescribe_pipeline_runs_total", "Number of full agent pipeline runs completed"
)

PIPELINE_LATENCY = Histogram(
    "carescribe_pipeline_latency_seconds", "End-to-end agent pipeline latency"
)

AGENT_CONFIDENCE = Histogram(
    "carescribe_agent_confidence",
    "Per-agent confidence score for each pipeline run",
    ["agent"],
    buckets=[round(i * 0.1, 1) for i in range(11)],
)

VALIDATION_FLAGS = Counter(
    "carescribe_validation_flags_total", "Total validator flags raised across all pipeline runs"
)
