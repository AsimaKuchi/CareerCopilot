import os
import cairosvg

OUT = "/app/scripts/logo_output/preview_v4"
os.makedirs(OUT, exist_ok=True)

# Same plane glyph as website navbar, pointing up-right, with contrail
# leading directly out of the plane's tail (matches site branding)
SVG = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 128 128">
  <rect x="0" y="0" width="128" height="128" rx="28" fill="#ffffff"/>
  <rect x="1.5" y="1.5" width="125" height="125" rx="26.5" fill="none" stroke="#e5e7eb" stroke-width="3"/>
  <!-- indigo contrail flowing out of the plane's tail -->
  <path d="M50 74 C 40 88, 30 98, 16 106" fill="none" stroke="#6366f1" stroke-width="6" stroke-linecap="round" opacity="0.9"/>
  <path d="M44 66 C 32 78, 22 86, 12 92" fill="none" stroke="#a5b4fc" stroke-width="4.5" stroke-linecap="round" opacity="0.75"/>
  <!-- website plane glyph, pointing up-right -->
  <g transform="translate(72,48) rotate(45) scale(3.4) translate(-12,-12)">
    <path d="M21 16v-2l-8-5V3.5A1.5 1.5 0 0 0 11.5 2A1.5 1.5 0 0 0 10 3.5V9l-8 5v2l8-2.5V19l-2 1.5V22l3.5-1 3.5 1v-1.5L13 19v-5.5l8 2.5z" fill="#6b7280"/>
  </g>
</svg>"""

with open(f"{OUT}/icon.svg", "w") as f:
    f.write(SVG)

for size in [16, 48, 128, 1024]:
    cairosvg.svg2png(bytestring=SVG.encode(), write_to=f"{OUT}/icon{size}.png",
                     output_width=size, output_height=size)
print("done", os.listdir(OUT))
