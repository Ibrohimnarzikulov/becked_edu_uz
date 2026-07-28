"""Telegram bot — EduHub login orqali kirib, bajarilmagan vazifalarni ko'rsatadi.

Ishga tushirish: python manage.py runbot
"""
from asgiref.sync import sync_to_async
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)

from apps.telegrambot.models import TelegramLink
from apps.telegrambot.services import build_todo_message

User = get_user_model()

USERNAME, PASSWORD = range(2)

MENU = ReplyKeyboardMarkup([['📋 Vazifalarim'], ['🚪 Chiqish']], resize_keyboard=True)


def _get_linked_user(telegram_id):
    link = TelegramLink.objects.filter(telegram_id=telegram_id).select_related('user').first()
    return link.user if link else None


def _authenticate(username, password):
    try:
        user = User.objects.get(username=username)
    except User.DoesNotExist:
        return None, "❌ Bunday foydalanuvchi topilmadi."
    if user.is_blocked:
        return None, "❌ Hisobingiz bloklangan."
    if not user.check_password(password):
        return None, "❌ Login yoki parol noto'g'ri."
    return user, None


def _link_telegram(telegram_id, user):
    TelegramLink.objects.update_or_create(telegram_id=telegram_id, defaults={'user': user})


def _unlink_telegram(telegram_id):
    TelegramLink.objects.filter(telegram_id=telegram_id).delete()


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = await sync_to_async(_get_linked_user)(update.effective_user.id)
    if user:
        await update.message.reply_text(
            f"Salom, {user.full_name or user.username}! 👋\nKerakli bo'limni tanlang:",
            reply_markup=MENU,
        )
        return ConversationHandler.END

    await update.message.reply_text(
        "Salom! Bu EduHub bot 🎓\n\n"
        "Vazifalaringizni ko'rish uchun EduHub hisobingiz bilan kiring.\n\n"
        "Foydalanuvchi nomingizni yuboring:",
        reply_markup=ReplyKeyboardRemove(),
    )
    return USERNAME


async def receive_username(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['username'] = update.message.text.strip().lower()
    await update.message.reply_text("Endi parolingizni yuboring:")
    return PASSWORD


async def receive_password(update: Update, context: ContextTypes.DEFAULT_TYPE):
    username = context.user_data.get('username', '')
    password = update.message.text

    # Xavfsizlik: parol matnini suhbatdan darhol o'chiramiz.
    try:
        await context.bot.delete_message(
            chat_id=update.effective_chat.id, message_id=update.message.message_id,
        )
    except Exception:
        pass

    user, error = await sync_to_async(_authenticate)(username, password)
    if error:
        await update.message.reply_text(f"{error} /start bilan qayta urinib ko'ring.")
        return ConversationHandler.END

    await sync_to_async(_link_telegram)(update.effective_user.id, user)
    await update.message.reply_text(
        f"✅ Muvaffaqiyatli bog'landi, {user.full_name or user.username}!",
        reply_markup=MENU,
    )
    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Bekor qilindi. /start bilan qayta boshlashingiz mumkin.",
        reply_markup=ReplyKeyboardRemove(),
    )
    return ConversationHandler.END


async def show_todo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = await sync_to_async(_get_linked_user)(update.effective_user.id)
    if not user:
        await update.message.reply_text("Avval /start orqali tizimga kiring.")
        return
    text = await sync_to_async(build_todo_message)(user)
    await update.message.reply_text(text, parse_mode='Markdown', reply_markup=MENU)


async def logout(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await sync_to_async(_unlink_telegram)(update.effective_user.id)
    await update.message.reply_text(
        "Chiqdingiz. Qayta kirish uchun /start bosing.",
        reply_markup=ReplyKeyboardRemove(),
    )


class Command(BaseCommand):
    help = "Telegram botni ishga tushiradi (long polling)"

    def handle(self, *args, **options):
        token = getattr(settings, 'TELEGRAM_BOT_TOKEN', '')
        if not token:
            self.stderr.write(self.style.ERROR("TELEGRAM_BOT_TOKEN sozlanmagan (.env)"))
            return

        application = Application.builder().token(token).build()

        conv = ConversationHandler(
            entry_points=[CommandHandler('start', start)],
            states={
                USERNAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_username)],
                PASSWORD: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_password)],
            },
            fallbacks=[CommandHandler('cancel', cancel)],
        )
        application.add_handler(conv)
        application.add_handler(MessageHandler(filters.Regex('^📋 Vazifalarim$'), show_todo))
        application.add_handler(CommandHandler('vazifalar', show_todo))
        application.add_handler(MessageHandler(filters.Regex('^🚪 Chiqish$'), logout))
        application.add_handler(CommandHandler('logout', logout))

        self.stdout.write(self.style.SUCCESS('Bot ishga tushdi (polling)...'))
        application.run_polling(allowed_updates=Update.ALL_TYPES)
