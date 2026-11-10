import os
from io import BytesIO
from pypdf import PdfReader
from docx import Document

def extract_document_text(file_storage):
    """
    Extracts text from uploaded Flask file storage (.txt, .pdf, .docx).
    """
    if not file_storage or not file_storage.filename:
        return ""
    
    filename = file_storage.filename.lower()
    data = file_storage.read()
    
    if filename.endswith(".txt"):
        try:
            return data.decode("utf-8")
        except UnicodeDecodeError:
            return data.decode("latin-1", errors="replace")
            
    elif filename.endswith(".pdf"):
        try:
            reader = PdfReader(BytesIO(data))
            text_parts = []
            for i, page in enumerate(reader.pages):
                extracted = page.extract_text()
                if extracted:
                    text_parts.append(extracted)
            if not text_parts:
                raise ValueError("PDF file contains no readable text or consists solely of scanned images.")
            return "\n\n".join(text_parts)
        except Exception as e:
            raise ValueError(f"Failed to read PDF document: {e}")
            
    elif filename.endswith(".docx"):
        try:
            doc = Document(BytesIO(data))
            paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
            return "\n\n".join(paragraphs)
        except Exception as e:
            raise ValueError(f"Failed to read DOCX document: {e}")
            
    else:
        raise ValueError("Unsupported document format. Please upload .txt, .pdf, or .docx files.")
