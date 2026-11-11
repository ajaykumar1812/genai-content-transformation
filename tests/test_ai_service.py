import unittest
from unittest.mock import patch, MagicMock
from app import app
from backend.ai_service import (
    summarize_text, paraphrase_text, correct_grammar,
    transform_tone, generate_blog, generate_business_report,
    generate_presentation, generate_faq, generate_key_takeaways,
    generate_social_media, transform_content, resolve_provider_and_model,
    AIServiceAuthError
)

class TestAIService(unittest.TestCase):
    def setUp(self):
        self.sample_text = (
            "Generative Artificial Intelligence is transforming modern enterprise productivity. "
            "Organizations are deploying large language models to automate customer communication, "
            "synthesize unstructured financial reports, and optimize software development life cycles. "
            "However, deploying AI models at scale requires robust governance, low-latency infrastructure, "
            "and strict data privacy protocols to mitigate hallucination and compliance liabilities."
        )

    @patch("backend.ai_service._gemini_service.generate")
    def test_gemini_summarizer(self, mock_gemini):
        mock_gemini.return_value = {
            "output": "# Summary Overview\nGenerative AI accelerates enterprise productivity while requiring strict data governance.",
            "provider": "Google Gemini",
            "model": "gemini-2.5-flash"
        }
        with patch("backend.ai_service._gemini_service.is_configured", return_value=True):
            output, provider, model = summarize_text(self.sample_text, summary_type="Executive Summary", provider="gemini")
            self.assertIn("Generative AI accelerates", output)
            self.assertEqual(provider, "Google Gemini")
            self.assertEqual(model, "gemini-2.5-flash")

    @patch("backend.ai_service._openai_service.generate")
    def test_openai_paraphraser(self, mock_openai):
        mock_openai.return_value = {
            "output": "Large language models streamline business operations across various sectors.",
            "provider": "OpenAI",
            "model": "gpt-4o-mini"
        }
        with patch("backend.ai_service._openai_service.is_configured", return_value=True):
            output, provider, model = paraphrase_text(self.sample_text, style="Professional", provider="openai")
            self.assertIn("streamline business operations", output)
            self.assertEqual(provider, "OpenAI")
            self.assertEqual(model, "gpt-4o-mini")

    @patch("backend.ai_service._gemini_service.generate")
    def test_grammar_corrector(self, mock_gemini):
        mock_gemini.return_value = {
            "output": "# Corrected Text\nAI models optimize software development.\n\n# Key Corrections Made\n- Fixed subject-verb agreement.",
            "provider": "Google Gemini",
            "model": "gemini-2.5-flash"
        }
        with patch("backend.ai_service._gemini_service.is_configured", return_value=True):
            output, provider, model = correct_grammar(self.sample_text, provider="gemini")
            self.assertIn("# Corrected Text", output)
            self.assertIn("# Key Corrections Made", output)

    @patch("backend.ai_service._gemini_service.generate")
    def test_tone_transformer(self, mock_gemini):
        mock_gemini.return_value = {
            "output": "We're super excited about how Gen AI speeds up work everywhere!",
            "provider": "Google Gemini",
            "model": "gemini-2.5-flash"
        }
        with patch("backend.ai_service._gemini_service.is_configured", return_value=True):
            output, provider, model = transform_tone(self.sample_text, target_tone="Casual & Friendly", provider="gemini")
            self.assertIn("super excited", output)

    @patch("backend.ai_service._gemini_service.generate")
    def test_blog_generator(self, mock_gemini):
        mock_gemini.return_value = {
            "output": "# How Generative AI is Reshaping Modern Business\n\n**Meta Description:** Discover how AI drives ROI.\n\n## Introduction\nAI is here.",
            "provider": "Google Gemini",
            "model": "gemini-2.5-flash"
        }
        with patch("backend.ai_service._gemini_service.is_configured", return_value=True):
            output, provider, model = generate_blog(self.sample_text, tone="Engaging", provider="gemini")
            self.assertIn("Meta Description", output)

    @patch("backend.ai_service._gemini_service.generate")
    def test_report_generator(self, mock_gemini):
        mock_gemini.return_value = {
            "output": "# Enterprise AI Adoption Report\n\n## 1. Executive Overview\nAdoption is accelerating rapidly.",
            "provider": "Google Gemini",
            "model": "gemini-2.5-flash"
        }
        with patch("backend.ai_service._gemini_service.is_configured", return_value=True):
            output, provider, model = generate_business_report(self.sample_text, detail="Medium", provider="gemini")
            self.assertIn("Executive Overview", output)

    @patch("backend.ai_service._gemini_service.generate")
    def test_presentation_generator(self, mock_gemini):
        mock_gemini.return_value = {
            "output": "# Presentation Title: Gen AI in Enterprise\n\n## Slide 1: Introduction\n- Transformational technology\n- Scalable architectures",
            "provider": "Google Gemini",
            "model": "gemini-2.5-flash"
        }
        with patch("backend.ai_service._gemini_service.is_configured", return_value=True):
            output, provider, model = generate_presentation(self.sample_text, num_slides=5, provider="gemini")
            self.assertIn("## Slide 1:", output)

    @patch("backend.ai_service._gemini_service.generate")
    def test_faq_generator(self, mock_gemini):
        mock_gemini.return_value = {
            "output": "### Q: What is the main benefit of Generative AI?\n**A:** It automates repetitive workflows and enhances efficiency.",
            "provider": "Google Gemini",
            "model": "gemini-2.5-flash"
        }
        with patch("backend.ai_service._gemini_service.is_configured", return_value=True):
            output, provider, model = generate_faq(self.sample_text, provider="gemini")
            self.assertIn("### Q:", output)
            self.assertIn("**A:**", output)

    @patch("backend.ai_service._gemini_service.generate")
    def test_key_takeaways_generator(self, mock_gemini):
        mock_gemini.return_value = {
            "output": "# Key Strategic Takeaways\n\n## 1. Governance is Crucial\n- Strict data privacy required.",
            "provider": "Google Gemini",
            "model": "gemini-2.5-flash"
        }
        with patch("backend.ai_service._gemini_service.is_configured", return_value=True):
            output, provider, model = generate_key_takeaways(self.sample_text, provider="gemini")
            self.assertIn("Key Strategic Takeaways", output)

    @patch("backend.ai_service._gemini_service.generate")
    def test_social_media_generator(self, mock_gemini):
        mock_gemini.return_value = {
            "output": "🚀 AI is revolutionizing business workflows! Here is what leaders need to know: #AI #Enterprise #Innovation",
            "provider": "Google Gemini",
            "model": "gemini-2.5-flash"
        }
        with patch("backend.ai_service._gemini_service.is_configured", return_value=True):
            output, provider, model = generate_social_media(self.sample_text, platform="LinkedIn", provider="gemini")
            self.assertIn("#AI", output)

    def test_provider_switching_and_unconfigured_error(self):
        # When neither provider key is configured and user requests gemini
        with patch("backend.ai_service._gemini_service.is_configured", return_value=False):
            with self.assertRaises(AIServiceAuthError) as ctx:
                resolve_provider_and_model("gemini")
            self.assertIn("GEMINI_API_KEY is not configured", str(ctx.exception))

        # When OpenAI key is not configured and user requests openai
        with patch("backend.ai_service._openai_service.is_configured", return_value=False):
            with self.assertRaises(AIServiceAuthError) as ctx:
                resolve_provider_and_model("openai")
            self.assertIn("OPENAI_API_KEY is not configured", str(ctx.exception))

if __name__ == "__main__":
    unittest.main()
