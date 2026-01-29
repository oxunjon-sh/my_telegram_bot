import logging
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib
from datetime import datetime
from typing import List, Dict
import io
import config

# Matplotlib sozlamalari
matplotlib.use('Agg')
plt.rcParams['font.family'] = 'DejaVu Sans'

logger = logging.getLogger(__name__)


def setup_logging():
    """Logging sozlash"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(config.LOG_FILE, encoding='utf-8'),
            logging.StreamHandler()
        ]
    )


def is_admin(user_id: int) -> bool:
    """Foydalanuvchi admin ekanligini tekshirish"""
    return user_id in config.ADMIN_IDS


def format_datetime(dt: datetime) -> str:
    """
    Sana va vaqtni formatlash (Toshkent vaqti)

    MUHIM:
    - Database UTC da saqlaydi
    - Ko'rsatish Toshkent vaqtida bo'ladi (+5 soat)
    - UTC → Toshkent: +5 soat

    Masalan:
    Input: 2026-01-25 10:00:00 (UTC)
    Output: "25.01.2026 15:00" (Toshkent vaqti)
    """
    from datetime import timedelta
    # UTC dan Toshkent vaqtiga convert (+5 soat)
    tashkent_dt = dt + timedelta(hours=5)
    return tashkent_dt.strftime("%d.%m.%Y %H:%M")


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


def format_results_text(results: List[Dict], contest_name: str = "") -> str:
    """Natijalarni text formatda shakllantirish"""
    text = f"📊 <b>{contest_name}</b>\n\n"

    if not results:
        text += "❌ Hozircha ovozlar yo'q\n"
        return text

    total_votes = sum(r['votes'] for r in results)
    text += f"📈 Jami ovozlar: <b>{total_votes}</b>\n\n"

    for i, result in enumerate(results, 1):
        medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
        name = result['candidate_name']
        votes = result['votes']
        percentage = result['percentage'] or 0

        bar = "█" * int(percentage / 5) + "░" * (20 - int(percentage / 5))

        text += f"{medal} <b>{name}</b>\n"
        text += f"   {bar} {percentage}% ({votes} ovoz)\n\n"

    return text


async def create_excel_report(report_data: Dict) -> io.BytesIO:
    """Excel hisobot yaratish"""
    output = io.BytesIO()

    contest = report_data['contest']
    candidates = report_data['candidates']
    stats = report_data['stats']

    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        # Umumiy ma'lumotlar
        info_data = {
            'Parametr': ['Konkurs nomi', 'Boshlanish sanasi', 'Tugash sanasi',
                         'Jami ovoz berganlar', 'Jami ovozlar'],
            'Qiymat': [
                contest['name'],
                format_datetime(contest['start_date']),
                format_datetime(contest['end_date']),
                stats['total_voters'],
                stats['total_votes']
            ]
        }
        df_info = pd.DataFrame(info_data)
        df_info.to_excel(writer, sheet_name='Ma\'lumot', index=False)

        # Natijalar
        results_data = {
            'Nomzod': [c['candidate_name'] for c in candidates],
            'Ovozlar': [c['votes'] for c in candidates],
            'Foiz': [f"{c['percentage']}%" for c in candidates]
        }
        df_results = pd.DataFrame(results_data)
        df_results.to_excel(writer, sheet_name='Natijalar', index=False)

    output.seek(0)
    return output


async def create_csv_report(candidates: List[Dict]) -> io.BytesIO:
    """CSV hisobot yaratish"""
    output = io.BytesIO()

    df = pd.DataFrame([
        {
            'Nomzod': c['candidate_name'],
            'Ovozlar': c['votes'],
            'Foiz': c['percentage']
        }
        for c in candidates
    ])

    csv_data = df.to_csv(index=False, encoding='utf-8-sig')
    output.write(csv_data.encode('utf-8-sig'))
    output.seek(0)

    return output


async def create_chart(candidates: List[Dict], contest_name: str) -> io.BytesIO:
    """Grafik yaratish"""
    output = io.BytesIO()

    names = [c['candidate_name'] for c in candidates]
    votes = [c['votes'] for c in candidates]

    # Grafik yaratish
    fig, ax = plt.subplots(figsize=(10, 6))
    bars = ax.barh(names, votes, color='#3498db')

    # Ranglarni sozlash (birinchi 3ta uchun)
    if len(bars) > 0:
        bars[0].set_color('#FFD700')  # Oltin
    if len(bars) > 1:
        bars[1].set_color('#C0C0C0')  # Kumush
    if len(bars) > 2:
        bars[2].set_color('#CD7F32')  # Bronza

    ax.set_xlabel('Ovozlar soni', fontsize=12)
    ax.set_title(f'📊 {contest_name}', fontsize=14, fontweight='bold')
    ax.grid(axis='x', alpha=0.3)

    # Qiymatlarni ko'rsatish
    for i, (name, vote) in enumerate(zip(names, votes)):
        ax.text(vote + 0.5, i, str(vote), va='center', fontsize=10)

    plt.tight_layout()
    plt.savefig(output, format='png', dpi=150, bbox_inches='tight')
    plt.close()

    output.seek(0)
    return output


def parse_datetime(date_str: str) -> datetime:
    """
    String'dan datetime'ga o'tkazish (Toshkent vaqti)

    MUHIM:
    - Kiritilgan vaqt Toshkent vaqti deb qabul qilinadi (+5 UTC)
    - Natija UTC da qaytariladi (database UTC da saqlaydi)
    - Toshkent → UTC: -5 soat

    Masalan:
    Input: "25.01.2026 15:00" (Toshkent vaqti)
    Output: 2026-01-25 10:00:00 (UTC)
    """
    formats = [
        "%d.%m.%Y %H:%M",
        "%d/%m/%Y %H:%M",
        "%Y-%m-%d %H:%M",
        "%d.%m.%Y",
        "%d/%m/%Y",
        "%Y-%m-%d"
    ]

    for fmt in formats:
        try:
            # Parse (naive datetime - Toshkent vaqti)
            tashkent_dt = datetime.strptime(date_str, fmt)

            # UTC ga convert (-5 soat)
            from datetime import timedelta
            utc_dt = tashkent_dt - timedelta(hours=5)

            return utc_dt

        except ValueError:
            continue

    raise ValueError(f"Sana formati noto'g'ri: {date_str}")


def get_current_datetime() -> datetime:
    """
    Joriy vaqtni olish (Toshkent vaqti)

    MUHIM:
    - Server UTC da ishlaydi
    - Natija UTC da qaytariladi (database bilan mos)
    - Taqqoslash uchun ishlatiladi

    Returns:
        datetime: Joriy UTC vaqt
    """
    return datetime.utcnow()


def validate_channel_link(link: str) -> bool:
    """Kanal linkini tekshirish"""
    return link.startswith('https://t.me/') or link.startswith('@')


def log_user_action(user_id: int, username: str, action: str):
    """Foydalanuvchi harakatini loglash"""
    logger.info(f"User: {user_id} (@{username}) - Action: {action}")