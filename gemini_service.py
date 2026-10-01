import json
import logging
import os
import re
from typing import Dict, Any, List, Optional
from fastapi import HTTPException
from dotenv import load_dotenv

from app.config import get_settings

logger = logging.getLogger("edugenie.gemini")

def get_current_api_key() -> str:
    load_dotenv(override=True)
    settings = get_settings()
    key = settings.gemini_api_key.strip() or os.getenv("GEMINI_API_KEY", "").strip()
    return key

def get_current_model() -> str:
    load_dotenv(override=True)
    settings = get_settings()
    model = settings.gemini_model.strip() or os.getenv("GEMINI_MODEL", "gemini-2.5-flash").strip()
    return model

def get_gemini_client():
    """Returns an authenticated Google GenAI Client instance."""
    api_key = get_current_api_key()
    if not api_key or api_key in ("", "your_gemini_api_key_here"):
        raise HTTPException(
            status_code=400,
            detail="Gemini API Key is missing. Please set a valid GEMINI_API_KEY in your .env file."
        )
    try:
        from google import genai
        return genai.Client(api_key=api_key)
    except ImportError:
        logger.error("google-genai package is not installed.")
        raise HTTPException(
            status_code=500,
            detail="The google-genai SDK package is not installed on the server."
        )
    except Exception as e:
        logger.error(f"Failed to initialize Gemini Client: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to initialize Gemini API client."
        )

def _handle_gemini_exception(e: Exception):
    """Parses Gemini SDK exceptions and converts them to clear HTTP Exceptions."""
    err_str = str(e).lower()
    model_name = get_current_model()
    logger.error(f"Gemini API Exception caught: {type(e).__name__}: {e}")

    if "429" in err_str or "quota" in err_str or "resource_exhausted" in err_str or "rate limit" in err_str:
        raise HTTPException(
            status_code=429,
            detail="Gemini API rate limit or quota exceeded. Please wait a short while and try again."
        )
    elif "api_key" in err_str or "invalid" in err_str or "401" in err_str or "unauthorized" in err_str:
        raise HTTPException(
            status_code=401,
            detail="Invalid Gemini API key. Please check your GEMINI_API_KEY setting in .env."
        )
    elif "404" in err_str or "not found" in err_str or "unsupported model" in err_str:
        raise HTTPException(
            status_code=404,
            detail=f"Model '{model_name}' was not found or is unsupported. Update GEMINI_MODEL in .env."
        )
    else:
        raise HTTPException(
            status_code=500,
            detail=f"Gemini API request failed: {str(e)}"
        )

def _clean_json_text(text: str) -> str:
    """Extracts raw JSON content from markdown code fences if present."""
    text = text.strip()
    match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text, re.IGNORECASE)
    if match:
        return match.group(1).strip()
    return text

def answer_question(question: str, context: Optional[str] = None) -> Dict[str, Any]:
    """Answers a student question using Gemini API."""
    client = get_gemini_client()
    model_name = get_current_model()
    prompt = f"You are EduGenie, an encouraging and expert AI tutor. Answer the student's question clearly and accurately.\n"
    if context:
        prompt += f"Context/Topic: {context}\n"
    prompt += f"Student Question: {question}\n\nAnswer:"

    try:
        from google.genai import types
        response = client.models.generate_content(
            model=model_name,
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.4,
                max_output_tokens=1024,
            )
        )
        answer_text = response.text if response and response.text else "No response generated."
        return {
            "answer": answer_text,
            "sources": ["EduGenie AI Knowledge Base"],
            "model_used": model_name
        }
    except Exception as e:
        _handle_gemini_exception(e)

def explain_concept(concept: str) -> Dict[str, Any]:
    """Generates a beginner-friendly concept explanation using Gemini API."""
    client = get_gemini_client()
    model_name = get_current_model()
    prompt = (
        f"You are EduGenie, a patient AI teacher. Explain the following concept for a beginner learner.\n"
        f"Concept: {concept}\n\n"
        f"Structure your explanation with:\n"
        f"1. A simple 1-sentence analogy or definition.\n"
        f"2. Core breakdown (3-4 bullet points).\n"
        f"3. Real-world example.\n"
        f"4. Quick summary key takeaway."
    )

    try:
        from google.genai import types
        response = client.models.generate_content(
            model=model_name,
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.5,
                max_output_tokens=1024,
            )
        )
        explanation_text = response.text if response and response.text else "No explanation generated."
        return {
            "explanation": explanation_text,
            "mode_used": f"Gemini ({model_name})",
            "warning": None
        }
    except Exception as e:
        _handle_gemini_exception(e)

def generate_quiz(topic: str, num_questions: int = 3) -> Dict[str, Any]:
    """Generates exactly 3 multiple-choice quiz questions with 4 options each using Gemini API."""
    client = get_gemini_client()
    model_name = get_current_model()
    prompt = (
        f"Generate a quiz on the topic: '{topic}'.\n"
        f"You MUST return a valid JSON object with EXACTLY 3 questions.\n"
        f"Each question MUST have:\n"
        f"- 'id': integer (1, 2, or 3)\n"
        f"- 'question': clear question text\n"
        f"- 'options': an array of EXACTLY 4 string options\n"
        f"- 'correct_answer': a string that EXACTLY matches one of the 4 options\n"
        f"- 'explanation': a short sentence explaining why that answer is correct.\n\n"
        f"Format strictly as JSON:\n"
        f"{{\n"
        f'  "questions": [\n'
        f'    {{\n'
        f'      "id": 1,\n'
        f'      "question": "...",\n'
        f'      "options": ["Opt1", "Opt2", "Opt3", "Opt4"],\n'
        f'      "correct_answer": "Opt1",\n'
        f'      "explanation": "..."\n'
        f'    }}\n'
        f'  ]\n'
        f"}}\n"
    )

    try:
        from google.genai import types
        response = client.models.generate_content(
            model=model_name,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                temperature=0.3,
                max_output_tokens=1536,
            )
        )
        
        raw_text = response.text if response and response.text else "{}"
        cleaned = _clean_json_text(raw_text)
        data = json.loads(cleaned)
        
        raw_qs = data.get("questions", [])
        validated_questions = []

        for idx in range(1, 4):
            q_raw = raw_qs[idx - 1] if idx - 1 < len(raw_qs) else {}
            q_text = q_raw.get("question", f"Question {idx} about {topic}?")
            opts = q_raw.get("options", [])
            
            # Ensure exactly 4 options
            if not isinstance(opts, list):
                opts = []
            while len(opts) < 4:
                opts.append(f"Option {len(opts) + 1}")
            opts = [str(o) for o in opts[:4]]
            
            correct = str(q_raw.get("correct_answer", opts[0]))
            
            # Verify correct answer matches an option
            if correct not in opts:
                if correct.isdigit() and 0 <= int(correct) < len(opts):
                    correct = opts[int(correct)]
                elif correct.upper() in ["A", "B", "C", "D"]:
                    letter_map = {"A": 0, "B": 1, "C": 2, "D": 3}
                    correct = opts[letter_map[correct.upper()]]
                else:
                    correct = opts[0]
                    
            expl = q_raw.get("explanation", f"Understanding {topic} helps answer this question.")
            
            validated_questions.append({
                "id": idx,
                "question": q_text,
                "options": opts,
                "correct_answer": correct,
                "explanation": expl
            })

        return {
            "topic": topic,
            "questions": validated_questions,
            "model_used": model_name
        }
    except json.JSONDecodeError as json_err:
        logger.error(f"Failed to parse Gemini Quiz JSON output: {json_err}")
        raise HTTPException(
            status_code=500,
            detail="Failed to parse structured quiz data from Gemini API."
        )
    except Exception as e:
        _handle_gemini_exception(e)

def summarize_text(text: str, length: str = "medium") -> Dict[str, Any]:
    """Summarizes input text using Gemini API."""
    client = get_gemini_client()
    model_name = get_current_model()
    length_guidelines = {
        "short": "1-2 concise bullet points or sentences (under 50 words).",
        "medium": "A clear, structured summary with key points (100-150 words).",
        "detailed": "A thorough summary covering main ideas, sub-points, and conclusions (200+ words)."
    }
    target_guideline = length_guidelines.get(length.lower(), length_guidelines["medium"])
    
    prompt = (
        f"You are EduGenie, an expert educational content summarizer.\n"
        f"Summarize the following text accurately according to this requirement: {target_guideline}\n\n"
        f"Text to summarize:\n{text}\n\nSummary:"
    )

    try:
        from google.genai import types
        response = client.models.generate_content(
            model=model_name,
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.3,
                max_output_tokens=1024,
            )
        )
        summary_text = response.text if response and response.text else "No summary generated."
        return {
            "summary": summary_text,
            "original_length": len(text.split()),
            "summary_length": len(summary_text.split()),
            "model_used": model_name
        }
    except Exception as e:
        _handle_gemini_exception(e)

def generate_learning_path(topic: str, level: str = "beginner", goal: Optional[str] = None) -> Dict[str, Any]:
    """Generates a beginner-to-advanced learning path using Gemini API."""
    client = get_gemini_client()
    model_name = get_current_model()
    prompt = (
        f"Create a step-by-step learning path for the topic: '{topic}'.\n"
        f"User's Current Level: '{level}'.\n"
    )
    if goal:
        prompt += f"User's Specific Goal: '{goal}'.\n"
    
    prompt += (
        f"\nReturn a valid JSON object with an array of 4-5 sequential learning modules.\n"
        f"Format strictly as JSON:\n"
        f"{{\n"
        f'  "modules": [\n'
        f'    {{\n'
        f'      "title": "Module 1: Title",\n'
        f'      "level": "Beginner",\n'
        f'      "summary": "Brief module summary",\n'
        f'      "key_takeaways": ["Takeaway 1", "Takeaway 2"],\n'
        f'      "action_steps": ["Action 1", "Action 2"]\n'
        f'    }}\n'
        f'  ]\n'
        f"}}\n"
    )

    try:
        from google.genai import types
        response = client.models.generate_content(
            model=model_name,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                temperature=0.4,
                max_output_tokens=1536,
            )
        )
        raw_text = response.text if response and response.text else "{}"
        cleaned = _clean_json_text(raw_text)
        data = json.loads(cleaned)
        
        modules = data.get("modules", [])
        validated_modules = []
        for idx, m in enumerate(modules, 1):
            validated_modules.append({
                "title": m.get("title", f"Module {idx}: Fundamentals of {topic}"),
                "level": m.get("level", "Beginner" if idx <= 2 else ("Intermediate" if idx <= 4 else "Advanced")),
                "summary": m.get("summary", f"Learn key concepts for module {idx}."),
                "key_takeaways": m.get("key_takeaways", ["Understand core concepts", "Apply in practice"]),
                "action_steps": m.get("action_steps", ["Read recommended guide", "Complete practical exercise"])
            })

        return {
            "topic": topic,
            "current_level": level,
            "modules": validated_modules,
            "model_used": model_name
        }
    except json.JSONDecodeError as json_err:
        logger.error(f"Failed to parse Gemini Learning Path JSON: {json_err}")
        raise HTTPException(
            status_code=500,
            detail="Failed to parse learning path data from Gemini API."
        )
    except Exception as e:
        _handle_gemini_exception(e)
