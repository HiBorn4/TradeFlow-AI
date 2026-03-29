# 🎤 Presentation Flow - TradeFlow AI

A guide for showcasing this project in portfolio reviews, interviews, or demo calls.

---

## 1-Minute Pitch

> "TradeFlow AI is an agentic pipeline that takes a messy multi-page logistics PDF - the kind that might have 18 pages with Tax Invoices, Bills of Lading, Packing Lists, and Import Declarations all jumbled together - and outputs perfectly structured, ERP-ready JSON, automatically. It uses Google's Agent Development Kit to orchestrate a multi-step workflow exposed over Model Context Protocol, with GPT-4.1 Vision doing the heavy lifting on document understanding."

---

## Demo Flow (10 minutes)

### 1. Problem Statement (1 min)
- Open with a real logistics PDF - show a messy 18-page document
- "Manual data entry for a document like this takes 30–45 minutes per shipment"
- "Logistics teams process dozens of these weekly"

### 2. Architecture Overview (2 min)
- Show the `assets/architecture.svg` diagram
- Walk through: Frontend → FastAPI → ADK Agent → MCP → Pipeline
- Highlight: "The agent doesn't know the implementation details - it just calls tools over MCP"

### 3. Live Demo (5 min)
- Open `http://localhost:8501`
- Point out: clean dark UI, backend connected, MCP tools listed in sidebar
- Upload `InfrabuildTest invoice-3.pdf`
- Click "🚀 Process Document"
- While processing: explain what's happening at each step
  - "Right now, each page is being converted to PNG and sent through Tesseract OCR..."
  - "Then GPT-4.1 classifies the document type based on the extracted text..."
- Show final output - structured JSON with proper field names

### 4. Tech Deep Dive (1 min)
- "The interesting architectural choice here is MCP"
- "The ADK agent is completely decoupled from the implementation - it just sees tool names"
- "This makes it easy to swap out the LLM, add new tools, or replace the backend"

### 5. Results & Metrics (1 min)
- 100% classification accuracy on the test document (18/18 pages)
- Parallel extraction: 5 document classes processed simultaneously
- Full pipeline: ~4–5 minutes for an 18-page document

---

## Key Technical Talking Points

**Why Google ADK?**
> "ADK handles session management, agent orchestration, and async event streaming out of the box. It gives you a proper agentic loop without the boilerplate."

**Why MCP?**
> "MCP gives the agent a standardized interface to tools - the agent doesn't care if tools run locally, in Docker, or remotely. It's the 'USB-C for AI tools' concept."

**Why parallel extraction?**
> "Document classes are independent - there's no reason to wait for Packing List extraction to finish before starting Commercial Invoice. ThreadPoolExecutor gives us a 5x speedup on extraction."

**ERPNext schemas?**
> "The end goal is ERP integration. By mapping directly to Frappe/ERPNext DocType schemas, extracted data can be pushed directly to the ERP without any transformation layer."

---

## Questions You Might Get

**"How accurate is the extraction?"**
> "For well-formatted digital PDFs, very high. Scanned/poor-quality PDFs need better pre-processing. We have ground-truth JSON in `accurate_data/` for comparison."

**"Can it handle different document formats?"**
> "Yes - the classification prompt is flexible. New document types can be added by updating the CLASSES list and adding a corresponding extraction prompt."

**"What happens if classification is wrong?"**
> "Each misclassified page ends up in the wrong folder, which means extraction quality degrades. Future work: confidence scores + human-in-the-loop review for low-confidence pages."

**"Could this work with Claude instead of GPT-4.1?"**
> "Absolutely - LiteLLM makes swapping trivial. The same pipeline works with any vision-capable model."
