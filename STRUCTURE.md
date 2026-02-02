# 🗂 Project Structure

```text
c:\Workspaces\SKN22-3rd-4Team
├── .env                  # API 키 및 환경 변수 설정
├── .gitignore            # Git 제외 파일 목록
├── LICENSE               # 라이선스 정보
├── README.md             # 프로젝트 개요 및 배지
├── STRUCTURE.md          # 프로젝트 구조 상세 설명 (본 파일)
├── app.py                # Streamlit 메인 엔트리포인트 (애플리케이션 실행)
├── requirements.txt      # 파이썬 의존성 패키지 목록
├── config/               # 전역 설정
│   └── settings.py       # 모델 설정, 경로 상수 등
├── data/                 # 로컬 데이터 저장소 (DB 아님)
│   ├── 10k_documents/    # 수집된 SEC 10-K 보고서 원본 (PDF/TXT)
│   └── processed/        # 전처리 및 가공된 중간 데이터
├── docs/                 # 문서화
│   └── TUTORIAL.md       # 사용자 매뉴얼 및 가이드
├── fonts/                # PDF 리포트 생성용 폰트
│   ├── NanumGothic.ttf
│   └── NanumGothicBold.ttf
├── models/               # 사용자 정의 ML 모델 (필요 시)
├── scripts/              # 데이터 파이프라인 및 배치 스크립트
│   ├── collect_10k_relationships.py   # 10-K 기반 기업 관계 추출
│   ├── collect_top100_financials.py   # 주요 100대 기업 재무 수집
│   ├── embed_10k_documents.py         # 문서 임베딩 및 벡터 저장
│   ├── expand_to_sp500.py             # S&P 500 확장 수집
│   ├── sp500_scheduler.py             # 정기 수집 스케줄러
│   ├── update_existing_companies.py   # 기 존재 기업 최신화
│   ├── upload_relationships_to_supabase.py # 관계 데이터 DB 업로드
│   └── upload_to_supabase.py          # 범용 데이터 DB 업로드
└── src/                  # 애플리케이션 핵심 소스 코드
    ├── core/             # 코어 비즈니스 로직
    │   ├── chat_connector.py          # LLM 채팅 핸들러
    │   └── input_validator.py         # 사용자 입력 검증기
    ├── data/             # 외부 데이터 API 클라이언트
    │   ├── filing_processor.py        # 공시 데이터 가공
    │   ├── sec_collector.py           # EDGAR SEC 데이터 수집
    │   ├── seeking_alpha_client.py    # Seeking Alpha 뉴스/분석 수집
    │   ├── stock_api_client.py        # 통합 주식 데이터 (Finnhub, yfinance)
    │   └── supabase_client.py         # Supabase DB 입출력 핸들러
    ├── prompts/          # LangChain 프롬프트 템플릿
    │   ├── analyst_chat.txt           # 재무 분석가 페르소나
    │   ├── report_generator.txt       # 리포트 생성 프롬프트
    │   └── system_defense.txt         # 시스템 보안/입력 방어
    ├── rag/              # RAG (검색 증강 생성) 엔진
    │   ├── analyst_chat.py            # 채팅 로직 구현체
    │   ├── chat_tools.py              # 채팅 중 사용되는 도구 모음
    │   ├── data_retriever.py          # 데이터 통합 조회 (DB+Vector+Graph)
    │   ├── graph_rag.py               # 그래프 기반 관계 검색
    │   ├── rag_base.py                # RAG 기본 클래스
    │   ├── report_generator.py        # 투자 리포트 생성기
    │   └── vector_store.py            # 벡터 DB 인터페이스
    ├── sql/              # Natural Language to SQL
    │   └── text_to_sql.py             # 자연어 질의 -> SQL 변환기
    ├── tools/            # LangGraph/Agent 전용 도구
    │   ├── calculator_tool.py         # 계산 도구
    │   ├── finnhub_tool.py           # Finnhub 연동 도구
    │   ├── search_tool.py             # 웹 검색 도구 (Tavily 등)
    │   └── vector_tool.py             # 벡터 검색 도구
    ├── ui/               # Streamlit 사용자 인터페이스
    │   ├── helpers/      # UI 컴포넌트 분리
    │   │   ├── chart_helpers.py       # 차트 그리기/설정 헬퍼
    │   │   ├── chat_helpers.py        # 채팅 UI 구성 헬퍼
    │   │   └── insights_helper.py     # 인사이트/티커 리졸버 헬퍼
    │   └── pages/        # 개별 페이지
    │       ├── calendar_page.py       # 경제 캘린더 페이지
    │       ├── home.py                # 메인 대시보드
    │       ├── insights.py            # 인사이트 채팅 페이지
    │       └── report_page.py         # 레포트 생성 페이지
    └── utils/            # 공통 유틸리티
        ├── chart_utils.py             # Matplotlib 차트 생성 (PDF용)
        ├── common.py                  # 공통 설정 및 싱글톤 관리
        ├── financial_calcs.py         # 재무 지표 계산 로직
        ├── helpers.py                 # 기타 잡다한 헬퍼
        ├── pdf_utils.py               # PDF 생성 및 레이아웃
        ├── plotly_charts.py           # Plotly 차트 생성 (웹용)
        ├── supabase_helper.py         # Supabase 간편 유틸
        └── ticker_search_agent.py     # ✅ 지능형 티커 검색/변환 에이전트
```
