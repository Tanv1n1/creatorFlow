import logging
import shutil
import tempfile
from pathlib import Path

from creatorflow.config import settings
from creatorflow.db.models.job import JobStatus
from creatorflow.db.repos import job_repo
from creatorflow.workers import storage, transcriber, llm, editor, thumbnailer

logger = logging.getLogger(__name__)
WORK_DIR = Path(tempfile.gettempdir()) / "creatorflow_jobs"
WORK_DIR.mkdir(parents=True, exist_ok=True)


async def process_job(job_id: str) -> None:
    job = await job_repo.get(job_id)
    if not job:
        logger.error(f"[pipeline] job {job_id} not found")
        return

    job_dir = WORK_DIR / job_id
    job_dir.mkdir(parents=True, exist_ok=True)

    try:
        # 1 — Download
        await job_repo.set_status(job_id, JobStatus.DOWNLOADING)
        input_path = str(job_dir / "input.mp4")
        storage.download_file(job.input_r2_key, input_path)
        duration = editor.get_video_duration(input_path)
        _validate_duration(duration)

        # 2 — Transcribe
        await job_repo.set_status(job_id, JobStatus.TRANSCRIBING)
        tx = transcriber.transcribe(input_path)
        await job_repo.update_fields(job_id, transcript={
            "source_segments":   [{"start": s.start, "end": s.end, "text": s.text} for s in tx.source_segments],
            "english_segments":  [{"start": s.start, "end": s.end, "text": s.text} for s in tx.english_segments],
            "detected_language": tx.detected_language,
            "language_probability": tx.language_probability,
        })

        # 3 — LLM analysis
        await job_repo.set_status(job_id, JobStatus.ANALYZING)
        edit_plan     = llm.plan_edits(tx.source_segments, duration)
        quality_report= llm.generate_quality_report(tx.source_segments)
        captions      = llm.generate_captions(tx.source_segments)

        await job_repo.update_fields(job_id,
            status=JobStatus.RENDERING,
            edit_plan={
                "keep": [{"start": r.start, "end": r.end, "reason": r.reason} for r in edit_plan.keep_segments],
                "cut":  [{"start": r.start, "end": r.end, "reason": r.reason} for r in edit_plan.cut_segments],
                "total_kept_duration": edit_plan.total_kept_duration,
            },
            quality_report={
                "overall_score":    quality_report.overall_score,
                "pacing_score":     quality_report.pacing_score,
                "clarity_score":    quality_report.clarity_score,
                "filler_word_count":quality_report.filler_word_count,
                "filler_words":     quality_report.filler_words,
                "retake_count":     quality_report.retake_count,
                "feedback":         quality_report.feedback,
                "recommendations":  quality_report.recommendations,
            },
            caption_suggestions="\n\n".join(captions),
        )

        # 4 — Render
        output_path = str(job_dir / "output.mp4")
        editor.render_reel(
            input_path=input_path,
            output_path=output_path,
            edit_plan=edit_plan,
            subtitle_segments=tx.english_segments,
            burn_subtitles=True,
        )
        await job_repo.set_status(job_id, JobStatus.GENERATING_ASSETS)

        # 5 — Thumbnails
        thumb_dir = str(job_dir / "thumbnails")
        candidates = thumbnailer.extract_thumbnail_candidates(output_path, thumb_dir, top_n=5)
        for c in candidates:
            storage.upload_file(c.frame_path, f"jobs/{job_id}/thumbnails/{Path(c.frame_path).name}")

        # 6 — Upload & complete
        output_r2_key = f"jobs/{job_id}/output.mp4"
        storage.upload_file(output_path, output_r2_key)
        await job_repo.complete(
            job_id,
            output_r2_key=output_r2_key,
            thumbnail_timestamps=[{"timestamp": c.timestamp, "score": round(c.score, 3)} for c in candidates],
        )
        logger.info(f"[pipeline] ✓ {job_id}")

    except Exception as e:
        logger.exception(f"[pipeline] failed {job_id}: {e}")
        await job_repo.fail(job_id, str(e))
        raise
    finally:
        shutil.rmtree(job_dir, ignore_errors=True)


def _validate_duration(d: float) -> None:
    if d < settings.min_video_duration_seconds:
        raise ValueError(f"Video too short ({d:.0f}s, min {settings.min_video_duration_seconds}s)")
    if d > settings.max_video_duration_seconds:
        raise ValueError(f"Video too long ({d:.0f}s, max {settings.max_video_duration_seconds}s)")
