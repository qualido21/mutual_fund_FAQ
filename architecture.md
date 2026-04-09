# Mutual Fund FAQ Assistant — Detailed Phase-wise Architecture

> **Project:** Facts-Only Mutual Fund FAQ Assistant (Groww Use Case)
> **Stack:** Next.js 15 (App Router) · OpenAI API · Supabase pgvector · Vercel
> **Constraint:** Official sources only (AMC, AMFI, SEBI) — no investment advice
> **API Key:** Single `OPENAI_API_KEY` in `.env` — used across all phases for embeddings and LLM

---

## Phase 1 — Corpus Collection & Ingestion

### Goal
Build a curated, verified, official-only knowledge base of 15–25 pages covering 1 AMC and 3–5 schemes.

### 1.1 Source Selection

Pick one AMC (e.g., Mirae Asset) and 3–5 schemes:

| Scheme | Type | Source URLs |
|---|---|---|
| Mirae Asset Large Cap Fund | Equity | AMC scheme page, AMFI page |
| Mirae Asset ELSS Tax Saver | Equity-ELSS | AMC scheme page, AMFI page |
| Mirae Asset Liquid Fund | Debt | AMC scheme page, AMFI page |
| SEBI Investor Charter | Regulatory | SEBI website |
| AMFI FAQs | General | AMFI website |

**Source Registry file (`data/sources.json`):**
```json
[
  {
    "id": "src_001",
    "url": "https://www.amfiindia.com/...",
    "type": "amfi",
    "scheme": "Mirae Asset Large Cap Fund",
    "description": "Scheme information document",
    "fetched_at": null
  }
]
```

### 1.2 Data Collection Pipeline

```
sources.json
    │
    ▼
[Fetcher] ──► HTML pages  ──► [HTML Parser]  ──► cleaned_text/
             PDF files    ──► [PDF Parser]   ──► cleaned_text/
    │
    ▼
[Metadata Tagger]
    │
    ▼
corpus/
  ├── src_001.txt
  ├── src_001.meta.json
  ├── src_002.txt
  └── ...
```

**Environment (`scripts/phase1/fetch_corpus.py` reads from `.env`):**
```
OPENAI_API_KEY=sk-...   # not used in Phase 1 but .env is loaded uniformly
```

**Fetcher (`scripts/phase1/fetch_corpus.py`):**
- Use `requests` + `BeautifulSoup` for HTML pages
- Use `pdfplumber` for scheme information documents (SIDs/KIMs)
- Respect `robots.txt`; add 2s delay between requests
- Save raw + cleaned versions separately

**HTML Parser rules:**
- Remove nav, footer, cookie banners, ads
- Keep: headings, paragraphs, tables (expense ratio, exit load grids)
- Convert tables → markdown format for LLM readability

**PDF Parser rules:**
- Extract text page by page using `pdfplumber`
- Detect and preserve tabular data (fund factsheets)
- Skip image-only pages (flag for manual review)

**Metadata per document (`src_001.meta.json`):**
```json
{
  "id": "src_001",
  "url": "https://...",
  "source_type": "amfi | amc | sebi",
  "scheme_name": "Mirae Asset Large Cap Fund",
  "fact_types": ["expense_ratio", "exit_load", "benchmark"],
  "fetched_at": "2026-04-09T10:00:00Z",
  "content_hash": "sha256:abc123..."
}
```

### 1.3 Fact Extraction (Structured)

Run a structured extractor after parsing to pull known fields into a lookup table.

**Schema (`data/scheme_facts.json`):**
```json
{
  "scheme_name": "Mirae Asset Large Cap Fund",
  "category": "Large Cap Fund",
  "expense_ratio": "0.54% (Direct)",
  "exit_load": "1% if redeemed within 1 year",
  "min_sip": "₹1,000",
  "min_lumpsum": "₹5,000",
  "lock_in": "None",
  "benchmark": "Nifty 100 TRI",
  "riskometer": "Very High",
  "source_url": "https://...",
  "fetched_at": "2026-04-09"
}
```

This structured store acts as a fast-path lookup before hitting the vector index.

### 1.4 Corpus Quality Checklist

- [ ] All URLs are `.gov.in`, `.amfiindia.com`, or official AMC domains
- [ ] No third-party blogs, news articles, or aggregators
- [ ] Content hash stored to detect stale data
- [ ] `sources.json` is the single source of truth for all URLs used

---

## Phase 2 — Chunking, Embedding & Vector Index

### Goal
Transform cleaned corpus text into a semantically searchable vector index with full source traceability per chunk.

### 2.1 Chunking Strategy

```
src_001.txt
    │
    ▼
[Chunker]
    │
    ├── Chunk 1: "The expense ratio of Mirae Asset Large Cap Fund..."
    ├── Chunk 2: "Exit load is 1% if redeemed within 1 year..."
    └── Chunk N: ...
```

**Chunking rules:**
- Chunk size: **400 tokens** with **50-token overlap**
- Respect paragraph and section boundaries — never cut mid-sentence
- Tables: treat each row as an independent chunk (avoids cross-row confusion)
- Attach full metadata to every chunk (source_url, scheme_name, fact_type)

**Chunk Schema:**
```json
{
  "chunk_id": "src_001_chunk_003",
  "text": "The exit load for Mirae Asset Large Cap Fund is 1%...",
  "source_id": "src_001",
  "source_url": "https://...",
  "scheme_name": "Mirae Asset Large Cap Fund",
  "fact_type": "exit_load",
  "token_count": 387,
  "fetched_at": "2026-04-09"
}
```

### 2.2 Embedding Generation

**Model:** OpenAI `text-embedding-3-small` (1536 dimensions, cosine similarity)

**API key loaded from `.env`:**
```
OPENAI_API_KEY=sk-...
```

**Batch embedding script (`scripts/phase2/embed_corpus.py`):**
```
chunks[]
    │
    ▼ (batch of 100)
OpenAI Embeddings API  ← OPENAI_API_KEY from .env
  model: text-embedding-3-small
    │
    ▼
supabase.table('mutual_fund_chunks').upsert(
  { chunk_id, text, embedding, source_url, source_type, scheme_name, ... },
  on_conflict='chunk_id'
)
```

- `OPENAI_API_KEY` read from `.env` at startup (no shell export needed)
- `SUPABASE_URL` + `SUPABASE_SERVICE_ROLE_KEY` read from `.env` for DB writes
- Process in batches of 100 to stay within API rate limits
- Log embedding cost per run (~$0.02 / 1M tokens)
- Skip already-embedded chunks (upsert on `chunk_id` conflict)

### 2.3 Vector Store

**Both dev and prod:** Supabase pgvector (single setup, no environment switch needed)

**Why Supabase pgvector:**
- Free tier generous enough for this corpus (7,297 vectors × 1536 dims ≈ 45 MB)
- No separate vector DB service to manage — same Postgres used for everything
- Native cosine similarity via `<=>` operator
- Vercel-compatible via HTTPS REST API (`@supabase/supabase-js`)

**Supabase schema (run once in SQL editor):**
```sql
-- Enable pgvector extension
create extension if not exists vector;

-- Chunks table
create table mutual_fund_chunks (
  id           bigserial primary key,
  chunk_id     text unique not null,
  text         text not null,
  embedding    vector(1536),
  source_id    text,
  source_url   text,
  source_type  text,     -- 'amfi' | 'amc' | 'sebi'
  scheme_name  text,
  fact_types   text,     -- comma-separated e.g. "exit_load, benchmark"
  fetched_at   text,
  token_count  integer
);

-- IVFFlat index for fast cosine search
create index on mutual_fund_chunks
  using ivfflat (embedding vector_cosine_ops)
  with (lists = 100);

-- RPC function used by the retriever
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
    chunk_id, text, source_url, source_type,
    scheme_name, fact_types, fetched_at,
    1 - (embedding <=> query_embedding) as similarity
  from mutual_fund_chunks
  where 1 - (embedding <=> query_embedding) > match_threshold
    and source_type = any(array['amfi', 'amc', 'sebi'])
  order by embedding <=> query_embedding
  limit match_count;
$$;
```

**Similarity metric:** Cosine via pgvector `<=>` operator (same as ChromaDB dev setup)

### 2.4 Index Validation

After indexing, run a smoke test:

```
Query: "expense ratio Mirae Large Cap"
Expected top result: chunk from src_001 with fact_type=expense_ratio
Pass criteria: cosine similarity > 0.60
Note: 0.60 is the validated floor for natural-language questions vs. structured
PDF/KIM chunks. Scores of 0.60–0.75 are semantically meaningful for this corpus.
```

Run 5–10 such smoke tests covering all fact types before moving to Phase 3.

---

## Phase 3 — Retrieval Pipeline & Guard Rails

### Goal
Given a user query, retrieve the most relevant approved chunks and block any advisory or PII-related questions before they reach the LLM.

### 3.1 Full Pipeline Flow

```
User Query (raw text)
    │
    ▼
[1. Input Sanitizer]          ← strip PII signals, length check
    │
    ▼
[2. Intent Classifier]        ← factual vs. advisory vs. out-of-scope
    │
    ├──[BLOCK]──► Refusal Response (no LLM call)
    │
    └──[PASS]──►
                │
                ▼
         [3. Query Rewriter]  ← normalize and expand query
                │
                ▼
         [4. Vector Retriever] ← top-K from vector store
                │
                ▼
         [5. Metadata Filter] ← ensure retrieved chunks are from approved sources
                │
                ▼
         [6. Context Assembler] ← build prompt context with source citations
                │
                ▼
              LLM (Phase 4)
```

### 3.2 Input Sanitizer

Runs before everything else. Fast, rule-based.

**Rules:**
- Max input length: 500 characters (reject longer)
- Detect and reject inputs containing: PAN patterns (`[A-Z]{5}[0-9]{4}[A-Z]`), phone numbers, email addresses, Aadhaar patterns
- Strip HTML/markdown from input
- Normalize whitespace

```typescript
function sanitizeInput(query: string): { clean: string; blocked: boolean; reason?: string } {
  if (query.length > 500) return { clean: '', blocked: true, reason: 'too_long' };
  if (/[A-Z]{5}[0-9]{4}[A-Z]/.test(query)) return { clean: '', blocked: true, reason: 'pii_pan' };
  if (/\b\d{10}\b/.test(query)) return { clean: '', blocked: true, reason: 'pii_phone' };
  // ...
  return { clean: query.trim(), blocked: false };
}
```

### 3.3 Intent Classifier

Two-layer classifier for reliability:

**Layer 1 — Rule-based (fast, no API call):**

Keyword blocklist triggers immediate refusal:
```
advisory_keywords = [
  "should i", "is it good", "recommend", "better fund",
  "which fund", "should i invest", "stop sip", "exit now",
  "compare", "returns comparison", "future returns", "will it grow"
]
```

**Layer 2 — LLM-based (for ambiguous cases):**

If Layer 1 passes, send a cheap classification call via OpenAI (`gpt-4o-mini`):
```
Prompt: Classify this question as FACTUAL or ADVISORY.
FACTUAL = asks for a specific fund fact (expense ratio, exit load, SIP amount, lock-in, etc.)
ADVISORY = asks for investment opinion, recommendation, or comparison.

Question: "{query}"
Answer with only: FACTUAL or ADVISORY
```

Uses `OPENAI_API_KEY` from `.env`. Model: `gpt-4o-mini` — fast and cheap for classification.

**Out-of-scope detection:**
- Questions about stocks, crypto, FDs, insurance → "Out of scope"
- Questions about specific portfolio → "Out of scope"

### 3.4 Query Rewriter

Normalize the query for better retrieval using OpenAI `gpt-4o-mini` (reads `OPENAI_API_KEY` from `.env`):

```
"whats the exit load" → "What is the exit load for [scheme]?"
"min sip amount"      → "What is the minimum SIP amount?"
"how risky is it"     → "What is the riskometer rating?"
```

Simple prompt:
```
Rewrite this mutual fund question into a clear factual query.
Keep it under 20 words. Preserve the user's intent exactly.
Query: "{clean_query}"
```

### 3.5 Vector Retriever

Query embedding also uses OpenAI `text-embedding-3-small` (same model as indexing — `OPENAI_API_KEY` from `.env`):

```typescript
async function retrieve(query: string, topK = 5) {
  // embed uses OPENAI_API_KEY from process.env (loaded from .env)
  const queryEmbedding = await embed(query);  // text-embedding-3-small

  // Calls match_chunks RPC — source_type filter + threshold applied in SQL
  const { data, error } = await supabase.rpc('match_chunks', {
    query_embedding: queryEmbedding,
    match_count: topK,
    match_threshold: 0.60,
  });

  if (error) throw error;
  return data;  // rows: { chunk_id, text, source_url, source_type, scheme_name, similarity, ... }
}
```

**Retrieval parameters:**
- `topK = 5` (retrieve 5, use top 3 in context)
- Minimum similarity score: `0.60` (validated floor for Q&A-to-PDF-chunk retrieval)
- Metadata filter: only `amfi`, `amc`, `sebi` source types

### 3.6 Context Assembler

Build the final context block for the LLM:

```
Retrieved Chunks (top 3):
---
[1] Source: https://amfiindia.com/...
    "The expense ratio of Mirae Asset Large Cap Fund (Direct Plan) is 0.54% per annum..."

[2] Source: https://miraeassetmf.co.in/...
    "Exit load: 1% if units are redeemed or switched out within 365 days from the date of allotment..."

[3] Source: https://sebi.gov.in/...
    "Total Expense Ratio (TER) is charged by the fund house to manage the scheme..."
---
Primary citation: [1] (highest similarity score)
```

The primary citation (highest scoring chunk's URL) is what gets shown to the user.

---

## Phase 4 — LLM Answer Generation

### Goal
Generate a ≤3 sentence, factual, citation-backed answer using only the retrieved context.

### 4.1 Prompt Architecture

**System Prompt (fixed, never changes):**
```
You are a facts-only mutual fund information assistant for Groww.

RULES (strictly enforced):
1. Answer ONLY using the provided context. Do not use any prior knowledge.
2. Keep answers to a maximum of 3 sentences.
3. Do NOT give investment advice, recommendations, or opinions.
4. Do NOT compare fund performance or predict returns.
5. If the context does not contain the answer, say: "I don't have verified information on this."
6. Always end with the source URL provided.
7. Do not mention any competitor or external product.
```

**User Prompt (assembled per request):**
```
Context:
{assembled_context}

Question: {rewritten_query}

Answer in this exact format:
[Direct factual answer in 1–3 sentences]
Source: {primary_citation_url}
Last updated: {fetched_at}
```

### 4.2 Model Configuration

Uses OpenAI `gpt-4o-mini` — loaded via `OPENAI_API_KEY` from `.env`:

```typescript
import OpenAI from 'openai';

const openai = new OpenAI({ apiKey: process.env.OPENAI_API_KEY });

const response = await openai.chat.completions.create({
  model: 'gpt-4o-mini',      // fast + cheap for factual Q&A
  max_tokens: 256,
  temperature: 0.1,           // low = more deterministic
  messages: [
    { role: 'system', content: SYSTEM_PROMPT },
    { role: 'user',   content: userPrompt }
  ]
});
```

**Why `gpt-4o-mini`:** Factual retrieval tasks don't need frontier-model reasoning. `gpt-4o-mini` is significantly cheaper and faster with equivalent accuracy for structured Q&A.

**Fallback:** If answer contains hedging language, retry with `gpt-4o` (full model) for higher accuracy.

### 4.3 Output Validation

After LLM responds, run post-processing:

```typescript
function validateAnswer(raw: string, citationUrl: string): ValidatedAnswer {
  // 1. Check citation is present and matches approved source list
  if (!raw.includes(citationUrl)) throw new Error('citation_missing');

  // 2. Check for advisory language (second safety net)
  const advisorySignals = ['recommend', 'should invest', 'suggest', 'opinion'];
  if (advisorySignals.some(s => raw.toLowerCase().includes(s))) {
    return { type: 'refusal', text: ADVISORY_REFUSAL_MESSAGE };
  }

  // 3. Enforce 3-sentence max
  const sentences = raw.split(/[.!?]+/).filter(Boolean);
  if (sentences.length > 5) {
    return { type: 'truncated', text: sentences.slice(0, 3).join('. ') + '.' };
  }

  return { type: 'answer', text: raw, source: citationUrl };
}
```

### 4.4 Refusal Messages

```typescript
const REFUSAL_MESSAGES = {
  advisory:    "I can only share factual information about mutual funds. For investment advice, please consult a SEBI-registered financial advisor.",
  out_of_scope: "This question is outside the scope of mutual fund facts. I can help with expense ratios, exit loads, SIP amounts, lock-in periods, and similar factual queries.",
  no_context:  "I don't have verified information on this from official sources.",
  pii:         "Please do not share personal information like PAN, phone number, or account details."
};
```

---

## Phase 5 — Backend API

### Goal
Expose the full pipeline as a clean, stateless API with rate limiting, logging, and streaming support.

### 5.1 API Routes (Next.js App Router)

```
app/
└── api/
    ├── ask/
    │   └── route.ts        POST /api/ask
    ├── sources/
    │   └── route.ts        GET  /api/sources
    └── health/
        └── route.ts        GET  /api/health
```

### 5.2 POST /api/ask

**Request:**
```json
{ "question": "What is the exit load of Mirae Asset Large Cap Fund?" }
```

**Response (success):**
```json
{
  "type": "answer",
  "answer": "The exit load for Mirae Asset Large Cap Fund is 1% if units are redeemed within 365 days of allotment. After 365 days, there is no exit load.",
  "source_url": "https://miraeassetmf.co.in/...",
  "last_updated": "2026-04-09",
  "scheme": "Mirae Asset Large Cap Fund"
}
```

**Response (refusal):**
```json
{
  "type": "refusal",
  "reason": "advisory",
  "message": "I can only share factual information about mutual funds..."
}
```

**Route handler flow:**
```typescript
export async function POST(req: Request) {
  const { question } = await req.json();

  // 1. Sanitize
  const sanitized = sanitizeInput(question);
  if (sanitized.blocked) return refusalResponse(sanitized.reason);

  // 2. Classify intent
  const intent = await classifyIntent(sanitized.clean);
  if (intent !== 'FACTUAL') return refusalResponse('advisory');

  // 3. Rewrite query
  const rewritten = await rewriteQuery(sanitized.clean);

  // 4. Retrieve
  const chunks = await retrieve(rewritten);
  if (chunks.length === 0) return noContextResponse();

  // 5. Generate
  const answer = await generateAnswer(rewritten, chunks);

  // 6. Validate + return
  const validated = validateAnswer(answer, chunks[0].metadata.source_url);
  return Response.json(validated);
}
```

### 5.3 GET /api/sources

Returns the full list of URLs in the corpus — satisfies the deliverable requirement.

```json
{
  "total": 18,
  "last_updated": "2026-04-09",
  "sources": [
    {
      "id": "src_001",
      "url": "https://...",
      "type": "amfi",
      "scheme": "Mirae Asset Large Cap Fund",
      "description": "Scheme information document"
    }
  ]
}
```

### 5.4 Rate Limiting

Use Vercel's built-in rate limiting via `@vercel/kv` or a simple in-memory counter:

```typescript
const RATE_LIMIT = 20; // requests per IP per hour
```

For production, use Vercel Firewall rules (no code required).

### 5.5 Logging (No PII)

Log for observability — never log raw user queries (potential PII):

```typescript
console.log(JSON.stringify({
  event: 'ask',
  intent: 'FACTUAL',
  retrieved_chunks: 3,
  top_score: 0.89,
  scheme_matched: 'Mirae Asset Large Cap Fund',
  latency_ms: 420,
  timestamp: new Date().toISOString()
  // ⚠️ NO question text, NO IP, NO user data
}));
```

---

## Phase 6 — Frontend UI

### Goal
A clean, minimal chat interface with persistent disclaimer, citation display, and source transparency.

### 6.1 Page Structure

```
app/
├── page.tsx              ← Main chat UI
├── sources/
│   └── page.tsx          ← /sources — all corpus URLs
└── layout.tsx            ← Disclaimer banner (persistent)
```

### 6.2 Component Tree

```
<Layout>
  ├── <DisclaimerBanner />          ← sticky top/bottom bar
  └── <main>
        ├── <Header />              ← "Mutual Fund FAQ — Groww"
        ├── <ChatWindow>
        │     ├── <MessageList>
        │     │     ├── <UserMessage />
        │     │     └── <AnswerCard>
        │     │           ├── answer text
        │     │           ├── <SourceLink />  ← clickable official URL
        │     │           └── "Last updated: ..."
        │     └── <RefusalCard />   ← shown for blocked questions
        └── <QuestionInput />       ← text field + submit button
```

### 6.3 Key Components

**`<AnswerCard />`**
```tsx
export function AnswerCard({ answer, sourceUrl, lastUpdated }: AnswerCardProps) {
  return (
    <div className="rounded-lg border p-4 bg-white shadow-sm">
      <p className="text-sm text-gray-800">{answer}</p>
      <div className="mt-3 flex items-center gap-2 text-xs text-blue-600">
        <ExternalLinkIcon className="h-3 w-3" />
        <a href={sourceUrl} target="_blank" rel="noopener noreferrer">
          Official Source
        </a>
        <span className="text-gray-400">· Last updated: {lastUpdated}</span>
      </div>
    </div>
  );
}
```

**`<DisclaimerBanner />`** (always visible):
```tsx
export function DisclaimerBanner() {
  return (
    <div className="bg-amber-50 border-b border-amber-200 px-4 py-2 text-xs text-amber-800 text-center">
      This tool provides factual information only and is <strong>not investment advice</strong>.
      Consult a SEBI-registered financial advisor before investing.
      Data sourced from official AMC, AMFI, and SEBI documents.
    </div>
  );
}
```

**`<RefusalCard />`:**
```tsx
export function RefusalCard({ reason }: { reason: string }) {
  return (
    <div className="rounded-lg border border-orange-200 bg-orange-50 p-4 text-sm text-orange-700">
      <strong>Out of scope:</strong> {REFUSAL_MESSAGES[reason]}
    </div>
  );
}
```

### 6.4 Sample Questions (shown in UI)

Display 4–5 clickable sample questions on first load:
```
• What is the expense ratio of Mirae Asset Large Cap Fund?
• What is the exit load for Mirae Asset ELSS?
• What is the minimum SIP amount?
• How do I download my capital gains statement?
• What is the lock-in period for ELSS funds?
```

### 6.5 `/sources` Page

Lists all corpus URLs in a table:

| # | Source | Type | Scheme | URL |
|---|---|---|---|---|
| 1 | AMFI | amfi | Mirae Large Cap | [link] |
| 2 | AMC | amc | Mirae ELSS | [link] |

---

## Phase 7 — Testing, Deployment & Deliverables

### 7.1 Testing Checklist

**Unit tests:**
- [ ] `sanitizeInput()` blocks PAN / phone / email patterns
- [ ] `classifyIntent()` correctly flags advisory questions
- [ ] `validateAnswer()` rejects answers missing citation

**Integration tests (sample_qa.md coverage):**
- [ ] 5 factual questions → correct answers with citations
- [ ] 5 advisory questions → all blocked, no LLM call made
- [ ] 2 PII inputs → blocked at sanitizer, not logged
- [ ] 1 out-of-corpus question → "no verified information" response

**Retrieval quality:**
- [ ] Smoke test: top result similarity > 0.60 for all fact types (validated floor for this corpus)
- [ ] No chunk from non-approved source ever appears in results

### 7.2 Deployment (Vercel)

**Environment variables:**
```
OPENAI_API_KEY=...                    # embeddings (text-embedding-3-small) + LLM (gpt-4o-mini / gpt-4o)
SUPABASE_URL=https://xxxx.supabase.co # pgvector host (same for dev and prod)
SUPABASE_SERVICE_ROLE_KEY=...         # service role key for server-side writes and RPC calls
```

> **Note:** `OPENAI_API_KEY` is the primary AI credential. It is used in Phase 2 (embedding), Phase 3 (classifier + rewriter + retriever), and Phase 4 (answer generation). `SUPABASE_URL` and `SUPABASE_SERVICE_ROLE_KEY` are used in Phase 2 (upsert chunks), Phase 3/5 (retrieval via `match_chunks` RPC), and set via `vercel env add` for deployment. All scripts load these from `.env` at startup.

**`vercel.json` (or `vercel.ts`):**
```json
{
  "functions": {
    "app/api/ask/route.ts": {
      "maxDuration": 30
    }
  }
}
```

**Deploy commands:**
```bash
vercel env pull .env.local        # sync env vars
vercel --prod                     # deploy to production
```

### 7.3 Deliverables Checklist

```
✅ Working prototype (Vercel URL)
✅ data/sources.json             ← all 15–25 URLs with fetch dates
✅ data/scheme_facts.json        ← structured facts per scheme
✅ README.md                     ← setup, scope, known limitations
✅ sample_qa.md                  ← 10 Q&A pairs (5 factual, 5 refused)
✅ Disclaimer banner in UI
✅ /sources page listing all corpus URLs
```

---

## Architecture Summary Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                        FRONTEND (Next.js)                    │
│  DisclaimerBanner · ChatWindow · AnswerCard · SourcesPage   │
└───────────────────────────┬─────────────────────────────────┘
                            │ POST /api/ask
┌───────────────────────────▼─────────────────────────────────┐
│                     BACKEND API (Next.js)                    │
│                                                              │
│  Sanitizer → Intent Classifier → Query Rewriter              │
│       │              │                  │                    │
│    [BLOCK]        [BLOCK]          Retriever                 │
│       │              │          (Vector Store)               │
│  Refusal Resp   Refusal Resp          │                      │
│                                Context Assembler             │
│                                       │                      │
│                              LLM (OpenAI gpt-4o-mini)        │
│                                       │                      │
│                               Output Validator               │
│                                       │                      │
│                               JSON Response                  │
└───────────────────────────────────────┬─────────────────────┘
                                        │
              ┌─────────────────────────┼──────────────────────┐
              │                         │                       │
┌─────────────▼──────┐   ┌─────────────▼──────┐  ┌────────────▼──────┐
│   Vector Store     │   │  Scheme Facts JSON  │  │  Sources Registry │
│ (Supabase pgvector)│   │  (structured data)  │  │  (sources.json)   │
│                    │   │                     │  │                   │
│ Chunks + Embeddings│   │ expense_ratio, etc. │  │ 15–25 official    │
│ from 15–25 sources │   │ per scheme          │  │ URLs + metadata   │
└────────────────────┘   └─────────────────────┘  └───────────────────┘
```

---

## Technology Stack Summary

| Layer | Technology | Reason |
|---|---|---|
| Frontend | Next.js 15 App Router + Tailwind + shadcn/ui | Fast, Vercel-native |
| Backend API | Next.js API Routes (Fluid Compute) | Co-located with frontend |
| Embeddings | OpenAI `text-embedding-3-small` (1536 dims) | Best cost/quality ratio; ~$0.02/1M tokens |
| LLM (classifier + rewriter) | OpenAI `gpt-4o-mini` | Fast + cheap for classification/rewriting |
| LLM (generation) | OpenAI `gpt-4o-mini` | Factual tasks; deterministic at temp=0.1 |
| LLM (fallback) | OpenAI `gpt-4o` | For low-confidence or hedging answers |
| Vector Store | Supabase pgvector | Single setup for dev + prod; free tier fits corpus; cosine via `<=>` |
| DB Client | `@supabase/supabase-js` | HTTPS REST + RPC, Vercel-compatible |
| API Credential | `OPENAI_API_KEY` in `.env` | Single key for all phases — embeddings + LLM |
| DB Credentials | `SUPABASE_URL` + `SUPABASE_SERVICE_ROLE_KEY` | Loaded from `.env`; set via `vercel env add` |
| Deployment | Vercel | Native Next.js support |
| Corpus Scripts | Python (`requests`, `pdfplumber`, `beautifulsoup4`) | Best PDF/HTML parsing libs |

## Environment File (`.env`)

A single `.env` file at project root is loaded by all scripts and the Next.js app:

```
# .env — required for Phase 2, 3, 4, 5
OPENAI_API_KEY=sk-...

# Required for vector store — same values for dev and prod
SUPABASE_URL=https://xxxx.supabase.co
SUPABASE_SERVICE_ROLE_KEY=eyJ...
```

**Per-phase usage:**

| Phase | Uses `OPENAI_API_KEY` for |
|---|---|
| Phase 1 | Not used (corpus collection is API-free) |
| Phase 2 | `text-embedding-3-small` — embed all 7,297 chunks; upsert into Supabase pgvector |
| Phase 3 | `text-embedding-3-small` — embed query; `gpt-4o-mini` — classify + rewrite |
| Phase 4 | `gpt-4o-mini` — generate factual answer; `gpt-4o` fallback |
| Phase 5 | Via Next.js `process.env.OPENAI_API_KEY` (loaded from `.env.local`) |
| Phase 6 | Not used directly (frontend calls backend API) |
| Phase 7 | Set via `vercel env add OPENAI_API_KEY` for deployment |

> **Security:** `.env` is in `.gitignore` and never committed. Use `.env.example` (committed) to document required keys without values.
