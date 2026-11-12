"""
AI service for AI-SMS.
Uses Groq (primary) and Google Gemini (fallback) for three advisory features:
  1. Neutral decision summary
  2. Evidence gap detection
  3. Options trade-off analysis

All features are advisory only. The human decides.
"""
import os
import re
import json
from groq import Groq

_client = None
MODEL_NAME = 'openai/gpt-oss-20b'
GEMINI_MODEL = 'gemini-2.5-flash'


def _get_client():
    global _client
    if _client is not None:
        return _client

    api_key = os.environ.get('GROQ_API_KEY')
    if not api_key:
        print("[ai_service] GROQ_API_KEY not set.")
        return None

    try:
        _client = Groq(api_key=api_key, timeout=20.0)
        return _client
    except Exception as e:
        print(f"[ai_service] Failed to init Groq client: {e}")
        return None


def _build_case_context(case, evidence_list):
    evidence_text = "\n".join([
        f"- [{e['evidence_type']}] {e['text']}"
        for e in evidence_list
    ]) or "- No evidence recorded."

    return f"""Case title: {case['title']}
Category: {case['category']}
Question: {case['decision_question']}
Intended outcome: {case['intended_outcome']}

Evidence:
{evidence_text}"""


def _call_llm(prompt):
    # 1. Primary Provider: Groq
    client = _get_client()
    if client is not None:
        try:
            response = client.chat.completions.create(
                model=MODEL_NAME,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2,
                max_tokens=2048,  # Increased from 1024 so Option 3 never gets cut off
            )
            content = (response.choices[0].message.content or "").strip()
            if content:
                return content
        except Exception as e:
            print(f"[ai_service] Groq error: {e}")

    # 2. Fallback Provider: Google Gemini (if GEMINI_API_KEY is configured)
    gemini_key = os.environ.get('GEMINI_API_KEY')
    if gemini_key:
        try:
            from google import genai
            g_client = genai.Client(api_key=gemini_key)
            g_resp = g_client.models.generate_content(
                model=GEMINI_MODEL,
                contents=prompt,
            )
            if g_resp and g_resp.text:
                return g_resp.text.strip()
        except Exception as e:
            print(f"[ai_service] Gemini fallback error: {e}")

    return None


def generate_summary(case, evidence_list):
    """
    Feature 1: Neutral Decision Summary (3-4 sentences).
    """
    context = _build_case_context(case, evidence_list)
    prompt = f"""You are an advisory assistant for a school leader.

{context}

Write a short, neutral decision summary (3-4 sentences).
Rules:
- State the problem plainly.
- Note what evidence exists.
- Do NOT recommend a decision.
- Do NOT give opinions or value judgements.
- Do NOT speculate about facts that are not present.
- Do NOT use markdown bolding, asterisks, or bullet points.
- Keep it factual, brief, and neutral.
"""
    raw = _call_llm(prompt)
    if not raw:
        return None
    return raw.replace("**", "").strip()


def generate_gaps(case, evidence_list):
    """
    Feature 2: AI-Suggested Evidence Gaps (JSON array of 3-5 short strings).
    """
    context = _build_case_context(case, evidence_list)
    prompt = f"""You are an advisory assistant for a school leader.

{context}

Identify 3 to 5 pieces of information that are MISSING or UNVERIFIED
before this decision can be made.

Rules:
- Each item must be a short phrase (max 12 words).
- Do NOT recommend a decision.
- Do NOT speculate about what the answer might be.
- Only list what is absent or unconfirmed.

Return ONLY a valid JSON array of strings. Example format:
["Item one", "Item two", "Item three"]

Do not include any other text.
"""
    raw = _call_llm(prompt)
    if not raw:
        return None

    try:
        # Robustly extract JSON array even if the model wraps it in text or backticks
        start_idx = raw.find('[')
        end_idx = raw.rfind(']')
        if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
            raw_json = raw[start_idx:end_idx + 1]
        else:
            raw_json = raw.strip("`").strip()

        gaps = json.loads(raw_json)
        if isinstance(gaps, list):
            cleaned = [str(g).strip().lstrip("*-• ") for g in gaps if str(g).strip()]
            return cleaned[:5] if cleaned else None
        return None
    except Exception as e:
        print(f"[ai_service] Gap parsing error: {e}")
        return None


def evaluate_options(case, evidence_list, options_list):
    """
    Feature 3: AI Trade-off Analysis.
    Compares all 3 options against the evidence to highlight pros/cons.
    """
    context = _build_case_context(case, evidence_list)
    options_text = "\n".join([
        f"Option {o['display_order']}: {o['option_text']}"
        for o in options_list
    ])

    prompt = f"""You are an advisory AI for a school leader.

{context}

The leader is considering these options:
{options_text}

Analyze the trade-offs of ALL {len(options_list)} options based on the evidence.
Rules:
- You MUST include all {len(options_list)} options (Option 1, Option 2, and Option 3).
- Do NOT pick a "best" option or rank them.
- Do NOT recommend a final decision.
- Do NOT use markdown asterisks (* or **).
- Keep each Benefit and Risk concise (1 clear sentence, max 25 words).

You MUST follow this EXACT plain-text format for every option:
Option 1
Benefit: [One sentence explaining a potential benefit of Option 1]
Risk: [One sentence explaining a potential risk of Option 1]

Option 2
Benefit: [One sentence explaining a potential benefit of Option 2]
Risk: [One sentence explaining a potential risk of Option 2]

Option 3
Benefit: [One sentence explaining a potential benefit of Option 3]
Risk: [One sentence explaining a potential risk of Option 3]
"""
    return _call_llm(prompt)
