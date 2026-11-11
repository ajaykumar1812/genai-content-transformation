import os
import re
from io import BytesIO
from collections import Counter
from typing import Dict, Any, List
from pypdf import PdfReader
from docx import Document
from werkzeug.datastructures import FileStorage

def _clean_pdf_text(raw_pages: List[str]) -> str:
    """
    Cleans raw per-page text extracted from a PDF:
    1. Detects and strips repeated header/footer lines (appearing on 40%+ of pages).
    2. Strips standalone page-number lines ("Page 1", "1", "Page 1 of 10", "- 1 -").
    3. Identifies and isolates section headings.
    4. Unwraps soft-wrapped lines into flowing paragraphs.
    5. Standardizes bullet markers into clean Markdown lists.
    """
    page_lines = [page.splitlines() for page in raw_pages]

    # Count frequency of stripped lines across pages to find running headers/footers
    line_page_count = Counter()
    for lines in page_lines:
        seen_on_page = set(l.strip() for l in lines if l.strip())
        for line in seen_on_page:
            line_page_count[line] += 1

    total_pages = len(raw_pages)
    repeated_threshold = max(2, int(total_pages * 0.4))
    heading_re = re.compile(r'^\d+(\.\d+)*\.?\s+[A-Z]')

    repeated_lines = {
        line for line, count in line_page_count.items()
        if count >= repeated_threshold and len(line) < 120 and not heading_re.match(line)
    }

    page_num_re = re.compile(
        r'^[\-–—]?\s*(page\s+)?\d+(\s+of\s+\d+)?\s*[\-–—]?$',
        re.IGNORECASE
    )
    bullet_re = re.compile(r'^(\x7f|[-*•]|\d+\))\s+')

    cleaned_blocks = []
    current_para = []

    def flush_para():
        if current_para:
            text = ' '.join(current_para).strip()
            text = re.sub(r'^\x7f\s*', '- ', text)
            if text:
                cleaned_blocks.append(text)
            current_para.clear()

    for lines in page_lines:
        for line in lines:
            stripped = line.strip()
            if not stripped:
                flush_para()
                continue
            if stripped in repeated_lines or page_num_re.match(stripped):
                continue

            # Section heading check (e.g. "1. Introduction", "2.1 Background")
            if heading_re.match(stripped):
                flush_para()
                cleaned_blocks.append(stripped)
                continue

            # Short all-caps document title
            if stripped.isupper() and 5 <= len(stripped) <= 80 and not current_para:
                flush_para()
                cleaned_blocks.append(stripped)
                continue

            # Bullet item
            if bullet_re.match(stripped):
                flush_para()
                cleaned_bullet = bullet_re.sub('- ', stripped)
                current_para.append(cleaned_bullet)
                continue

            current_para.append(stripped)

        flush_para()

    return '\n\n'.join(cleaned_blocks)


def extract_document_text(file_storage: FileStorage) -> str:
    """
    Extracts text from uploaded Flask file storage (.txt, .pdf, .docx).
    Validates document contents, strips layout noise, and detects scanned documents.
    """
    if not file_storage or not file_storage.filename:
        return ""

    filename = file_storage.filename.lower()
    
    # Read file buffer safely
    file_storage.seek(0)
    data = file_storage.read()
    file_storage.seek(0)  # Reset pointer

    if len(data) == 0:
        raise ValueError("Uploaded document is completely empty (0 bytes).")

    if filename.endswith(".txt"):
        try:
            content = data.decode("utf-8")
        except UnicodeDecodeError:
            content = data.decode("latin-1", errors="replace")
        if not content.strip():
            raise ValueError("The uploaded text document contains no readable text.")
        return content.strip()

    elif filename.endswith(".pdf"):
        try:
            reader = PdfReader(BytesIO(data))
            if len(reader.pages) == 0:
                raise ValueError("PDF document contains no pages.")
            raw_pages = []
            for page in reader.pages:
                extracted = page.extract_text() or ""
                raw_pages.append(extracted)

            if not any(p.strip() for p in raw_pages):
                raise ValueError(
                    "The uploaded PDF contains no extractable text or consists solely of scanned images. "
                    "Scanned image-based documents require Optical Character Recognition (OCR) before processing."
                )

            cleaned = _clean_pdf_text(raw_pages)
            if not cleaned.strip():
                raise ValueError("Could not extract legible text from the PDF.")
            return cleaned.strip()

        except ValueError:
            raise
        except Exception as e:
            raise ValueError(f"Failed to read PDF document: {str(e)}")

    elif filename.endswith(".docx"):
        try:
            doc = Document(BytesIO(data))
            paragraphs = [p.text.strip() for p in doc.paragraphs if p.text.strip()]
            if not paragraphs:
                raise ValueError("The Word document (.docx) contains no text paragraphs.")
            return "\n\n".join(paragraphs)
        except ValueError:
            raise
        except Exception as e:
            raise ValueError(f"Failed to read DOCX document: {str(e)}")

    else:
        raise ValueError("Unsupported document format. Please upload .txt, .pdf, or .docx files.")


def get_document_metadata(file_storage: FileStorage) -> Dict[str, Any]:
    """
    Extracts text and generates rich metadata for UI previews before transformation.
    """
    text = extract_document_text(file_storage)
    words = len(text.split())
    chars = len(text)
    preview = text[:600] + ("..." if len(text) > 600 else "")

    return {
        "filename": file_storage.filename,
        "content_type": file_storage.content_type,
        "character_count": chars,
        "word_count": words,
        "preview": preview,
        "full_text": text
    }
