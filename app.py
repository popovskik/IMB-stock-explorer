import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(page_title="Stock Explorer", layout="wide")
st.title("📈 Stock Price Explorer")

st.info(
    "Did you know? Apple became the first U.S. company to reach a $1 trillion market "
    "cap in August 2018 — just months after the start of this dataset."
)


@st.cache_data
def load_data():
    df = px.data.stocks()  # columns: date + 6 big tech stocks
    df["date"] = pd.to_datetime(df["date"])
    return df


df = load_data()
tickers = [c for c in df.columns if c != "date"]

chosen = st.sidebar.multiselect("Choose stocks", tickers, default=["AAPL", "MSFT", "GOOG"])
if not chosen:
    st.warning("Pick at least one stock from the sidebar.")
    st.stop()

st.caption("Prices are indexed to 1.00 at the start, so each line shows growth since Jan 2018.")

cols = st.columns(len(chosen))
for col, t in zip(cols, chosen):
    growth = (df[t].iloc[-1] - 1) * 100
    col.metric(t, f"{df[t].iloc[-1]:.2f}x", f"{growth:+.1f}%")

best = max(chosen, key=lambda t: df[t].iloc[-1])
best_growth = (df[best].iloc[-1] - 1) * 100
st.success(f"🏆 Best performer among selected stocks: **{best}** (+{best_growth:.1f}% since Jan 2018)")

fig = px.line(df, x="date", y=chosen, title="Normalized price over time")
st.plotly_chart(fig, use_container_width=True)
