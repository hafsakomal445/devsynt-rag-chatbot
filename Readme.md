# Meridian Homes Realty — AI-Powered Document RAG Chatbot Dashboard

An AI-powered document question-answering system built for DevSynt's AI Internship Program (Task 5). Users upload documents (PDF/DOCX/TXT), the system extracts, chunks, and embeds their content into a searchable vector store, and a chatbot answers questions using only information retrieved from those documents — with source citations and a built-in hallucination guardrail.

Test dataset: 5 sample PDFs for a fictional real estate company, **Meridian Homes Realty** (Company Overview, Property Listings, Services & Fees, FAQs, Policies & Terms), generated for internal consistency so cross-document questions and hallucination tests are meaningful.



---

## Features

- **Document upload & management** — upload PDF/DOCX/TXT, view processing status, view document info, delete, and re-process
- **Automatic text extraction, chunking, and embedding** — per-page extraction, recursive chunking with overlap, Gemini embeddings stored in a FAISS vector index
- **Semantic search chatbot** — ask natural-language questions, get grounded answers with source citations (document name + page number)
- **Hallucination guardrails** — a distance-based relevance filter plus an explicit system-prompt instruction ensure the chatbot says "I couldn't find that information" instead of fabricating an answer when the knowledge base doesn't contain it
- **Live dashboard stats** — total documents, processed/processing/failed counts, indexed chunks, and total chats, all sourced from the backend in real time
- **New chat / chat history** within a session, with a collapsible sources panel per answer

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend API | Python + FastAPI |
| Vector database | FAISS (`IndexFlatL2`) |
| Embeddings | Google Gemini (`gemini-embedding-001`) |
| LLM (answer generation) | Google Gemini (`gemini-3.6-flash`) |
| Document parsing | `pypdf`, `python-docx` |
| Chunking | LangChain `RecursiveCharacterTextSplitter` |
| Frontend | Streamlit |
| Persistence | Local disk (FAISS index file, JSON metadata/registry files) |

---

## Project Structure

```
devsynt-rag-chatbot/
├── backend/
│   ├── main.py            # FastAPI app: upload, list, delete, reprocess, chat, stats endpoints
│   ├── ingestion.py        # Text extraction from PDF/DOCX/TXT (per-page)
│   ├── chunking.py         # Splits page text into chunks with metadata
│   ├── vectorstore.py       # FAISS index wrapper: add, search, remove-by-doc
│   ├── rag.py              # Retrieval + prompt building + Gemini call + guardrails
│   ├── document_store.py    # Document registry (status/metadata) + chat counter
│   └── requirements.txt
├── frontend/
│   └── app.py              # Streamlit dashboard: Home, Documents, Chatbot pages
├── data/
│   ├── sample_pdfs/         # 5 generated test PDFs (Meridian Homes Realty)
│   ├── uploads/             # Runtime-uploaded documents (gitignored)
│   ├── faiss_index.bin       # Persisted vector index (gitignored)
│   ├── chunk_metadata.pkl     # Persisted chunk metadata (gitignored)
│   ├── documents.json        # Document registry (gitignored)
│   └── chat_stats.json       # Chat counter (gitignored)
├── TEST_REPORT.md           # 10-question test report with results and known limitations
├── .env                    # API key (not committed)
├── .gitignore
└── README.md
```

---

## Setup & Installation

### Prerequisites
- Python 3.10+
- A free Gemini API key from [aistudio.google.com/apikey](https://aistudio.google.com/apikey)

### 1. Clone the repository
```bash
git clone https://github.com/yourusername/devsynt-rag-chatbot.git
cd devsynt-rag-chatbot
```

### 2. Create and activate a virtual environment
```bash
python -m venv venv
# Windows
venv\Scripts\activate
# Mac/Linux
source venv/bin/activate
```

### 3. Install dependencies
```bash
pip install fastapi uvicorn python-multipart
pip install langchain langchain-community langchain-google-genai langchain-text-splitters
pip install faiss-cpu
pip install pypdf python-docx
pip install streamlit requests
pip install python-dotenv
```

### 4. Configure environment variables
Create a `.env` file in the project root:
```
GOOGLE_API_KEY=your_gemini_api_key_here
```

---

## Running the App

You need **two terminals** running simultaneously (both with the venv activated).

**Terminal 1 — Backend:**
```bash
cd backend
uvicorn main:app --reload --port 8000
```
API docs available at `http://127.0.0.1:8000/docs`

**Terminal 2 — Frontend:**
```bash
cd frontend
streamlit run app.py
```
Dashboard opens at `http://localhost:8501`

### First-time use
1. Go to the **Documents** page and upload the 5 sample PDFs from `data/sample_pdfs/`
2. Wait for each to show "processed" status
3. Go to the **Chatbot** page and start asking questions
4. Check the **Home** page for live stats

---

## RAG Architecture

```
DOCUMENT SIDE                          QUESTION SIDE
─────────────                          ─────────────
Upload PDF/DOCX/TXT                    User Question
        │                                     │
        ▼                                     ▼
Text Extraction (per page)             Semantic Search (FAISS)
        │                                     │
        ▼                                     ▼
Chunking (RecursiveCharacterTextSplitter,   Relevance filter
 chunk_size=500, overlap=80)            (distance < 1.35, top_k=6)
        │                                     │
        ▼                                     ▼
Embeddings (Gemini gemini-embedding-001)   Relevant chunks + question
        │                                     │  → prompt → LLM
        ▼                                     ▼
FAISS Vector Store (IndexFlatL2)        Grounded Answer + Sources
 + metadata (doc name, doc ID,               │
   page, chunk ID)                            ▼
                                        Chatbot Dashboard
```

### Hallucination guardrails (two layers)
1. **Retrieval-level filter:** chunks with a FAISS L2 distance above `1.35` are discarded before ever reaching the LLM. If no chunks pass this filter, the system returns "I couldn't find that information" without calling the LLM at all.
2. **Prompt-level instruction:** the system prompt explicitly instructs Gemini to answer only from the provided excerpts and to say "I couldn't find that information in the uploaded documents" if the excerpts don't contain the answer, with `temperature=0` to reduce creative/fabricated responses.

---

## API Reference

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/documents/upload` | Upload a PDF/DOCX/TXT file; extracts, chunks, embeds, and indexes it |
| `GET` | `/documents` | List all documents with status and chunk counts |
| `GET` | `/documents/{doc_id}` | Get a single document's details |
| `DELETE` | `/documents/{doc_id}` | Remove a document and its chunks from the vector store |
| `POST` | `/documents/{doc_id}/reprocess` | Re-run extraction/chunking/embedding for an existing document |
| `POST` | `/chat` | Ask a question; returns `{answer, sources[]}` |
| `GET` | `/stats` | Dashboard stats: document counts by status, indexed chunks, total chats |

---

## Testing

See [`TEST_REPORT.md`](./TEST_REPORT.md) for the full 10-question test suite covering direct-answer, cross-document, multi-document, no-answer-in-KB, and hallucination-trigger questions, along with retrieval tuning notes.

**Summary:** 9/10 test questions behaved correctly. No hallucinations were observed in any test — every failure case was an over-cautious refusal rather than a fabricated answer.

---

## Known Limitations

- **Multi-topic compound questions** occasionally fail to retrieve chunks for both topics when one document (e.g., Property Listings, with 5 similar entries) has many semantically similar chunks that crowd out a chunk from a different topic/document. The system correctly declines to answer rather than guessing in this case, preserving the hallucination guardrail at the cost of completeness. See `TEST_REPORT.md` for details and possible future fixes (query decomposition, re-ranking).
- **DOCX and TXT files** don't have native page boundaries, so all their content is attributed to "page 1" in source citations. PDF page numbers are accurate.
- **Chat history is session-only** (Streamlit `session_state`), not persisted server-side — a new chat is lost if the browser tab is closed.
- **LLM latency:** Gemini API calls occasionally take 60+ seconds; the frontend timeout is set to 90 seconds to accommodate this.
- **FAISS `IndexFlatL2`** rebuilds the entire index on document deletion (no native delete support). Fine at this project's scale (a handful of documents); would need a different index type for large-scale production use.
- Model names for Gemini (embeddings and chat) are subject to deprecation over time; if you hit a `404 NOT_FOUND` error, check [ai.google.dev/gemini-api/docs/models](https://ai.google.dev/gemini-api/docs/models) for current model names and update `EMBEDDING_MODEL` in `vectorstore.py` or `CHAT_MODEL` in `rag.py` accordingly.

---

## Author

Built by Hafsa Komal for DevSynt's AI Internship Program — Task 5.