"""
Данные о качестве воздуха.

Это ВРЕМЕННЫЙ файл, чтобы фронтенд уже работал.
Команда бэкенда (Азизбек) может переписать функции внутри,
но НЕ МЕНЯЙТЕ их названия и формат того, что они возвращают —
иначе сломается фронтенд (app.py).

Сейчас: пытаемся взять реальные данные из бесплатного API Open-Meteo.
Если интернета нет или API не ответил — показываем демо-данные.
"""

import random
from datetime import datetime, timedelta

import pandas as pd
import requests

# Районы Шымкента и примерные координаты их центров
DISTRICTS = {
    "Абайский": (42.360, 69.550),
    "Аль-Фарабийский": (42.320, 69.600),
    "Енбекшинский": (42.300, 69.630),
    "Каратауский": (42.370, 69.650),
    "Туранский": (42.280, 69.550),
}

API_URL = "https://air-quality-api.open-meteo.com/v1/air-quality"
HOURLY_FIELDS = "pm2_5,pm10,nitrogen_dioxide,us_aqi"


def _fetch_from_api(lat, lon):
    """Почасовые данные из Open-Meteo: 24 ч назад + 24 ч прогноза."""
    params = {
        "latitude": lat,
        "longitude": lon,
        "hourly": HOURLY_FIELDS,
        "past_days": 1,
        "forecast_days": 2,
        "timezone": "Asia/Almaty",
    }
    r = requests.get(API_URL, params=params, timeout=10)
    r.raise_for_status()
    h = r.json()["hourly"]
    df = pd.DataFrame({
        "time": pd.to_datetime(h["time"]),
        "pm2_5": h["pm2_5"],
        "pm10": h["pm10"],
        "no2": h["nitrogen_dioxide"],
        "aqi": h["us_aqi"],
    })
    return df.dropna()


def _demo_data(district):
    """Правдоподобные выдуманные данные, если API недоступен."""
    rnd = random.Random(district)  # у каждого района свои, но стабильные цифры
    base = rnd.uniform(25, 90)
    now = datetime.now().replace(minute=0, second=0, microsecond=0)
    rows = []
    for i in range(-24, 25):
        t = now + timedelta(hours=i)
        # утром и вечером воздух хуже (пробки, отопление)
        peak = 25 if t.hour in (8, 9, 19, 20, 21) else 0
        aqi = max(10, base + peak + rnd.uniform(-10, 10))
        rows.append({
            "time": t,
            "pm2_5": round(aqi * 0.35, 1),
            "pm10": round(aqi * 0.6, 1),
            "no2": round(aqi * 0.3, 1),
            "aqi": round(aqi),
        })
    return pd.DataFrame(rows)


def get_hourly(district):
    """
    Возвращает (таблица, источник).
    Таблица: колонки time, pm2_5, pm10, no2, aqi — по часам.
    Источник: "api" или "demo".
    """
    lat, lon = DISTRICTS[district]
    try:
        df = _fetch_from_api(lat, lon)
        if not df.empty:
            return df, "api"
    except Exception:
        pass
    return _demo_data(district), "demo"
