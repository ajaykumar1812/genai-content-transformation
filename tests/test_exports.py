import unittest
from backend.exporters import export_as_txt, export_as_docx, export_as_pdf, export_as_pptx

class TestExports(unittest.TestCase):
    def setUp(self):
        self.title = "Enterprise AI Architecture"
        self.content = (
            "# Executive Summary\n"
            "This report outlines the deployment of AI infrastructure across cloud regions.\n\n"
            "## Key Strategic Points\n"
            "- Multi-model orchestration improves reliability.\n"
            "- Strict token rate limiting avoids quota exhaustion.\n"
            "- ReportLab and python-docx format outputs cleanly.\n\n"
            "1. First milestone completed.\n"
            "2. Second milestone on track."
        )

    def test_txt_export(self):
        buf, mime, filename = export_as_txt(self.content, title=self.title)
        self.assertEqual(mime, "text/plain")
        self.assertTrue(filename.endswith(".txt"))
        val = buf.getvalue().decode("utf-8")
        self.assertIn("Enterprise AI Architecture", val)
        self.assertIn("Multi-model orchestration", val)

    def test_docx_export(self):
        buf, mime, filename = export_as_docx(self.title, self.content)
        self.assertTrue(filename.endswith(".docx"))
        self.assertEqual(mime, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")
        size = len(buf.getvalue())
        self.assertGreater(size, 1000, "DOCX buffer should contain substantive binary Word package.")

    def test_pdf_export(self):
        buf, mime, filename = export_as_pdf(self.title, self.content)
        self.assertTrue(filename.endswith(".pdf"))
        self.assertIn("pdf", mime)
        size = len(buf.getvalue())
        self.assertGreater(size, 500, "PDF buffer should contain valid PDF bytes.")
        self.assertTrue(buf.getvalue().startswith(b"%PDF"), "PDF buffer should start with PDF magic bytes.")

    def test_pptx_export(self):
        buf, mime, filename = export_as_pptx(self.title, self.content)
        self.assertTrue(filename.endswith(".pptx"))
        self.assertIn("presentation", mime)
        size = len(buf.getvalue())
        self.assertGreater(size, 1000, "PPTX buffer should contain valid PowerPoint slide package.")

if __name__ == "__main__":
    unittest.main()
