import logging
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib
from datetime import datetime
from typing import List, Dict
import io
import config

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
    return user_id in config.ADMIN_IDS


def format_datetime(dt: datetime) -> str:
    """Sana va vaqtni formatlash"""
    return dt.strftime("%d.%m.%Y %H:%M")


def format_vote_count(count: int) -> str:
    if count < 1000:
        return str(count)
    elif count < 1000000:
        k_value = count / 1000
        if k_value >= 10:
            return f"{int(k_value)}K"
        else:
            formatted = f"{k_value:.1f}K"
            return formatted.replace('.0K', 'K')
    else:
        m_value = count / 1000000
        if m_value >= 10:
            return f"{int(m_value)}M"
        else:
            formatted = f"{m_value:.1f}M"
            return formatted.replace('.0M', 'M')


def format_results_text(results: List[Dict], contest_name: str = "") -> str:
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
    output = io.BytesIO()

    contest = report_data['contest']
    candidates = report_data['candidates']
    stats = report_data['stats']

    with pd.ExcelWriter(output, engine='openpyxl') as writer:

        info_data = {
            'Parametr': [
                'Konkurs nomi',
                'Boshlanish sanasi',
                'Tugash sanasi',
                'Jami ovoz berganlar',
                'Jami ovozlar'
            ],
            'Qiymat': [
                contest['name'],
                format_datetime(contest['start_date']),
                format_datetime(contest['end_date']),
                stats['total_voters'],
                stats['total_votes']
            ]
        }

        df_info = pd.DataFrame(info_data)
        df_info.to_excel(writer, sheet_name="Ma'lumot", index=False)

        sheet_info = writer.book["Ma'lumot"]
        sheet_info.column_dimensions['A'].width = 25
        sheet_info.column_dimensions['B'].width = 40


        results_data = {
            'Nomzod': [c['candidate_name'] for c in candidates],
            'Ovozlar': [c['votes'] for c in candidates],
            'Foiz': [f"{c['percentage']}%" for c in candidates]
        }

        df_results = pd.DataFrame(results_data)
        df_results.to_excel(writer, sheet_name='Natijalar', index=False)

        sheet_results = writer.book['Natijalar']
        sheet_results.column_dimensions['A'].width = 30
        sheet_results.column_dimensions['B'].width = 15
        sheet_results.column_dimensions['C'].width = 15

    output.seek(0)
    return output


async def create_csv_report(candidates: List[Dict]) -> io.BytesIO:
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
    output = io.BytesIO()

    names = [c['candidate_name'] for c in candidates]
    votes = [c['votes'] for c in candidates]

    fig, ax = plt.subplots(figsize=(10, 6))
    bars = ax.barh(names, votes, color='#3498db')

    if len(bars) > 0:
        bars[0].set_color('#FFD700')  # Oltin
    if len(bars) > 1:
        bars[1].set_color('#C0C0C0')  # Kumush
    if len(bars) > 2:
        bars[2].set_color('#CD7F32')  # Bronza

    ax.set_xlabel('Ovozlar soni', fontsize=12)
    ax.set_title(f'📊 {contest_name}', fontsize=14, fontweight='bold')
    ax.grid(axis='x', alpha=0.3)

    for i, (name, vote) in enumerate(zip(names, votes)):
        ax.text(vote + 0.5, i, str(vote), va='center', fontsize=10)

    plt.tight_layout()
    plt.savefig(output, format='png', dpi=150, bbox_inches='tight')
    plt.close()

    output.seek(0)
    return output


def parse_datetime(date_str: str) -> datetime:
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
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue

    raise ValueError(f"Sana formati noto'g'ri: {date_str}")


def validate_channel_link(link: str) -> bool:
    return link.startswith('https://t.me/') or link.startswith('@')


def log_user_action(user_id: int, username: str, action: str):
    logger.info(f"User: {user_id} (@{username}) - Action: {action}")