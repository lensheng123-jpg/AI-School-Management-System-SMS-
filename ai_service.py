"""
AI service for AI-SMS.
Uses Groq for three advisory features:
  1. Neutral decision summary
  2. Evidence gap detection
  3. Options trade-off analysis

Both features are advisory only. The human decides.
"""
import os
import json
from groq import Groq

_client = None
MODEL_NAME = 'openai/gpt-oss-20b'

def _get_client():
    global _client
    if _client is not None:
        return _client

    api_key = os.environ.get('GROQ_API_KEY')
    if not api_key:
        print("[ai_service] GROQ_API_KEY not set.")
        return None

    try:
        _client = Groq(api_key=api_key, timeout=15.0)
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
    client = _get_client()
    if client is None:
        return None

    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=500,
        )
        return (response.choices[0].message.content or "").strip()
    except Exception as e:
        print(f"[ai_service] Groq error: {e}")
        return None


def generate_summary(case, evidence_list):
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
- Keep it factual, brief, and neutral.
"""
    return _call_llm(prompt)


def generate_gaps(case, evidence_list):
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

Return ONLY a JSON array of strings. Example format:
["Item one", "Item two", "Item three"]

Do not include any other text.
"""
    raw = _call_llm(prompt)
    if not raw:
        return None

    try:
        if raw.startswith("```"):
            raw = raw.strip("`")
            if raw.lower().startswith("json"):
                raw = raw[4:].strip()

        gaps = json.loads(raw)
        if isinstance(gaps, list) and all(isinstance(g, str) for g in gaps):
            return gaps[:5]
        return None
    except Exception as e:
        print(f"[ai_service] Gap parsing error: {e}")
        return None


def evaluate_options(case, evidence_list, options_list):
    """
    Feature 3: AI Trade-off Analysis.
    Compares the options against the evidence to highlight pros/cons.
    """
    context = _build_case_context(case, evidence_list)
    
    options_text = "\n".join([f"Option {o['display_order']}: {o['option_text']}" for o in options_list])

    prompt = f"""You are an advisory AI for a school leader.
    
{context}

The leader is considering these options:
{options_text}

Analyze the trade-offs of these options based on the evidence. 
Rules:
- Do NOT pick a "best" option.
- Do NOT recommend a final decision.
- For EACH option, provide one sentence explaining a potential benefit and one sentence explaining a potential risk based on the evidence.
- Note: The issue may involve one student, a whole class, or the entire school. Adjust your analysis accordingly.
"""

    return _call_llm(prompt)