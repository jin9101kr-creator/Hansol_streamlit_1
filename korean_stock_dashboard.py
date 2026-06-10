import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta

st.set_page_config(
    page_title="국내 주식 대시보드",
    page_icon="📈",
    layout="wide",
)

STOCKS = {
    "삼성전자": "005930.KS",
    "SK하이닉스": "000660.KS",
    "LG에너지솔루션": "373220.KS",
    "삼성바이오로직스": "207940.KS",
    "현대차": "005380.KS",
    "NAVER": "035420.KS",
    "카카오": "035720.KS",
    "셀트리온": "068270.KS",
    "KB금융": "105560.KS",
    "POSCO홀딩스": "005490.KS",
}

PERIOD_OPTIONS = {
    "1개월": "1mo",
    "3개월": "3mo",
    "6개월": "6mo",
    "1년": "1y",
    "2년": "2y",
    "5년": "5y",
}


@st.cache_data(ttl=300)
def fetch_stock_info(tickers: list[str]) -> pd.DataFrame:
    rows = []
    for name, ticker in STOCKS.items():
        if ticker not in tickers:
            continue
        try:
            t = yf.Ticker(ticker)
            info = t.fast_info
            rows.append({
                "종목명": name,
                "티커": ticker,
                "현재가": info.last_price,
                "전일종가": info.previous_close,
                "등락률(%)": round((info.last_price - info.previous_close) / info.previous_close * 100, 2),
                "시가총액(억)": round(info.market_cap / 1e8) if info.market_cap else None,
                "52주 최고": info.year_high,
                "52주 최저": info.year_low,
            })
        except Exception:
            pass
    return pd.DataFrame(rows)


@st.cache_data(ttl=300)
def fetch_history(ticker: str, period: str) -> pd.DataFrame:
    t = yf.Ticker(ticker)
    df = t.history(period=period)
    df.index = pd.to_datetime(df.index).tz_localize(None)
    return df


def color_change(val):
    if isinstance(val, float):
        color = "red" if val > 0 else ("blue" if val < 0 else "gray")
        return f"color: {color}"
    return ""


# ── 사이드바 ──────────────────────────────────────────────
st.sidebar.title("⚙️ 설정")
selected_names = st.sidebar.multiselect(
    "종목 선택",
    options=list(STOCKS.keys()),
    default=list(STOCKS.keys()),
)
period_label = st.sidebar.selectbox("조회 기간", list(PERIOD_OPTIONS.keys()), index=2)
period = PERIOD_OPTIONS[period_label]

chart_type = st.sidebar.radio("차트 유형", ["캔들스틱", "라인"], index=0)
show_volume = st.sidebar.checkbox("거래량 표시", value=True)

if st.sidebar.button("🔄 데이터 새로고침"):
    st.cache_data.clear()
    st.rerun()

# ── 메인 ─────────────────────────────────────────────────
st.title("📈 국내 주식 대시보드")
st.caption(f"데이터 출처: Yahoo Finance  |  마지막 업데이트: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if not selected_names:
    st.warning("사이드바에서 종목을 하나 이상 선택해주세요.")
    st.stop()

selected_tickers = [STOCKS[n] for n in selected_names]

# ── 시세 요약 테이블 ───────────────────────────────────────
st.subheader("📊 시세 요약")
with st.spinner("시세 데이터 불러오는 중..."):
    summary_df = fetch_stock_info(selected_tickers)

if not summary_df.empty:
    styled = (
        summary_df.style
        .map(color_change, subset=["등락률(%)"])
        .format({
            "현재가": "{:,.0f}",
            "전일종가": "{:,.0f}",
            "등락률(%)": "{:+.2f}%",
            "시가총액(억)": "{:,.0f}",
            "52주 최고": "{:,.0f}",
            "52주 최저": "{:,.0f}",
        })
    )
    st.dataframe(styled, use_container_width=True, hide_index=True)

# ── 등락률 바 차트 ─────────────────────────────────────────
st.subheader("📉 등락률 비교")
if not summary_df.empty:
    bar_fig = px.bar(
        summary_df,
        x="종목명",
        y="등락률(%)",
        color="등락률(%)",
        color_continuous_scale=["blue", "white", "red"],
        color_continuous_midpoint=0,
        text="등락률(%)",
    )
    bar_fig.update_traces(texttemplate="%{text:+.2f}%", textposition="outside")
    bar_fig.update_layout(height=350, showlegend=False, coloraxis_showscale=False)
    st.plotly_chart(bar_fig, use_container_width=True)

# ── 개별 종목 차트 ─────────────────────────────────────────
st.subheader(f"🕯️ 종목별 차트 ({period_label})")

cols_per_row = 2
rows = [selected_names[i:i + cols_per_row] for i in range(0, len(selected_names), cols_per_row)]

for row in rows:
    cols = st.columns(cols_per_row)
    for col, name in zip(cols, row):
        ticker = STOCKS[name]
        with col:
            with st.spinner(f"{name} 차트 불러오는 중..."):
                hist = fetch_history(ticker, period)

            if hist.empty:
                st.warning(f"{name}: 데이터 없음")
                continue

            fig = go.Figure()

            if chart_type == "캔들스틱":
                fig.add_trace(go.Candlestick(
                    x=hist.index,
                    open=hist["Open"],
                    high=hist["High"],
                    low=hist["Low"],
                    close=hist["Close"],
                    name=name,
                    increasing_line_color="red",
                    decreasing_line_color="blue",
                ))
            else:
                fig.add_trace(go.Scatter(
                    x=hist.index,
                    y=hist["Close"],
                    mode="lines",
                    name=name,
                    line=dict(color="royalblue", width=2),
                ))

            if show_volume:
                fig.add_trace(go.Bar(
                    x=hist.index,
                    y=hist["Volume"],
                    name="거래량",
                    marker_color="lightgray",
                    opacity=0.4,
                    yaxis="y2",
                ))
                fig.update_layout(
                    yaxis2=dict(overlaying="y", side="right", showgrid=False),
                )

            fig.update_layout(
                title=name,
                height=350,
                margin=dict(l=10, r=10, t=40, b=10),
                xaxis_rangeslider_visible=False,
                legend=dict(orientation="h", y=1.1),
            )
            st.plotly_chart(fig, use_container_width=True)

# ── 누적 수익률 비교 ───────────────────────────────────────
st.subheader("📈 누적 수익률 비교")
with st.spinner("수익률 계산 중..."):
    returns_data = {}
    for name in selected_names:
        ticker = STOCKS[name]
        hist = fetch_history(ticker, period)
        if not hist.empty:
            returns_data[name] = (hist["Close"] / hist["Close"].iloc[0] - 1) * 100

if returns_data:
    returns_df = pd.DataFrame(returns_data)
    fig_ret = px.line(returns_df, labels={"value": "누적 수익률 (%)", "index": "날짜", "variable": "종목"})
    fig_ret.add_hline(y=0, line_dash="dash", line_color="gray", opacity=0.5)
    fig_ret.update_layout(height=400)
    st.plotly_chart(fig_ret, use_container_width=True)

st.markdown("---")
st.caption("※ 본 대시보드는 투자 권유가 아니며 교육 목적으로만 사용하세요.")
