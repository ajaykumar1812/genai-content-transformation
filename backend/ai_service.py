import os
import logging
from typing import Tuple, Dict, Any, Optional
from config import Config
from backend.openai_service import OpenAIService
from backend.gemini_service import GeminiService

logger = logging.getLogger("AIService")

# ==============================================================================
# CUSTOM AI SERVICE EXCEPTION HIERARCHY
# ==============================================================================

class AIServiceError(Exception):
    """Base exception for all AI provider service failures."""
    status_code = 500
    category = "internal_error"

class AIServiceAuthError(AIServiceError):
    """Raised when API key is missing, invalid, or unauthorized."""
    status_code = 401
    category = "authentication_error"

class AIServiceQuotaError(AIServiceError):
    """Raised when API quota or rate limits are exceeded."""
    status_code = 429
    category = "quota_error"

class AIServiceNetworkError(AIServiceError):
    """Raised on connection timeout, DNS failure, or network unreachable."""
    status_code = 503
    category = "network_error"

class AIServiceModelError(AIServiceError):
    """Raised when an invalid, deprecated, or unsupported model is requested."""
    status_code = 404
    category = "model_error"

class AIServiceInputError(AIServiceError):
    """Raised when prompt exceeds context limits or violates input requirements."""
    status_code = 400
    category = "invalid_input"


# ==============================================================================
# SINGLETON SERVICE INSTANCES
# ==============================================================================

_openai_service = OpenAIService()
_gemini_service = GeminiService()


def get_active_provider_status() -> Dict[str, Any]:
    """
    Returns real-time configuration status of AI providers without exposing secrets.
    """
    gemini_ready = _gemini_service.is_configured()
    openai_ready = _openai_service.is_configured()

    active_list = []
    if gemini_ready:
        active_list.append(f"Google Gemini ({Config.GEMINI_MODEL})")
    if openai_ready:
        active_list.append(f"OpenAI ({Config.OPENAI_MODEL})")

    primary = "None Configured"
    if gemini_ready:
        primary = "Google Gemini"
    elif openai_ready:
        primary = "OpenAI"

    return {
        "gemini_available": gemini_ready,
        "openai_available": openai_ready,
        "gemini_model": Config.GEMINI_MODEL,
        "openai_model": Config.OPENAI_MODEL,
        "gemini_models": Config.GEMINI_SUPPORTED_MODELS,
        "openai_models": Config.OPENAI_SUPPORTED_MODELS,
        "active_providers": active_list,
        "primary_provider": primary,
        "online_mode": True
    }


def resolve_provider_and_model(
    requested_provider: Optional[str] = "auto",
    requested_model: Optional[str] = None
) -> Tuple[str, str]:
    """
    Resolves the target AI provider and model.
    STRICT REQUIREMENT: Never silently switch to offline fake generators.
    If requested or default provider is unconfigured, raises AIServiceAuthError.
    """
    req_p = (requested_provider or "auto").strip().lower()

    if req_p == "openai":
        if not _openai_service.is_configured():
            raise AIServiceAuthError(
                "OpenAI provider selected, but OPENAI_API_KEY is not configured in your environment. "
                "Please configure OPENAI_API_KEY or switch to Google Gemini."
            )
        model = (requested_model or Config.OPENAI_MODEL or "gpt-4o-mini").strip()
        return "openai", model

    elif req_p == "gemini":
        if not _gemini_service.is_configured():
            raise AIServiceAuthError(
                "Google Gemini provider selected, but GEMINI_API_KEY is not configured in your environment. "
                "Please configure GEMINI_API_KEY or switch to OpenAI."
            )
        model = (requested_model or Config.GEMINI_MODEL or "gemini-3.8-flash").strip()
        return "gemini", model

    elif req_p == "auto":
        # Check Gemini first, then OpenAI
        if _gemini_service.is_configured():
            model = (requested_model or Config.GEMINI_MODEL or "gemini-3.8-flash").strip()
            return "gemini", model
        elif _openai_service.is_configured():
            model = (requested_model or Config.OPENAI_MODEL or "gpt-4o-mini").strip()
            return "openai", model
        else:
            raise AIServiceAuthError(
                "No online AI provider configured. Please set GEMINI_API_KEY (recommended) or OPENAI_API_KEY "
                "in your environment variables or .env file to enable online AI transformations."
            )
    else:
        raise AIServiceInputError(f"Unsupported AI provider '{requested_provider}'. Use 'gemini' or 'openai'.")


def dispatch_ai_request(
    system_prompt: str,
    user_prompt: str,
    provider: str = "auto",
    model: Optional[str] = None,
    temperature: float = 0.4,
    max_tokens: Optional[int] = None
) -> Tuple[str, str, str]:
    """
    Dispatches generation to the chosen official AI SDK.
    Returns: (generated_text, provider_label, model_name)
    """
    target_provider, target_model = resolve_provider_and_model(provider, model)

    if target_provider == "openai":
        result = _openai_service.generate(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            model=target_model,
            temperature=temperature,
            max_tokens=max_tokens
        )
        return result["output"], "OpenAI", target_model
    else:
        result = _gemini_service.generate(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            model=target_model,
            temperature=temperature,
            max_tokens=max_tokens
        )
        return result["output"], "Google Gemini", target_model


# ==============================================================================
# PROMPT CONSTRUCTION & SPECIALIZED TRANSFORMATION ENGINES
# ==============================================================================

SYSTEM_CORE = (
    "You are an expert enterprise AI Content Transformation Engine. "
    "Your objective is to produce accurate, high-impact, professionally structured content based strictly "
    "on the provided source text. Never fabricate unstated facts, hallucinations, or unverifiable claims. "
    "Format your response with clean GitHub Flavored Markdown headings, bullet points, and spacing."
)

def summarize_text(
    source: str,
    summary_type: str = "Executive Summary",
    detail: str = "Medium",
    provider: str = "auto",
    model: Optional[str] = None
) -> Tuple[str, str, str]:
    """
    A. AI Summarizer:
    Options: Short, Medium, Detailed, Bullet-point, Executive Summary.
    Output: Accurate summary, main points, important facts, key conclusions.
    """
    instructions = {
        "Short": "Produce an ultra-concise 1-2 paragraph executive summary capturing the core premise and conclusion.",
        "Medium": "Produce a balanced summary with an overview paragraph, key points with bullet highlights, and strategic conclusions.",
        "Detailed": "Produce a comprehensive, multi-section detailed summary preserving all critical data points, nuances, and findings.",
        "Bullet-point": "Distill into a prioritized, categorized bullet-point briefing with bold thematic keywords for rapid consumption.",
        "Executive Summary": "Deliver a formal Executive Summary featuring: Context, Problem Statement, Key Findings, and Actionable Recommendations."
    }.get(summary_type, "Deliver a balanced, well-structured summary.")

    system_prompt = (
        f"{SYSTEM_CORE}\n"
        f"Task: Text Summarization\n"
        f"Type: {summary_type} | Detail: {detail}\n"
        f"Guideline: {instructions}\n"
        f"Structure required:\n"
        f"# Summary Overview\n"
        f"# Core Findings & Important Facts\n"
        f"# Strategic Takeaways & Key Conclusions\n"
        f"Do not invent facts not in the source."
    )

    user_prompt = f"Source Text to Summarize:\n\"\"\"\n{source}\n\"\"\""
    return dispatch_ai_request(system_prompt, user_prompt, provider=provider, model=model, temperature=0.3)


def paraphrase_text(
    source: str,
    style: str = "Standard",
    provider: str = "auto",
    model: Optional[str] = None
) -> Tuple[str, str, str]:
    """
    B. AI Paraphraser:
    Options: Standard, Professional, Academic, Simple English, Creative.
    Preserves original meaning, improves readability, avoids repetition.
    """
    style_guidance = {
        "Standard": "Rephrase naturally with clear phrasing, varied sentence structures, and crisp flow while preserving the exact meaning.",
        "Professional": "Rewrite with polished corporate diction, executive phrasing, and smooth professional transitions.",
        "Academic": "Rewrite using scholarly language, precise terminology, objective analytical framing, and formal syntax.",
        "Simple English": "Rewrite using plain English, short words, active voice, and effortless readability without jargon.",
        "Creative": "Rewrite with vivid imagery, dynamic rhythm, compelling narrative hooks, and engaging expression."
    }.get(style, "Rewrite clearly while preserving original meaning.")

    system_prompt = (
        f"{SYSTEM_CORE}\n"
        f"Task: Content Paraphrasing\n"
        f"Style: {style}\n"
        f"Directive: {style_guidance}\n"
        f"Rules: Strictly preserve all original information, facts, and intent. Eliminate awkward repetitions and fluff. "
        f"Output the rewritten content directly in polished Markdown."
    )

    user_prompt = f"Original Source Text:\n\"\"\"\n{source}\n\"\"\""
    return dispatch_ai_request(system_prompt, user_prompt, provider=provider, model=model, temperature=0.4)


def correct_grammar(
    source: str,
    provider: str = "auto",
    model: Optional[str] = None
) -> Tuple[str, str, str]:
    """
    C. Grammar Corrector:
    Corrects grammar, spelling, punctuation, sentence structure.
    Displays: Corrected text, Main corrections made, Explanation of important corrections.
    """
    system_prompt = (
        f"{SYSTEM_CORE}\n"
        f"Task: Comprehensive Grammar, Spelling & Syntax Correction\n"
        f"You must strictly output your response using the following three sections:\n"
        f"# Corrected Text\n"
        f"[Provide the complete, flawlessly corrected version of the source text here.]\n\n"
        f"# Key Corrections Made\n"
        f"[Provide a bulleted list of specific grammatical, spelling, punctuation, and structural fixes applied.]\n\n"
        f"# Clarity & Style Improvements\n"
        f"[Explain how the changes improved sentence structure, flow, and tone without changing the original meaning.]"
    )

    user_prompt = f"Source Text to Inspect & Correct:\n\"\"\"\n{source}\n\"\"\""
    return dispatch_ai_request(system_prompt, user_prompt, provider=provider, model=model, temperature=0.2)


def transform_tone(
    source: str,
    target_tone: str = "Professional",
    audience: str = "General audience",
    provider: str = "auto",
    model: Optional[str] = None
) -> Tuple[str, str, str]:
    """
    D. Tone Transformer:
    Options: Professional, Formal, Casual, Academic, Persuasive, Friendly, Confident, Business, Creative.
    Preserves all facts while adapting tone and audience.
    """
    tone_directives = {
        "Professional": "Project competence, reliability, and business poise.",
        "Formal": "Use strictly authoritative, respectful, and institutionally dignified language.",
        "Casual": "Adopt an easygoing, conversational, and natural tone.",
        "Academic": "Use rigorous, scholarly, research-backed analytical diction.",
        "Persuasive": "Use compelling, action-oriented, and convincing rhetoric.",
        "Friendly": "Radiate warmth, approachability, and supportive encouragement.",
        "Confident": "Speak with decisive certainty, authority, and conviction.",
        "Business": "Focus on ROI, strategic outcomes, efficiency, and executive metrics.",
        "Creative": "Employ evocative phrasing, dynamic pace, and expressive flair."
    }.get(target_tone, "Transform tone to match the target specification.")

    system_prompt = (
        f"{SYSTEM_CORE}\n"
        f"Task: Tone Transformation\n"
        f"Target Tone: {target_tone}\n"
        f"Target Audience: {audience}\n"
        f"Guideline: {tone_directives}\n"
        f"Rule: Retain every key piece of factual information, metric, and premise from the source."
    )

    user_prompt = f"Source Text:\n\"\"\"\n{source}\n\"\"\""
    return dispatch_ai_request(system_prompt, user_prompt, provider=provider, model=model, temperature=0.5)


def generate_blog(
    source: str,
    tone: str = "Engaging",
    target_length: str = "Medium",
    provider: str = "auto",
    model: Optional[str] = None
) -> Tuple[str, str, str]:
    """
    E. Blog Generator:
    Generates: Blog title, Catchy Introduction, Main sections with subheadings,
    Actionable conclusion, SEO keywords, Meta description.
    """
    system_prompt = (
        f"{SYSTEM_CORE}\n"
        f"Task: High-Conversion SEO Blog Post Generation\n"
        f"Tone: {tone} | Length: {target_length}\n"
        f"You must strictly include the following structured sections:\n"
        f"# [Compelling, Click-Worthy Blog Post Title]\n\n"
        f"**Meta Description:** [A concise 150-160 character SEO meta description]\n\n"
        f"**Target SEO Keywords:** [5-8 comma-separated high-intent search keywords]\n\n"
        f"## Introduction\n"
        f"[Hook the reader, introduce the central problem, and outline key insights]\n\n"
        f"## [Section 1 Title]\n"
        f"[Detailed analysis, actionable tips, and practical examples]\n\n"
        f"## [Section 2 Title]\n"
        f"[In-depth examination of core themes and practical insights]\n\n"
        f"## Key Takeaways & Best Practices\n"
        f"[Bulleted list of immediate actionable insights]\n\n"
        f"## Conclusion\n"
        f"[Inspiring closing thought and clear call-to-action (CTA)]"
    )

    user_prompt = f"Source Material:\n\"\"\"\n{source}\n\"\"\""
    return dispatch_ai_request(system_prompt, user_prompt, provider=provider, model=model, temperature=0.6)


def generate_executive_summary(
    source: str,
    detail: str = "Medium",
    provider: str = "auto",
    model: Optional[str] = None
) -> Tuple[str, str, str]:
    """
    F. Executive Summary Generator:
    Generates: Overview, Problem statement, Main findings, Important recommendations, Conclusion.
    """
    system_prompt = (
        f"{SYSTEM_CORE}\n"
        f"Task: Strategic Executive Briefing\n"
        f"Deliver a rigorous C-suite executive briefing structured as follows:\n"
        f"# Executive Overview\n"
        f"# Problem Statement & Context\n"
        f"# Core Findings & Strategic Analysis\n"
        f"# Key Recommendations & Action Plan\n"
        f"# Conclusion & Expected Outcomes"
    )

    user_prompt = f"Source Material:\n\"\"\"\n{source}\n\"\"\""
    return dispatch_ai_request(system_prompt, user_prompt, provider=provider, model=model, temperature=0.3)


def generate_business_report(
    source: str,
    detail: str = "Medium",
    provider: str = "auto",
    model: Optional[str] = None
) -> Tuple[str, str, str]:
    """
    G. Business Report Generator:
    Generates: Title, Executive overview, Background, Analysis, Findings, Recommendations, Conclusion.
    """
    system_prompt = (
        f"{SYSTEM_CORE}\n"
        f"Task: Corporate Business Report\n"
        f"Produce a formal business report with the following mandatory sections:\n"
        f"# [Formal Report Title]\n\n"
        f"## 1. Executive Overview\n\n"
        f"## 2. Background & Strategic Context\n\n"
        f"## 3. Comprehensive Analysis\n\n"
        f"## 4. Key Findings & Data Insights\n\n"
        f"## 5. Strategic Recommendations\n\n"
        f"## 6. Implementation Timeline & Conclusion"
    )

    user_prompt = f"Source Material:\n\"\"\"\n{source}\n\"\"\""
    return dispatch_ai_request(system_prompt, user_prompt, provider=provider, model=model, temperature=0.3)


def generate_presentation(
    source: str,
    num_slides: int = 7,
    provider: str = "auto",
    model: Optional[str] = None
) -> Tuple[str, str, str]:
    """
    H. Presentation Content Generator:
    Generates: Presentation title, Slide headings, Slide-wise bullet points, Introduction, Main content, Conclusion.
    Formatted cleanly for direct export to PPTX.
    """
    system_prompt = (
        f"{SYSTEM_CORE}\n"
        f"Task: Presentation Deck Content Generation\n"
        f"Create a high-impact presentation deck with approximately {num_slides} slides.\n"
        f"Format strictly using Markdown headers for slides so our PPTX converter parses each slide:\n"
        f"# Presentation Title: [Title of the Presentation]\n\n"
        f"## Slide 1: [Introduction / Title]\n"
        f"- [Bullet point 1]\n"
        f"- [Bullet point 2]\n"
        f"- [Bullet point 3]\n\n"
        f"## Slide 2: [Context / Problem]\n"
        f"- [Bullet point 1]\n"
        f"- [Bullet point 2]\n\n"
        f"[Continue for each slide with clean '## Slide X: Title' and 3-5 concise bullet points per slide]\n"
        f"Ensure the final slide is '## Slide {num_slides}: Conclusion & Next Steps'."
    )

    user_prompt = f"Source Material:\n\"\"\"\n{source}\n\"\"\""
    return dispatch_ai_request(system_prompt, user_prompt, provider=provider, model=model, temperature=0.4)


def generate_faq(
    source: str,
    provider: str = "auto",
    model: Optional[str] = None
) -> Tuple[str, str, str]:
    """
    I. FAQ Generator:
    Generates relevant questions and answers based strictly on the source content.
    """
    system_prompt = (
        f"{SYSTEM_CORE}\n"
        f"Task: Frequently Asked Questions (FAQ) Extraction & Formulation\n"
        f"Analyze the source content and formulate 6 to 10 comprehensive, high-value Q&A pairs.\n"
        f"Structure each item as:\n"
        f"### Q: [Clear, natural question]\n"
        f"**A:** [Accurate, complete answer derived strictly from the content]"
    )

    user_prompt = f"Source Material:\n\"\"\"\n{source}\n\"\"\""
    return dispatch_ai_request(system_prompt, user_prompt, provider=provider, model=model, temperature=0.3)


def generate_key_takeaways(
    source: str,
    provider: str = "auto",
    model: Optional[str] = None
) -> Tuple[str, str, str]:
    """
    J. Key Takeaways Generator:
    Extracts: Important points, Main findings, Critical information, Actionable insights.
    """
    system_prompt = (
        f"{SYSTEM_CORE}\n"
        f"Task: Key Takeaways & Core Insights Extraction\n"
        f"Distill the content into numbered core takeaways structured as follows:\n"
        f"# Key Strategic Takeaways\n\n"
        f"## 1. [Critical Finding / Core Theme]\n"
        f"- **Context:** [Explanation]\n"
        f"- **Impact:** [Implication]\n\n"
        f"## 2. [Actionable Insight]\n"
        f"- **Context:** [Explanation]\n"
        f"- **Action Required:** [Guidance]\n\n"
        f"[Provide 5-8 total takeaways formatted consistently.]"
    )

    user_prompt = f"Source Material:\n\"\"\"\n{source}\n\"\"\""
    return dispatch_ai_request(system_prompt, user_prompt, provider=provider, model=model, temperature=0.3)


def generate_social_media(
    source: str,
    platform: str = "LinkedIn",
    tone: str = "Professional",
    provider: str = "auto",
    model: Optional[str] = None
) -> Tuple[str, str, str]:
    """
    K. Social Media Content Generator:
    Generates tailored posts for LinkedIn, Instagram, Facebook, and X (Twitter).
    """
    platform_clean = platform.capitalize()
    system_prompt = (
        f"{SYSTEM_CORE}\n"
        f"Task: Social Media Content Creation for {platform_clean}\n"
        f"Tone: {tone}\n"
        f"Platform requirements:\n"
        f"- LinkedIn: Thought-leadership opening hook, structured insight bullets, engaging question, 3-5 relevant hashtags.\n"
        f"- X / Twitter: Punchy multi-tweet thread (1/X format), compelling hook, bite-sized value tweets, hashtags.\n"
        f"- Instagram: Visual caption with engaging hook, formatted spacing, emojis, call-to-action, 10-15 targeted hashtags.\n"
        f"- Facebook: Conversational, community-focused post with discussion prompt and shareable value.\n"
        f"Generate ready-to-publish content tailored specifically for {platform_clean}."
    )

    user_prompt = f"Source Material:\n\"\"\"\n{source}\n\"\"\""
    return dispatch_ai_request(system_prompt, user_prompt, provider=provider, model=model, temperature=0.6)


def transform_content(
    source: str,
    output_format: str = "Executive Summary",
    audience: str = "General audience",
    tone: str = "Professional",
    detail: str = "Medium",
    provider: str = "auto",
    model: Optional[str] = None
) -> Tuple[str, str, str]:
    """
    Central AI Studio dispatcher routing to specific transformation engines.
    """
    fmt = output_format.strip()

    if "Blog" in fmt:
        return generate_blog(source, tone=tone, target_length=detail, provider=provider, model=model)
    elif "Business Report" in fmt or "Report" in fmt:
        return generate_business_report(source, detail=detail, provider=provider, model=model)
    elif "Presentation" in fmt or "Deck" in fmt:
        return generate_presentation(source, num_slides=7, provider=provider, model=model)
    elif "Social" in fmt:
        return generate_social_media(source, platform="LinkedIn", tone=tone, provider=provider, model=model)
    elif "FAQ" in fmt:
        return generate_faq(source, provider=provider, model=model)
    elif "Takeaways" in fmt:
        return generate_key_takeaways(source, provider=provider, model=model)
    elif "Summar" in fmt:
        return summarize_text(source, summary_type=fmt, detail=detail, provider=provider, model=model)
    elif "Paraphrase" in fmt:
        return paraphrase_text(source, style=tone, provider=provider, model=model)
    elif "Grammar" in fmt:
        return correct_grammar(source, provider=provider, model=model)
    elif "Tone" in fmt:
        return transform_tone(source, target_tone=tone, audience=audience, provider=provider, model=model)
    elif "Executive Summary" in fmt:
        return generate_executive_summary(source, detail=detail, provider=provider, model=model)
    else:
        # Generic high-quality transformation
        system_prompt = (
            f"{SYSTEM_CORE}\n"
            f"Deliverable: {output_format}\n"
            f"Target Audience: {audience}\n"
            f"Tone: {tone} | Detail: {detail}\n"
            f"Transform the source material into the specified deliverable format with clear Markdown structure."
        )
        user_prompt = f"Source Content:\n\"\"\"\n{source}\n\"\"\""
        return dispatch_ai_request(system_prompt, user_prompt, provider=provider, model=model, temperature=0.4)
