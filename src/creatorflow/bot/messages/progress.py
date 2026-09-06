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
    if job.status == JobStatus.QUEUED:
        return (
            "⏳ *Your video is queued*\n\n"
            "Videos are processed in hourly batches — yours will start in the next run. "
            "I'll message you here as soon as it's ready."
        )

    current = next((i for i, (s, _) in enumerate(_STAGES) if s == job.status), 0)
    lines = []
    for i, (_, label) in enumerate(_STAGES):
        icon = "✓" if i < current else ("⟳" if i == current else "○")
        lines.append(f"{icon} Step {i+1}/6 — {label}")

    return "⚙️ *Processing your video now…*\n\n" + "\n".join(lines) + "\n\n_Usually done within a few minutes._"


def build_failed(job: Job) -> str:
    return (
        "❌ *We couldn't finish this video*\n\n"
        f"{_friendly_reason(job.error_message)}\n\n"
        "Feel free to send it again — if it keeps happening, double-check the video meets the "
        "requirements in /help."
    )


def _friendly_reason(raw: str | None) -> str:
    if not raw:
        return "Something went wrong on our end."
    r = raw.lower()
    if "too short" in r or "too long" in r:
        return raw
    if "unsupported" in r or "could not open" in r or "could not read" in r or "could not extract" in r or "unreadable" in r:
        return "We couldn't read that video file — it may be corrupted. Try re-exporting or re-recording it."
    if "ffmpeg error" in r:
        return "We hit a problem while rendering your video. This can happen with unusual formats or codecs — try a standard MP4 export."
    if "invalid json" in r or "llm returned" in r:
        return "Our AI editor had trouble analysing this video. Please try again — it usually works on a retry."
    return "Something went wrong while processing your video."
