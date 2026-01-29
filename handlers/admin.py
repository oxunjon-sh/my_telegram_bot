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
    archive_keyboard, yes_no_keyboard, back_keyboard,
    vote_keyboard
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


class AdminStates(StatesGroup):
    # Konkurs yaratish
    waiting_contest_name = State()
    waiting_contest_image = State()
    waiting_start_date = State()
    waiting_end_date = State()

    # Kanal qo'shish
    waiting_channel_count = State()
    waiting_channel_id = State()
    waiting_channel_name = State()
    waiting_channel_link = State()

    # Nomzodlar qo'shish
    waiting_candidate_count = State()
    waiting_candidate_name = State()

    # Tasdiqlash
    confirm_contest = State()


def admin_only(func):
    """Admin huquqlarini tekshirish"""

    async def wrapper(event, **kwargs):
        user_id = event.from_user.id
        if not is_admin(user_id):
            if isinstance(event, Message):
                await event.answer("❌ Sizda admin huquqi yo'q!")
            else:
                await event.answer("❌ Ruxsat yo'q!", show_alert=True)
            return
        import inspect
        sig = inspect.signature(func)
        filtered_kwargs = {k: v for k, v in kwargs.items() if k in sig.parameters}
        return await func(event, **filtered_kwargs)

    return wrapper


# ==================== YORDAMCHI FUNKSIYALAR ====================

def back_inline_keyboard() -> InlineKeyboardBuilder:
    """⬅️ Orqaga inline tugmasi"""
    kb = InlineKeyboardBuilder()
    kb.button(text="⬅️ Orqaga", callback_data="cancel_contest_creation")
    return kb


async def return_to_admin_panel(message: Message, state: FSMContext):
    """Admin panelga qaytish"""
    await state.clear()
    text = "❌ <b>Bekor qilindi</b>\n\n👨‍💼 Admin Panel"
    await message.answer(text, reply_markup=admin_menu_keyboard())


# ==================== ADMIN PANEL ====================

@router.message(F.text == "👨‍💼 Admin Panel")
@admin_only
async def admin_panel(message: Message, state: FSMContext):
    """Admin panel"""
    await state.clear()
    text = """
👨‍💼 <b>Admin Panel</b>

Xush kelibsiz! Quyidagi amallardan birini tanlang:

➕ <b>Yangi konkurs</b> - yangi ovoz berish yaratish
⏸ <b>Konkursni to'xtatish</b> - faol konkursni to'xtatish
📊 <b>Natijalar</b> - joriy konkurs natijalarini ko'rish
📋 <b>Batafsil hisobot</b> - to'liq statistika
📥 <b>Eksport</b> - ma'lumotlarni yuklab olish
🗑 <b>Ovozlarni tozalash</b> - barcha ovozlarni o'chirish
📚 <b>Arxiv</b> - eski konkurslarni ko'rish
"""
    await message.answer(text, reply_markup=admin_menu_keyboard())
    log_user_action(message.from_user.id, message.from_user.username, "ADMIN_PANEL")


@router.message(F.text == "⬅️ Orqaga")
@admin_only
async def back_to_main(message: Message, state: FSMContext):
    """Orqaga tugmasi - Asosiy menyuga qaytish"""
    await state.clear()

    text = """
👋 <b>Asosiy menyu</b>

Botdan foydalanish uchun quyidagi tugmalardan foydalaning:

🗳 <b>Ovoz berish</b> - konkursda ovoz berish
📊 <b>Natijalar</b> - joriy natijalarni ko'rish
ℹ️ <b>Ma'lumot</b> - bot haqida ma'lumot

👨‍💼 Admin huquqlari bilan kirgansiz
"""

    await message.answer(text, reply_markup=main_menu_keyboard(True))
    log_user_action(message.from_user.id, message.from_user.username, "BACK_TO_MAIN_MENU")


# ==================== KONKURS YARATISH ====================

@router.message(F.text == "➕ Yangi konkurs")
@admin_only
async def create_new_contest(message: Message, state: FSMContext):
    """Yangi konkurs yaratish boshlash"""
    text = """
📝 <b>Yangi konkurs yaratish</b>

Konkurs nomini kiriting:
(masalan: "Yilning eng yaxshi shifokorlari 2025")
"""
    kb = back_inline_keyboard()
    await message.answer(text, reply_markup=kb.as_markup())
    await state.set_state(AdminStates.waiting_contest_name)


@router.callback_query(F.data == "cancel_contest_creation")
@admin_only
async def cancel_contest_creation(callback: CallbackQuery, state: FSMContext):
    """Konkurs yaratishni bekor qilish"""
    await callback.answer("Bekor qilindi")
    await callback.message.delete()
    await return_to_admin_panel(callback.message, state)


@router.message(AdminStates.waiting_contest_name)
@admin_only
async def process_contest_name(message: Message, state: FSMContext):
    """Konkurs nomini saqlash"""
    await state.update_data(contest_name=message.text)

    # YANGI: Tavsifni so'ramaslik - to'g'ridan-to'g'ri rasmga
    text = """
🖼 Konkurs rasmini yuboring:
(JPG, PNG format)

Yoki /skip yozing (ixtiyoriy)
"""
    kb = back_inline_keyboard()
    await message.answer(text, reply_markup=kb.as_markup())
    await state.set_state(AdminStates.waiting_contest_image)


@router.message(AdminStates.waiting_contest_image, F.photo)
@admin_only
async def process_contest_image(message: Message, state: FSMContext):
    """Konkurs rasmini saqlash"""
    photo = message.photo[-1]
    file_id = photo.file_id
    await state.update_data(contest_image=file_id)

    text = """
📅 Boshlanish sana va vaqtini kiriting:

Format: <code>DD.MM.YYYY HH:MM</code>
Masalan: <code>20.01.2026 09:00</code>
"""
    kb = back_inline_keyboard()
    await message.answer(text, reply_markup=kb.as_markup())
    await state.set_state(AdminStates.waiting_start_date)


@router.message(AdminStates.waiting_contest_image, F.text == "/skip")
@admin_only
async def skip_contest_image(message: Message, state: FSMContext):
    """Rasmni o'tkazib yuborish"""
    await state.update_data(contest_image=None)

    text = """
📅 Boshlanish sana va vaqtini kiriting:

Format: <code>DD.MM.YYYY HH:MM</code>
Masalan: <code>20.01.2026 09:00</code>
"""
    kb = back_inline_keyboard()
    await message.answer(text, reply_markup=kb.as_markup())
    await state.set_state(AdminStates.waiting_start_date)


@router.message(AdminStates.waiting_contest_image)
@admin_only
async def invalid_image(message: Message):
    """Noto'g'ri rasm formati"""
    kb = back_inline_keyboard()
    await message.answer(
        "❌ Iltimos, rasm yuboring yoki /skip yozing!",
        reply_markup=kb.as_markup()
    )


@router.message(AdminStates.waiting_start_date)
@admin_only
async def process_start_date(message: Message, state: FSMContext):
    """Boshlanish sanasini saqlash - TIMEZONE SUPPORT"""
    try:
        start_date = parse_datetime(message.text)

        # 🔍 DEBUG - vaqtni tekshirish (UTC da)
        now = get_current_datetime()
        logger.info(f"🕐 Kiritilgan boshlanish vaqti (UTC): {start_date}")
        logger.info(f"🕐 Hozirgi vaqt (UTC): {now}")
        logger.info(f"🕐 Farq: {start_date - now}")

        # Agar o'tgan vaqt kiritilsa
        if start_date < now:
            kb = back_inline_keyboard()
            await message.answer(
                "❌ O'tgan vaqtni kirita olmaysiz!\n\n"
                f"Hozirgi vaqt: {format_datetime(now)} (Toshkent)\n"
                f"Siz kiritdingiz: {format_datetime(start_date)} (Toshkent)\n\n"
                "Iltimos, kelajak vaqtni kiriting:",
                reply_markup=kb.as_markup()
            )
            return

        await state.update_data(start_date=start_date)

        text = """
⏰ Tugash sana va vaqtini kiriting:

Format: <code>DD.MM.YYYY HH:MM</code>
Masalan: <code>30.01.2026 23:59</code>
"""
        kb = back_inline_keyboard()
        await message.answer(text, reply_markup=kb.as_markup())
        await state.set_state(AdminStates.waiting_end_date)
    except ValueError:
        kb = back_inline_keyboard()
        await message.answer(
            "❌ Noto'g'ri format!\n\n"
            "Iltimos, <code>DD.MM.YYYY HH:MM</code> formatida kiriting.\n"
            "Masalan: <code>20.01.2026 09:00</code>",
            reply_markup=kb.as_markup()
        )


@router.message(AdminStates.waiting_end_date)
@admin_only
async def process_end_date(message: Message, state: FSMContext, db: Database):
    """Tugash sanasini saqlash"""
    try:
        end_date = parse_datetime(message.text)
        data = await state.get_data()
        start_date = data['start_date']

        if end_date <= start_date:
            kb = back_inline_keyboard()
            await message.answer(
                "❌ Tugash sanasi boshlanish sanasidan katta bo'lishi kerak!\n"
                "Qaytadan kiriting:",
                reply_markup=kb.as_markup()
            )
            return

        await state.update_data(end_date=end_date)

        text = """
📢 Nechta kanal talab qilinadi?

Raqam kiriting (0 - kanal talabi yo'q):
Masalan: <code>2</code>
"""
        kb = back_inline_keyboard()
        await message.answer(text, reply_markup=kb.as_markup())
        await state.set_state(AdminStates.waiting_channel_count)
    except ValueError:
        kb = back_inline_keyboard()
        await message.answer(
            "❌ Noto'g'ri format!\n"
            "Iltimos, <code>DD.MM.YYYY HH:MM</code> formatida kiriting.",
            reply_markup=kb.as_markup()
        )


@router.message(AdminStates.waiting_channel_count)
@admin_only
async def process_channel_count(message: Message, state: FSMContext):
    """Kanallar sonini saqlash"""
    try:
        count = int(message.text)

        if count < 0:
            kb = back_inline_keyboard()
            await message.answer(
                "❌ Raqam 0 yoki undan katta bo'lishi kerak!",
                reply_markup=kb.as_markup()
            )
            return

        await state.update_data(channel_count=count, current_channel=0, channels=[])

        if count == 0:
            await ask_candidate_count(message, state)
        else:
            await ask_channel_info(message, state, 1, count)
    except ValueError:
        kb = back_inline_keyboard()
        await message.answer(
            "❌ Iltimos, raqam kiriting!",
            reply_markup=kb.as_markup()
        )


async def ask_channel_info(message: Message, state: FSMContext, current: int, total: int):
    """Kanal ma'lumotlarini so'rash"""
    text = f"""
📢 <b>Kanal {current}/{total}</b>

Kanal ID yoki username ni kiriting:

<b>Misol:</b>
• <code>@mychannel</code>
• <code>-1001234567890</code>

⚠️ <b>MUHIM:</b>
• Bot kanal adminlarida bo'lishi kerak!
• Kanal PUBLIC bo'lishi kerak!
"""
    kb = back_inline_keyboard()
    await message.answer(text, reply_markup=kb.as_markup())
    await state.set_state(AdminStates.waiting_channel_id)


@router.message(AdminStates.waiting_channel_id)
@admin_only
async def process_channel_id(message: Message, state: FSMContext):
    """
    Kanal ID ni tekshirish va to'g'ri NUMERIC ID ni olish

    Bot faqat NUMERIC ID bilan ishlaydi: -1001234567890
    Username (@kanal) ishlamaydi get_chat_member da
    """
    channel_input = message.text.strip()

    try:
        # Kanal haqida ma'lumot olish
        chat = await message.bot.get_chat(channel_input)

        # NUMERIC ID ni olish (bu har doim ishlaydi)
        numeric_id = chat.id

        logger.info(f"Kanal topildi: {chat.title}, ID: {numeric_id}, Type: {chat.type}")

        # Faqat channel yoki supergroup ekanini tekshirish
        if chat.type not in ['channel', 'supergroup']:
            kb = back_inline_keyboard()
            await message.answer(
                f"❌ Bu kanal emas! Type: {chat.type}\n"
                "Iltimos, PUBLIC kanal yoki supergrup ID sini kiriting.",
                reply_markup=kb.as_markup()
            )
            return

        # NUMERIC ID ni saqlash (STRING formatda - database VARCHAR)
        await state.update_data(
            temp_channel_id=str(numeric_id),  # ✅ INT → STR
            temp_channel_title=chat.title  # Avtomatik nom
        )

        # Nomni tasdiqlash yoki o'zgartirish
        text = f"""
✅ Kanal topildi!

📢 <b>Nom:</b> {chat.title}
🆔 <b>ID:</b> <code>{numeric_id}</code>

Bu nomni qoldirasizmi yoki o'zgartirmoqchimisiz?
Nom kiriting (yoki /skip nom o'zgarmaydi):
"""
        kb = back_inline_keyboard()
        await message.answer(text, reply_markup=kb.as_markup())
        await state.set_state(AdminStates.waiting_channel_name)

    except Exception as e:
        logger.error(f"Kanal topilmadi: {channel_input}, Xato: {e}")
        kb = back_inline_keyboard()
        await message.answer(
            f"❌ Kanal topilmadi!\n\n"
            f"Xato: {str(e)}\n\n"
            f"Iltimos, to'g'ri kanal ID sini kiriting:\n"
            f"• Username: <code>@mychannel</code>\n"
            f"• Yoki numeric ID: <code>-1001234567890</code>\n\n"
            f"⚠️ Bot kanal adminlarida bo'lishi kerak!",
            reply_markup=kb.as_markup()
        )


@router.message(AdminStates.waiting_channel_name)
@admin_only
async def process_channel_name(message: Message, state: FSMContext):
    """Kanal nomini saqlash yoki avtomatik nomni qoldirish"""
    data = await state.get_data()

    if message.text.strip() == "/skip":
        # Avtomatik nom (chat.title)
        channel_name = data.get('temp_channel_title', 'Kanal')
    else:
        # Custom nom
        channel_name = message.text.strip()

    await state.update_data(temp_channel_name=channel_name)

    text = """
🔗 Kanal linkini kiriting:
(masalan: <code>https://t.me/mychannel</code>)
"""
    kb = back_inline_keyboard()
    await message.answer(text, reply_markup=kb.as_markup())
    await state.set_state(AdminStates.waiting_channel_link)


@router.message(AdminStates.waiting_channel_link)
@admin_only
async def process_channel_link(message: Message, state: FSMContext):
    """Kanal linkini saqlash"""
    link = message.text.strip()

    if not validate_channel_link(link):
        kb = back_inline_keyboard()
        await message.answer(
            "❌ Noto'g'ri link!\n"
            "Link https://t.me/ bilan boshlanishi kerak.",
            reply_markup=kb.as_markup()
        )
        return

    data = await state.get_data()
    channels = data.get('channels', [])

    # MUHIM: channel_id ni STRING formatda saqlash (database VARCHAR)
    channels.append({
        'id': str(data['temp_channel_id']),  # ✅ INT → STR
        'name': data['temp_channel_name'],
        'link': link
    })

    current = len(channels)
    total = data['channel_count']

    await state.update_data(channels=channels)

    if current < total:
        await ask_channel_info(message, state, current + 1, total)
    else:
        await ask_candidate_count(message, state)


async def ask_candidate_count(message: Message, state: FSMContext):
    """Nomzodlar sonini so'rash"""
    text = """
👥 Nechta nomzod bo'ladi?

Raqam kiriting (kamida 2):
"""
    kb = back_inline_keyboard()
    await message.answer(text, reply_markup=kb.as_markup())
    await state.set_state(AdminStates.waiting_candidate_count)


@router.message(AdminStates.waiting_candidate_count)
@admin_only
async def process_candidate_count(message: Message, state: FSMContext):
    """Nomzodlar sonini saqlash"""
    try:
        count = int(message.text)

        if count < 2:
            kb = back_inline_keyboard()
            await message.answer(
                "❌ Kamida 2 ta nomzod bo'lishi kerak!",
                reply_markup=kb.as_markup()
            )
            return

        await state.update_data(candidate_count=count, candidates=[])
        await ask_candidate_name(message, state, 1, count)
    except ValueError:
        kb = back_inline_keyboard()
        await message.answer(
            "❌ Iltimos, raqam kiriting!",
            reply_markup=kb.as_markup()
        )


async def ask_candidate_name(message: Message, state: FSMContext, current: int, total: int):
    """Nomzod nomini so'rash"""
    text = f"""
👤 <b>Nomzod {current}/{total}</b>

Nomzod nomini kiriting:
"""
    kb = back_inline_keyboard()
    await message.answer(text, reply_markup=kb.as_markup())
    await state.set_state(AdminStates.waiting_candidate_name)


@router.message(AdminStates.waiting_candidate_name)
@admin_only
async def process_candidate_name(message: Message, state: FSMContext, db: Database):
    """Nomzod nomini saqlash - TAVSIF YO'Q!"""
    name = message.text.strip()

    data = await state.get_data()
    candidates = data.get('candidates', [])

    # To'g'ridan-to'g'ri saqlash (description yo'q)
    candidates.append({
        'name': name,
        'description': None
    })

    current = len(candidates)
    total = data['candidate_count']

    await state.update_data(candidates=candidates)

    if current < total:
        # Keyingi nomzodni so'rash
        await ask_candidate_name(message, state, current + 1, total)
    else:
        # Barcha nomzodlar kiritildi - preview
        await show_contest_preview(message, state, db)


# ==================== PREVIEW VA TASDIQLASH ====================

async def show_contest_preview(message: Message, state: FSMContext, db: Database):
    """
    Kanalga post qilishdan oldin konkursni ko'rsatish va tasdiqlash
    """
    data = await state.get_data()

    # Preview matni
    text = f"""
📋 <b>KONKURS TAYYORLANDI!</b>

<b>📝 Nom:</b> {data['contest_name']}
<b>🖼 Rasm:</b> {'✅ Bor' if data.get('contest_image') else '❌ Yo\'q'}
<b>📅 Boshlanish:</b> {data['start_date'].strftime('%d.%m.%Y %H:%M')}
<b>⏰ Tugash:</b> {data['end_date'].strftime('%d.%m.%Y %H:%M')}
<b>📢 Kanallar:</b> {len(data.get('channels', []))} ta
<b>👥 Nomzodlar:</b> {len(data['candidates'])} ta

<b>Nomzodlar:</b>
"""

    for i, cand in enumerate(data['candidates'], 1):
        text += f"{i}. {cand['name']}\n"

    text += "\n❓ <b>Kanalga post qilishni tasdiqlaysizmi?</b>"

    # Tasdiqlash tugmalari
    kb = InlineKeyboardBuilder()
    kb.button(text="✅ Ha, kanalga post qiling", callback_data="confirm_post_to_channel")
    kb.button(text="❌ Yo'q, bekor qiling", callback_data="cancel_contest_posting")
    kb.adjust(1)

    # Agar rasm bor bo'lsa, rasm bilan ko'rsatish
    if data.get('contest_image'):
        await message.answer_photo(
            photo=data['contest_image'],
            caption=text,
            reply_markup=kb.as_markup()
        )
    else:
        await message.answer(text, reply_markup=kb.as_markup())

    await state.set_state(AdminStates.confirm_contest)


@router.callback_query(F.data == "confirm_post_to_channel")
@admin_only
async def confirm_post_to_channel(callback: CallbackQuery, state: FSMContext, db: Database):
    """
    Kanalga post qilishni tasdiqlash
    """
    await callback.answer("Konkurs yaratilmoqda...", show_alert=True)

    data = await state.get_data()

    try:
        # Konkurs yaratish (description yo'q - None)
        contest_id = await db.create_contest(
            name=data['contest_name'],
            description=None,  # Tavsif yo'q!
            start_date=data['start_date'],
            end_date=data['end_date'],
            image_file_id=data.get('contest_image')
        )

        # Kanallarni qo'shish
        for channel in data.get('channels', []):
            await db.add_channel_to_contest(
                contest_id,
                channel['id'],
                channel['name'],
                channel['link']
            )

        # Nomzodlarni qo'shish
        for candidate in data['candidates']:
            await db.add_candidate(
                contest_id,
                candidate['name'],
                candidate['description']
            )

        # Kanalga post qilish VA message_id saqlash
        await post_contest_to_channel(callback.bot, db, contest_id, data)

        text = f"""
✅ <b>KONKURS YARATILDI VA KANALGA YUBORILDI!</b>

📝 <b>Nom:</b> {data['contest_name']}
📅 <b>Boshlanish:</b> {data['start_date'].strftime('%d.%m.%Y %H:%M')}
⏰ <b>Tugash:</b> {data['end_date'].strftime('%d.%m.%Y %H:%M')}
📢 <b>Kanallar:</b> {len(data.get('channels', []))}
👥 <b>Nomzodlar:</b> {len(data['candidates'])}

🎉 Konkurs faol! Foydalanuvchilar ovoz bera oladi.
📺 Post kanalga yuborildi!
✨ Ovozlar soni real-time yangilanadi!
"""

        # Eski xabarni o'chirish
        try:
            await callback.message.delete()
        except:
            pass

        await callback.message.answer(text)
        await state.clear()

        # Admin panelga qaytish
        await callback.message.answer(
            "👨‍💼 <b>Admin Panel</b>",
            reply_markup=admin_menu_keyboard()
        )

        log_user_action(
            callback.from_user.id,
            callback.from_user.username,
            f"CREATED_CONTEST: {data['contest_name']}"
        )
    except Exception as e:
        logger.error(f"Konkurs yaratishda xato: {e}", exc_info=True)

        try:
            await callback.message.delete()
        except:
            pass

        await callback.message.answer(
            f"❌ Xatolik yuz berdi: {str(e)}\n\n"
            "Iltimos, qaytadan urinib ko'ring."
        )
        await state.clear()


@router.callback_query(F.data == "cancel_contest_posting")
@admin_only
async def cancel_contest_posting(callback: CallbackQuery, state: FSMContext):
    """
    Kanalga post qilishni bekor qilish
    """
    await callback.answer("Bekor qilindi", show_alert=True)
    await callback.message.delete()
    await state.clear()

    # Admin panelga qaytish
    text = "❌ <b>Konkurs bekor qilindi</b>\n\n👨‍💼 Admin Panel"
    await callback.message.answer(text, reply_markup=admin_menu_keyboard())


async def post_contest_to_channel(bot, db: Database, contest_id: int, data: dict):
    """
    Konkursni kanalga post qilish

    YANGI: Message ID va Chat ID saqlash - real-time update uchun!
    """
    try:
        # Bot username
        bot_info = await bot.get_me()
        bot_username = bot_info.username

        # Nomzodlarni olish (ovoz soni 0 bilan boshlanadi)
        candidates = await db.get_candidates(contest_id)

        # Post matni - SODDA VERSIYA
        post_text = f"🗳 <b>{data['contest_name']}</b>"

        # Inline keyboard - ovozlar soni bilan
        keyboard = vote_keyboard(candidates, contest_id, bot_username)

        # Kanalga yuborish
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

        # YANGI: Message ID va Chat ID saqlash!
        if sent_message:
            await db.save_contest_channel_post(
                contest_id=contest_id,
                channel_chat_id=str(config.CHANNEL_ID),
                message_id=sent_message.message_id
            )
            logger.info(f"✅ Konkurs {contest_id} kanalga yuborildi va saqlandi: "
                        f"{config.CHANNEL_ID}:{sent_message.message_id}")

    except Exception as e:
        logger.error(f"Kanalga post qilishda xato: {e}", exc_info=True)
        raise


# ==================== KONKURSNI TO'XTATISH ====================

@router.message(F.text == "⏸ Konkursni to'xtatish")
@admin_only
async def stop_contest_menu(message: Message, db: Database):
    """AKTIV konkurslarni ko'rsatish va tanlash"""
    contests = await db.get_all_active_contests()

    if not contests:
        await message.answer("❌ Hozirda faol konkurs yo'q")
        return

    text = f"""
⏸ <b>Konkursni To'xtatish</b>

Qaysi konkursni to'xtatmoqchisiz?

<b>Faol konkurslar:</b> {len(contests)} ta
"""

    kb = InlineKeyboardBuilder()

    for contest in contests:
        button_text = f"🗳 {contest['name'][:40]}..." if len(contest['name']) > 40 else f"🗳 {contest['name']}"
        kb.button(
            text=button_text,
            callback_data=f"stop_contest:{contest['id']}"
        )

    kb.adjust(1)

    await message.answer(text, reply_markup=kb.as_markup())


@router.callback_query(F.data.startswith("stop_contest:"))
@admin_only
async def stop_contest_confirm(callback: CallbackQuery, db: Database):
    """Tanlangan konkursni to'xtatishni tasdiqlash"""
    await callback.answer()

    contest_id = int(callback.data.split(":")[1])
    contest = await db.get_contest_by_id(contest_id)

    if not contest:
        await callback.message.edit_text("❌ Konkurs topilmadi")
        return

    if not contest['is_active']:
        await callback.message.edit_text("❌ Bu konkurs allaqachon to'xtatilgan")
        return

    # Statistika
    report = await db.get_detailed_report(contest_id)

    text = f"""
⚠️ <b>KONKURSNI TO'XTATISH</b>

Quyidagi konkursni to'xtatmoqchisiz:

🗳 <b>Nom:</b> {contest['name']}
📅 <b>Boshlanish:</b> {contest['start_date'].strftime('%d.%m.%Y %H:%M')}
⏰ <b>Tugash:</b> {contest['end_date'].strftime('%d.%m.%Y %H:%M')}

📊 <b>Joriy statistika:</b>
👥 Ishtirokchilar: {report['stats']['total_voters']}
🗳 Jami ovozlar: {report['stats']['total_votes']}

⚠️ <b>OGOHLANTIRISH:</b>
• Konkurs darhol to'xtatiladi
• Foydalanuvchilar endi ovoz bera olmaydi
• Konkurs avtomatik arxivga o'tkaziladi
• Bu amalni bekor qilib bo'lmaydi!

Davom etasizmi?
"""

    await callback.message.edit_text(
        text,
        reply_markup=yes_no_keyboard(f"stop_contest_exec:{contest_id}")
    )


@router.callback_query(F.data.startswith("yes:stop_contest_exec:"))
@admin_only
async def stop_contest_execute(callback: CallbackQuery, db: Database):
    """Konkursni to'xtatish"""
    await callback.answer()

    contest_id = int(callback.data.split(":")[2])
    contest = await db.get_contest_by_id(contest_id)

    if not contest:
        await callback.message.edit_text("❌ Konkurs topilmadi")
        return

    try:
        # Konkursni to'xtatish
        await db.stop_contest(contest['id'])

        # Yakuniy natijalar
        report = await db.get_detailed_report(contest['id'])

        # G'oliblar
        winners_text = ""
        for i, candidate in enumerate(report['candidates'][:3], 1):
            medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉"
            percentage = candidate.get('percentage') or 0
            winners_text += f"{medal} <b>{candidate['candidate_name']}</b> - {candidate['votes']} ovoz ({percentage:.1f}%)\n"

        text = f"""
✅ <b>KONKURS TO'XTATILDI!</b>

🗳 <b>Konkurs:</b> {contest['name']}
📊 <b>Yakuniy statistika:</b>
👥 Jami ishtirokchilar: {report['stats']['total_voters']}
🗳 Jami ovozlar: {report['stats']['total_votes']}

🏆 <b>G'oliblar:</b>
{winners_text}

📁 Konkurs arxivga o'tkazildi.
"""

        await callback.message.edit_text(text)

        log_user_action(
            callback.from_user.id,
            callback.from_user.username,
            f"STOPPED_CONTEST: {contest['name']}"
        )

    except Exception as e:
        logger.error(f"Konkursni to'xtatishda xato: {e}", exc_info=True)
        await callback.message.edit_text("❌ Xatolik yuz berdi!")


@router.callback_query(F.data.startswith("no:stop_contest_exec:"))
async def stop_contest_cancel(callback: CallbackQuery):
    """To'xtatishni bekor qilish"""
    await callback.answer("Bekor qilindi")
    await callback.message.delete()


# ==================== BOSHQA ADMIN FUNKSIYALARI ====================

@router.message(F.text == "📊 Natijalar")
@admin_only
async def admin_results(message: Message, db: Database):
    """Natijalarni ko'rsatish (Admin)"""
    contest = await db.get_active_contest()

    if not contest:
        await message.answer("❌ Faol konkurs yo'q")
        return

    results = await db.get_vote_results(contest['id'])
    text = format_results_text(results, contest['name'])

    await message.answer(text)


@router.message(F.text == "📋 Batafsil hisobot")
@admin_only
async def detailed_report(message: Message, db: Database):
    """Batafsil hisobot"""
    contest = await db.get_active_contest()

    if not contest:
        await message.answer("❌ Faol konkurs yo'q")
        return

    report = await db.get_detailed_report(contest['id'])

    text = f"""
📋 <b>Batafsil Hisobot</b>

🗳 <b>Konkurs:</b> {report['contest']['name']}
📅 <b>Boshlanish:</b> {report['contest']['start_date'].strftime('%d.%m.%Y %H:%M')}
⏰ <b>Tugash:</b> {report['contest']['end_date'].strftime('%d.%m.%Y %H:%M')}

📊 <b>Statistika:</b>
👥 Jami ishtirokchilar: {report['stats']['total_voters']}
🗳 Jami ovozlar: {report['stats']['total_votes']}

<b>Natijalar:</b>
"""

    for i, candidate in enumerate(report['candidates'], 1):
        medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
        percentage = candidate.get('percentage') or 0
        text += f"\n{medal} <b>{candidate['candidate_name']}</b>\n"
        text += f"   📊 {candidate['votes']} ovoz ({percentage:.1f}%)\n"

    await message.answer(text)
    log_user_action(message.from_user.id, message.from_user.username, "VIEW_REPORT")


@router.message(F.text == "📥 Eksport")
@admin_only
async def export_menu(message: Message, db: Database):
    """Eksport menyu"""
    contests = await db.get_all_contests()

    if not contests:
        await message.answer("❌ Hech qanday konkurs yo'q")
        return

    text = f"""
📥 <b>Ma'lumotlarni eksport qilish</b>

Qaysi konkursni eksport qilmoqchisiz?

<b>Jami konkurslar:</b> {len(contests)}
"""

    kb = InlineKeyboardBuilder()

    for contest in contests:
        if contest['is_active']:
            status = "🟢"
        elif contest.get('is_archived'):
            status = "📁"
        else:
            status = "⚪️"

        name = contest['name'][:40] + "..." if len(contest['name']) > 40 else contest['name']
        button_text = f"{status} {name}"

        kb.button(
            text=button_text,
            callback_data=f"export_select:{contest['id']}"
        )

    kb.adjust(1)

    await message.answer(text, reply_markup=kb.as_markup())


@router.callback_query(F.data.startswith("export_select:"))
@admin_only
async def export_select_format(callback: CallbackQuery, db: Database):
    """Format tanlash"""
    await callback.answer()

    contest_id = int(callback.data.split(":")[1])
    contest = await db.get_contest_by_id(contest_id)

    if not contest:
        await callback.message.answer("❌ Konkurs topilmadi!")
        return

    text = f"""
📥 <b>Eksport formati</b>

<b>Konkurs:</b> {contest['name']}
📅 {contest['start_date'].strftime('%d.%m.%Y')} - {contest['end_date'].strftime('%d.%m.%Y')}

Qaysi formatda yuklab olmoqchisiz?
"""

    await callback.message.edit_text(
        text,
        reply_markup=export_keyboard(contest_id)
    )


@router.callback_query(F.data.startswith("export:excel:"))
@admin_only
async def export_excel(callback: CallbackQuery, db: Database):
    """Excel eksport"""
    await callback.answer("Excel tayyorlanmoqda...")

    contest_id = int(callback.data.split(":")[2])
    report = await db.get_detailed_report(contest_id)

    try:
        excel_file = await create_excel_report(report)
        contest_name = report['contest']['name']
        filename = f"hisobot_{contest_name.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx"

        with open(filename, 'wb') as f:
            f.write(excel_file.read())

        await callback.message.answer_document(
            FSInputFile(filename),
            caption=f"📊 <b>{contest_name}</b>\n\nBatafsil hisobot Excel formatda"
        )

        os.remove(filename)
        log_user_action(callback.from_user.id, callback.from_user.username, "EXPORT_EXCEL")
    except Exception as e:
        logger.error(f"Excel eksport xato: {e}", exc_info=True)
        await callback.message.answer("❌ Xatolik yuz berdi!")


@router.callback_query(F.data.startswith("export:csv:"))
@admin_only
async def export_csv(callback: CallbackQuery, db: Database):
    """CSV eksport"""
    await callback.answer("CSV tayyorlanmoqda...")

    contest_id = int(callback.data.split(":")[2])
    report = await db.get_detailed_report(contest_id)

    try:
        csv_file = await create_csv_report(report['candidates'])
        contest_name = report['contest']['name']
        filename = f"hisobot_{contest_name.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M')}.csv"

        with open(filename, 'wb') as f:
            f.write(csv_file.read())

        await callback.message.answer_document(
            FSInputFile(filename),
            caption=f"📄 <b>{contest_name}</b>\n\nNatijalar CSV formatda"
        )

        os.remove(filename)
        log_user_action(callback.from_user.id, callback.from_user.username, "EXPORT_CSV")
    except Exception as e:
        logger.error(f"CSV eksport xato: {e}", exc_info=True)
        await callback.message.answer("❌ Xatolik yuz berdi!")


@router.callback_query(F.data.startswith("export:chart:"))
@admin_only
async def export_chart(callback: CallbackQuery, db: Database):
    """Grafik eksport"""
    await callback.answer("Grafik yaratilmoqda...")

    contest_id = int(callback.data.split(":")[2])
    report = await db.get_detailed_report(contest_id)

    try:
        chart = await create_chart(report['candidates'], report['contest']['name'])
        filename = f"grafik_{datetime.now().strftime('%Y%m%d_%H%M')}.png"

        with open(filename, 'wb') as f:
            f.write(chart.read())

        await callback.message.answer_photo(
            FSInputFile(filename),
            caption=f"📈 <b>{report['contest']['name']}</b>\n\nNatijalar grafigi"
        )

        os.remove(filename)
        log_user_action(callback.from_user.id, callback.from_user.username, "EXPORT_CHART")
    except Exception as e:
        logger.error(f"Grafik eksport xato: {e}", exc_info=True)
        await callback.message.answer("❌ Xatolik yuz berdi!")


@router.message(F.text == "🗑 Ovozlarni tozalash")
@admin_only
async def reset_votes_confirm(message: Message):
    """Ovozlarni tozalash tasdiq"""
    text = """
⚠️ <b>OGOHLANTIRISH!</b>

Siz barcha ovozlarni o'chirmoqchisiz!
Bu amalni bekor qilib bo'lmaydi.

Davom etasizmi?
"""
    await message.answer(text, reply_markup=yes_no_keyboard("reset_votes"))


@router.callback_query(F.data == "yes:reset_votes")
@admin_only
async def reset_votes_execute(callback: CallbackQuery, db: Database):
    """Ovozlarni tozalash"""
    await callback.answer()

    contest = await db.get_active_contest()

    if not contest:
        await callback.message.edit_text("❌ Faol konkurs yo'q")
        return

    try:
        await db.reset_contest_votes(contest['id'])

        await callback.message.edit_text(
            f"✅ <b>Ovozlar tozalandi!</b>\n\n"
            f"Konkurs: {contest['name']}\n"
            f"Barcha ovozlar o'chirildi."
        )

        log_user_action(callback.from_user.id, callback.from_user.username, "RESET_VOTES")
    except Exception as e:
        logger.error(f"Ovozlarni tozalashda xato: {e}", exc_info=True)
        await callback.message.edit_text("❌ Xatolik yuz berdi!")


@router.callback_query(F.data == "no:reset_votes")
async def reset_votes_cancel(callback: CallbackQuery):
    """Bekor qilish"""
    await callback.answer("Bekor qilindi")
    await callback.message.delete()


@router.message(F.text == "📚 Arxiv")
@admin_only
async def view_archive(message: Message, db: Database):
    """Arxivni ko'rish"""
    contests = await db.get_archived_contests()

    text = "📚 <b>Arxivlangan konkurslar</b>\n\n"

    if contests:
        text += f"Jami: {len(contests)} ta konkurs\n\n"
        await message.answer(text, reply_markup=archive_keyboard(contests))
    else:
        text += "📭 Arxiv bo'sh"
        await message.answer(text)


@router.callback_query(F.data.startswith("archive:"))
@admin_only
async def view_archived_contest(callback: CallbackQuery, db: Database):
    """Arxivlangan konkurs"""
    await callback.answer()

    contest_id = int(callback.data.split(":")[1])
    report = await db.get_detailed_report(contest_id)

    text = f"""
📁 <b>Arxivlangan Konkurs</b>

🗳 <b>Nom:</b> {report['contest']['name']}
📅 <b>Boshlanish:</b> {report['contest']['start_date'].strftime('%d.%m.%Y %H:%M')}
⏰ <b>Tugash:</b> {report['contest']['end_date'].strftime('%d.%m.%Y %H:%M')}

📊 <b>Yakuniy natijalar:</b>
👥 Ishtirokchilar: {report['stats']['total_voters']}
🗳 Jami ovozlar: {report['stats']['total_votes']}

<b>G'oliblar:</b>
"""

    for i, candidate in enumerate(report['candidates'][:3], 1):
        medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉"
        percentage = candidate.get('percentage') or 0
        text += f"\n{medal} <b>{candidate['candidate_name']}</b>\n"
        text += f"   {candidate['votes']} ovoz ({percentage:.1f}%)\n"

    await callback.message.edit_text(text, reply_markup=export_keyboard(contest_id))


@router.message(Command("stats"))
@admin_only
async def quick_stats(message: Message, db: Database):
    """Tezkor statistika"""
    contest = await db.get_active_contest()

    if not contest:
        await message.answer("❌ Faol konkurs yo'q")
        return

    report = await db.get_detailed_report(contest['id'])
    top_candidate = report['candidates'][0] if report['candidates'] else None

    text = f"""
⚡️ <b>Tezkor Statistika</b>

🗳 {report['contest']['name']}
👥 {report['stats']['total_voters']} kishi ovoz berdi
📊 {report['stats']['total_votes']} ovoz
"""

    if top_candidate:
        text += f"\n🏆 Lider: <b>{top_candidate['candidate_name']}</b>\n"
        text += f"       ({top_candidate['votes']} ovoz)"

    await message.answer(text)