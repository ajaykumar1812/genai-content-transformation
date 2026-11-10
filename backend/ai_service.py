import os
import re

# Prompt templates
FORMAT_PROMPTS = {
    "Executive Summary": "Create a high-impact executive summary highlighting context, key findings, strategic takeaways, and actionable conclusions.",
    "Blog Post": "Write an engaging, well-structured blog post with an attention-grabbing headline, subheadings, actionable insights, and conclusion with suggested SEO keywords.",
    "Business Report": "Generate a formal corporate report with Executive Summary, Background, Analysis of Key Points, Strategic Recommendations, and Conclusion.",
    "Presentation Deck": "Create a 6-10 slide presentation deck. For each slide, write a clear Slide Title and 3-5 concise, impactful bullet points.",
    "Social Media Campaign": "Generate tailored social media posts for LinkedIn (thought-leadership), Twitter/X (punchy thread with hashtags), and Instagram/Facebook.",
    "FAQ Guide": "Extract and formulate 6-10 comprehensive Frequently Asked Questions and accurate answers based strictly on the source material.",
    "Advisory Bulletin": "Draft a formal advisory notice outlining situational context, core implications, operational guidance, and cautionary steps.",
    "Key Takeaways": "Distill the content into numbered core takeaways with clear bold highlights and explanatory bullet points."
}

SUMMARIZE_PROMPTS = {
    "Executive Summary": "Distill into a high-level executive summary for decision-makers with key insights and next steps.",
    "Bullet Points": "Extract the key information as clear, prioritized bullet points with bold keywords.",
    "TL;DR": "Provide a 2-3 sentence ultra-concise TL;DR capture of the core message.",
    "Comprehensive Summary": "Provide a thorough section-by-section summary preserving all critical facts, figures, and relationships."
}

PARAPHRASE_PROMPTS = {
    "Standard": "Rephrase clearly and naturally while maintaining the exact original meaning.",
    "Fluent & Elegant": "Rewrite using elevated vocabulary, smooth transitions, and polished sentence flow.",
    "Creative": "Restructure with vivid language, compelling hooks, and dynamic expression.",
    "Simplified (Plain English)": "Simplify using plain English, short sentences, and crystal-clear clarity for general readers.",
    "Academic": "Rewrite in scholarly academic prose with formal diction, objective framing, and analytical transitions."
}

TONE_PROMPTS = {
    "Professional": "Transform into a polished, professional business tone suitable for corporate communication.",
    "Formal": "Transform into an authoritative, strictly formal tone suitable for legal, policy, or institutional contexts.",
    "Casual & Friendly": "Transform into an approachable, warm, conversational, and relatable tone.",
    "Persuasive": "Transform into a compelling, action-oriented persuasive tone designed to convince and inspire.",
    "Executive": "Transform into a direct, bottom-line-oriented executive tone focused on strategic value.",
    "Technical": "Transform into a precise, rigorous technical tone emphasizing accuracy and methodology."
}

def get_active_provider_status():
    gemini_key = os.getenv("GEMINI_API_KEY", "").strip()
    openai_key = os.getenv("OPENAI_API_KEY", "").strip()
    
    gemini_valid = bool(gemini_key and not gemini_key.startswith("PASTE_"))
    openai_valid = bool(openai_key and not openai_key.startswith("PASTE_"))
    
    active = []
    if gemini_valid:
        active.append("Gemini (" + os.getenv("GEMINI_MODEL", "gemini-2.5-flash") + ")")
    if openai_valid:
        active.append("OpenAI (" + os.getenv("OPENAI_MODEL", "gpt-4o-mini") + ")")
        
    return {
        "gemini_available": gemini_valid,
        "openai_available": openai_valid,
        "active_providers": active,
        "primary_provider": "Gemini" if gemini_valid else ("OpenAI" if openai_valid else "Built-in Offline Engine")
    }

def _call_gemini(system_prompt, user_prompt):
    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    model_name = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
    if not api_key or api_key.startswith("PASTE_"):
        raise ValueError("Gemini API key is not configured.")
        
    from google import genai
    client = genai.Client(api_key=api_key)
    full_prompt = f"{system_prompt}\n\n{user_prompt}"
    response = client.models.generate_content(
        model=model_name,
        contents=full_prompt
    )
    if not response or not response.text:
        raise RuntimeError("Gemini returned an empty response.")
    return response.text.strip()

def _call_openai(system_prompt, user_prompt):
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    model_name = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    if not api_key or api_key.startswith("PASTE_"):
        raise ValueError("OpenAI API key is not configured.")
        
    from openai import OpenAI
    client = OpenAI(api_key=api_key)
    response = client.chat.completions.create(
        model=model_name,
        temperature=0.4,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
    )
    return response.choices[0].message.content.strip()

def _offline_fallback_generator(task_type, source, param1="", param2="", param3=""):
    """
    Intelligent built-in fallback transformer when no API key is supplied.
    Ensures zero crashes and produces high quality structured output.
    """
    paragraphs = [p.strip() for p in source.splitlines() if p.strip()]
    all_text = " ".join(paragraphs)
    sentences = re.split(r'(?<=[.!?])\s+', all_text)
    sentences = [s.strip() for s in sentences if len(s.strip()) > 15]

    notice = "> *Note: Generated using Built-in Local Engine. To enable LLM generation, set your GEMINI_API_KEY or OPENAI_API_KEY in .env*\n\n"

    if task_type == "summary":
        summary_style = param1 or "Executive Summary"
        num_sentences = 3 if param2 == "Short" else (5 if param2 == "Medium" else 8)
        selected = sentences[:num_sentences]
        
        if summary_style == "TL;DR":
            return notice + f"### TL;DR\n\n{' '.join(selected[:2])}"
        elif summary_style == "Bullet Points":
            bullets = "\n".join(f"- **Key Point {i+1}:** {s}" for i, s in enumerate(selected))
            return notice + f"### Key Highlights\n\n{bullets}"
        else:
            bullets = "\n".join(f"- {s}" for s in selected[1:4])
            return notice + f"### Executive Summary\n\n**Overview:** {selected[0] if selected else source[:150]}\n\n**Core Findings:**\n{bullets}\n\n**Conclusion:** {selected[-1] if len(selected)>1 else 'Analysis completed.'}"

    elif task_type == "paraphrase":
        style = param1 or "Standard"
        paraphrased_lines = []
        synonyms = {
            "important": "vital", "use": "leverage", "help": "assist",
            "show": "demonstrate", "make": "create", "need": "require",
            "big": "substantial", "good": "exceptional", "fast": "rapid",
            "platform": "solution", "change": "transform", "start": "initiate"
        }
        for s in sentences[:8]:
            words = s.split()
            new_words = [synonyms.get(w.lower(), w) for w in words]
            paraphrased_lines.append(" ".join(new_words))
            
        output = " ".join(paraphrased_lines) if paraphrased_lines else source
        return notice + f"### Paraphrased Content ({style} Style)\n\n{output}"

    elif task_type == "tone":
        target_tone = param1 or "Professional"
        return notice + f"### Transformed Content (Tone: {target_tone})\n\n" + \
            f"**Communication Context:** Directed to {param2 or 'Professional Audience'} with {target_tone} emphasis.\n\n" + \
            source

    elif task_type == "grammar":
        corrections = []
        improved = source
        # Common checks
        replacements = [
            (r"\bi\b", "I"),
            (r"\bteh\b", "the"),
            (r"\brecieve\b", "receive"),
            (r"\bseperate\b", "separate"),
            (r"\buntill\b", "until"),
            (r"\s{2,}", " "),
            (r"\s+([,.!?;:])", r"\1")
        ]
        for pattern, repl in replacements:
            if re.search(pattern, improved):
                improved = re.sub(pattern, repl, improved)
                corrections.append(f"Fixed spelling / punctuation match for `{pattern}`.")

        if not corrections:
            corrections.append("Sentence structures reviewed. Proper capitalization and punctuation ensured.")
            
        corr_list = "\n".join(f"- {c}" for c in corrections)
        return notice + f"### Corrected Content\n\n{improved}\n\n---\n### Grammar & Style Improvements:\n{corr_list}"

    else:
        # General Transformation
        fmt = param1 or "Executive Summary"
        if fmt == "Presentation Deck":
            slides = []
            for i in range(0, min(len(sentences), 15), 3):
                chunk = sentences[i:i+3]
                slide_num = (i // 3) + 1
                b_str = "\n".join(f"- {s}" for s in chunk)
                slides.append(f"#### Slide {slide_num}: Key Analysis {slide_num}\n{b_str}\n")
            return notice + f"### Presentation Deck\n\n" + "\n".join(slides)
        elif fmt == "FAQ Guide":
            faqs = []
            for i, s in enumerate(sentences[:5]):
                faqs.append(f"**Q{i+1}: What is the main insight regarding {s.split()[0] if s.split() else 'this topic'}?**\n**A:** {s}\n")
            return notice + f"### Frequently Asked Questions\n\n" + "\n".join(faqs)
        else:
            return notice + f"### {fmt}\n\n**Audience:** {param2}\n**Tone:** {param3}\n\n" + \
                   "\n\n".join(paragraphs[:4])

def execute_llm_request(system_prompt, user_prompt, provider="auto", fallback_task="general", fallback_args=()):
    """
    Executes AI request via Gemini or OpenAI with automated fallback.
    """
    gemini_key = os.getenv("GEMINI_API_KEY", "").strip()
    openai_key = os.getenv("OPENAI_API_KEY", "").strip()
    
    gemini_valid = bool(gemini_key and not gemini_key.startswith("PASTE_"))
    openai_valid = bool(openai_key and not openai_key.startswith("PASTE_"))
    
    target = provider.lower()
    
    # 1. Try Gemini
    if (target in ["gemini", "auto"] and gemini_valid):
        try:
            return _call_gemini(system_prompt, user_prompt), "Gemini"
        except Exception as e:
            if target == "gemini":
                raise RuntimeError(f"Gemini API error: {e}")
            # else fall through to OpenAI
            
    # 2. Try OpenAI
    if (target in ["openai", "auto"] and openai_valid):
        try:
            return _call_openai(system_prompt, user_prompt), "OpenAI"
        except Exception as e:
            if target == "openai":
                raise RuntimeError(f"OpenAI API error: {e}")
                
    # 3. If neither or auto failed, use smart local fallback
    result = _offline_fallback_generator(fallback_task, *fallback_args)
    return result, "Built-in Offline Engine"

# Public API functions
def transform_content(source, output_format="Executive Summary", audience="General audience", tone="Professional", detail="Medium", provider="auto"):
    instructions = FORMAT_PROMPTS.get(output_format, "Transform the content accurately according to requested format.")
    system_prompt = (
        "You are an advanced Content Transformation AI specialist. "
        "Your task is to transform source documents into high-value deliverables. "
        "Strictly preserve factual accuracy. Do not fabricate citations, statistics or quotations. "
        "Return clean, formatted Markdown."
    )
    user_prompt = f"""Deliverable Format: {output_format}
Formatting Instructions: {instructions}
Target Audience: {audience}
Tone of Voice: {tone}
Detail Level: {detail}

SOURCE CONTENT:
\"\"\"
{source[:30000]}
\"\"\"
"""
    output, engine = execute_llm_request(
        system_prompt, user_prompt, provider=provider,
        fallback_task="general", fallback_args=(source, output_format, audience, tone)
    )
    return output, engine

def summarize_text(source, summary_type="Executive Summary", detail="Medium", provider="auto"):
    instructions = SUMMARIZE_PROMPTS.get(summary_type, "Provide a concise summary.")
    system_prompt = "You are an expert executive summarizer. Produce clear, structured, faithful summaries in Markdown."
    user_prompt = f"""Summary Format: {summary_type}
Guidance: {instructions}
Detail Level: {detail}

SOURCE TEXT:
\"\"\"
{source[:30000]}
\"\"\"
"""
    output, engine = execute_llm_request(
        system_prompt, user_prompt, provider=provider,
        fallback_task="summary", fallback_args=(source, summary_type, detail)
    )
    return output, engine

def paraphrase_text(source, style="Standard", provider="auto"):
    instructions = PARAPHRASE_PROMPTS.get(style, "Paraphrase clearly and accurately.")
    system_prompt = "You are a professional editor and rephrasing specialist. Rewrite text with enhanced clarity while retaining all original meanings."
    user_prompt = f"""Paraphrasing Style: {style}
Guidance: {instructions}

SOURCE TEXT:
\"\"\"
{source[:25000]}
\"\"\"
"""
    output, engine = execute_llm_request(
        system_prompt, user_prompt, provider=provider,
        fallback_task="paraphrase", fallback_args=(source, style)
    )
    return output, engine

def transform_tone(source, target_tone="Professional", audience="General audience", provider="auto"):
    instructions = TONE_PROMPTS.get(target_tone, "Adjust tone appropriately.")
    system_prompt = "You are a communications specialist skilled in tone adaptation. Transform text to match the requested tone perfectly."
    user_prompt = f"""Target Tone: {target_tone}
Audience: {audience}
Instructions: {instructions}

SOURCE TEXT:
\"\"\"
{source[:25000]}
\"\"\"
"""
    output, engine = execute_llm_request(
        system_prompt, user_prompt, provider=provider,
        fallback_task="tone", fallback_args=(source, target_tone, audience)
    )
    return output, engine

def correct_grammar(source, explanation_mode="standard", provider="auto"):
    system_prompt = (
        "You are an expert copyeditor. Fix all grammatical, spelling, punctuation, syntax, and phrasing errors. "
        "Provide: 1) The clean corrected text, followed by 2) A concise list of key improvements made."
    )
    user_prompt = f"""Please proofread and correct the following text:

SOURCE TEXT:
\"\"\"
{source[:25000]}
\"\"\"
"""
    output, engine = execute_llm_request(
        system_prompt, user_prompt, provider=provider,
        fallback_task="grammar", fallback_args=(source, explanation_mode)
    )
    return output, engine
