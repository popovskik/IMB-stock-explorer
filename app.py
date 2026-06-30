import pandas as pd
import plotly.express as px
import streamlit as st
import yfinance as yf
from datetime import date, timedelta

FACTS = [
    "Apple became the first U.S. company to reach a $1 trillion market cap in August 2018.",
    "NVIDIA's stock rose over 200% in 2023, driven by the global AI boom.",
    "Amazon's AWS cloud division generates more operating profit than its entire retail business.",
    "Microsoft's acquisition of Activision Blizzard in 2023 was the largest gaming deal ever — $69 billion.",
    "Meta lost over $700 billion in market cap in 2022, only to fully recover — and then some — in 2023.",
    "Netflix has more than 260 million paid subscribers across 190 countries.",
    "Google processes over 8.5 billion searches every single day.",
    "Tesla delivered over 1.8 million vehicles in 2023, a company record.",
    "The S&P 500 has returned an average of ~10% per year since 1957, before inflation.",
    "Warren Buffett's Berkshire Hathaway has never paid a dividend — all returns come from share price growth.",
]

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(page_title="Stock Explorer", layout="wide", page_icon="📈")

# ── Around Design System ──────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Poppins:wght@600;700;800&family=Inter:wght@400;500;600&display=swap');

html, body, [class*="css"], .stApp {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
}
h1, h2, h3,
[data-testid="stMarkdownContainer"] h1,
[data-testid="stMarkdownContainer"] h2,
[data-testid="stMarkdownContainer"] h3 {
    font-family: 'Poppins', sans-serif !important;
    font-weight: 700 !important;
    letter-spacing: -0.02em !important;
    color: #0F1217;
}
[data-testid="stMetricValue"] {
    font-family: 'Poppins', sans-serif !important;
    font-weight: 700 !important;
    letter-spacing: -0.02em;
}
[data-testid="stMetricLabel"] {
    font-family: 'Inter', sans-serif !important;
    font-weight: 600 !important;
    font-size: 11px;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    color: #667085;
}
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p {
    font-family: 'Inter', sans-serif;
    font-size: 13px;
    color: #475467;
}
</style>
""", unsafe_allow_html=True)

# ── Stock universe ────────────────────────────────────────────────────────────
SECTORS = {
    "Big Tech":   ["AAPL", "MSFT", "GOOGL", "AMZN", "META", "NFLX", "NVDA", "TSLA"],
    "Finance":    ["JPM", "GS", "V", "MA", "BRK-B"],
    "Energy":     ["XOM", "CVX", "NEE", "BP"],
    "Healthcare": ["JNJ", "UNH", "PFE", "ABBV"],
    "ETFs":       ["SPY", "QQQ", "VTI", "ARKK"],
}

PALETTE = [
    "#FF4800", "#000000", "#177245", "#185bdb",
    "#8c5a00", "#b42318", "#667085", "#ff6d2f",
]

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 📈 Stock Explorer")
    st.divider()

    sector = st.selectbox("Sector preset", list(SECTORS.keys()))
    chosen = st.multiselect("Choose stocks", SECTORS[sector], default=SECTORS[sector][:3])

    custom_raw = st.text_input("➕ Add any ticker", placeholder="e.g. NVDA, BTC-USD, TSM")
    if custom_raw:
        for t in custom_raw.upper().replace(" ", "").split(","):
            if t and t not in chosen:
                chosen.append(t)

    st.divider()

    today = date.today()
    col_a, col_b = st.columns(2)
    start_date = col_a.date_input("From", today - timedelta(days=365 * 3),
                                  min_value=date(2000, 1, 1), max_value=today)
    end_date   = col_b.date_input("To", today,
                                  min_value=start_date, max_value=today)

    st.divider()

    invest_amount = st.number_input(
        "Hypothetical investment ($)",
        min_value=100, value=1_000, step=100,
        help="Enter any dollar amount. Each stock card below will show what that investment would be worth today.",
    )
    show_benchmark = st.checkbox("📊 vs S&P 500 (SPY)", value=True)

if not chosen:
    st.warning("Pick at least one stock from the sidebar.")
    st.stop()

# ── Data ──────────────────────────────────────────────────────────────────────
@st.cache_data(ttl=3600, show_spinner="Fetching prices…")
def load_prices(tickers: tuple, start: str, end: str) -> pd.DataFrame:
    frames = {}
    for t in tickers:
        try:
            hist = yf.Ticker(t).history(start=start, end=end, auto_adjust=True)
            if not hist.empty:
                s = hist["Close"].copy()
                s.index = s.index.tz_localize(None)
                frames[t] = s
        except Exception:
            pass
    if not frames:
        return pd.DataFrame()
    return pd.DataFrame(frames).dropna(how="all")

fetch_set = tuple(sorted(set(chosen + (["SPY"] if show_benchmark else []))))
df = load_prices(fetch_set, str(start_date), str(end_date))

valid = [t for t in chosen if t in df.columns]
if not valid:
    st.error("No data returned — check your tickers or widen the date range.")
    st.stop()

# Normalise to 1.00 on the first trading day
norm_cols = valid + (["SPY"] if show_benchmark and "SPY" in df.columns else [])
norm = df[norm_cols].copy()
norm = norm / norm.iloc[0]

spx_growth = (norm["SPY"].iloc[-1] - 1) * 100 if (show_benchmark and "SPY" in norm.columns) else None

# ── Header ────────────────────────────────────────────────────────────────────
st.title("📈 Stock Price Explorer")

if "fact_idx" not in st.session_state:
    st.session_state.fact_idx = 0

fact_col, btn_col = st.columns([11, 1])
fact_col.info(f"💡 Did you know? {FACTS[st.session_state.fact_idx]}")
if btn_col.button("🔄", help="Next fact"):
    st.session_state.fact_idx = (st.session_state.fact_idx + 1) % len(FACTS)
    st.rerun()

st.caption(
    f"Prices normalised to 1.00 on {start_date.strftime('%b %d, %Y')} · "
    "Data via Yahoo Finance · Any publicly traded ticker supported"
)

# ── KPI cards ─────────────────────────────────────────────────────────────────
kpi_cols = st.columns(len(valid))
for col, t in zip(kpi_cols, valid):
    growth    = (norm[t].iloc[-1] - 1) * 100
    final_val = invest_amount * norm[t].iloc[-1]

    if spx_growth is not None:
        badge = " ✅ beats S&P" if growth > spx_growth else " ❌ trails S&P"
    else:
        badge = ""

    col.metric(
        label=f"{t}{badge}",
        value=f"{norm[t].iloc[-1]:.2f}x",
        delta=f"{growth:+.1f}%",
    )
    col.caption(f"${invest_amount:,.0f} invested → ${final_val:,.0f} today")

best   = max(valid, key=lambda t: norm[t].iloc[-1])
best_g = (norm[best].iloc[-1] - 1) * 100
st.success(
    f"🏆 Best performer among selected stocks: **{best}** "
    f"({best_g:+.1f}% since {start_date.strftime('%b %Y')})"
)

# ── Tabs ──────────────────────────────────────────────────────────────────────
tab_chart, tab_corr, tab_fun = st.tabs(["📈 Price chart", "🔗 Correlation", "⚡ Fun stats"])

# ─ Tab 1: Price chart + bar ──────────────────────────────────────────────────
with tab_chart:
    plot_tickers = valid[:]
    if show_benchmark and "SPY" in norm.columns and "SPY" not in valid:
        plot_tickers.append("SPY")

    melted = (
        norm[plot_tickers]
        .reset_index()
        .rename(columns={"index": "Date"})
        .melt("Date", var_name="Ticker", value_name="Growth")
    )
    fig = px.line(
        melted, x="Date", y="Growth", color="Ticker",
        color_discrete_sequence=PALETTE,
        title="Normalised price — 1.00 = start date",
    )
    fig.add_hline(
        y=1.0, line_dash="dash", line_color="#D0D5DD",
        annotation_text="Baseline", annotation_font_color="#667085",
    )
    fig.update_layout(
        paper_bgcolor="#FCFCFD", plot_bgcolor="#FCFCFD",
        font_family="Inter", legend_title_text="",
        hovermode="x unified", yaxis_tickformat=".2f",
    )
    st.plotly_chart(fig, use_container_width=True)

    growth_vals = {t: (norm[t].iloc[-1] - 1) * 100 for t in valid}
    fig_bar = px.bar(
        x=list(growth_vals.keys()),
        y=list(growth_vals.values()),
        labels={"x": "", "y": "Total growth (%)"},
        color=list(growth_vals.values()),
        color_continuous_scale=["#ffebe8", "#FF4800"],
        title="Total growth comparison",
    )
    fig_bar.update_layout(
        paper_bgcolor="#FCFCFD", plot_bgcolor="#FCFCFD",
        font_family="Inter", showlegend=False, coloraxis_showscale=False,
    )
    fig_bar.update_traces(hovertemplate="%{x}: %{y:.1f}%<extra></extra>")
    if spx_growth is not None:
        fig_bar.add_hline(
            y=spx_growth, line_dash="dot", line_color="#000",
            annotation_text=f"S&P 500 ({spx_growth:+.1f}%)",
        )
    st.plotly_chart(fig_bar, use_container_width=True)

# ─ Tab 2: Correlation heatmap ─────────────────────────────────────────────────
with tab_corr:
    if len(valid) < 2:
        st.info("Select at least 2 stocks to see the correlation matrix.")
    else:
        daily_ret = df[valid].pct_change().dropna()
        corr = daily_ret.corr()

        fig_corr = px.imshow(
            corr,
            text_auto=".2f",
            color_continuous_scale=[[0, "#ffebe8"], [0.5, "#FCFCFD"], [1, "#FF4800"]],
            zmin=-1, zmax=1,
            title="Daily return correlation",
            aspect="auto",
        )
        fig_corr.update_layout(font_family="Inter", paper_bgcolor="#FCFCFD")
        fig_corr.update_traces(hovertemplate="%{y} / %{x}: %{z:.2f}<extra></extra>")
        st.plotly_chart(fig_corr, use_container_width=True)
        st.caption(
            "**1.0** = move in perfect lockstep · "
            "**0** = no relationship · "
            "**−1** = mirror opposites. "
            "High correlation between two stocks means less diversification benefit."
        )

# ─ Tab 3: Fun stats ───────────────────────────────────────────────────────────
with tab_fun:
    daily_ret = df[valid].pct_change().dropna()

    st.markdown("#### ⚡ Current win/loss streak")
    st.caption("How many consecutive trading days has each stock moved in the same direction?")

    streak_cols = st.columns(len(valid))
    for col, t in zip(streak_cols, valid):
        streak, direction = 0, None
        for v in daily_ret[t].iloc[::-1]:
            d = "up" if v > 0 else "down"
            if direction is None:
                direction = d
            if d == direction:
                streak += 1
            else:
                break
        emoji = "🟢" if direction == "up" else "🔴"
        col.metric(t, f"{streak} days {direction}", emoji)

    st.divider()

    st.markdown("#### 🌪 Annualised volatility")
    st.caption("Measured as the standard deviation of daily returns, scaled to a full year.")
    ann_vol = (daily_ret.std() * (252 ** 0.5) * 100).sort_values(ascending=True)

    fig_vol = px.bar(
        ann_vol,
        orientation="h",
        labels={"value": "Volatility (%)", "index": ""},
        color=ann_vol.values,
        color_continuous_scale=["#e9f7ef", "#FF4800"],
        title="Which stock takes you on the wildest ride?",
    )
    fig_vol.update_layout(
        paper_bgcolor="#FCFCFD", plot_bgcolor="#FCFCFD",
        font_family="Inter", showlegend=False, coloraxis_showscale=False,
        xaxis_tickformat=".1f",
    )
    fig_vol.update_traces(hovertemplate="%{y}: %{x:.1f}%<extra></extra>")
    st.plotly_chart(fig_vol, use_container_width=True)
