import os
import cairosvg

OUT = "/app/scripts/logo_output/preview_v4"
os.makedirs(OUT, exist_ok=True)

# Exact plane path from Navbar.jsx, grey (#9ca3af = gray-400), rotated -45deg
# Contrail curve in indigo-500 (#6366f1) matching the CoPilot accent
SVG = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 128 128">
  <rect x="0" y="0" width="128" height="128" rx="28" fill="#ffffff"/>
  <rect x="1.5" y="1.5" width="125" height="125" rx="26.5" fill="none" stroke="#e5e7eb" stroke-width="3"/>
  <!-- indigo contrail behind the plane -->
  <path d="M18 104 C 40 96, 50 88, 62 72" fill="none" stroke="#6366f1" stroke-width="6" stroke-linecap="round" opacity="0.9"/>
  <path d="M14 116 C 34 110, 44 104, 54 92" fill="none" stroke="#a5b4fc" stroke-width="5" stroke-linecap="round" opacity="0.8"/>
  <!-- website plane glyph, gray-500 for contrast, rotated -45 -->
  <g transform="translate(64,52) rotate(-45) scale(3.4) translate(-12,-12)">
    <path d="M21 16v-2l-8-5V3.5A1.5 1.5 0 0 0 11.5 2A1.5 1.5 0 0 0 10 3.5V9l-8 5v2l8-2.5V19l-2 1.5V22l3.5-1 3.5 1v-1.5L13 19v-5.5l8 2.5z" fill="#6b7280"/>
  </g>
</svg>"""

with open(f"{OUT}/icon.svg", "w") as f:
    f.write(SVG)

for size in [16, 48, 128, 1024]:
    cairosvg.svg2png(bytestring=SVG.encode(), write_to=f"{OUT}/icon{size}.png",
                     output_width=size, output_height=size)
print("done", os.listdir(OUT))
