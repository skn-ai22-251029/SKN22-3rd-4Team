"""
Main Streamlit application for Financial Analysis Bot
"""

import streamlit as st
import sys
import logging
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from config.settings import settings
from config.logging_config import setup_logging
from tools.scheduler_manager import init_scheduler, render_sidebar_status

# Setup logging
setup_logging(settings.LOG_LEVEL)
logger = logging.getLogger(__name__)


# ============================================================
# S&P 500 스케줄러 초기화 (앱 시작 시 1회만 실행)
# ============================================================
if "scheduler_initialized" not in st.session_state:
    init_scheduler()
    st.session_state.scheduler_initialized = True

# Page configuration
st.set_page_config(
    page_title="미국 재무제표 분석 및 투자 인사이트 봇",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)


# Custom CSS Loading
def load_css(file_name):
    with open(file_name, encoding="utf-8") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)


# Load global styles
css_path = Path(__file__).parent / "src" / "ui" / "styles.css"
if css_path.exists():
    load_css(str(css_path))
else:
    # Fallback if file not found (keep basic styles)
    st.markdown(
        """
    <style>
        [data-testid="stVerticalBlock"] > [style*="flex-direction"] {
            margin-top: -2rem !important;
        }
    </style>
    """,
        unsafe_allow_html=True,
    )

# ============================================================
# 로그인 체크
# ============================================================
if "is_logged_in" not in st.session_state:
    st.session_state.is_logged_in = False
    st.session_state.user = None

if not st.session_state.is_logged_in:
    import ui.pages.login_page as login_page

    login_page.render()
    st.stop()  # 로그인 전에는 메인 앱 실행 중단

# ============================================================
# Sidebar navigation (로그인 후 표시)
# ============================================================
st.sidebar.title("🏦 메뉴")
st.sidebar.markdown("---")

# Page navigation
pages = {
    "🏠 홈": "ui.pages.home",
    "💡 투자 인사이트 (챗봇)": "ui.pages.insights",
    "📅 실적 캘린더": "ui.pages.calendar_page",
    "📊 레포트 생성": "ui.pages.report_page",
}

selected_page = st.sidebar.radio(
    "페이지 선택", list(pages.keys()), label_visibility="collapsed"
)

# 로그아웃 버튼
if st.sidebar.button("로그아웃"):
    st.session_state.is_logged_in = False
    st.session_state.user = None
    st.session_state.watchlist = []
    st.rerun()

# ============================================================
# 스케줄러 상태 표시 / 관심 기업 표시 (사이드바)
# ============================================================
st.sidebar.markdown("---")
render_sidebar_status()

st.sidebar.markdown("---")
with st.sidebar.expander("⭐ 관심 기업", expanded=True):
    from ui.helpers.sidebar_manager import render_watchlist_sidebar

    render_watchlist_sidebar()


st.sidebar.markdown("---")

# Main content routing (Lazy Loading)
if selected_page in pages:
    module_path = pages[selected_page]
    try:
        # importlib을 사용하여 동적 import
        import importlib

        # ui.pages가 src 패키지 아래에 있으므로 경로 조정이 필요할 수 있음
        # sys.path에 src가 이미 추가되어 있으므로 바로 import 가능
        page_module = importlib.import_module(module_path)

        if hasattr(page_module, "render"):
            page_module.render()
        else:
            st.error(f"모듈 {module_path}에 render 함수가 없습니다.")

    except Exception as e:
        st.error(f"페이지 로드 실패: {e}")
        # 디버깅을 위한 상세 로그
        logger.error(f"Failed to load page {module_path}: {e}", exc_info=True)
