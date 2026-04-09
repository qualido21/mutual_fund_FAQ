# Problem Statement: Facts-Only Mutual Fund FAQ Assistant (Groww Use Case)

Build a **facts-only mutual fund FAQ assistant** for **Groww** that answers user questions using only **official AMC, AMFI, and SEBI sources**.

## Objective

Design and implement an application that:

- Answers factual mutual fund questions such as:
  - expense ratio
  - exit load
  - minimum SIP
  - lock-in period
  - riskometer
  - benchmark
  - statement / capital-gains statement download process
- Uses a small verified corpus of official public documents
- Uses an LLM + RAG setup to generate concise, citation-backed responses
- Refuses advisory, opinion-based, and portfolio-related questions
- Shows one source link in every answer

## System Workflow

### 1. Data Ingestion
- Select **1 AMC** and **3–5 schemes**
- Collect **15–25 official public pages** from AMC, AMFI, and SEBI
- Extract key facts like scheme name, category, expense ratio, exit load, SIP amount, lock-in, benchmark, and riskometer

### 2. User Input
Accept natural-language factual questions, such as:
- “What is the exit load of this fund?”
- “What is the minimum SIP?”
- “How do I download my capital gains statement?”

Do **not** collect or store PAN, Aadhaar, folio number, OTP, email, or phone number.

### 3. Retrieval + LLM Layer
- Retrieve relevant content only from the approved corpus
- Pass the retrieved context into the LLM
- Generate a short factual answer with exactly **one citation link**
- Refuse advice questions like:
  - “Should I invest?”
  - “Which fund is better?”
  - “Should I stop my SIP?”

### 4. Output
Display answers in a simple format:
- Direct answer
- One official source link
- “Last updated from sources:”

## Constraints
- Public official sources only
- No third-party blogs
- No investment advice
- No performance comparisons or return calculations
- Keep answers within **3 sentences**

## Deliverables
- Working prototype
- Source list of URLs used
- README with setup and scope
- Sample Q&A file
- Disclaimer snippet for the UI