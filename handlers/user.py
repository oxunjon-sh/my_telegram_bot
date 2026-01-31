from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from datetime import datetime
import logging

from database import Database
from keyboards import main_menu_keyboard, confirm_vote_keyboard, vote_keyboard
from utils import (
    is_admin, format_results_text, log_user_action,
    format_vote_count, get_current_datetime, format_datetime
)
import config

router = Router()
logger = logging.getLogger(__name__)


class VotingStates(StatesGroup):
    waiting_for_subscription = State()
    selecting_candidate = State()
    confirming_vote = State()


# ==================== KANAL POSTINI YANGILASH ====================

async def update_channel_post(bot, db: Database, contest_id: int):
    """
    Kanal postidagi ovozlar sonini yangilash

    REAL-TIME UPDATE!
    Har safar ovoz berilganda kanalda ovozlar soni avtomatik yangilanadi.

    Misol:
    - Dr.Aziz - 234 → Dr.Aziz - 235
    - Dr.Nodir - 2.3K → Dr.Nodir - 2.4K
    """
    try:
        # Kanal post ma'lumotlarini olish
        post_info = await db.get_contest_channel_post(contest_id)

        if not post_info:
            logger.warning(f"Konkurs {contest_id} uchun kanal post topilmadi")
            return

        # Yangi ovozlar soni bilan nomzodlarni olish
        candidates = await db.get_candidates(contest_id)

        # Bot username
        bot_info = await bot.get_me()
        bot_username = bot_info.username

        # Yangi keyboard yaratish (ovozlar soni bilan)
        new_keyboard = vote_keyboard(candidates, contest_id, bot_username)

        # Kanal postini yangilash (faqat keyboard)
        await bot.edit_message_reply_markup(
            chat_id=post_info['chat_id'],
            message_id=post_info['message_id'],
            reply_markup=new_keyboard
        )

        logger.info(f"✅ Kanal post yangilandi: Contest {contest_id}, "
                    f"Chat {post_info['chat_id']}, Msg {post_info['message_id']}")

    except Exception as e:
        # Xatolik bo'lsa ham ovoz saqlanadi - post yangilanmaydi
        logger.error(f"Kanal postini yangilashda xato (Contest {contest_id}): {e}")


# ==================== START KOMANDA ====================

@router.message(Command("start"))
async def cmd_start(message: Message, db: Database, state: FSMContext):
    """Start komandasi - Deep link"""
    user = message.from_user
    await db.update_user_activity(user.id, user.username, user.first_name, user.last_name)
    is_user_admin = is_admin(user.id)

    args = message.text.split()
    if len(args) > 1 and args[1].startswith("vote_"):
        try:
            parts = args[1].split("_")
            contest_id = int(parts[1])
            candidate_id = int(parts[2])
            logger.info(f"Deep link: User {user.id}, Contest {contest_id}, Candidate {candidate_id}")

            contest = await db.get_contest_by_id(contest_id)
            if not contest or not contest['is_active']:
                await message.answer("❌ Bu konkurs tugagan yoki faol emas!",
                                     reply_markup=main_menu_keyboard(is_user_admin))
                return

            now = get_current_datetime()
            if now < contest['start_date']:
                await message.answer(
                    f"⏰ Konkurs hali boshlanmagan!\n📅 Boshlanish: {format_datetime(contest['start_date'])}",
                    reply_markup=main_menu_keyboard(is_user_admin))
                return
            if now > contest['end_date']:
                await message.answer("⌛️ Konkurs tugagan!", reply_markup=main_menu_keyboard(is_user_admin))
                return
            if await db.has_voted(contest_id, user.id):
                await message.answer("✅ Siz allaqachon ovoz bergansiz!",
                                     reply_markup=main_menu_keyboard(is_user_admin))
                return

            await show_contest_post_deep_link(message, db, state, contest_id, candidate_id)
            return
        except Exception as e:
            logger.error(f"Deep link xato: {e}")

    welcome_text = f"""
👋 <b>Assalomu alaykum, {user.first_name}!</b>

🗳 <b>Ovoz berish botiga xush kelibsiz!</b>

<b>Botdan foydalanish:</b>
1️⃣ Kerakli kanallarga obuna bo'ling
2️⃣ "🗳 Ovoz berish" tugmasini bosing
3️⃣ O'zingizga yoqqan nomzodni tanlang

📊 Natijalarni real vaqtda kuzatib boring!
"""
    if is_user_admin:
        welcome_text += "\n👨‍💼 <i>Siz admin huquqlariga egasiz</i>"

    await message.answer(welcome_text, reply_markup=main_menu_keyboard(is_user_admin))
    log_user_action(user.id, user.username, "START")


async def show_contest_post_deep_link(message: Message, db: Database, state: FSMContext,
                                      contest_id: int, candidate_id: int):
    """Deep link orqali ovoz berish"""
    contest = await db.get_contest_by_id(contest_id)
    candidates = await db.get_candidates(contest_id)

    # SODDA POST - faqat konkurs nomi
    post_text = f"🗳 <b>{contest['name']}</b>"

    if contest.get('image_file_id'):
        await message.answer_photo(photo=contest['image_file_id'], caption=post_text)
    else:
        await message.answer(post_text)

    text = "👇 O'zingizga yoqqan nomzodni tanlang va ovoz bering:"
    kb = InlineKeyboardBuilder()
    for candidate in candidates:
        vote_count = candidate.get('vote_count', 0)
        formatted_count = format_vote_count(vote_count)
        kb.button(
            text=f"👤 {candidate['name']} - {formatted_count}",
            callback_data=f"vote_deep_{contest_id}_{candidate['id']}"
        )
    kb.adjust(1)
    await message.answer(text, reply_markup=kb.as_markup())
    await state.update_data(contest_id=contest_id, from_deep_link=True)


async def show_contest_post_for_voting(message: Message, db: Database, contest_id: int, state: FSMContext):
    """Bot ichidan ovoz berish"""
    contest = await db.get_contest_by_id(contest_id)
    candidates = await db.get_candidates(contest_id)

    if not candidates:
        await message.answer("❌ Nomzodlar qo'shilmagan.")
        return

    # SODDA POST - faqat konkurs nomi
    post_text = f"🗳 <b>{contest['name']}</b>"

    kb = InlineKeyboardBuilder()
    for candidate in candidates:
        vote_count = candidate.get('vote_count', 0)
        formatted_count = format_vote_count(vote_count)
        kb.button(
            text=f"👤 {candidate['name']} - {formatted_count}",
            callback_data=f"vote_{candidate['id']}"
        )
    kb.adjust(1)

    if contest.get('image_file_id'):
        await message.answer_photo(photo=contest['image_file_id'], caption=post_text, reply_markup=kb.as_markup())
    else:
        await message.answer(post_text, reply_markup=kb.as_markup())

    await state.update_data(contest_id=contest_id)
    await state.set_state(VotingStates.selecting_candidate)
    log_user_action(message.from_user.id, message.from_user.username, "VIEW_CANDIDATES")


# ==================== CALLBACKS ====================

@router.callback_query(F.data.startswith("vote_deep_"))
async def vote_from_deep_link(callback: CallbackQuery, db: Database, state: FSMContext):
    """
    Deep link orqali ovoz berish

    YANGI: Ovoz bergandan keyin kanal postini yangilash!
    """
    await callback.answer()
    parts = callback.data.split("_")
    contest_id = int(parts[2])
    candidate_id = int(parts[3])
    user = callback.from_user

    # Kanal obunasini tekshirish
    channels = await db.get_contest_channels(contest_id)
    not_subscribed = []

    for channel in channels or []:
        try:
            member = await callback.bot.get_chat_member(channel['channel_id'], user.id)
            if member.status in ['left', 'kicked']:
                not_subscribed.append(channel)
        except:
            not_subscribed.append(channel)

    if not_subscribed:
        text = "⚠️ <b>Ovoz berish uchun quyidagi kanallarga obuna bo'ling:</b>\n\n"
        kb = InlineKeyboardBuilder()
        for i, channel in enumerate(not_subscribed, 1):
            kb.button(text=f"📢 {i}. {channel['channel_name']}", url=channel['channel_link'])
        kb.button(text="✅ Obunani tekshirish", callback_data=f"check_sub_deep_{contest_id}_{candidate_id}")
        kb.adjust(1)
        await callback.message.answer(text, reply_markup=kb.as_markup())
        await state.update_data(contest_id=contest_id, candidate_id=candidate_id)
        return

    # Nomzodni topish
    candidates = await db.get_candidates(contest_id)
    candidate = next((c for c in candidates if c['id'] == candidate_id), None)
    if not candidate:
        await callback.message.answer("❌ Nomzod topilmadi!")
        return

    # Ovoz qo'shish
    success = await db.add_vote(contest_id, candidate_id, user.id, user.username)

    if success:
        # ✅ YANGI: Kanal postini yangilash!
        await update_channel_post(callback.bot, db, contest_id)

        text = f"✅ <b>Ovozingiz qabul qilindi!</b>\n\nSiz <b>{candidate['name']}</b> ga ovoz berdingiz.\n\nRahmat! 🎉"
        await callback.message.answer(text, reply_markup=main_menu_keyboard(is_admin(user.id)))
        log_user_action(user.id, user.username, f"VOTED: {candidate['name']}")
    else:
        await callback.message.answer("❌ Siz allaqachon ovoz bergansiz!")


@router.callback_query(F.data.startswith("check_sub_deep_"))
async def check_subscription_deep(callback: CallbackQuery, db: Database, state: FSMContext):
    """Obunani tekshirish (deep link)"""
    await callback.answer("Tekshirilmoqda...")

    parts = callback.data.split("_")
    contest_id = int(parts[3])
    candidate_id = int(parts[4])

    channels = await db.get_contest_channels(contest_id)
    not_subscribed = []

    for channel in channels or []:
        try:
            member = await callback.bot.get_chat_member(channel['channel_id'], callback.from_user.id)
            if member.status in ['left', 'kicked']:
                not_subscribed.append(channel)
        except:
            not_subscribed.append(channel)

    if not_subscribed:
        await callback.answer("❌ Barcha kanallarga obuna bo'ling!", show_alert=True)
        text = "⚠️ <b>Obuna bo'lishni unutmang!</b>\n\nQuyidagi kanallarga obuna bo'ling:\n"
        kb = InlineKeyboardBuilder()
        for i, channel in enumerate(not_subscribed, 1):
            kb.button(text=f"📢 {i}. {channel['channel_name']}", url=channel['channel_link'])
        kb.button(text="🔄 Qayta tekshirish", callback_data=f"check_sub_deep_{contest_id}_{candidate_id}")
        kb.adjust(1)
        try:
            await callback.message.edit_text(text, reply_markup=kb.as_markup())
        except:
            await callback.message.answer(text, reply_markup=kb.as_markup())
    else:
        # Obuna tasdiqlandi - ovoz berish
        await callback.answer("✅ Obuna tasdiqlandi!", show_alert=True)

        candidates = await db.get_candidates(contest_id)
        candidate = next((c for c in candidates if c['id'] == candidate_id), None)

        if not candidate:
            await callback.message.answer("❌ Nomzod topilmadi!")
            return

        success = await db.add_vote(contest_id, candidate_id, callback.from_user.id, callback.from_user.username)

        if success:
            # ✅ YANGI: Kanal postini yangilash!
            await update_channel_post(callback.bot, db, contest_id)

            text = f"✅ <b>Ovozingiz qabul qilindi!</b>\n\nSiz <b>{candidate['name']}</b> ga ovoz berdingiz.\n\nRahmat! 🎉"
            await callback.message.edit_text(text)
            log_user_action(callback.from_user.id, callback.from_user.username, f"VOTED: {candidate['name']}")
        else:
            await callback.message.edit_text("❌ Siz allaqachon ovoz bergansiz!")


@router.callback_query(F.data.startswith("vote_"))
async def select_candidate(callback: CallbackQuery, db: Database, state: FSMContext):
    """Nomzodni tanlash (bot ichidan)"""
    await callback.answer()
    candidate_id = int(callback.data.split("_")[1])
    data = await state.get_data()
    contest_id = data.get('contest_id')
    candidates = await db.get_candidates(contest_id)
    candidate = next((c for c in candidates if c['id'] == candidate_id), None)
    if not candidate:
        await callback.message.answer("❌ Nomzod topilmadi!")
        return

    text = f"❓ <b>Tasdiqlang</b>\n\nSiz <b>{candidate['name']}</b> ga ovoz berasiz?\n\nOvozingizni tasdiqlaysizmi?"

    if callback.message.photo:
        await callback.message.answer(text, reply_markup=confirm_vote_keyboard(candidate_id))
    else:
        await callback.message.edit_text(text, reply_markup=confirm_vote_keyboard(candidate_id))

    await state.update_data(candidate_id=candidate_id)
    await state.set_state(VotingStates.confirming_vote)


@router.callback_query(F.data.startswith("confirm_vote_"))
async def confirm_vote(callback: CallbackQuery, db: Database, state: FSMContext):
    """
    Ovozni tasdiqlash

    YANGI: Ovoz bergandan keyin kanal postini yangilash!
    """
    await callback.answer()
    candidate_id = int(callback.data.split("_")[2])
    data = await state.get_data()
    contest_id = data.get('contest_id')
    user = callback.from_user

    # Ovoz qo'shish
    success = await db.add_vote(contest_id, candidate_id, user.id, user.username)

    if success:
        # ✅ YANGI: Kanal postini yangilash!
        await update_channel_post(callback.bot, db, contest_id)

        candidates = await db.get_candidates(contest_id)
        candidate = next((c for c in candidates if c['id'] == candidate_id), None)
        text = f"✅ <b>Ovozingiz qabul qilindi!</b>\nSiz <b>{candidate['name']}</b> ga ovoz berdingiz.\n\nRahmat! 🎉"
        await callback.message.edit_text(text)
        log_user_action(user.id, user.username, f"VOTED: {candidate['name']}")
    else:
        await callback.message.edit_text("❌ Siz allaqachon ovoz bergansiz!")

    await state.clear()


@router.callback_query(F.data == "cancel_vote")
async def cancel_vote(callback: CallbackQuery, state: FSMContext):
    """Bekor qilish"""
    await callback.answer("Bekor qilindi")
    await callback.message.delete()
    await state.clear()


# ==================== OVOZ BERISH TUGMASI ====================

@router.message(F.text == "🗳 Ovoz berish")
async def vote_button(message: Message, db: Database, state: FSMContext):
    """Bot ichidan ovoz berish tugmasi"""
    user = message.from_user
    user_is_admin = is_admin(user.id)

    if not await db.check_rate_limit(user.id):
        await message.answer("⏳ Iltimos, biroz kuting...")
        return

    await db.update_user_activity(user.id, user.username)

    contest = await db.get_active_contest()
    if not contest:
        await message.answer("❌ Hozirda faol konkurs yo'q.", reply_markup=main_menu_keyboard(user_is_admin))
        return

    now = get_current_datetime()
    if now < contest['start_date']:
        await message.answer(f"⏰ Konkurs hali boshlanmagan!\n📅 Boshlanish: {format_datetime(contest['start_date'])}")
        return
    if now > contest['end_date']:
        await message.answer("⌛️ Konkurs tugagan!")
        return
    if await db.has_voted(contest['id'], user.id):
        await message.answer("✅ Siz allaqachon ovoz bergansiz!\n📊 Natijalarni ko'ring.",
                             reply_markup=main_menu_keyboard(user_is_admin))
        return

    # Kanal obunasini tekshirish
    channels = await db.get_contest_channels(contest['id'])
    not_subscribed = []
    for channel in channels or []:
        try:
            member = await message.bot.get_chat_member(channel['channel_id'], user.id)
            if member.status in ['left', 'kicked']:
                not_subscribed.append(channel)
        except:
            not_subscribed.append(channel)

    if not_subscribed:
        text = "⚠️ <b>Ovoz berish uchun quyidagi kanallarga obuna bo'ling:</b>\n\n"
        kb = InlineKeyboardBuilder()
        for i, channel in enumerate(not_subscribed, 1):
            kb.button(text=f"📢 {i}. {channel['channel_name']}", url=channel['channel_link'])
        kb.button(text="✅ Obunani tekshirish", callback_data="check_subscription_vote")
        kb.adjust(1)
        await message.answer(text, reply_markup=kb.as_markup())
        await state.update_data(contest_id=contest['id'])
        await state.set_state(VotingStates.waiting_for_subscription)
        return

    await show_contest_post_for_voting(message, db, contest['id'], state)


@router.callback_query(F.data == "check_subscription_vote")
async def check_subscription_vote(callback: CallbackQuery, db: Database, state: FSMContext):
    """Obunani tekshirish (bot ichidan)"""
    await callback.answer("Tekshirilmoqda...")
    data = await state.get_data()
    contest_id = data.get('contest_id')
    if not contest_id:
        await callback.message.answer("❌ Xatolik. Qaytadan boshlang.")
        await state.clear()
        return

    channels = await db.get_contest_channels(contest_id)
    not_subscribed = []
    for channel in channels or []:
        try:
            member = await callback.bot.get_chat_member(channel['channel_id'], callback.from_user.id)
            if member.status in ['left', 'kicked']:
                not_subscribed.append(channel)
        except:
            not_subscribed.append(channel)

    if not_subscribed:
        await callback.answer("❌ Barcha kanallarga obuna bo'ling!", show_alert=True)
        text = "⚠️ <b>Obuna bo'lishni unutmang!</b>\n\nQuyidagi kanallarga obuna bo'ling:\n"
        kb = InlineKeyboardBuilder()
        for i, channel in enumerate(not_subscribed, 1):
            kb.button(text=f"📢 {i}. {channel['channel_name']}", url=channel['channel_link'])
        kb.button(text="🔄 Qayta tekshirish", callback_data="check_subscription_vote")
        kb.adjust(1)
        try:
            await callback.message.edit_text(text, reply_markup=kb.as_markup())
        except:
            await callback.message.answer(text, reply_markup=kb.as_markup())
    else:
        await callback.answer("✅ Obuna tasdiqlandi!", show_alert=True)
        await callback.message.delete()
        await show_contest_post_for_voting(callback.message, db, contest_id, state)


# ==================== NATIJALAR ====================

@router.message(F.text == "📊 Natijalar")
async def show_results(message: Message, db: Database):
    """Natijalarni ko'rish"""
    contest = await db.get_active_contest()
    if not contest:
        await message.answer("❌ Faol konkurs yo'q")
        return

    results = await db.get_vote_results(contest['id'])
    text = format_results_text(results, contest['name'])
    await message.answer(text)
    log_user_action(message.from_user.id, message.from_user.username, "VIEW_RESULTS")


# ==================== MA'LUMOT ====================

@router.message(F.text == "ℹ️ Ma'lumot")
async def show_info(message: Message, db: Database):
    """Bot haqida ma'lumot"""
    contest = await db.get_active_contest()
    text = "ℹ️ <b>Bot haqida</b>\n\n"
    if contest:
        text += f"🗳 <b>Joriy konkurs:</b> {contest['name']}\n"
        text += f"📅 Boshlanish: {format_datetime(contest['start_date'])}\n"
        text += f"⏰ Tugash: {format_datetime(contest['end_date'])}\n\n"
        stats = await db.get_detailed_report(contest['id'])
        text += f"👥 Ishtirokchilar: {stats['stats']['total_voters']}\n"
        text += f"🗳 Jami ovozlar: {stats['stats']['total_votes']}\n\n"
    else:
        text += "❌ Hozirda faol konkurs yo'q\n\n"

    text += "📌 <b>Qoidalar:</b>\n"
    text += "• Har bir foydalanuvchi 1 marta ovoz beradi\n"
    text += "• PUBLIC kanallarga obuna bo'lish shart\n"
    text += "• Natijalar real vaqtda yangilanadi\n"
    text += "• Ovozlar soni kanalda ham ko'rinadi\n"

    await message.answer(text)