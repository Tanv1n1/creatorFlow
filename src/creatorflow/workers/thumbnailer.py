import logging
from dataclasses import dataclass
from pathlib import Path
import cv2
import numpy as np

logger = logging.getLogger(__name__)
SAMPLE_RATE = 2  # frames per second to sample


@dataclass
class ThumbnailCandidate:
    timestamp:  float
    score:      float
    frame_path: str


def extract_thumbnail_candidates(video_path: str, output_dir: str, top_n: int = 5) -> list[ThumbnailCandidate]:
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        cap.release()
        raise ValueError(f"Could not open rendered video for thumbnail extraction: {video_path}")

    try:
        fps      = cap.get(cv2.CAP_PROP_FPS) or 30
        interval = max(int(fps / SAMPLE_RATE), 1)
        cascade  = _cascade()
        results: list[ThumbnailCandidate] = []
        idx = 0

        while True:
            cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
            ok, frame = cap.read()
            if not ok:
                break
            ts   = idx / fps
            path = str(Path(output_dir) / f"thumb_{ts:.2f}s.jpg")
            cv2.imwrite(path, frame, [cv2.IMWRITE_JPEG_QUALITY, 90])
            results.append(ThumbnailCandidate(ts, _score(frame, cascade), path))
            idx += interval
    except cv2.error as e:
        raise ValueError(f"Could not read frames from the rendered video: {e}") from e
    finally:
        cap.release()

    if not results:
        raise ValueError("Could not extract any thumbnail frames from the rendered video")

    results.sort(key=lambda c: c.score, reverse=True)
    top = results[:top_n]
    logger.info(f"[thumbnailer] top {len(top)}: {[f'{c.timestamp:.1f}s={c.score:.2f}' for c in top]}")
    return top


def _score(frame: np.ndarray, cascade) -> float:
    gray  = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    sharp = min(cv2.Laplacian(gray, cv2.CV_64F).var() / 500.0, 1.0)
    mean  = gray.mean()
    brite = 1.0 - abs(mean - 128) / 128 if 40 <= mean <= 220 else 0.2
    face  = 0.0
    if cascade is not None:
        faces = cascade.detectMultiScale(gray, 1.1, 5)
        face  = 1.0 if len(faces) > 0 else 0.0
    return 0.5 * sharp + 0.3 * brite + 0.2 * face


def _cascade():
    try:
        c = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
        return None if c.empty() else c
    except Exception:
        return None
