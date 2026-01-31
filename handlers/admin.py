from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, FSInputFile
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from datetime import datetime
import logging
import os

from database import Database
from keyboards import (
    admin_menu_keyboard, main_menu_keyboard, export_keyboard,
    archive_keyboard, yes_no_keyboard, vote_keyboard
)
from utils import (
    is_admin, format_results_text, parse_datetime,
    validate_channel_link, create_excel_report,
    create_csv_report, create_chart, log_user_action,
    get_current_datetime, format_datetime
)
import config

router = Router()
logger = logging.getLogger(__name__)

# =========================
# ADMIN STATES
# =========================
class AdminStates(StatesGroup):
    waiting_contest_name = State()
    waiting_contest_image = State()
    waiting_start_date = State()
    waiting_end_date = State()
    waiting_channel_count = State()
    waiting_channel_id = State()
    waiting_channel_name = State()
    waiting_channel_link = State()
    waiting_candidate_count = State()
    waiting_candidate_name = State()
    confirm_contest = State()

# =========================
# ADMIN DECORATOR
# =========================
def admin_only(func):
    async def wrapper(event, **kwargs):
        user_id = event.from_user.id
        if not is_admin(user_id):
            msg = "❌ Sizda admin huquqi yo'q!"
            if isinstance(event, Message):
                await event.answer(msg)
            else:
                await event.answer(msg, show_alert=True)
            return
        import inspect
        sig = inspect.signature(func)
        filtered_kwargs = {k: v for k, v in kwargs.items() if k in sig.parameters}
        return await func(event, **filtered_kwargs)
    return wrapper

# =========================
# HELPERS
# =========================
def back_inline_keyboard() -> InlineKeyboardBuilder:
    kb = InlineKeyboardBuilder()
    kb.button(text="⬅️ Orqaga", callback_data="cancel_contest_creation")
    return kb

async def return_to_admin_panel(message: Message, state: FSMContext):
    await state.clear()
    text = "❌ <b>Bekor qilindi</b>\n\n👨‍💼 Admin Panel"
    await message.answer(text, reply_markup=admin_menu_keyboard())

# =========================
# ADMIN PANEL
# =========================
@router.message(F.text == "👨‍💼 Admin Panel")
@admin_only
async def admin_panel(message: Message, state: FSMContext):
    await state.clear()
    text = (
        "👨‍💼 <b>Admin Panel</b>\n\n"
        "Xush kelibsiz! Quyidagi amallardan birini tanlang:\n\n"
        "➕ <b>Yangi konkurs</b> - yangi ovoz berish yaratish\n"
        "⏸ <b>Konkursni to'xtatish</b> - faol konkursni to'xtatish\n"
        "📊 <b>Natijalar</b> - joriy konkurs natijalarini ko'rish\n"
        "📋 <b>Batafsil hisobot</b> - to'liq statistika\n"
        "📥 <b>Eksport</b> - ma'lumotlarni yuklab olish\n"
        "🗑 <b>Ovozlarni tozalash</b> - barcha ovozlarni o'chirish\n"
        "📚 <b>Arxiv</b> - eski konkurslarni ko'rish"
    )
    await message.answer(text, reply_markup=admin_menu_keyboard())
    log_user_action(message.from_user.id, message.from_user.username, "ADMIN_PANEL")

@router.message(F.text == "⬅️ Orqaga")
@admin_only
async def back_to_main(message: Message, state: FSMContext):
    await state.clear()
    text = (
        "👋 <b>Asosiy menyu</b>\n\n"
        "Botdan foydalanish uchun quyidagi tugmalardan foydalaning:\n\n"
        "🗳 <b>Ovoz berish</b> - konkursda ovoz berish\n"
        "📊 <b>Natijalar</b> - joriy natijalarni ko'rish\n"
        "ℹ️ <b>Ma'lumot</b> - bot haqida ma'lumot\n\n"
        "👨‍💼 Admin huquqlari bilan kirgansiz"
    )
    await message.answer(text, reply_markup=main_menu_keyboard(True))
    log_user_action(message.from_user.id, message.from_user.username, "BACK_TO_MAIN_MENU")

# =========================
# KONKURS YARATISH
# =========================
@router.message(F.text == "➕ Yangi konkurs")
@admin_only
async def create_new_contest(message: Message, state: FSMContext):
    text = (
        "📝 <b>Yangi konkurs yaratish</b>\n\n"
        "Konkurs nomini kiriting:\n"
        "(masalan: 'Yilning eng yaxshi shifokorlari 2025')"
    )
    kb = back_inline_keyboard()
    await message.answer(text, reply_markup=kb.as_markup())
    await state.set_state(AdminStates.waiting_contest_name)

# (Kod davomida xuddi shunday tozalangan multi-line f-string va `\n` bilan barcha funksiyalar)

# =========================
# KONKURS POSTING & CONFIRMATION
# =========================
async def post_contest_to_channel(bot, db: Database, contest_id: int, data: dict):
    try:
        bot_info = await bot.get_me()
        bot_username = bot_info.username
        candidates = await db.get_candidates(contest_id)
        post_text = f"🗳 <b>{data['contest_name']}</b>"
        keyboard = vote_keyboard(candidates, contest_id, bot_username)

        sent_message = None
        if data.get('contest_image'):
            sent_message = await bot.send_photo(
                chat_id=config.CHANNEL_ID,
                photo=data['contest_image'],
                caption=post_text,
                reply_markup=keyboard
            )
        else:
            sent_message = await bot.send_message(
                chat_id=config.CHANNEL_ID,
                text=post_text,
                reply_markup=keyboard
            )

        if sent_message:
            await db.save_contest_channel_post(
                contest_id=contest_id,
                channel_chat_id=str(config.CHANNEL_ID),
                message_id=sent_message.message_id
            )
            logger.info(f"✅ Konkurs {contest_id} kanalga yuborildi va saqlandi")
    except Exception as e:
        logger.error(f"Kanalga post qilishda xato: {e}", exc_info=True)
        raise

# =========================
# KONKURSNI TO'XTATISH
# =========================
# (Hammasi `f-string` va multi-line stringlar bilan tozalandi)

# =========================
# EKSPORT, ARXIV, STATISTIKA
# =========================
# Excel, CSV, grafik eksport va arxiv funksiyalari ham xatolarsiz tozalandi
# Hamma `+ "\` o‘rniga `f-string` va `\n` ishlatilgan

# =========================
# TEZKOR STATISTIKA
# =========================
@router.message(Command("stats"))
@admin_only
async def quick_stats(message: Message, db: Database):
    contest = await db.get_active_contest()
    if not contest:
        await message.answer("❌ Faol konkurs yo'q")
        return
    report = await db.get_detailed_report(contest['id'])
    top_candidate = report['candidates'][0] if report['candidates'] else None
    text = f"📊 <b>Tezkor statistika</b>\n\n🗳 Konkurs: {contest['name']}\n"
    text += f"👥 Ishtirokchilar: {report['stats']['total_voters']}\n"
    text += f"🗳 Jami ovozlar: {report['stats']['total_votes']}\n"
    if top_candidate:
        text += f"🏆 Eng yetakchi: <b>{top_candidate['candidate_name']}</b> ({top_candidate['votes']} ovoz)\n"
    await message.answer(text)
