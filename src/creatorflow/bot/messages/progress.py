from datetime import datetime
from creatorflow.db.models.job import Job, JobStatus

_STAGES = [
    (JobStatus.DOWNLOADING,       "Downloading your video"),
    (JobStatus.TRANSCRIBING,      "Listening to your audio"),
    (JobStatus.ANALYZING,         "Analysing for improvements"),
    (JobStatus.PLANNING_EDITS,    "Planning the edits"),
    (JobStatus.RENDERING,         "Creating your edited video"),
    (JobStatus.GENERATING_ASSETS, "Extracting best thumbnails"),
]


def build(job: Job) -> str:
    current = next((i for i, (s, _) in enumerate(_STAGES) if s == job.status), 0)
    lines = []
    for i, (_, label) in enumerate(_STAGES):
        icon = "✓" if i < current else ("⟳" if i == current else "○")
        lines.append(f"{icon} Step {i+1}/6 — {label}")

    elapsed  = (datetime.utcnow() - job.created_at).total_seconds()
    eta_secs = max(0, 180 - elapsed)
    eta_str  = f"{int(eta_secs // 60)}m {int(eta_secs % 60)}s" if eta_secs > 60 else f"{int(eta_secs)}s"

    return "⏳ *Processing your video…*\n\n" + "\n".join(lines) + f"\n\n_Estimated time remaining: ~{eta_str}_"


def build_failed(job: Job) -> str:
    return (
        "❌ *Something went wrong*\n\n"
        "We hit an error while processing your video. Please try uploading it again.\n\n"
        f"_Error: {job.error_message or 'Unknown error'}_"
    )
