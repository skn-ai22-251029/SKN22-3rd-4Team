"""
Investment Report Generation Page
"""

import streamlit as st
import streamlit as st
from utils.pdf_utils import create_pdf


def render():
    """Render Report Generator Page"""
    st.markdown('<h1 class="main-header">📊 레포트 생성</h1>', unsafe_allow_html=True)
    st.caption("gpt-4.1-mini 기반 | 단일 기업 분석 & 비교 분석 레포트 생성")

    st.markdown("---")

    st.info(
        "💡 **단일 분석**: `AAPL` 또는 `애플` | **비교 분석**: `애플, 마이크로소프트, 구글` (콤마로 구분)"
    )

    col1, col2 = st.columns([3, 1])

    with col1:
        ticker = st.text_input(
            "분석할 회사 (티커 또는 한글명)",
            placeholder="애플 또는 애플, 마이크로소프트, 구글",
            key="report_ticker_main",
        )

    with col2:
        generate_btn = st.button(
            "📝 레포트 생성",
            type="primary",
            use_container_width=True,
            key="gen_btn_main",
        )

    if generate_btn and ticker:
        try:
            from rag.report_generator import ReportGenerator  # Lazy import
            from src.data.supabase_client import SupabaseClient

            def resolve_to_ticker(term: str) -> str:
                """한글명이나 영문명을 티커로 변환"""
                term = term.strip()
                # 이미 티커 형식 (대문자 영문)이면 그대로 반환
                if term.isupper() and term.isalpha():
                    return term
                # DB에서 검색
                try:
                    df = SupabaseClient.search_companies(term)
                    if not df.empty:
                        return df.iloc[0]["ticker"]
                except:
                    pass
                return term.upper()  # 못 찾으면 대문자로 반환

            generator = ReportGenerator()

            # Check if multiple tickers (comma separated)
            if "," in ticker:
                raw_terms = [t.strip() for t in ticker.split(",") if t.strip()]
                tickers = [resolve_to_ticker(t) for t in raw_terms]
                if len(tickers) > 1:
                    with st.spinner(
                        f"⚖️ {', '.join(tickers)} 비교 분석 레포트 생성 중..."
                    ):
                        report = generator.generate_comparison_report(tickers)
                        file_prefix = f"comparison_{'_'.join(tickers)}"
                else:
                    with st.spinner(f"📊 {tickers[0]} 분석 레포트 생성 중..."):
                        report = generator.generate_report(tickers[0])
                        file_prefix = f"{tickers[0]}_analysis_report"
            else:
                resolved_ticker = resolve_to_ticker(ticker)
                with st.spinner(f"📊 {resolved_ticker} 분석 레포트 생성 중..."):
                    report = generator.generate_report(resolved_ticker)
                    file_prefix = f"{resolved_ticker}_analysis_report"

            st.markdown("---")
            st.markdown(report)

            # Download button
            try:
                pdf_bytes = create_pdf(report)
                mime_type = "application/pdf"
                file_ext = "pdf"
                label = "📥 레포트 다운로드 (PDF)"
            except:
                pdf_bytes = report.encode("utf-8")
                mime_type = "text/markdown"
                file_ext = "md"
                label = "📥 레포트 다운로드 (MD)"

            st.download_button(
                label=label,
                data=pdf_bytes,
                file_name=f"{file_prefix}.{file_ext}",
                mime=mime_type,
            )

        except Exception as e:
            st.error(f"레포트 생성 실패: {e}")

    elif generate_btn:
        st.warning("티커를 입력해주세요")
