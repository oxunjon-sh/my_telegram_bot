# Python 3.11 barqaror versiyasi
FROM python:3.11-slim

# Ishlash papkasi
WORKDIR /app

# System dependencies (asyncpg, pandas, matplotlib uchun)
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libpq-dev \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# requirements.txt ni alohida nusxalash va o‘rnatish
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

# Qolgan loyihani nusxalash
COPY . .

# Bot ishga tushadi
CMD ["python", "bot.py"]
