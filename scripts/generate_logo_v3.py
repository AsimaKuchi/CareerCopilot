"""Preview-only v3: just the jet + contrail (no letters)."""
import asyncio, base64, os, sys
from pathlib import Path
sys.path.insert(0, "/app/backend")
from dotenv import load_dotenv
from emergentintegrations.llm.chat import LlmChat, UserMessage

load_dotenv("/app/backend/.env")
OUT = Path("/app/scripts/logo_output/preview_v3"); OUT.mkdir(parents=True, exist_ok=True)

PROMPT = """Design a clean, modern, minimalist icon logo for a career-tech SaaS brand.

DESIGN:
- A single, side-view stylized COMMERCIAL PASSENGER JET (like a 737 or A320 silhouette), NOT a paper airplane
- The jet is flying UP and to the RIGHT at roughly a 20-30 degree ascending angle, positioned in the upper-right area of the composition
- The jet is solid indigo purple color (#6366F1)
- Behind and below the jet is a bold, smooth, curved JET CONTRAIL that sweeps up from the lower-left of the canvas, arcs gracefully, and connects to the tail of the jet
- The contrail is a solid, slightly-tapered curved ribbon/stroke (like a smooth calligraphic brushstroke), NOT a dotted line, NOT dashed, thicker at the jet end and slightly thinner at the origin
- The contrail is the SAME indigo purple color (#6366F1) as the jet — creates one flowing shape
- The overall composition should feel like the jet is "taking off" and lifting upward — aspirational, career-launching, forward motion

STYLE: flat vector illustration, crisp geometric shapes, high contrast, iconic minimal — Stripe / Linear / Vercel logo aesthetic. No 3D, no shading, no gradients, no drop shadows, no outlines.

DO NOT INCLUDE ANY LETTERS, TEXT, NUMBERS, OR WORDMARK. This is a pure icon — no MCC, no words at all.

BACKGROUND: fully transparent (alpha = 0). No colored background, no border, no frame.

COMPOSITION: the jet+contrail should fill about 75% of the square canvas, well-centered, so it reads clearly at very small sizes like 16x16 pixels (browser favicon size).

OUTPUT: a single square 1024x1024 PNG with transparent background."""

async def main():
    api_key = os.getenv("EMERGENT_LLM_KEY")
    chat = LlmChat(api_key=api_key, session_id="mcc-logo-v3",
                   system_message="You are a professional brand designer generating flat vector icon logos.")
    chat.with_model("gemini", "gemini-3-pro-image-preview").with_params(modalities=["image", "text"])
    print("Generating v3 (jet + contrail only, no letters)...")
    _, images = await chat.send_message_multimodal_response(UserMessage(text=PROMPT))
    if not images:
        print("No image returned."); return
    (OUT / "jet_only_1024.png").write_bytes(base64.b64decode(images[0]["data"]))
    print(f"Saved: {OUT / 'jet_only_1024.png'}")

asyncio.run(main())
