import logging
from typing import Dict, Any
from app.config import settings
from app.services import gemini_service

logger = logging.getLogger("edugenie.local_model")

# Module-level cached model and tokenizer
_tokenizer = None
_model = None
_local_model_status = None

def get_local_model_status() -> Dict[str, Any]:
    """Returns the current loading status of the optional local model."""
    if not settings.enable_local_model:
        return {
            "enabled": False,
            "status": "Disabled via configuration (ENABLE_LOCAL_MODEL=false)"
        }
    global _local_model_status
    if _local_model_status:
        return _local_model_status
    return {
        "enabled": True,
        "status": "Configured (lazy-loading on request)"
    }

def _load_local_model():
    """Attempts to load the LaMini-Flan-T5 model and tokenizer directly."""
    global _tokenizer, _model, _local_model_status
    if _tokenizer is not None and _model is not None:
        return _tokenizer, _model, None

    if not settings.enable_local_model:
        msg = "Local model is disabled in environment settings (ENABLE_LOCAL_MODEL=false)."
        _local_model_status = {"enabled": False, "status": msg}
        return None, None, msg

    try:
        import torch
        from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
    except ImportError as e:
        msg = f"Transformers or PyTorch dependency missing ({str(e)}). Install 'transformers' and 'torch'."
        logger.warning(msg)
        _local_model_status = {"enabled": True, "status": f"Unavailable: {msg}"}
        return None, None, msg

    try:
        model_name = settings.local_model_name
        logger.info(f"Loading local model '{model_name}'...")
        _tokenizer = AutoTokenizer.from_pretrained(model_name)
        _model = AutoModelForSeq2SeqLM.from_pretrained(model_name)
        _local_model_status = {"enabled": True, "status": f"Loaded model '{model_name}' successfully"}
        logger.info("Local model loaded successfully.")
        return _tokenizer, _model, None
    except Exception as e:
        msg = f"Failed to download/load local model '{settings.local_model_name}': {str(e)}"
        logger.error(msg)
        _local_model_status = {"enabled": True, "status": f"Failed: {msg}"}
        return None, None, msg

def explain_with_local_model_or_fallback(concept: str) -> Dict[str, Any]:
    """
    Attempts to generate an explanation using the local LaMini-Flan-T5 model.
    If unavailable or fails, gracefully falls back to Gemini API with an informative warning message.
    """
    tokenizer, model, load_error = _load_local_model()

    if load_error or tokenizer is None or model is None:
        logger.info(f"Local model unavailable ({load_error}). Falling back to Gemini API.")
        fallback_res = gemini_service.explain_concept(concept)
        fallback_res["warning"] = f"Local model unavailable ({load_error}). Gemini was used for explanation."
        fallback_res["mode_used"] = f"Gemini Fallback ({settings.gemini_model})"
        return fallback_res

    try:
        input_text = f"Please explain the concept for a beginner: {concept}"
        inputs = tokenizer(input_text, return_tensors="pt", max_length=512, truncation=True)
        outputs = model.generate(
            **inputs,
            max_new_tokens=256,
            num_beams=2,
            early_stopping=True
        )
        explanation_text = tokenizer.decode(outputs[0], skip_special_tokens=True)

        return {
            "explanation": explanation_text,
            "mode_used": f"Local Model ({settings.local_model_name})",
            "warning": None
        }
    except Exception as e:
        logger.error(f"Error during local model inference: {e}. Falling back to Gemini.")
        fallback_res = gemini_service.explain_concept(concept)
        fallback_res["warning"] = f"Local model execution error ({str(e)}). Gemini was used for explanation."
        fallback_res["mode_used"] = f"Gemini Fallback ({settings.gemini_model})"
        return fallback_res
