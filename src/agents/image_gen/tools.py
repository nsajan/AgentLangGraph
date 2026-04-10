"""Replicate image generation tools for Pruna AI models."""

from __future__ import annotations

import os
from typing import Optional

import replicate
from langchain_core.tools import tool


PRUNA_MODELS = {
    "flux-schnell": "prunaai/flux-schnell",
    "flux-dev": "prunaai/flux.1-dev",
    "flux-juiced": "prunaai/flux.1-juiced",
}

DEFAULT_MODEL = "flux-schnell"


@tool
def generate_image(
    prompt: str,
    model: str = "flux-schnell",
    width: int = 1024,
    height: int = 768,
    num_inference_steps: int = 4,
    guidance_scale: float = 7.5,
) -> str:
    """Generate an image using Pruna AI models on Replicate.

    Args:
        prompt: Detailed image description. Be specific about style, lighting,
                composition, and subject matter for best results.
        model: Which Pruna model to use. Options: flux-schnell (fastest),
               flux-dev (highest quality), flux-juiced (balanced).
        width: Image width in pixels (must be multiple of 64). Default 1024.
        height: Image height in pixels (must be multiple of 64). Default 768.
        num_inference_steps: Number of denoising steps. More = better quality
                            but slower. flux-schnell works great at 4.
        guidance_scale: How closely to follow the prompt (1-20). Higher = more
                        literal. Default 7.5.

    Returns:
        URL of the generated image.
    """
    model_id = PRUNA_MODELS.get(model, PRUNA_MODELS[DEFAULT_MODEL])

    api_token = os.environ.get("REPLICATE_API_TOKEN")
    if not api_token:
        return "Error: REPLICATE_API_TOKEN not set in environment."

    # Ensure dimensions are multiples of 64
    width = (width // 64) * 64
    height = (height // 64) * 64

    try:
        output = replicate.run(
            model_id,
            input={
                "prompt": prompt,
                "width": width,
                "height": height,
                "num_inference_steps": num_inference_steps,
                "guidance_scale": guidance_scale,
            },
        )

        # Output can be a list of FileOutput or a single FileOutput
        if isinstance(output, list):
            url = str(output[0]) if output else "No output"
        else:
            url = str(output)

        return f"Image generated successfully!\nURL: {url}\nModel: {model_id}\nPrompt used: {prompt}"

    except Exception as e:
        return f"Error generating image: {e}"


@tool
def list_pruna_models() -> str:
    """List available Pruna AI image generation models and their characteristics.

    Returns:
        Description of available models.
    """
    return """Available Pruna AI Models:

1. **flux-schnell** (default) — Fastest option, ~3x faster than base FLUX.1 Schnell
   - Best for: Quick iterations, previews, high-volume generation
   - Recommended steps: 4
   - Cost: ~$0.003/image

2. **flux-dev** — Highest quality Pruna model, optimized FLUX.1 Dev
   - Best for: Final quality images, detailed scenes
   - Recommended steps: 20-30
   - Cost: ~$0.012/image

3. **flux-juiced** — Balanced speed and quality
   - Best for: Good quality at reasonable speed
   - Recommended steps: 8-12
   - Cost: ~$0.006/image

Tips for best results:
- Be specific about style: "cinematic", "photorealistic", "8k", "studio lighting"
- Describe composition: "close-up portrait", "wide landscape", "aerial view"
- Mention lighting: "golden hour", "dramatic shadows", "soft diffused light"
- Add quality modifiers: "highly detailed", "professional photography", "sharp focus"
"""
