"""
llm_utils.py — All LLM calls via OpenRouter API.
Primary model: meta-llama/llama-3.3-70b-instruct:free
Fallback model: mistralai/mistral-7b-instruct:free
"""

import os
import json
import time
import requests
import streamlit as st

PRIMARY_MODEL = "meta-llama/llama-3.1-70b-instruct"
FALLBACK_MODEL = "mistralai/mistral-7b-instruct:free"
BASE_URL = "https://openrouter.ai/api/v1/chat/completions"


def _get_api_key() -> str:
    try:
        return st.secrets.get("OPENROUTER_API_KEY", "") or os.environ.get("OPENROUTER_API_KEY", "")
    except Exception:
        return os.environ.get("OPENROUTER_API_KEY", "")


def _call_llm(messages: list, model: str = PRIMARY_MODEL, retries: int = 2) -> str:
    """Core LLM call with retry logic and fallback."""
    api_key = _get_api_key()
    if not api_key:
        raise ValueError("OPENROUTER_API_KEY not set.")

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://interviewcoach.ai",
        "X-Title": "InterviewCoach AI",
    }
    payload = {
        "model": model,
        "messages": messages,
        "max_tokens": 1200,
        "temperature": 0.7,
    }

    for attempt in range(retries + 1):
        try:
            resp = requests.post(BASE_URL, headers=headers, json=payload, timeout=45)
            if resp.status_code == 429 and model == PRIMARY_MODEL:
                # Rate limited — try fallback
                return _call_llm(messages, FALLBACK_MODEL, retries=1)
            resp.raise_for_status()
            data = resp.json()
            return data["choices"][0]["message"]["content"].strip()
        except requests.exceptions.Timeout:
            if attempt < retries:
                time.sleep(2)
                continue
            raise
        except Exception as e:
            if attempt < retries:
                time.sleep(1)
                continue
            raise


# ─────────────────────────────────────────────
# 1. Generate a single practice question
# ─────────────────────────────────────────────
def generate_question(job_title: str, companies: list, experience: str, asked_before: list = None) -> str:
    asked_str = "\n".join(asked_before or [])
    companies_str = ", ".join(companies) if companies else "top tech companies"
    messages = [
        {
            "role": "system",
            "content": (
                "You are an expert technical interviewer. Generate exactly ONE interview question. "
                "Return only the question text — no numbering, no preamble, no quotes."
            ),
        },
        {
            "role": "user",
            "content": (
                f"Generate one interview question for a {experience} {job_title} candidate "
                f"targeting {companies_str}.\n"
                f"Mix question types: Behavioral, Technical, Situational, Company-Specific.\n"
                f"Do NOT repeat these questions:\n{asked_str}\n"
                f"Return only the question."
            ),
        },
    ]
    return _call_llm(messages)


# ─────────────────────────────────────────────
# 2. Generate AI feedback on a practice answer
# ─────────────────────────────────────────────
def generate_feedback(question: str, transcript: str, scores: dict) -> dict:
    messages = [
        {
            "role": "system",
            "content": (
                "You are an expert interview coach. Analyze the candidate's answer and return ONLY valid JSON. "
                "No markdown, no code fences, no preamble. Return exactly this structure:\n"
                '{"what_went_well": ["point1","point2","point3"], '
                '"areas_to_improve": ["point1","point2","point3"], '
                '"ideal_answer_structure": ["step1","step2","step3","step4"], '
                '"example_strong_answer": "2-3 sentence example", '
                '"specific_tips": ["tip1","tip2"], '
                '"filler_word_advice": "one sentence advice on filler words"}'
            ),
        },
        {
            "role": "user",
            "content": (
                f"Interview Question: {question}\n\n"
                f"Candidate's Answer: {transcript}\n\n"
                f"Local Analysis Scores:\n"
                f"- Overall: {scores.get('overall_score', 0)}/100\n"
                f"- Clarity: {scores.get('clarity_score', 0)}/100\n"
                f"- Confidence: {scores.get('confidence_score', 0)}/100\n"
                f"- Word Count: {scores.get('word_count', 0)} words\n"
                f"- Filler Words Detected: {scores.get('total_fillers', 0)}\n\n"
                f"Provide structured feedback as JSON."
            ),
        },
    ]
    raw = _call_llm(messages)
    return _parse_json(raw, _default_feedback())


# ─────────────────────────────────────────────
# 3. Score an answer with AI (replaces hardcoded local scoring)
# ─────────────────────────────────────────────
def score_answer_with_ai(question: str, transcript: str, local_analysis: dict) -> dict:
    """
    Uses OpenRouter AI to evaluate the candidate's answer and return
    meaningful scores based on actual content quality.

    Returns a dict with keys:
      overall_score, clarity_score, confidence_score,
      relevance_score, structure_score, score_reasoning
    Falls back to local analysis scores on failure.
    """
    messages = [
        {
            "role": "system",
            "content": (
                "You are an expert interview evaluator. Score the candidate's answer "
                "based on its actual content quality. Return ONLY valid JSON — no markdown, "
                "no code fences, no preamble. Use this exact structure:\n"
                '{"overall_score": 0-100, '
                '"clarity_score": 0-100, '
                '"confidence_score": 0-100, '
                '"relevance_score": 0-100, '
                '"structure_score": 0-100, '
                '"score_reasoning": "1-2 sentence explanation of the overall score"}\n\n'
                "Scoring rubric:\n"
                "- overall_score: Holistic quality of the answer (content, delivery, relevance)\n"
                "- clarity_score: How clearly and concisely the answer is expressed\n"
                "- confidence_score: Evidence of confidence via specific examples, metrics, ownership language\n"
                "- relevance_score: How directly the answer addresses the specific question asked\n"
                "- structure_score: Logical flow and organisation (e.g. STAR method for behavioral questions)\n\n"
                "Be honest and calibrated. A vague or off-topic answer should score 20-40. "
                "A decent but unstructured answer: 45-65. A strong, specific, well-structured answer: 70-90. "
                "An exceptional answer with metrics and clear impact: 91-100."
            ),
        },
        {
            "role": "user",
            "content": (
                f"Interview Question: {question}\n\n"
                f"Candidate's Answer: {transcript}\n\n"
                f"Additional context from local analysis:\n"
                f"- Word count: {local_analysis.get('word_count', 0)} words\n"
                f"- Filler words detected: {local_analysis.get('total_fillers', 0)} "
                f"({list(local_analysis.get('filler_words', {}).keys())})\n\n"
                f"Evaluate the answer content and return scores as JSON only."
            ),
        },
    ]
    try:
        raw = _call_llm(messages)
        result = _parse_json(raw, {})
        # Validate all required keys are present and are integers 0-100
        required_keys = ["overall_score", "clarity_score", "confidence_score",
                         "relevance_score", "structure_score", "score_reasoning"]
        if all(k in result for k in required_keys):
            # Clamp scores to 0-100
            for key in ["overall_score", "clarity_score", "confidence_score",
                        "relevance_score", "structure_score"]:
                result[key] = max(0, min(100, int(result[key])))
            return result
    except Exception:
        pass

    # Fallback: return local scores so UI never breaks
    return {
        "overall_score": local_analysis.get("overall_score", 50),
        "clarity_score": local_analysis.get("clarity_score", 50),
        "confidence_score": local_analysis.get("confidence_score", 50),
        "relevance_score": 50,
        "structure_score": 50,
        "score_reasoning": "AI scoring unavailable — showing estimated scores.",
    }


# ─────────────────────────────────────────────
# 4. Generate a 15-question bank  (was 3)
# ─────────────────────────────────────────────
def generate_question_bank(job_title: str, companies: list, experience: str) -> list:
    companies_str = ", ".join(companies) if companies else "top tech companies"
    messages = [
        {
            "role": "system",
            "content": (
                "You are an expert interview coach. Return ONLY a valid JSON array of 15 questions. "
                "No markdown, no code fences. Each item must have: "
                '"question", "category" (Behavioral/Technical/Situational/Company-Specific), '
                '"difficulty" (Easy/Medium/Hard), "why_asked" (one sentence).'
            ),
        },
        {
            "role": "user",
            "content": (
                f"Generate 15 interview questions for a {experience} {job_title} "
                f"targeting {companies_str}. "
                f"Mix: 5 Behavioral, 5 Technical, 3 Situational, 2 Company-Specific. "
                f"Vary difficulty. Return as JSON array only."
            ),
        },
    ]
    raw = _call_llm(messages)
    result = _parse_json(raw, [])
    if isinstance(result, list) and len(result) > 0:
        return result
    return _default_question_bank(job_title)


# ─────────────────────────────────────────────
# 4. Generate a coding problem
# ─────────────────────────────────────────────
def generate_coding_question(job_title: str, companies: list, experience: str, asked_titles: list = None) -> dict:
    companies_str = ", ".join(companies) if companies else "top tech companies"
    asked_str = ", ".join(asked_titles or [])
    messages = [
        {
            "role": "system",
            "content": (
                "You are a technical interviewer. Return ONLY a valid JSON object for a coding problem. "
                "No markdown fences. Structure: "
                '"title", "difficulty" (Easy/Medium/Hard), "topic" (e.g. Array/HashMap/Tree), '
                '"company", "description", '
                '"examples": [{"input":"...","output":"...","explanation":"..."}], '
                '"constraints": ["..."], "hint": "one sentence hint", '
                '"starter_code": {"python":"...","javascript":"...","java":"...","cpp":"..."}, '
                '"optimal_approach": "brief description"'
            ),
        },
        {
            "role": "user",
            "content": (
                f"Create a coding interview problem for a {experience} {job_title} at {companies_str}. "
                f"Do NOT use these problems: {asked_str}. "
                f"Include realistic starter code for all 4 languages with function signatures only (body as pass/return null). "
                f"Return only JSON."
            ),
        },
    ]
    raw = _call_llm(messages)
    return _parse_json(raw, _default_coding_problem())


# ─────────────────────────────────────────────
# 5. Get AI code review / feedback
# ─────────────────────────────────────────────
def get_code_feedback(problem: dict, user_code: str, language: str) -> dict:
    messages = [
        {
            "role": "system",
            "content": (
                "You are a senior software engineer reviewing interview code. "
                "Return ONLY valid JSON with this exact structure:\n"
                '{"score": 0-100, '
                '"verdict": "Optimal|Good|Average|Needs Work", '
                '"user_time_complexity": "O(?)", '
                '"user_space_complexity": "O(?)", '
                '"optimal_time_complexity": "O(?)", '
                '"optimal_space_complexity": "O(?)", '
                '"what_is_correct": ["point1","point2","point3"], '
                '"improvements": ["point1","point2","point3"], '
                '"optimal_approach": "explanation in 2-3 sentences", '
                '"optimal_solution": "complete working code as a string"}'
            ),
        },
        {
            "role": "user",
            "content": (
                f"Problem: {problem.get('title','')}\n"
                f"Description: {problem.get('description','')}\n\n"
                f"Candidate's {language} solution:\n{user_code}\n\n"
                f"Review this solution thoroughly. Provide the complete optimal solution in {language}."
            ),
        },
    ]
    raw = _call_llm(messages)
    return _parse_json(raw, _default_code_feedback())


# ─────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────
def _parse_json(raw: str, default):
    """Safely parse JSON from LLM output, stripping markdown fences if present."""
    if not raw:
        return default
    cleaned = raw.strip()
    if cleaned.startswith("```"):
        lines = cleaned.split("\n")
        cleaned = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:])
    try:
        return json.loads(cleaned)
    except Exception:
        # Try to extract JSON substring
        start = cleaned.find("{") if "{" in cleaned else cleaned.find("[")
        end = cleaned.rfind("}") + 1 if "{" in cleaned else cleaned.rfind("]") + 1
        if start >= 0 and end > start:
            try:
                return json.loads(cleaned[start:end])
            except Exception:
                pass
    return default


def _default_feedback():
    return {
        "what_went_well": ["Answer was provided", "Topic was addressed"],
        "areas_to_improve": ["Add more specific examples", "Structure using STAR method", "Reduce filler words"],
        "ideal_answer_structure": ["Situation (context)", "Task (your role)", "Action (what you did)", "Result (outcome with numbers)"],
        "example_strong_answer": "Provide a concise answer using the STAR method with specific metrics.",
        "specific_tips": ["Practice out loud daily", "Record yourself and review"],
        "filler_word_advice": "Pause and breathe instead of using filler words — silence is professional.",
    }


def _default_code_feedback():
    return {
        "score": 50,
        "verdict": "Average",
        "user_time_complexity": "O(n²)",
        "user_space_complexity": "O(1)",
        "optimal_time_complexity": "O(n)",
        "optimal_space_complexity": "O(n)",
        "what_is_correct": ["Approach is understandable"],
        "improvements": ["Optimize time complexity", "Add edge case handling"],
        "optimal_approach": "Consider using a hash map to reduce time complexity.",
        "optimal_solution": "# Optimal solution here\npass",
    }


def _default_coding_problem():
    return {
        "title": "Two Sum",
        "difficulty": "Easy",
        "topic": "Array / HashMap",
        "company": "Google",
        "description": "Given an array of integers nums and a target, return indices of two numbers that add up to target.",
        "examples": [{"input": "nums = [2,7,11,15], target = 9", "output": "[0,1]", "explanation": "2+7=9"}],
        "constraints": ["2 ≤ nums.length ≤ 10⁴", "Only one valid answer"],
        "hint": "Try using a hash map to store complements.",
        "starter_code": {
            "python": "def two_sum(nums, target):\n    pass",
            "javascript": "function twoSum(nums, target) {\n    // Your code here\n}",
            "java": "class Solution {\n    public int[] twoSum(int[] nums, int target) {\n        return new int[]{};\n    }\n}",
            "cpp": "class Solution {\npublic:\n    vector<int> twoSum(vector<int>& nums, int target) {\n        return {};\n    }\n};",
        },
        "optimal_approach": "Use a hash map for O(n) time complexity.",
    }


def _default_question_bank(job_title: str) -> list:
    return [
        {"question": f"Tell me about yourself and why you want to be a {job_title}.", "category": "Behavioral", "difficulty": "Easy", "why_asked": "Sets the tone for the interview."},
        {"question": "Describe a challenging project and how you overcame obstacles.", "category": "Behavioral", "difficulty": "Medium", "why_asked": "Tests problem-solving and resilience."},
        {"question": "How do you handle tight deadlines?", "category": "Situational", "difficulty": "Medium", "why_asked": "Evaluates time management skills."},
        {"question": "Explain the difference between a stack and a queue.", "category": "Technical", "difficulty": "Easy", "why_asked": "Core data structures knowledge."},
        {"question": "What interests you most about our company?", "category": "Company-Specific", "difficulty": "Easy", "why_asked": "Tests culture fit and research."},
    ]