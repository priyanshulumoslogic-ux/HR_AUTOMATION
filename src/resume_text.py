import io

import docx
import pdfplumber


def extract_text(filename, data_bytes):
    lowered = filename.lower()
    if lowered.endswith(".pdf"):
        return _extract_pdf_text(data_bytes)
    if lowered.endswith(".docx"):
        return _extract_docx_text(data_bytes)
    return ""


def _extract_pdf_text(data_bytes):
    chunks = []
    with pdfplumber.open(io.BytesIO(data_bytes)) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                chunks.append(text)
    return "\n".join(chunks)


def _extract_docx_text(data_bytes):
    document = docx.Document(io.BytesIO(data_bytes))
    return "\n".join(p.text for p in document.paragraphs if p.text)
