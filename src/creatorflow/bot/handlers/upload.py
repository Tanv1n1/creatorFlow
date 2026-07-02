import asyncio
import logging
import tempfile
import uuid
from pathlib import Path

from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters

from creatorflow.config import settings
from creatorflow.db.models.job import JobStatus
from creatorflow.db.repos import job_repo, user_repo
from creatorflow.services import queue
from creatorflow.workers import storage
from creatorflow.bot.messages import progress as progress_msg, results as results_msg

logger = logging.getLogger(__name__)

POLL_INTERVAL = settings.progress_update_interval
POLL_TIMEOUT  = 600  # 10 min
VALID_EXTS    = {".mp4", ".mov", ".webm", ".avi", ".mkv"}


async def upload_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/upload — prompts the user to send a video if none attached."""
    await update.message.reply_text("Send your video as a message and I'll take it from there. Over 50 MB? Use /bigupload")


async def handle_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Triggered automatically when a user sends a video or document file."""
    file_obj = update.message.video or update.message.document
    if file_obj is None:
        return

    filename = getattr(file_obj, "file_name", None) or "input.mp4"
    ext = Path(filename).suffix.lower() or ".mp4"
    if ext not in VALID_EXTS:
        await update.message.reply_text(f"❌ Unsupported format `{ext}`. Supported: {', '.join(VALID_EXTS)}", parse_mode="Markdown")
        return
    if file_obj.file_size and file_obj.file_size > settings.max_upload_size_mb * 1024 * 1024:
        await update.message.reply_text(f"❌ File too large ({file_obj.file_size // 1_000_000} MB, max {settings.max_upload_size_mb} MB)")
        return

    thinking = await update.message.reply_text("📥 Downloading your video…")
    tg_file = await context.bot.get_file(file_obj.file_id)
    with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as tmp:
        await tg_file.download_to_drive(tmp.name)
        r2_key = f"jobs/{uuid.uuid4()}/input{ext}"
        await asyncio.get_event_loop().run_in_executor(None, storage.upload_file, tmp.name, r2_key)
    await thinking.delete()

    await _create_and_process(update, context, r2_key)


async def bigupload_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    #/bigupload — returns a presigned upload URL for large files.
    r2_key = f"jobs/{uuid.uuid4()}/input.mp4"
    url = storage.presigned_upload(r2_key, expires_in=3600)
    await update.message.reply_text(
        f"📤 *Secure upload link (valid 1 hour)*\n\n"
        f"[Click here to upload your video]({url})\n\n"
        f"After uploading, come back and type:\n`/confirm {r2_key}`",
        parse_mode="Markdown",
        disable_web_page_preview=True,
    )


async def confirm_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    #/confirm <r2_key> — confirms a large upload was completed.
    if not context.args:
        await update.message.reply_text("Usage: `/confirm <key>`", parse_mode="Markdown")
        return
    await _create_and_process(update, context, context.args[0])


async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/status [job_id] — shows progress or final results for a job."""
    uid = str(update.effective_user.id)
    job_id = context.args[0] if context.args else None

    if job_id is None:
        jobs = await job_repo.list_by_user(uid, limit=1)
        if not jobs:
            await update.message.reply_text("No videos found. Send me a video to start!")
            return
        job_id = jobs[0].id

    job = await job_repo.get(job_id)
    if not job or job.discord_user_id != uid:
        await update.message.reply_text("Job not found.")
        return

    if job.status == JobStatus.DONE:
        await _send_results(update.effective_chat.id, context, job, uid)
    elif job.status == JobStatus.FAILED:
        await update.message.reply_text(progress_msg.build_failed(job), parse_mode="Markdown")
    else:
        await update.message.reply_text(progress_msg.build(job), parse_mode="Markdown")


# ── internal ──────────────────────────────────────────────────────────────────

async def _create_and_process(update: Update, context: ContextTypes.DEFAULT_TYPE, r2_key: str):
    uid = str(update.effective_user.id)
    job = await job_repo.create(
        discord_user_id=uid,                              # holds Telegram user id
        discord_channel_id=str(update.effective_chat.id),  # holds Telegram chat id
        input_r2_key=r2_key,
        discord_message_id=str(update.message.message_id),
    )
    await queue.enqueue(job.id)

    sent = await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=progress_msg.build(await job_repo.get(job.id)),
        parse_mode="Markdown",
    )
    asyncio.create_task(_poll(context, update.effective_chat.id, sent.message_id, job.id, uid))


async def _poll(context: ContextTypes.DEFAULT_TYPE, chat_id: int, message_id: int, job_id: str, uid: str):
    elapsed = 0
    while elapsed < POLL_TIMEOUT:
        await asyncio.sleep(POLL_INTERVAL)
        elapsed += POLL_INTERVAL
        job = await job_repo.get(job_id)

        if job.status == JobStatus.FAILED:
            await context.bot.edit_message_text(chat_id=chat_id, message_id=message_id, text=progress_msg.build_failed(job), parse_mode="Markdown")
            return
        if job.status == JobStatus.DONE:
            await context.bot.delete_message(chat_id=chat_id, message_id=message_id)
            await _send_results(chat_id, context, job, uid)
            return

        try:
            await context.bot.edit_message_text(chat_id=chat_id, message_id=message_id, text=progress_msg.build(job), parse_mode="Markdown")
        except Exception:
            pass  # message unchanged — Telegram rejects identical edits

    await context.bot.edit_message_text(chat_id=chat_id, message_id=message_id, text="⏱️ This is taking longer than expected. Use /status to check later.")


async def _send_results(chat_id: int, context: ContextTypes.DEFAULT_TYPE, job, uid: str):
    profile = (await user_repo.get_or_create(uid)).profile

    await context.bot.send_message(chat_id=chat_id, text=results_msg.build_main(job, profile), parse_mode="Markdown", disable_web_page_preview=True)

    detail = results_msg.build_detail(job)
    if detail:
        await context.bot.send_message(chat_id=chat_id, text=detail, parse_mode="Markdown")

    tips = results_msg.build_tips(job, profile)
    if tips:
        await context.bot.send_message(chat_id=chat_id, text=tips, parse_mode="Markdown")

    captions = results_msg.build_captions(job)
    if captions:
        await context.bot.send_message(chat_id=chat_id, text=captions, parse_mode="Markdown")

    thumbs = results_msg.build_thumbnails(job)
    if thumbs:
        await context.bot.send_message(chat_id=chat_id, text=thumbs, parse_mode="Markdown")


def register(app: Application):
    app.add_handler(CommandHandler("upload", upload_command))
    app.add_handler(CommandHandler("bigupload", bigupload_command))
    app.add_handler(CommandHandler("confirm", confirm_command))
    app.add_handler(CommandHandler("status", status_command))
    app.add_handler(MessageHandler(filters.VIDEO | filters.Document.VIDEO, handle_video))
