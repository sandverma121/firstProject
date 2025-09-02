# Backend (FastAPI)

## Setup

1. Create virtual environment (optional but recommended)
```bash
python -m venv .venv
. .venv/Scripts/activate
```

2. Install dependencies
```bash
pip install -r requirements.txt
```

3. Set environment variables
- `OPENAI_API_KEY`: your OpenAI API key
- Optional: `OPENAI_MODEL` (default: `gpt-4o-mini`)
- Optional: `ALLOWED_ORIGINS` (comma-separated, default includes Vite dev server)

On PowerShell:
```powershell
$Env:OPENAI_API_KEY="sk-..."
$Env:OPENAI_MODEL="gpt-4o-mini"
```

4. Run the server
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## Endpoints
- `GET /health` – health check
- `POST /upload-pdf` – multipart file upload; extracts text and parses questions
- `POST /process` – accepts parsed questions and uses OpenAI to rewrite & reason; saves `storage/output.json`

## Notes
- Uses `pdfplumber` when available, falls back to `PyPDF2`.
- Parsing heuristics handle common MCQ formats; adjust `parser.py` for your PDFs.

