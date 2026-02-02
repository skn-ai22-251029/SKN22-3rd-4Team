import streamlit as st
import logging
from data.supabase_client import SupabaseClient

logger = logging.getLogger(__name__)


def render_sidebar_status():
    """스케줄러 상태 및 기본 정보 표시 (placeholder if needed)"""
    pass  # app.py에서 scheduler status를 이미 처리하고 있을 수 있음. 확인 필요.


def render_watchlist_sidebar():
    """로그인 사용자용 관심 기업 사이드바 렌더링"""

    # 1. 상태 초기화
    if "watchlist" not in st.session_state:
        st.session_state.watchlist = []

    watchlist = st.session_state.watchlist

    # 2. Add UI
    add_col1, add_col2 = st.columns([3, 1])
    with add_col1:
        new_ticker = st.text_input(
            "관심기업 추가",
            placeholder="기업명/티커 입력",
            label_visibility="collapsed",
            key="sidebar_quick_add_ticker",
        )
    with add_col2:
        add_clicked = st.button("﹢", key="sidebar_add_btn", help="관심 기업 추가")

    # 3. Add Logic
    if add_clicked and new_ticker:
        search_term = new_ticker.strip()
        try:
            df = SupabaseClient.search_companies(search_term)

            if not df.empty:
                found_ticker = df.iloc[0]["ticker"]
                found_name = df.iloc[0].get("korean_name") or df.iloc[0]["company_name"]

                if found_ticker not in st.session_state.watchlist:
                    # DB 저장
                    if st.session_state.user:
                        SupabaseClient.add_favorite(
                            st.session_state.user["id"], found_ticker
                        )

                    st.session_state.watchlist.append(found_ticker)
                    st.toast(f"✅ {found_name} ({found_ticker}) 추가됨")
                    st.rerun()
                else:
                    st.toast(f"⚠️ {found_name} ({found_ticker})은(는) 이미 등록됨")
            else:
                st.toast(f"❌ '{search_term}' 검색 결과가 없습니다")
        except Exception as e:
            st.toast(f"⚠️ DB 연결 오류: {str(e)[:30]}")
            logger.error(f"Watchlist add error: {e}")

    st.markdown("---")

    # 4. List UI (List Layout)
    if watchlist:
        st.markdown("##### ⭐ 관심 기업")
        for ticker in list(watchlist):
            col1, col2 = st.columns([3, 1])
            with col1:
                st.markdown(f"📈 **{ticker}**")
            with col2:
                if st.button("x", key=f"sidebar_rm_{ticker}", help=f"{ticker} 삭제"):
                    try:
                        success = True
                        if st.session_state.user:
                            user_id = st.session_state.user["id"]
                            logger.info(
                                f"Removing favorite: User={user_id}, Ticker={ticker}"
                            )
                            success, error_msg = SupabaseClient.remove_favorite(
                                user_id, ticker
                            )
                            if not success:
                                st.toast(f"❌ DB 삭제 실패: {error_msg}")
                                logger.error(f"DB Delete Failed: {error_msg}")

                        if success:
                            st.session_state.watchlist.remove(ticker)
                            st.rerun()
                    except Exception as e:
                        st.toast(f"삭제 오류: {e}")
                        logger.error(f"Remove Error: {e}")

        st.caption(f"총 {len(watchlist)}개")
    else:
        st.caption("위 입력창에 기업명/티커를 입력하세요\n(예: 애플, MSFT)")
