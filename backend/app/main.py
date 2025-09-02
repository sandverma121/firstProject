from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import os
import io
import json
from typing import List, Optional

from .services.pdf_service import extract_text_from_pdf
from .services.parser import parse_questions_from_text
from .services.openai_service import rewrite_questions_with_reasoning


class ProcessResponse(BaseModel):
    questions: List[dict]
    json_path: Optional[str]


app = FastAPI(title="Quiz PDF Processor", version="1.0.0")


ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/upload-pdf", response_model=ProcessResponse)
async def upload_pdf(file: UploadFile = File(...)):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")

    try:
        file_bytes = await file.read()
        text = extract_text_from_pdf(io.BytesIO(file_bytes))
        if not text or text.strip() == "":
            raise HTTPException(status_code=422, detail="No extractable text found in PDF")

        parsed = parse_questions_from_text(text)
        return ProcessResponse(questions=parsed, json_path=None)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to process PDF: {exc}")


class ProcessBody(BaseModel):
    questions: List[dict]
    model: Optional[str] = None


@app.post("/process", response_model=ProcessResponse)
async def process_questions(body: ProcessBody):
    if not body.questions:
        raise HTTPException(status_code=400, detail="No questions provided")

    try:
        rewritten = rewrite_questions_with_reasoning(body.questions, model_override=body.model)

        os.makedirs("storage", exist_ok=True)
        output_path = os.path.join("storage", "output.json")
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(rewritten, f, ensure_ascii=False, indent=2)

        return ProcessResponse(questions=rewritten, json_path=output_path)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Processing failed: {exc}")


