from aiogram.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    ReplyKeyboardMarkup,
    KeyboardButton
)
from aiogram.utils.keyboard import InlineKeyboardBuilder
from typing import List, Dict


# =========================
# REPLY KEYBOARDS
# =========================

def main_menu_keyboard(is_admin: bool = False) -> ReplyKeyboardMarkup:
    """Asosiy menyu klaviaturasi"""
    keyboard = [
        [KeyboardButton(text="🗳 Ovoz berish")],
        [KeyboardButton(text="📊 Natijalar"), KeyboardButton(text="ℹ️ Ma'lumot")]
    ]

    if is_admin:
        keyboard.append([KeyboardButton(text="👨‍💼 Admin Panel")])

    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True,
        input_field_placeholder="Menyudan tanlang..."
    )


def admin_menu_keyboard() -> ReplyKeyboardMarkup:
    """Admin menyu klaviaturasi"""
    keyboard = [
        [KeyboardButton(text="➕ Yangi konkurs"), KeyboardButton(text="📊 Natijalar")],
        [KeyboardButton(text="📋 Batafsil hisobot"), KeyboardButton(text="📥 Eksport")],
        [KeyboardButton(text="⏸ Konkursni to'xtatish"), KeyboardButton(text="📚 Arxiv")],
        [KeyboardButton(text="🗑 Ovozlarni tozalash")],
        [KeyboardButton(text="⬅️ Orqaga")]
    ]

    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True,
        input_field_placeholder="Admin amallarini tanlang..."
    )


# =========================
# INLINE KEYBOARDS
# =========================

def format_vote_count(count: int) -> str:
    """
    Ovozlar sonini formatlash:
    0-999: 123
    1000-999999: 1.2K
    1000000+: 1.2M

    Misol:
    - 0 → "0"
    - 234 → "234"
    - 1500 → "1.5K"
    - 2300 → "2.3K"
    - 15000 → "15K"
    - 1500000 → "1.5M"
    """
    if count < 1000:
        return str(count)
    elif count < 1000000:
        # 1000-999999: K format
        k_value = count / 1000
        if k_value >= 10:
            # 10K+ → "15K" (integer)
            return f"{int(k_value)}K"
        else:
            # 1.0K-9.9K → "2.3K" (1 decimal)
            formatted = f"{k_value:.1f}K"
            # "2.0K" → "2K"
            return formatted.replace('.0K', 'K')
    else:
        # 1000000+: M format
        m_value = count / 1000000
        if m_value >= 10:
            return f"{int(m_value)}M"
        else:
            formatted = f"{m_value:.1f}M"
            return formatted.replace('.0M', 'M')


def channels_keyboard(channels: List[Dict]) -> InlineKeyboardMarkup:
    """Kanallarga obuna bo'lish klaviaturasi"""
    keyboard = []

    for i, channel in enumerate(channels, 1):
        keyboard.append([
            InlineKeyboardButton(
                text=f"📢 {i}. {channel['channel_name']}",
                url=channel['channel_link']
            )
        ])

    keyboard.append([
        InlineKeyboardButton(
            text="✅ Obunani tekshirish",
            callback_data="check_subscription"
        )
    ])

    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def vote_keyboard(candidates: List[Dict], contest_id: int,
                  bot_username: str = "uznmc_bot") -> InlineKeyboardMarkup:
    """
    Kanalga post uchun inline keyboard (Deep link)

    REAL-TIME OVOZLAR SONI BILAN!

    Har bir nomzod yonida ovozlar soni dinamik ko'rsatiladi:
    - Dr.Aziz - 234
    - Dr.Nodir - 2.3K
    - Dr.Jasur - 15K

    Ovoz berganda bu keyboard avtomatik yangilanadi!
    """
    kb = InlineKeyboardBuilder()

    for candidate in candidates:
        # Real-time ovozlar sonini olish
        vote_count = candidate.get('vote_count', 0)

        # Formatlangan ovozlar soni (234 yoki 2.3K)
        formatted_count = format_vote_count(vote_count)

        # Tugma matni
        button_text = f"👤 {candidate['name']} - {formatted_count}"

        # Deep link URL
        deep_link = f"https://t.me/{bot_username}?start=vote_{contest_id}_{candidate['id']}"

        kb.button(
            text=button_text,
            url=deep_link
        )

    kb.adjust(1)  # Har bir nomzod alohida qatorda
    return kb.as_markup()


def candidates_keyboard(candidates: List[Dict], show_results: bool = False) -> InlineKeyboardMarkup:
    """Nomzodlar ro'yxati klaviaturasi"""
    keyboard = []

    for candidate in candidates:
        text = candidate['name']
        if show_results:
            votes = candidate.get('vote_count', 0)
            text = f"👤 {candidate['name']} - {format_vote_count(votes)} ovoz"

        keyboard.append([
            InlineKeyboardButton(
                text=text,
                callback_data=f"vote_{candidate['id']}" if not show_results else f"view_{candidate['id']}"
            )
        ])

    if show_results:
        keyboard.append([
            InlineKeyboardButton(
                text="🔄 Yangilash",
                callback_data="refresh_results"
            )
        ])

    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def confirm_vote_keyboard(candidate_id: int) -> InlineKeyboardMarkup:
    """Ovozni tasdiqlash klaviaturasi"""
    keyboard = [
        [
            InlineKeyboardButton(text="✅ Ha, tasdiqlash", callback_data=f"confirm_vote_{candidate_id}"),
            InlineKeyboardButton(text="❌ Bekor qilish", callback_data="cancel_vote")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def archive_keyboard(contests: List[Dict]) -> InlineKeyboardMarkup:
    """Arxiv klaviaturasi"""
    keyboard = []

    if not contests:
        keyboard.append([
            InlineKeyboardButton(text="📭 Arxiv bo'sh", callback_data="ignore")
        ])
    else:
        for contest in contests:
            text = f"📁 {contest['name']} ({contest['total_voters']} ovoz)"
            keyboard.append([
                InlineKeyboardButton(
                    text=text,
                    callback_data=f"archive:{contest['id']}"
                )
            ])

    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def export_keyboard(contest_id: int) -> InlineKeyboardMarkup:
    """Eksport turini tanlash klaviaturasi"""
    keyboard = [
        [
            InlineKeyboardButton(text="📊 Excel", callback_data=f"export:excel:{contest_id}"),
            InlineKeyboardButton(text="📄 CSV", callback_data=f"export:csv:{contest_id}")
        ],
        [
            InlineKeyboardButton(text="📈 Grafik", callback_data=f"export:chart:{contest_id}")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def yes_no_keyboard(action: str) -> InlineKeyboardMarkup:
    """Ha/Yo'q klaviaturasi"""
    keyboard = [
        [
            InlineKeyboardButton(text="✅ Ha", callback_data=f"yes:{action}"),
            InlineKeyboardButton(text="❌ Yo'q", callback_data=f"no:{action}")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def back_keyboard() -> InlineKeyboardMarkup:
    """Orqaga qaytish tugmasi"""
    keyboard = [
        [InlineKeyboardButton(text="⬅️ Orqaga", callback_data="back_to_menu")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)