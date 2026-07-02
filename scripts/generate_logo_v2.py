"""Preview-only regeneration of the MCC logo with adjusted design.

Does NOT overwrite anything in /app/browser-extension. Only writes to
/app/scripts/logo_output/preview_v2/ for user review.
"""
import asyncio
import base64
import os
import sys
from pathlib import Path

sys.path.insert(0, "/app/backend")
from dotenv import load_dotenv
from emergentintegrations.llm.chat import LlmChat, UserMessage

load_dotenv("/app/backend/.env")

OUT = Path("/app/scripts/logo_output/preview_v2")
OUT.mkdir(parents=True, exist_ok=True)

PROMPT = """Design a clean, modern, professional monogram logo for a career-tech SaaS brand.

TEXT (foreground layer, on top):
- The three letters "MCC" in a single row
- Bold, geometric sans-serif typeface (like Poppins Black, Inter Black, or Montserrat ExtraBold)
- The first "M" is solid black (#0F0F0F)
- The middle "C" is solid black (#0F0F0F)
- The third "C" is solid indigo purple (#6366F1)
- Letters tightly kerned but not touching, aligned on a single horizontal baseline

BACKGROUND ELEMENT (behind the text):
- A small, side-view stylized COMMERCIAL PASSENGER JET (like a 737 or A320 silhouette), NOT a paper airplane. Small enough that it reads as an icon, not a giant plane.
- The jet is flying from LEFT to RIGHT and is positioned in the upper-left area of the composition
- The jet leaves a bold, curved JET CONTRAIL/JETSTREAM that arcs behind it and passes THROUGH THE TEXT — flowing continuously behind the "MCC" letters and re-emerging on the right side of the composition, then arcing upward and off to the top-right
- The contrail should be a solid, slightly-tapered curved stroke (like a smooth ribbon or brush stroke), NOT a dotted line
- Both the jet and the contrail are the SAME indigo purple color (#6366F1) as the third "C" — so the contrail visually connects to and "becomes" the purple C
- Where the contrail passes behind the black letters, it disappears (occluded by the text) and re-emerges on the other side, creating a sense of speed and depth
- Where the contrail passes behind the purple "C", it can either merge with the C or subtly show behind it

STYLE: flat vector illustration, crisp geometric shapes, high contrast, iconic minimal — Stripe / Linear / Vercel aesthetic. No 3D, no shading, no gradients.

BACKGROUND: fully transparent (alpha channel = 0). No colored background, no border, no frame, no drop shadow.

COMPOSITION: tightly cropped, centered horizontally, filling ~80% of the square canvas so it reads at very small sizes.

OUTPUT: a single square 1024×1024 PNG with transparent background.
"""


async def main():
    api_key = os.getenv("EMERGENT_LLM_KEY")
    chat = LlmChat(
        api_key=api_key,
        session_id="mcc-logo-v2",
        system_message="You are a professional brand designer generating flat vector logos.",
    )
    chat.with_model("gemini", "gemini-3-pro-image-preview").with_params(
        modalities=["image", "text"]
    )
    print("Generating v2 (jet + contrail through text)...")
    msg = UserMessage(text=PROMPT)
    _, images = await chat.send_message_multimodal_response(msg)
    if not images:
        print("No image returned.")
        return
    src = OUT / "mcc_logo_v2_1024.png"
    src.write_bytes(base64.b64decode(images[0]["data"]))
    print(f"Saved: {src} ({src.stat().st_size} bytes)")


if __name__ == "__main__":
    asyncio.run(main())
