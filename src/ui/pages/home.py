"""
홈 페이지 - Supabase DB 연동 + Plotly 차트
"""

import streamlit as st
import pandas as pd
import sys
from pathlib import Path
from datetime import datetime

# 경로 설정
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

# Lazy Loading 상태
SUPABASE_AVAILABLE = False
EXCHANGE_AVAILABLE = False
PLOTLY_AVAILABLE = False

# Plotly import
try:
    import plotly.express as px
    import plotly.graph_objects as go

    PLOTLY_AVAILABLE = True
except ImportError:
    pass


def format_number(value, unit=""):
    """숫자 포맷팅 (억 단위)"""
    if pd.isna(value) or value is None:
        return "-"

    if abs(value) >= 1e12:
        return f"${value/1e12:.1f}조{unit}"
    elif abs(value) >= 1e9:
        return f"${value/1e9:.1f}B{unit}"
    elif abs(value) >= 1e6:
        return f"${value/1e6:.1f}M{unit}"
    else:
        return f"${value:,.0f}{unit}"


def _render_plotly_bar_chart(df: pd.DataFrame, x_col: str, y_col: str, title: str):
    """Plotly 바 차트 렌더링"""
    if not PLOTLY_AVAILABLE:
        st.bar_chart(df.set_index(x_col)[y_col])
        return

    fig = px.bar(
        df,
        x=x_col,
        y=y_col,
        title=title,
        color=y_col,
        color_continuous_scale="Blues",
    )
    fig.update_layout(
        height=400,
        xaxis_title="",
        yaxis_title="매출 (십억 USD)",
        showlegend=False,
        template="plotly_white",
    )
    st.plotly_chart(fig, use_container_width=True)


def _render_plotly_pie_chart(series: pd.Series, title: str):
    """Plotly 파이 차트 렌더링"""
    if not PLOTLY_AVAILABLE:
        st.bar_chart(series)
        return

    fig = px.pie(
        values=series.values,
        names=series.index,
        title=title,
        hole=0.4,  # 도넛 차트
    )
    fig.update_layout(
        height=350,
        template="plotly_white",
    )
    fig.update_traces(textposition="inside", textinfo="percent+label")
    st.plotly_chart(fig, use_container_width=True)


def _get_data_period(supabase_client) -> str:
    """DB에서 실제 데이터 기간 조회"""
    try:
        annual_df = supabase_client.get_annual_reports()
        if not annual_df.empty and "fiscal_year" in annual_df.columns:
            min_year = int(annual_df["fiscal_year"].min())
            max_year = int(annual_df["fiscal_year"].max())
            return f"{min_year}-{max_year}"
    except:
        pass
    return "2020-2024"


def _get_last_update() -> str:
    """마지막 업데이트 시간"""
    now = datetime.now()
    return now.strftime("%m/%d %H:%M")


# -----------------------------------------------------------------------------
# Caching Functions (Performance Optimization)
# -----------------------------------------------------------------------------


@st.cache_data(ttl=3600)
def _get_cached_companies(supabase_client):
    """모든 기업 목록 캐싱 (1시간)"""
    return supabase_client.get_all_companies()


@st.cache_data(ttl=3600)
def _get_cached_annual_reports(supabase_client):
    """연간 재무 데이터 캐싱 (1시간)"""
    return supabase_client.get_annual_reports()


@st.cache_data(ttl=3600)
def _get_cached_top_revenue_companies(supabase_client, year=2024, limit=20):
    """매출 상위 기업 캐싱 (1시간)"""
    return supabase_client.get_top_companies_by_revenue(year, limit)


@st.cache_data(ttl=3600)
def _get_cached_exchange_rates():
    """환율 정보 캐싱 (1시간)"""
    from tools.exchange_rate_client import get_exchange_client

    try:
        client = get_exchange_client()
        return client.get_major_rates_summary()
    except Exception:
        return {}


def render():
    """홈 페이지 렌더링"""
    global SUPABASE_AVAILABLE, EXCHANGE_AVAILABLE

    # Lazy Imports
    try:
        from data.supabase_client import (
            SupabaseClient,
            get_companies,
            get_top_revenue_companies,
        )

        SUPABASE_AVAILABLE = True
    except ImportError:
        SUPABASE_AVAILABLE = False

    try:
        from tools.exchange_rate_client import get_exchange_client

        EXCHANGE_AVAILABLE = True
    except ImportError:
        EXCHANGE_AVAILABLE = False

    # Header
    st.markdown(
        '<h1 class="main-header">📊 미국 재무제표 분석 및 투자 인사이트 봇</h1>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<p class="sub-header">AI 기반 미국 상장사 재무제표 분석 도구</p>',
        unsafe_allow_html=True,
    )

    # 데이터베이스 연결 상태
    if SUPABASE_AVAILABLE:
        try:
            # Cached Call
            companies_df = _get_cached_companies(SupabaseClient)
            company_count = len(companies_df)
        except Exception as e:
            st.warning(f"⚠️ 데이터 로드 중 오류: {e}")
            companies_df = pd.DataFrame()
            company_count = 0
    else:
        st.warning("⚠️ Supabase 연결이 설정되지 않았습니다. .env 파일을 확인하세요.")
        companies_df = pd.DataFrame()
        company_count = 0

    st.markdown("---")

    # 관심 기업 초기화
    if "watchlist" not in st.session_state:
        st.session_state.watchlist = []

    # 관심 기업 섹션 (있을 때만 표시)
    if st.session_state.watchlist:
        st.markdown("### ⭐ 관심 기업")
        # 왼쪽 정렬을 위해 넉넉한 컬럼 수 사용
        cols = st.columns(8)
        for i, ticker in enumerate(st.session_state.watchlist):
            if i < 8:  # 최대 8개까지만 한 줄에 표시 (더 많으면 ... 처리)
                with cols[i]:
                    if st.button(f"🗑️ {ticker}", key=f"home_rm_{ticker}", help="제거"):
                        # DB 삭제 로직 추가
                        try:
                            success = True
                            if st.session_state.user:
                                success, _ = SupabaseClient.remove_favorite(
                                    st.session_state.user["id"], ticker
                                )

                            if success:
                                st.session_state.watchlist.remove(ticker)
                                st.rerun()
                            else:
                                st.error("삭제 실패")
                        except Exception:
                            st.error("삭제 오류")

        if len(st.session_state.watchlist) > 8:
            st.caption(f"... +{len(st.session_state.watchlist) - 8}개 더")
        st.markdown("---")

    # 메트릭 카드 - 동적 데이터
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(label="📈 등록된 기업", value=f"{company_count}개")

    with col2:
        report_count = 0
        if SUPABASE_AVAILABLE and company_count > 0:
            try:
                # Cached Call
                annual_df = _get_cached_annual_reports(SupabaseClient)
                report_count = len(annual_df)
            except:
                pass
        st.metric(label="📊 재무 레코드", value=f"{report_count}개")

    with col3:
        # 동적 데이터 기간
        data_period = (
            _get_data_period(SupabaseClient) if SUPABASE_AVAILABLE else "2020-2024"
        )
        st.metric(label="📅 데이터 기간", value=data_period)

    with col4:
        # 동적 업데이트 시간
        st.metric(label="🔄 마지막 조회", value=_get_last_update())

    # 환율 정보 섹션
    st.markdown("---")
    st.markdown("### 💱 실시간 환율 정보")

    if EXCHANGE_AVAILABLE:
        try:
            # Cached Call
            summary = _get_cached_exchange_rates()
            display_rates = summary.get("display_rates", {})
            update_time = summary.get("update_time", "N/A")

            rate_cols = st.columns(4)
            rate_items = [
                ("🇺🇸 달러 (USD/KRW)", "USD/KRW"),
                ("🇯🇵 엔화 (100 JPY/KRW)", "JPY/KRW (100엔)"),
                ("🇪🇺 유로 (EUR/KRW)", "EUR/KRW"),
                ("🇬🇧 파운드 (GBP/KRW)", "GBP/KRW"),
            ]
            for col, (label, key) in zip(rate_cols, rate_items):
                with col:
                    st.metric(label=label, value=display_rates.get(key, "-"))

            st.caption(
                f"📅 실시간 정보 (한국시간: {update_time}) | 출처: Global Open Exchange | 기준: KRW (매매기준율)"
            )
        except Exception as e:
            st.warning(f"환율 정보를 불러올 수 없습니다: {e}")
    else:
        st.info("💱 환율 정보 서비스가 비활성화되어 있습니다.")

    st.markdown("---")

    # 탭 구성
    if "home_active_tab" not in st.session_state:
        st.session_state.home_active_tab = "📊 매출 상위 기업"

    tab_options = ["🏆 매출 상위 기업", "🔍 기업 검색", "💾 DB 현황", "💡 빠른 시작"]
    selected_tab = st.radio(
        "메뉴 선택",
        tab_options,
        horizontal=True,
        label_visibility="collapsed",
        key="home_tab_selection",
        index=(
            tab_options.index(st.session_state.home_active_tab)
            if st.session_state.home_active_tab in tab_options
            else 0
        ),
        on_change=lambda: st.session_state.update(
            home_active_tab=st.session_state.home_tab_selection
        ),
    )

    if selected_tab == "🏆 매출 상위 기업":
        _render_top_companies_tab(SUPABASE_AVAILABLE, company_count)

    elif selected_tab == "🔍 기업 검색":
        _render_search_tab(
            SUPABASE_AVAILABLE, SupabaseClient if SUPABASE_AVAILABLE else None
        )

    elif selected_tab == "💾 DB 현황":
        _render_db_status_tab(SUPABASE_AVAILABLE, companies_df, company_count)

    elif selected_tab == "💡 빠른 시작":
        _render_quick_start_tab()


def _render_top_companies_tab(supabase_available: bool, company_count: int):
    """매출 상위 기업 탭"""
    from data.supabase_client import get_top_revenue_companies

    st.markdown("### 📊 2024년 매출 상위 20개 기업")

    if supabase_available and company_count > 0:
        try:
            top_df = get_top_revenue_companies(year=2024, limit=20)

            if not top_df.empty:
                # 데이터 포맷팅
                display_df = top_df[
                    ["ticker", "company_name", "revenue", "net_income", "total_assets"]
                ].copy()
                display_df.columns = ["티커", "기업명", "매출", "순이익", "총자산"]

                display_df["매출"] = display_df["매출"].apply(format_number)
                display_df["순이익"] = display_df["순이익"].apply(format_number)
                display_df["총자산"] = display_df["총자산"].apply(format_number)

                st.dataframe(display_df, use_container_width=True, hide_index=True)

                # Plotly 바 차트
                st.markdown("### 📈 매출 비교 차트")
                chart_df = top_df[["ticker", "revenue"]].dropna().head(10).copy()
                chart_df["revenue"] = chart_df["revenue"] / 1e9  # 십억 달러 단위

                _render_plotly_bar_chart(
                    chart_df,
                    x_col="ticker",
                    y_col="revenue",
                    title="매출 상위 10개 기업 (십억 USD)",
                )
            else:
                st.info("2024년 데이터가 아직 없습니다.")
        except Exception as e:
            st.error(f"데이터 로드 오류: {e}")
    else:
        st.info("Supabase에 연결하여 데이터를 확인하세요.")


def _render_search_tab(supabase_available: bool, SupabaseClient):
    """기업 검색 탭"""
    st.markdown("### 🔍 기업 검색")

    if "search_query" not in st.session_state:
        st.session_state.search_query = ""

    def update_search():
        st.session_state.search_query = st.session_state.search_input

    search_query = st.text_input(
        "티커 또는 기업명으로 검색",
        placeholder="예: AAPL, Apple, Microsoft",
        value=st.session_state.search_query,
        key="search_input",
        on_change=update_search,
    )

    if search_query and supabase_available and SupabaseClient:
        try:
            results = SupabaseClient.search_companies(search_query)

            if not results.empty:
                st.success(f"{len(results)}개 기업 검색됨")

                for _, company in results.iterrows():
                    col_exp, col_star = st.columns([10, 1])
                    ticker = company["ticker"]
                    is_watched = ticker in st.session_state.watchlist

                    with col_star:
                        btn_label = "⭐" if is_watched else "☆"
                        if st.button(
                            btn_label,
                            key=f"star_search_{ticker}",
                            help="관심 기업 추가/제거",
                        ):
                            if is_watched:
                                st.session_state.watchlist.remove(ticker)
                            else:
                                st.session_state.watchlist.append(ticker)
                            st.rerun()

                    with col_exp:
                        with st.expander(
                            f"📊 {company['ticker']} - {company['company_name']}"
                        ):
                            financials = SupabaseClient.get_financial_summary(
                                company["ticker"]
                            )

                            if financials and financials.get("annual_reports"):
                                reports = financials["annual_reports"]
                                c1, c2, c3 = st.columns(3)
                                latest = reports[0] if reports else {}

                                with c1:
                                    st.metric(
                                        "매출", format_number(latest.get("revenue"))
                                    )
                                with c2:
                                    st.metric(
                                        "순이익",
                                        format_number(latest.get("net_income")),
                                    )
                                with c3:
                                    st.metric(
                                        "총자산",
                                        format_number(latest.get("total_assets")),
                                    )

                                reports_df = pd.DataFrame(reports)
                                if not reports_df.empty:
                                    display_cols = [
                                        "fiscal_year",
                                        "revenue",
                                        "net_income",
                                        "eps",
                                    ]
                                    available_cols = [
                                        c
                                        for c in display_cols
                                        if c in reports_df.columns
                                    ]
                                    st.dataframe(
                                        reports_df[available_cols], hide_index=True
                                    )
                            else:
                                st.info("재무 데이터가 없습니다.")
            else:
                st.warning("검색 결과가 없습니다.")
        except Exception as e:
            st.error(f"검색 오류: {e}")


def _render_db_status_tab(
    supabase_available: bool, companies_df: pd.DataFrame, company_count: int
):
    """DB 현황 탭"""
    st.markdown("### 💾 데이터베이스 현황")

    if supabase_available and company_count > 0:
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("**등록된 기업 (일부)**")
            if not companies_df.empty:
                st.dataframe(
                    companies_df[["ticker", "company_name"]].head(10),
                    hide_index=True,
                    use_container_width=True,
                )

        with col2:
            st.markdown("**섹터별 분포**")
            if (
                "sector" in companies_df.columns
                and companies_df["sector"].notna().any()
            ):
                sector_counts = companies_df["sector"].value_counts()

                # 유효하지 않은 섹터 필터링 (숫자로만 된 경우 또는 "11" 같은 오류 데이터)
                valid_sectors = [
                    s
                    for s in sector_counts.index
                    if s
                    and not str(s).strip().isdigit()
                    and str(s).strip() != "11"
                    and str(s).lower() != "nan"
                ]
                sector_counts = sector_counts[valid_sectors]

                # Plotly 파이 차트
                if not sector_counts.empty:
                    _render_plotly_pie_chart(sector_counts, title="섹터별 기업 분포")
                else:
                    st.info("유효한 섹터 정보가 없습니다.")
            else:
                st.info("섹터 정보가 아직 없습니다.")
    else:
        st.info("데이터베이스에 연결되지 않았거나 데이터가 없습니다.")


def _render_quick_start_tab():
    """빠른 시작 가이드 탭"""
    st.markdown("### 💡 빠른 시작 가이드")
    st.markdown(
        """
#### 🎯 주요 기능 안내

**1. 📊 홈 (Home)**
- **매출 상위 기업**: 2024년 기준 매출 Top 20 기업의 재무 현황 조회
- **기업 검색**: 티커/기업명으로 검색 및 관심 기업 등록
- **DB 현황**: 수집된 데이터 및 섹터별 분포 확인

**2. 📝 레포트 생성 (Reports)**
- **AI 투자 레포트**: 특정/복수 기업에 대한 심층 분석 보고서 생성
- **비교 분석**: 여러 경쟁사를 동시에 비교 분석 (최대 3개 권장)
- **차트 포함**: 주가, 거래량, 재무 차트가 포함된 PDF 레포트 다운로드

**3. 🤖 투자 인사이트 (Insights)**
- **AI 애널리스트**: 챗봇과 대화하며 투자 궁금증 해결
- **실시간 데이터**: "애플 주가 어때?", "테슬라 재무 보여줘" 등 자연어 질문
- **맞춤형 분석**: 사용자의 관심사에 맞춘 투자 조언 제공

**4. 🗓️ 실적 캘린더 (Calendar)**
- **관심 기업 일정**: 내가 등록한 관심 기업의 실적 발표일 확인
- **시장 예측**: EPS 예상치와 실제 발표치(Surprise) 비교
    """
    )
