"""
Gemini Vision analysis for construction images and plans.
"""

import json
import time
from pathlib import Path
from typing import Any

from google import genai
from google.genai import types as genai_types
from google.genai.errors import ClientError
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


def _generate_with_retry(
    client: genai.Client,
    settings: Any,
    contents: Any,
) -> Any:
    models = [settings.gemini_model]
    if settings.gemini_fallback_model != settings.gemini_model:
        models.append(settings.gemini_fallback_model)

    last_429: ClientError | None = None

    for model_name in models:
        for attempt in range(settings.gemini_max_retries):
            try:
                return client.models.generate_content(
                    model=model_name,
                    contents=contents,
                    config=genai_types.GenerateContentConfig(
                        response_mime_type="application/json",
                        temperature=0.1,
                    ),
                )
            except ClientError as exc:
                status_code = getattr(exc, "status_code", None)
                if status_code == 404:
                    raise RuntimeError(
                        "Gemini model "
                        f"`{model_name}` is unavailable for project "
                        f"`{settings.google_cloud_project}` in `{settings.gemini_location}`. "
                        "Update GEMINI_MODEL to a currently supported Vertex model, such as "
                        "`gemini-2.5-flash`."
                    ) from exc
                if status_code != 429:
                    raise

                last_429 = exc
                if attempt < settings.gemini_max_retries - 1:
                    time.sleep(2 ** attempt)
                    continue
                break

    raise RuntimeError(
        "Vertex Gemini is temporarily out of capacity for this request after multiple retries. "
        f"Tried `{settings.gemini_model}`"
        + (
            f" and fallback `{settings.gemini_fallback_model}`"
            if settings.gemini_fallback_model != settings.gemini_model
            else ""
        )
        + ". Try again in 1-2 minutes."
    ) from last_429


def analyze_image(image_bytes: bytes, mime_type: str = "image/jpeg") -> dict[str, Any]:
    """
    Send an image to Gemini 2.0 Flash for AEC compliance analysis.

    Returns structured analysis dict.
    """
    settings = get_settings()
    client = genai.Client(
        vertexai=True,
        project=settings.google_cloud_project,
        location=settings.gemini_location,
    )

    image_part = genai_types.Part.from_bytes(data=image_bytes, mime_type=mime_type)

    response = _generate_with_retry(client, settings, [VISION_PROMPT, image_part])

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
