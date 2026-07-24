"""Generate transparent favicon PNGs — just the indigo plane, no background tile."""
import os
import cairosvg

OUT = "/app/frontend/public"

# Just the plane on a transparent background. No white tile, no border.
# Same glyph and angle as the extension icon.
SVG = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 128 128">
  <g transform="translate(64,64) rotate(45) scale(4.6) translate(-12,-12)">
    <path d="M21 16v-2l-8-5V3.5A1.5 1.5 0 0 0 11.5 2A1.5 1.5 0 0 0 10 3.5V9l-8 5v2l8-2.5V19l-2 1.5V22l3.5-1 3.5 1v-1.5L13 19v-5.5l8 2.5z" fill="#6366f1"/>
  </g>
</svg>"""

for size, name in [
    (16, "favicon-16.png"),
    (48, "favicon-48.png"),
    (128, "favicon-128.png"),
    (180, "apple-touch-icon.png"),
]:
    cairosvg.svg2png(
        bytestring=SVG.encode(),
        write_to=os.path.join(OUT, name),
        output_width=size,
        output_height=size,
    )
    print(f"wrote {name}")

# favicon.ico as 16px png (browsers accept png inside .ico filename fine)
cairosvg.svg2png(
    bytestring=SVG.encode(),
    write_to=os.path.join(OUT, "favicon.ico"),
    output_width=32,
    output_height=32,
)
print("wrote favicon.ico (32px)")
