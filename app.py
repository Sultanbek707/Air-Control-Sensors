"""
Air Control Sensors — фронтенд (Streamlit).
Запуск:  streamlit run app.py
"""

from datetime import datetime

import pandas as pd
import streamlit as st

from backend.data import DISTRICTS, get_hourly

st.set_page_config(page_title="Air Control — Шымкент", page_icon="🌫️", layout="wide")


# ---------- Шкала качества воздуха (US AQI) ----------
LEVELS = [
    # (верхняя граница, название, цвет, совет)
    (50, "Хорошо", "#2ecc71", "Воздух чистый. Можно гулять и проветривать."),
    (100, "Умеренно", "#f1c40f", "Чувствительным людям лучше не находиться долго на улице."),
    (150, "Вредно для чувствительных", "#e67e22", "Детям, пожилым и астматикам — сократить время на улице."),
    (200, "Вредно", "#e74c3c", "Всем лучше ограничить прогулки, закрыть окна."),
    (300, "Очень вредно", "#8e44ad", "Оставайтесь дома, используйте очиститель воздуха."),
    (10_000, "Опасно", "#7f1d1d", "Не выходите на улицу без необходимости, наденьте респиратор."),
]


def level_of(aqi):
    for top, name, color, advice in LEVELS:
        if aqi <= top:
            return name, color, advice
    return LEVELS[-1][1:]


@st.cache_data(ttl=600)  # обновлять данные не чаще раза в 10 минут
def load(district):
    return get_hourly(district)


def split_now(df):
    """Делит таблицу на «прошлое до сейчас» и «прогноз», возвращает текущую строку."""
    now = datetime.now()
    past = df[df["time"] <= now]
    future = df[df["time"] > now]
    current = past.iloc[-1] if not past.empty else df.iloc[0]
    return current, past, future


# ---------- Боковая панель ----------
st.sidebar.title("🌫️ Air Control")
district = st.sidebar.selectbox("Район Шымкента", list(DISTRICTS.keys()))
st.sidebar.caption("Данные обновляются каждые 10 минут.")

df, source = load(district)
current, past, future = split_now(df)
name, color, advice = level_of(current["aqi"])

# ---------- Заголовок ----------
st.title(f"Качество воздуха: {district} район")
if source == "demo":
    st.warning("Сейчас показаны демо-данные: источник данных недоступен.")

# ---------- Главная карточка ----------
st.markdown(
    f"""
    <div style="background:{color};padding:24px;border-radius:16px;color:white;">
        <div style="font-size:18px;opacity:.9;">Индекс качества воздуха (AQI)</div>
        <div style="font-size:64px;font-weight:700;line-height:1.1;">{int(current['aqi'])}</div>
        <div style="font-size:24px;font-weight:600;">{name}</div>
        <div style="font-size:16px;margin-top:8px;">{advice}</div>
    </div>
    """,
    unsafe_allow_html=True,
)
st.write("")

# ---------- Показатели ----------
c1, c2, c3 = st.columns(3)
c1.metric("PM2.5, мкг/м³", current["pm2_5"])
c2.metric("PM10, мкг/м³", current["pm10"])
c3.metric("NO₂, мкг/м³", current["no2"])

# ---------- Графики ----------
left, right = st.columns(2)
with left:
    st.subheader("Последние 24 часа")
    st.line_chart(past.tail(24).set_index("time")[["aqi"]], height=260)
with right:
    st.subheader("Прогноз на 24 часа")
    if future.empty:
        st.info("Прогноза пока нет.")
    else:
        st.line_chart(future.head(24).set_index("time")[["aqi"]], height=260)
        worst = future.head(24).loc[future.head(24)["aqi"].idxmax()]
        st.caption(
            f"Хуже всего будет около {worst['time']:%H:%M} — AQI {int(worst['aqi'])} "
            f"({level_of(worst['aqi'])[0].lower()})."
        )

# ---------- Карта всех районов ----------
st.subheader("Карта районов")
points = []
for d, (lat, lon) in DISTRICTS.items():
    d_df, _ = load(d)
    d_now, _, _ = split_now(d_df)
    d_name, d_color, _ = level_of(d_now["aqi"])
    points.append({"lat": lat, "lon": lon, "color": d_color,
                   "Район": d, "AQI": int(d_now["aqi"]), "Уровень": d_name})
map_df = pd.DataFrame(points)
st.map(map_df, latitude="lat", longitude="lon", color="color", size=900, zoom=11)
st.dataframe(map_df[["Район", "AQI", "Уровень"]].sort_values("AQI"),
             hide_index=True, use_container_width=True)

st.caption("Источник: Open-Meteo Air Quality API · Air Control Sensors, 2026")
