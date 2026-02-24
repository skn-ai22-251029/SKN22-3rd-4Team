# 🗂 Project Structure

SKN22-3rd-4Team/
├── .streamlit/                 # Streamlit 설정
│   └── secrets.toml            # API 키 및 환경 변수
├── logs/                       # 로그 파일 저장소
├── scripts/                    # 유틸리티 및 배치 스크립트
│   ├── build_company_relationships.py  # [ETL] 기업 관계 추출 및 그래프 구축 (병렬 처리 지원)
│   ├── migrate_to_neo4j.py            # Supabase → Neo4j 관계 데이터 마이그레이션
│   └── upload_to_supabase.py          # 초기 데이터 업로드
├── src/                        # 애플리케이션 핵심 소스 코드
│   ├── core/                   # 코어 비즈니스 로직
│   │   ├── chat_connector.py   # 채팅 세션 및 UI 연결 관리
│   │   └── utils.py            # 공통 유틸리티
│   ├── data/                   # 데이터 관리
│   │   ├── stock_api_client.py # Finnhub + yfinance 주식 데이터 API 클라이언트
│   │   └── supabase_client.py  # Supabase DB 클라이언트 (PostgreSQL/pgvector)
│   ├── rag/                    # RAG (Retrieval-Augmented Generation) 엔진
│   │   ├── analyst_chat.py     # 금융 분석가 챗봇 비즈니스 로직
│   │   ├── chat_tools.py       # 도구 정의 + ToolExecutor (도구 실행 모듈)
│   │   ├── data_retriever.py   # 병렬 데이터 수집기
│   │   ├── graph_rag.py        # [CORE] Neo4j Cypher + NetworkX 그래프 분석
│   │   ├── llm_client.py       # [NEW] 통합 LLM Client (Gemini/OpenAI 추상화)
│   │   ├── rag_base.py         # RAG 기본 클래스 (LangSmith 트레이싱 포함)
│   │   ├── report_generator.py # 투자 리포트 생성기
│   │   └── vector_store.py     # 벡터 검색 (OpenAI Embeddings + Supabase pgvector)
│   ├── tools/                  # 도구 및 헬퍼
│   │   ├── exchange_rate_client.py # 환율 정보
│   │   └── favorites_manager.py    # 관심 기업 관리
│   └── ui/                     # UI 컴포넌트 (Streamlit)
│       ├── components/         # 재사용 가능한 UI 컴포넌트
│       ├── helpers/            # UI 헬퍼 함수
│       │   ├── chart_helpers.py
│       │   ├── chat_helpers.py
│       │   ├── home_dashboard.py
│       │   ├── insights_helper.py
│       │   └── sidebar_manager.py
│       └── pages/              # 페이지별 UI
│           ├── home.py
│           ├── insights.py     # [MAIN] AI 애널리스트 채팅 페이지
│           ├── login_page.py
│           └── report_page.py
├── app.py                      # 메인 애플리케이션 진입점
├── .env                        # 환경 변수 (Gemini, OpenAI, Neo4j, Supabase 등)
├── .env.example                # 환경 변수 템플릿 (팀 공유용)
├── requirements.txt            # 의존성 패키지 목록
└── STRUCTURE.md                # 프로젝트 구조 문서 (현재 파일)
