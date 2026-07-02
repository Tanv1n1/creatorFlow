import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

from creatorflow.db.repos import user_repo
from creatorflow.bot.messages import onboarding as ob_msg
from creatorflow.bot.keyboards import welcome_menu, profile_select, parse_profile, PROFILE_PREFIX, WELCOME_PREFIX

logger = logging.getLogger(__name__)


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/start — shows the profile wizard for new users, or the main menu for returning ones."""
    user = update.effective_user
    uid  = str(user.id)
    profile = await user_repo.get_or_create(uid, user.full_name)

    if not profile.onboarding_complete:
        await update.message.reply_text(ob_msg.profile_select(), parse_mode="Markdown", reply_markup=profile_select(PROFILE_PREFIX))
    else:
        await update.message.reply_text(ob_msg.welcome(), parse_mode="Markdown", reply_markup=welcome_menu())


async def handle_welcome_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Routes taps on the main welcome menu buttons."""
    query = update.callback_query
    await query.answer()
    action = query.data[len(WELCOME_PREFIX):]

    if action == "upload":
        await query.message.reply_text(ob_msg.upload_guide(), parse_mode="Markdown")
    elif action == "history":
        from creatorflow.bot.handlers.upload import status_command
        await status_command(update, context)
    elif action == "settings":
        from creatorflow.bot.handlers.settings import settings_command
        await settings_command(update, context)
    elif action == "howto":
        await query.message.reply_text(ob_msg.how_it_works(), parse_mode="Markdown")


async def handle_profile_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Routes the initial onboarding profile pick (first-time users only)."""
    query = update.callback_query
    await query.answer()
    chosen = parse_profile(query.data, PROFILE_PREFIX)
    if chosen is None:
        return

    uid = str(update.effective_user.id)
    await user_repo.set_profile(uid, chosen)
    await user_repo.mark_onboarded(uid, update.effective_user.full_name)

    await query.message.reply_text(ob_msg.profile_confirmed(chosen), parse_mode="Markdown")
    logger.info(f"[onboarding] user {uid} → profile={chosen.value}")


def register(app: Application):
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CallbackQueryHandler(handle_welcome_callback, pattern=f"^{WELCOME_PREFIX}"))
    app.add_handler(CallbackQueryHandler(handle_profile_callback, pattern=f"^{PROFILE_PREFIX}"))
