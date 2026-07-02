import logging
import os
import shutil
import subprocess
import tempfile
from pathlib import Path
from creatorflow.workers.llm import EditPlan, TimeRange
from creatorflow.workers.transcriber import Segment, segments_to_srt

logger = logging.getLogger(__name__)


def get_video_duration(path: str) -> float:
    r = subprocess.run(
        ["ffprobe","-v","error","-show_entries","format=duration","-of","default=noprint_wrappers=1:nokey=1", path],
        capture_output=True, text=True, check=True,
    )
    return float(r.stdout.strip())


def render_reel(
    input_path: str,
    output_path: str,
    edit_plan: EditPlan,
    subtitle_segments: list[Segment],
    burn_subtitles: bool = True,
) -> str:
    work = Path(tempfile.mkdtemp(prefix="cf_render_"))
    try:
        clips     = _extract_clips(input_path, edit_plan.keep_segments, work)
        concat    = str(work / "concat.mp4")
        _concat(clips, concat)
        if burn_subtitles and subtitle_segments:
            srt = str(work / "subs.srt")
            Path(srt).write_text(segments_to_srt(subtitle_segments), encoding="utf-8")
            _burn(concat, srt, output_path)
        else:
            shutil.move(concat, output_path)
        logger.info(f"[editor] render done → {output_path}")
        return output_path
    finally:
        shutil.rmtree(work, ignore_errors=True)


def _extract_clips(src: str, keeps: list[TimeRange], work: Path) -> list[str]:
    paths = []
    for i, seg in enumerate(keeps):
        out = str(work / f"clip_{i:04d}.mp4")
        _run(["ffmpeg","-y","-ss",str(seg.start),"-i",src,"-t",str(seg.end-seg.start),
              "-c:v","libx264","-preset","fast","-crf","18",
              "-c:a","aac","-b:a","128k",
              "-vf","scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2",
              "-r","30", out])
        paths.append(out)
    return paths


def _concat(clips: list[str], out: str) -> None:
    if len(clips) == 1:
        shutil.copy(clips[0], out); return
    manifest = Path(clips[0]).parent / "manifest.txt"
    manifest.write_text("\n".join(f"file '{p}'" for p in clips))
    _run(["ffmpeg","-y","-f","concat","-safe","0","-i",str(manifest),"-c","copy", out])


def _burn(src: str, srt: str, out: str) -> None:
    style = "FontName=Arial,FontSize=18,PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,Outline=2,Alignment=2,MarginV=60"
    _run(["ffmpeg","-y","-i",src,"-vf",f"subtitles={srt}:force_style='{style}'",
          "-c:v","libx264","-preset","fast","-crf","18","-c:a","copy", out])


def _run(cmd: list[str]) -> None:
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(f"ffmpeg error (code {r.returncode}): {r.stderr[-500:]}")
