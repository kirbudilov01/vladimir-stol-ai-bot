from __future__ import annotations

import base64
import textwrap
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter

from .config import Settings


STYLES = {
    "flowers": "luxury bouquet from a secret admirer, realistic social media story photo",
    "couple": "romantic couple hint, cinematic lifestyle photo, tasteful and realistic",
    "dubai": "Dubai trip atmosphere, premium travel lifestyle, realistic influencer photo",
    "car": "night luxury car pickup, neon city lights, realistic social media photo",
}


def build_prompt(style: str) -> str:
    base = STYLES.get(style, STYLES["flowers"])
    return (
        f"Create a photorealistic viral social-media image based on the uploaded person/reference. "
        f"Scenario: {base}. Keep identity cues from the input when safe, avoid nudity, avoid minors, "
        f"avoid explicit sexual content, make it premium and believable."
    )


class ImageGenerator:
    def __init__(self, settings: Settings):
        self.settings = settings

    async def generate(self, input_path: Path, output_path: Path, style: str) -> str:
        prompt = build_prompt(style)
        if self.settings.generation_provider.lower() == "openai":
            await self._openai_generate(input_path, output_path, prompt)
        else:
            self._mock_generate(input_path, output_path, style)
        return prompt

    def _mock_generate(self, input_path: Path, output_path: Path, style: str) -> None:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        img = Image.open(input_path).convert("RGB")
        img.thumbnail((1024, 1024))
        canvas = Image.new("RGB", (1024, 1024), (8, 10, 24))
        blurred = img.resize((1024, 1024)).filter(ImageFilter.GaussianBlur(18))
        canvas.paste(blurred)
        x = (1024 - img.width) // 2
        y = (1024 - img.height) // 2
        canvas.paste(img, (x, y))
        overlay = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)
        draw.rectangle((0, 800, 1024, 1024), fill=(0, 0, 0, 150))
        text = f"STOL AI demo\\nstyle: {style}\\nconnect OPENAI_API_KEY for real generation"
        draw.text((48, 832), textwrap.fill(text, 36), fill=(132, 255, 245, 255))
        canvas = Image.alpha_composite(canvas.convert("RGBA"), overlay)
        canvas.convert("RGB").save(output_path, quality=94)

    async def _openai_generate(self, input_path: Path, output_path: Path, prompt: str) -> None:
        from openai import AsyncOpenAI

        output_path.parent.mkdir(parents=True, exist_ok=True)
        client = AsyncOpenAI(api_key=self.settings.openai_api_key)
        with input_path.open("rb") as image_file:
            result = await client.images.edit(
                model=self.settings.openai_image_model,
                image=image_file,
                prompt=prompt,
                size="1024x1024",
            )
        data = result.data[0].b64_json
        if not data:
            raise RuntimeError("OpenAI returned no image data")
        output_path.write_bytes(base64.b64decode(data))

