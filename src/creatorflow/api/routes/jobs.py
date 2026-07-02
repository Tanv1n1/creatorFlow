from fastapi import APIRouter, HTTPException
from creatorflow.db.repos import job_repo
from creatorflow.workers.storage import presigned_download

router = APIRouter()


@router.get("/{job_id}")
async def get_job(job_id: str):
    job = await job_repo.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return {
        "id":             job.id,
        "status":         job.status.value,
        "quality_report": job.quality_report,
        "captions":       job.caption_suggestions,
        "thumbnails":     job.thumbnail_timestamps,
        "error":          job.error_message,
        "created_at":     job.created_at.isoformat(),
        "completed_at":   job.completed_at.isoformat() if job.completed_at else None,
    }


@router.get("/{job_id}/download")
async def get_download_url(job_id: str):
    job = await job_repo.get(job_id)
    if not job or not job.output_r2_key:
        raise HTTPException(status_code=404, detail="Output not ready")
    return {"url": presigned_download(job.output_r2_key, expires_in=3600)}


@router.get("/{job_id}/transcript")
async def get_transcript(job_id: str):
    job = await job_repo.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job.transcript or {}
