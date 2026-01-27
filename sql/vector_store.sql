-- ==========================================
-- Supabase Vector Store 설정 (pgvector)
-- ==========================================

-- 1. pgvector 확장 기능 활성화
create extension if not exists vector;

-- 2. 문서 테이블 생성 (10-K 공시 텍스트 저장)
create table if not exists documents (
    id uuid primary key default uuid_generate_v4(),
    company_id uuid references companies(id), -- 기업 ID (선택)
    ticker text not null,                     -- 티커
    content text not null,                    -- 텍스트 내용 (Chunk)
    metadata jsonb,                           -- 메타데이터 (섹션명, 연도, 출처 등)
    embedding vector(1536),                   -- OpenAI 임베딩 (text-embedding-3-small 기준)
    created_at timestamp with time zone default now()
);

-- 3. 검색 효율을 위한 인덱스 생성 (IVFFlat)
-- 데이터가 많아지면 인덱스 생성을 고려해야 함 (초기에는 없어도 무방)
-- create index on documents using ivfflat (embedding vector_cosine_ops)
-- with (lists = 100);

-- 4. 벡터 검색 함수 (RPC)
-- LangChain/LangGraph에서 호출할 검색 함수
create or replace function match_documents (
    query_embedding vector(1536),
    match_threshold float,
    match_count int,
    filter_ticker text default null
) returns table (
    id uuid,
    content text,
    metadata jsonb,
    similarity float
) language plpgsql stable as $$
begin
    return query (
        select
            d.id,
            d.content,
            d.metadata,
            1 - (d.embedding <=> query_embedding) as similarity
        from documents d
        where 1 - (d.embedding <=> query_embedding) > match_threshold
        and (filter_ticker is null or d.ticker = filter_ticker)
        order by d.embedding <=> query_embedding
        limit match_count
    );
end;
$$;
