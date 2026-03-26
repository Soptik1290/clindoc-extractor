# ClinDoc Extractor

Production-ready Python service for **structured extraction of clinical entities** from medical dictations.
Hybrid approach: **LLM (gpt-5.4-nano)** as primary extractor + **Regex fallback** with automatic merge and cross-verification.

## ✨ Features

- 🏥 **Clinical Entity Extraction** — Patient info, vitals, diagnoses (ICD-10), medications, dates, follow-up instructions
- 🤖 **Hybrid LLM + Regex Pipeline** — GPT-5.4-nano with Structured Outputs as primary, deterministic regex as fallback and cross-verifier
- 🔀 **Smart Merge** — LLM results have priority, regex supplements missing fields and validates critical data (ICD codes, dates)
- 🌍 **Bilingual Support** — Czech + English medical texts, auto-detection via `langdetect`
- 🔥 **FHIR R4 Bundle** — Maps extraction output to HL7 FHIR R4 (Patient, Condition, MedicationRequest)
- 📊 **Confidence Scoring** — Per-field and overall confidence (0.0–1.0) with weighted scoring and penalties
- ⚡ **Async Queue** — Redis-backed job queue (`/submit` → `/result/{job_id}`) for background processing
- 🗄️ **Redis Cache** — Identical texts cached for 24h to avoid redundant LLM calls
- 🧪 **32 Tests** — Full test coverage (extraction, API, regex, FHIR) with mocked OpenAI
- 🐳 **Docker Ready** — `docker compose up` spins up API + Redis in one command

## 🚀 Quick Start

### Docker (Recommended)

```bash
cp .env.example .env
# Edit .env — add your OpenAI API key

docker compose up --build
```

### Local

```bash
pip install -e ".[dev]"
uvicorn app.main:app --reload
```

API available at **http://localhost:8000** · Swagger docs at **http://localhost:8000/docs**

## 📡 API Endpoints

| Endpoint | Method | Description |
|---|---|---|
| `/extract` | POST | Synchronous clinical data extraction |
| `/extract/fhir` | POST | Extraction → FHIR R4 Bundle |
| `/submit` | POST | Async extraction via Redis queue |
| `/result/{job_id}` | GET | Poll async job result |
| `/health` | GET | Health check |
| `/docs` | GET | Swagger UI (auto) |

### Example

```bash
curl -X POST http://localhost:8000/extract \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Pacient Jan Novak, datum narozeni 15.3.1968, Diagnoza: I63.9",
    "language": "auto"
  }'
```

### Response

```json
{
  "patient": { "name": "Jan Novak", "birth_date": "1968-03-15" },
  "vitals": { "bp": "178/95", "spo2": "97%" },
  "diagnoses": [{ "code": "I63.9", "system": "ICD-10", "confidence": 0.95 }],
  "medications": [{ "name": "aspirin", "dose": "100mg", "frequency": "1x denne" }],
  "dates": { "admission": "2024-11-12" },
  "follow_up": "kontrola u neurologa za 6 tydnu",
  "confidence": 0.87,
  "extraction_method": "llm",
  "warnings": []
}
```

## 🏗️ Tech Stack

| Component | Technology |
|---|---|
| Language | Python 3.11+ |
| Framework | FastAPI + Uvicorn |
| LLM | OpenAI GPT-5.4-nano (Structured Outputs) |
| Queue | Redis (async job processing + caching) |
| Models | Pydantic v2 |
| Config | pydantic-settings + `.env` |
| NLP | langdetect (auto language detection) |
| Testing | pytest + respx (mocked OpenAI) |
| Container | Docker Compose (API + Redis) |

## 📁 Project Structure

```
clindoc-extractor/
├── app/
│   ├── main.py                  # FastAPI app + testing UI
│   ├── api/routes.py            # API endpoints
│   ├── core/
│   │   ├── config.py            # Settings (pydantic-settings)
│   │   └── exceptions.py        # Custom exceptions
│   ├── extraction/
│   │   ├── base.py              # Abstract BaseExtractor
│   │   ├── llm_extractor.py     # GPT-5.4-nano extraction
│   │   ├── regex_extractor.py   # Regex fallback with confidence
│   │   └── pipeline.py          # Hybrid orchestration + merge
│   ├── models/
│   │   ├── request.py           # Pydantic request models
│   │   ├── response.py          # Pydantic response models
│   │   └── fhir.py              # FHIR R4 Bundle models
│   ├── services/
│   │   ├── extractor_service.py # Business logic layer
│   │   ├── fhir_service.py      # FHIR R4 mapping
│   │   └── queue_service.py     # Redis async queue
│   └── utils/
│       ├── date_parser.py       # ISO 8601 normalization
│       └── language_detector.py # Auto language detection
├── tests/                       # 32 tests (extraction, API, FHIR, regex)
├── Dockerfile
├── docker-compose.yml
├── pyproject.toml
└── ARCHITECTURE.md              # Detailed technical notes
```

## 🧪 Tests

```bash
pytest tests/ -v --cov=app
```

**32 tests** covering: regex extraction (Diktát A + B), API endpoints (health, extract, edge cases), FHIR mapping, and confidence scoring.

## 📝 Architecture & Technical Details

See [ARCHITECTURE.md](ARCHITECTURE.md) for detailed notes on:
- Why LLM + Regex hybrid approach
- Pipeline merge logic
- Confidence scoring algorithm
- Known limitations
- Production improvement ideas

## License

MIT
