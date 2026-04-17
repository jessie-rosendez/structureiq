"""
Gemini Vision analysis for construction images and plans.
"""

import json
import base64
from pathlib import Path
from typing import Any

import google.generativeai as genai
from PIL import Image
import io

from app.core.config import get_settings
from app.core.cost_tracker import record_usage


VISION_PROMPT = """
You are an AEC compliance and safety engineer analyzing a construction image.

Analyze and return structured JSON only:
{
  "structural_elements": ["description of visible structural elements"],
  "safety_hazards": [
    {"issue": "", "severity": "HIGH|MEDIUM|LOW", "osha_reference": ""}
  ],
  "compliance_flags": [
    {"issue": "", "standard": "", "section": ""}
  ],
  "recommendations": ["actionable recommendation"],
  "confidence": "HIGH|MEDIUM|LOW",
  "limitations": ["what cannot be determined from this image alone"]
}

Be specific. Reference actual standards. Never fabricate observations.
"""


def analyze_image(image_bytes: bytes, mime_type: str = "image/jpeg") -> dict[str, Any]:
    """
    Send an image to Gemini 1.5 Pro Vision for AEC compliance analysis.

    Returns structured analysis dict.
    """
    settings = get_settings()
    genai.configure(api_key=settings.google_api_key)
    model = genai.GenerativeModel("gemini-1.5-pro-002")

    image_part = {"mime_type": mime_type, "data": base64.b64encode(image_bytes).decode()}

    response = model.generate_content(
        [VISION_PROMPT, image_part],
        generation_config=genai.GenerationConfig(
            response_mime_type="application/json",
            temperature=0.1,
        ),
    )

    raw_text = response.text.strip()
    if raw_text.startswith("```"):
        raw_text = raw_text.split("\n", 1)[-1]
        raw_text = raw_text.rsplit("```", 1)[0].strip()

    try:
        result = json.loads(raw_text)
    except json.JSONDecodeError:
        result = {
            "structural_elements": [],
            "safety_hazards": [],
            "compliance_flags": [],
            "recommendations": [],
            "confidence": "LOW",
            "limitations": ["Vision response could not be parsed"],
        }

    usage = response.usage_metadata
    input_tokens = getattr(usage, "prompt_token_count", 0)
    output_tokens = getattr(usage, "candidates_token_count", 0)
    cost = record_usage(input_tokens, output_tokens)

    result["tokens_used"] = {"input": input_tokens, "output": output_tokens}
    result["cost_usd"] = cost

    return result


def analyze_image_from_path(image_path: str) -> dict[str, Any]:
    path = Path(image_path)
    suffix = path.suffix.lower()
    mime_map = {".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png", ".webp": "image/webp"}
    mime_type = mime_map.get(suffix, "image/jpeg")
    with open(path, "rb") as f:
        return analyze_image(f.read(), mime_type)
