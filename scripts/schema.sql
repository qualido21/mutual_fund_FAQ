-- Mutual Fund FAQ — Supabase pgvector schema
-- Run once: supabase db execute --file scripts/schema.sql

-- 1. Enable pgvector extension
create extension if not exists vector;

-- 2. Chunks table
create table if not exists mutual_fund_chunks (
  id           bigserial primary key,
  chunk_id     text unique not null,
  text         text not null,
  embedding    vector(1536),
  source_id    text,
  source_url   text,
  source_type  text,        -- 'amfi' | 'amc' | 'sebi'
  scheme_name  text,
  fact_types   text,        -- comma-separated e.g. "exit_load, benchmark"
  fetched_at   text,
  token_count  integer
);

-- 3. IVFFlat index for fast cosine search
-- (only useful once table has data; safe to run now)
create index if not exists mutual_fund_chunks_embedding_idx
  on mutual_fund_chunks
  using ivfflat (embedding vector_cosine_ops)
  with (lists = 100);

-- 4. RPC function used by the retriever
create or replace function match_chunks(
  query_embedding  vector(1536),
  match_count      int      default 5,
  match_threshold  float    default 0.60
)
returns table (
  chunk_id    text,
  text        text,
  source_url  text,
  source_type text,
  scheme_name text,
  fact_types  text,
  fetched_at  text,
  similarity  float
)
language sql stable as $$
  select
    chunk_id,
    text,
    source_url,
    source_type,
    scheme_name,
    fact_types,
    fetched_at,
    1 - (embedding <=> query_embedding) as similarity
  from mutual_fund_chunks
  where 1 - (embedding <=> query_embedding) > match_threshold
    and source_type = any(array['amfi', 'amc', 'sebi'])
  order by embedding <=> query_embedding
  limit match_count;
$$;
