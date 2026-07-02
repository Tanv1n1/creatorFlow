from creatorflow.db.models.job import Job
from creatorflow.db.models.user import CreatorProfile
from creatorflow.services import formatter
from creatorflow.services.profiles import get as get_profile
from creatorflow.workers.storage import presigned_download


def build_main(job: Job, profile: CreatorProfile) -> str:
    qr     = job.quality_report or {}
    report = formatter.format_report(qr, profile)

    parts = [f"*{report.level} — your video is ready!*", f"{report.stars} ({report.score}/10)\n{report.summary}"]

    if report.strengths:
        parts.append("💚 *What works well*\n" + "\n".join(report.strengths))
    if report.improvements:
        parts.append("💡 *Optional improvements for next time*\n" + "\n".join(f"• {i}" for i in report.improvements))
    if job.output_r2_key:
        url = presigned_download(job.output_r2_key, expires_in=86400)
        parts.append(f"📥 [Download your video]({url}) _(valid 24h)_\nReady for Instagram / YouTube / TikTok")

    return "\n\n".join(parts)


def build_detail(job: Job) -> str | None:
    qr = job.quality_report or {}
    lines = []
    if qr.get("filler_word_count", 0) > 0:
        fi = formatter.explain_filler(qr)
        lines.append(f"💭 *Filler words ({fi['count']} found)*\n{fi['what_it_is']}\n✓ {fi['what_we_did']}\n_Tip: {fi['tip']}_")
    if qr.get("retake_count", 0) > 0:
        ri = formatter.explain_retakes(qr)
        lines.append(f"🔄 *Restarts detected ({ri['count']})*\n{ri['what_it_is']}\n✓ {ri['what_we_did']}\n_Tip: {ri['tip']}_")
    if not lines:
        return None
    return "ℹ️ *What the AI found — explained*\n\n" + "\n\n".join(lines)


def build_tips(job: Job, profile: CreatorProfile) -> str | None:
    qr     = job.quality_report or {}
    report = formatter.format_report(qr, profile)
    if not report.tips:
        return None
    cfg = get_profile(profile)
    return f"{cfg.emoji} *Tips for {cfg.name}s*\n\n" + "\n".join(f"• {t}" for t in report.tips)


def build_captions(job: Job) -> str | None:
    if not job.caption_suggestions:
        return None
    options = [c.strip() for c in job.caption_suggestions.split("\n\n") if c.strip()][:3]
    lines   = [f'{i}. "{c}"' for i, c in enumerate(options, 1)]
    return "💬 *Caption ideas — pick your favourite*\n\n" + "\n\n".join(lines) + "\n\n_Copy the one you like!_"


def build_thumbnails(job: Job) -> str | None:
    if not job.thumbnail_timestamps:
        return None
    reasons = ["You look engaged and expressive", "Great facial expression here", "Strong eye contact"]
    lines = [
        f"Option {i} — at {t['timestamp']:.1f}s (score {t['score']:.1f}/1.0)\n_{reasons[i-1]}_"
        for i, t in enumerate(job.thumbnail_timestamps[:3], 1)
    ]
    return "🖼️ *Best moments for your thumbnail*\n\n" + "\n\n".join(lines)
