from typing import Union
import io


def extract_text_from_pdf(pdf_stream: Union[io.BytesIO, bytes]) -> str:
    """
    Extract text from a PDF using pdfplumber if available, fallback to PyPDF2.
    Accepts a BytesIO or raw bytes.
    """
    # Lazy imports so the module is importable without optional deps
    try:
        import pdfplumber  # type: ignore
    except Exception:
        pdfplumber = None  # type: ignore

    text_chunks = []

    if pdfplumber is not None:
        stream = pdf_stream if isinstance(pdf_stream, io.BytesIO) else io.BytesIO(pdf_stream)
        with pdfplumber.open(stream) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text() or ""
                text_chunks.append(page_text)
        return "\n".join(text_chunks)

    # Fallback to PyPDF2
    from PyPDF2 import PdfReader  # type: ignore

    stream = pdf_stream if isinstance(pdf_stream, io.BytesIO) else io.BytesIO(pdf_stream)
    reader = PdfReader(stream)
    for page in reader.pages:
        try:
            page_text = page.extract_text() or ""
        except Exception:
            page_text = ""
        text_chunks.append(page_text)
    return "\n".join(text_chunks)


