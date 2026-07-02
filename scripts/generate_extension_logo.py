"""One-off logo generator for the Chrome extension.

Uses Gemini Nano Banana (Pro) via Emergent LLM key to produce a 1024x1024
transparent-background logo, then post-processes into the exact icon sizes
Chrome Web Store requires.

Run:
    cd /app/backend && python3 /app/scripts/generate_extension_logo.py
"""
import asyncio
import base64
import os
import sys
from pathlib import Path

sys.path.insert(0, "/app/backend")

from dotenv import load_dotenv
from emergentintegrations.llm.chat import LlmChat, UserMessage
from PIL import Image
from io import BytesIO

load_dotenv("/app/backend/.env")

OUT_DIR = Path("/app/scripts/logo_output")
OUT_DIR.mkdir(parents=True, exist_ok=True)

PROMPT = """Design a clean, modern, professional monogram logo for a career-tech SaaS brand called "MyCareer CoPilot".

Central design: The letters "MCC" in a single row, bold sans-serif geometric typeface (like Inter Black or Poppins Bold).
- The first "M" is solid black (#111111)
- The middle "C" is solid black (#111111)
- The third "C" is solid indigo purple (#6366F1)

Above and to the right of the "MCC" wordmark, a small stylized paper airplane in indigo purple (#6366F1) taking off, with a graceful curved dotted or dashed flight trail arcing behind it (like a jet contrail). The trail should feel light, elegant, aspirational — suggesting career takeoff.

Style: flat vector illustration, crisp geometric shapes, high contrast, iconic and minimal — think Stripe, Linear, Vercel logo aesthetic.

Background: fully transparent (alpha = 0), no background color, no borders, no frame.

Composition: The MCC + airplane composition should be tightly cropped, centered, and fill about 80% of the canvas so it reads clearly at very small sizes (16x16 pixels).

Output: a single, square 1024x1024 PNG with transparent background."""


async def main():
    api_key = os.getenv("EMERGENT_LLM_KEY")
    if not api_key:
        print("ERROR: EMERGENT_LLM_KEY missing")
        return

    chat = LlmChat(
        api_key=api_key,
        session_id="mcc-logo-gen",
        system_message="You are a professional brand designer generating SVG-quality flat vector logos.",
    )
    chat.with_model("gemini", "gemini-3-pro-image-preview").with_params(
        modalities=["image", "text"]
    )

    print("Generating logo (this can take 30-60s)...")
    msg = UserMessage(text=PROMPT)
    text, images = await chat.send_message_multimodal_response(msg)

    if not images:
        print(f"No image returned. Text response: {text[:200] if text else 'none'}")
        return

    img_data = base64.b64decode(images[0]["data"])
    src_path = OUT_DIR / "mcc_logo_1024.png"
    src_path.write_bytes(img_data)
    print(f"Saved source: {src_path}")

    # Post-process into Chrome extension icon sizes.
    src = Image.open(src_path).convert("RGBA")
    print(f"Source image: {src.size} mode={src.mode}")

    for size in (16, 48, 128):
        out = src.resize((size, size), Image.LANCZOS)
        out_path = OUT_DIR / f"icon{size}.png"
        out.save(out_path, "PNG", optimize=True)
        print(f"  Saved {out_path} ({out_path.stat().st_size} bytes)")

    # Chrome Web Store 440x280 store tile (white background so it looks good in listing).
    tile = Image.new("RGBA", (440, 280), (255, 255, 255, 255))
    logo_for_tile = src.resize((240, 240), Image.LANCZOS)
    tile.paste(logo_for_tile, ((440 - 240) // 2, (280 - 240) // 2), logo_for_tile)
    tile_path = OUT_DIR / "store_tile_440x280.png"
    tile.save(tile_path, "PNG", optimize=True)
    print(f"  Saved {tile_path} ({tile_path.stat().st_size} bytes)")

    print("\nDone. Review /app/scripts/logo_output/ before copying to extension.")


if __name__ == "__main__":
    asyncio.run(main())
