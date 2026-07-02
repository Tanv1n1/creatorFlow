from telegram import Update
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

from creatorflow.db.repos import user_repo
from creatorflow.services.profiles import get as get_profile
from creatorflow.bot.keyboards import profile_select, parse_profile, SETTINGS_PREFIX

_GLOSSARY = {
    "pacing": (
        "⏱️ *Pacing score*\n\n"
        "How fast or slow your video feels.\n\n"
        "*Why it matters:* Slow videos lose viewers fast. Fast = people stay.\n\n"
        "*Scores:* 1–4 Very slow • 5–6 OK • 7–8 Good • 9–10 Excellent\n\n"
        "*How to improve:* Speak faster, cut long silences, keep energy up."
    ),
    "clarity": (
        "🔊 *Clarity score*\n\n"
        "How easy it is to understand your voice.\n\n"
        "*Why it matters:* Bad audio = viewers give up or turn on subtitles.\n\n"
        "*How to improve:* Use a microphone, record in a quiet room, speak clearly."
    ),
    "filler": (
        "💭 *Filler words*\n\n"
        "Words like 'um', 'uh', 'like', 'basically' that we say while thinking.\n\n"
        "*Are they bad?* No — everyone does it. But fewer = more polished.\n\n"
        "*What we do:* Remove the pauses around them. Your video sounds smooth.\n\n"
        "*Next time:* Pause and breathe instead of saying 'um'."
    ),
    "retakes": (
        "🔄 *Restarts / retakes*\n\n"
        "Moments where you stopped mid-sentence and started again to get it right.\n\n"
        "*Are they bad?* Not at all — shows you care about quality.\n\n"
        "*What we do:* Detect and smooth them out so your video flows.\n\n"
        "*Next time:* Do one quick practice run before recording."
    ),
    "score": (
        "📊 *Quality score*\n\n"
        "An overall rating out of 10 for your video.\n\n"
        "1–4: Needs work — try recording again\n"
        "5–6: OK — watchable but could be better\n"
        "7–8: Good — most people will enjoy it\n"
        "9–10: Excellent — very professional\n\n"
        "Most videos score 6–8. That is completely normal!"
    ),
}


async def settings_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid  = str(update.effective_user.id)
    user = await user_repo.get_or_create(uid)
    cfg  = get_profile(user.profile)

    text = (
        f"⚙️ *Your settings*\n\n"
        f"Current profile: {cfg.emoji} *{cfg.name}* — {cfg.description}\n\n"
        f"Other preferences:\n"
        f"Captions:    {'✅' if user.prefer_captions else '❌'}\n"
        f"Subtitles:   {'✅' if user.prefer_subtitles else '❌'}\n"
        f"Thumbnails:  {'✅' if user.prefer_thumbnails else '❌'}\n\n"
        f"Tap below to change your profile:"
    )
    target = update.message or update.callback_query.message
    await target.reply_text(text, parse_mode="Markdown", reply_markup=profile_select(SETTINGS_PREFIX))


async def handle_settings_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    chosen = parse_profile(query.data, SETTINGS_PREFIX)
    if chosen is None:
        return

    uid = str(update.effective_user.id)
    await user_repo.set_profile(uid, chosen)
    cfg = get_profile(chosen)
    await query.message.reply_text(
        f"✅ *Profile updated: {cfg.emoji} {cfg.name}*\n\nI'll now optimise your videos for *{cfg.description}*.",
        parse_mode="Markdown",
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "❓ *CreatorFlow commands*\n\n"
        "*Getting started*\n"
        "/start — Open the menu\n"
        "Send a video — Process it directly (≤50 MB)\n"
        "/bigupload — Get a link for large videos\n"
        "/confirm <key> — Confirm a large upload\n"
        "/status — Check your latest video\n\n"
        "*Preferences*\n"
        "/settings — Change your creator profile\n"
        "/explain <term> — Explain any score or term\n\n"
        "*Explain terms*\n"
        "`/explain pacing`  `/explain clarity`  `/explain filler`  `/explain retakes`  `/explain score`"
    )
    await update.message.reply_text(text, parse_mode="Markdown")


async def explain_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    term = context.args[0].lower() if context.args else None
    if not term or term not in _GLOSSARY:
        keys = " • ".join(_GLOSSARY.keys())
        await update.message.reply_text(f"Available terms: {keys}\n\nUsage: `/explain pacing`", parse_mode="Markdown")
        return
    await update.message.reply_text(_GLOSSARY[term], parse_mode="Markdown")


def register(app: Application):
    app.add_handler(CommandHandler("settings", settings_command))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("explain", explain_command))
    app.add_handler(CallbackQueryHandler(handle_settings_callback, pattern=f"^{SETTINGS_PREFIX}"))
