import enum
import uuid
from datetime import datetime

from sqlalchemy import String, DateTime, Enum as SAEnum, JSON, Text, Integer
from sqlalchemy.orm import Mapped, mapped_column

from creatorflow.db.engine import Base


class JobStatus(str, enum.Enum):
    QUEUED            = "queued"
    DOWNLOADING       = "downloading"
    TRANSCRIBING      = "transcribing"
    TRANSLATING       = "translating"
    ANALYZING         = "analyzing"
    PLANNING_EDITS    = "planning_edits"
    RENDERING         = "rendering"
    GENERATING_ASSETS = "generating_assets"
    DONE              = "done"
    FAILED            = "failed"
    CANCELLED         = "cancelled"


class Job(Base):
    __tablename__ = "jobs"

    id:                  Mapped[str]      = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    telegram_user_id:    Mapped[str]      = mapped_column(String(32))
    telegram_chat_id:    Mapped[str]      = mapped_column(String(32))
    telegram_message_id: Mapped[str|None] = mapped_column(String(32), nullable=True)

    status: Mapped[JobStatus] = mapped_column(SAEnum(JobStatus), default=JobStatus.QUEUED)

    input_r2_key:     Mapped[str|None] = mapped_column(String(512), nullable=True)
    output_r2_key:    Mapped[str|None] = mapped_column(String(512), nullable=True)
    local_input_path: Mapped[str|None] = mapped_column(String(512), nullable=True)
    local_output_path:Mapped[str|None] = mapped_column(String(512), nullable=True)

    transcript:           Mapped[dict|None] = mapped_column(JSON, nullable=True)
    edit_plan:            Mapped[dict|None] = mapped_column(JSON, nullable=True)
    quality_report:       Mapped[dict|None] = mapped_column(JSON, nullable=True)
    caption_suggestions:  Mapped[str|None]  = mapped_column(Text, nullable=True)
    thumbnail_timestamps: Mapped[dict|None] = mapped_column(JSON, nullable=True)

    error_message: Mapped[str|None] = mapped_column(Text, nullable=True)
    retry_count:   Mapped[int]      = mapped_column(Integer, default=0)

    created_at:   Mapped[datetime]      = mapped_column(DateTime, default=datetime.utcnow)
    updated_at:   Mapped[datetime]      = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at: Mapped[datetime|None] = mapped_column(DateTime, nullable=True)
