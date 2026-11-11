import os
import unittest
from io import BytesIO
from werkzeug.datastructures import FileStorage
from backend.document_parser import extract_document_text, get_document_metadata
from backend.validators import validate_file_upload

class TestDocuments(unittest.TestCase):
    def setUp(self):
        self.test_dir = os.path.dirname(os.path.abspath(__file__))
        self.project_dir = os.path.dirname(self.test_dir)
        self.pdf_sample = os.path.join(self.project_dir, "test_document.pdf")

    def test_txt_extraction(self):
        sample_txt = "Title: Project Proposal\n\n1. Executive Summary\nThis proposal outlines automated AI transformations."
        file_storage = FileStorage(
            stream=BytesIO(sample_txt.encode("utf-8")),
            filename="proposal.txt",
            content_type="text/plain"
        )
        extracted = extract_document_text(file_storage)
        self.assertIn("Project Proposal", extracted)
        self.assertIn("Executive Summary", extracted)

    def test_pdf_extraction(self):
        if os.path.exists(self.pdf_sample):
            with open(self.pdf_sample, "rb") as f:
                data = f.read()
            file_storage = FileStorage(
                stream=BytesIO(data),
                filename="test_document.pdf",
                content_type="application/pdf"
            )
            extracted = extract_document_text(file_storage)
            self.assertTrue(len(extracted) > 100, "PDF extraction should yield substantive text.")
            meta = get_document_metadata(file_storage)
            self.assertEqual(meta["filename"], "test_document.pdf")
            self.assertTrue(meta["word_count"] > 20)

    def test_docx_extraction(self):
        from docx import Document
        doc = Document()
        doc.add_heading("Research Report on AI", level=1)
        doc.add_paragraph("Machine learning algorithms automate data synthesis effectively.")
        buf = BytesIO()
        doc.save(buf)
        buf.seek(0)

        file_storage = FileStorage(
            stream=buf,
            filename="report.docx",
            content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )
        extracted = extract_document_text(file_storage)
        self.assertIn("Research Report on AI", extracted)
        self.assertIn("Machine learning algorithms", extracted)

    def test_empty_file_handling(self):
        file_storage = FileStorage(
            stream=BytesIO(b""),
            filename="empty.txt",
            content_type="text/plain"
        )
        with self.assertRaises(ValueError) as ctx:
            extract_document_text(file_storage)
        self.assertIn("empty", str(ctx.exception).lower())

    def test_invalid_file_extension(self):
        file_storage = FileStorage(
            stream=BytesIO(b"malicious script"),
            filename="script.exe",
            content_type="application/octet-stream"
        )
        valid, err = validate_file_upload(file_storage)
        self.assertFalse(valid)
        self.assertIn("Unsupported file type", err)

if __name__ == "__main__":
    unittest.main()
