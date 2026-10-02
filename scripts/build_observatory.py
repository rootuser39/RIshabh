#!/usr/bin/env python3
"""Rebuild the self-contained README artwork with Python 3 (stdlib only)."""

from html import escape
from math import cos, sin, pi
from pathlib import Path
import random
import re
from void_dragon import DRAGON_CSS, dragon, sparks

OUT = Path(__file__).resolve().parents[1] / "assets"
INK, PAPER, MUTED, ACCENT = "#090810", "#f1eef8", "#a09aaf", "#bdacff"


def text(x, y, value, size=16, color=PAPER, weight=400, extra="", mono=False):
    font = "'DejaVu Sans Mono',monospace" if mono else "Arial,Helvetica,sans-serif"
    return (f'<text x="{x}" y="{y}" fill="{color}" font-family="{font}" '
            f'font-size="{size}" font-weight="{weight}" {extra}>{escape(value)}</text>')


def svg(name, width, height, title, body, desc=""):
    OUT.mkdir(parents=True, exist_ok=True)
    dragon_css = DRAGON_CSS if 'dragon-hover' in body else ''
    artwork = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-labelledby="title desc">
<title id="title">{escape(title)}</title><desc id="desc">{escape(desc or title)}</desc>
<defs>
 <radialGradient id="space"><stop stop-color="#211831"/><stop offset="1" stop-color="{INK}"/></radialGradient>
 <linearGradient id="metal" x1="0" y1="0" x2="1" y2="1"><stop stop-color="#494252"/><stop offset=".32" stop-color="#dad3e2"/><stop offset=".5" stop-color="#f5f1ff"/><stop offset=".72" stop-color="#776b81"/><stop offset="1" stop-color="#2b2432"/></linearGradient>
 <linearGradient id="trail"><stop stop-color="{ACCENT}" stop-opacity="0"/><stop offset="1" stop-color="{ACCENT}"/></linearGradient>
 <radialGradient id="void"><stop offset=".7" stop-color="#030207"/><stop offset="1" stop-color="#100b19"/></radialGradient>
 <filter id="glow" x="-100%" y="-100%" width="300%" height="300%"><feGaussianBlur stdDeviation="3"/></filter>
 <pattern id="grid" width="48" height="48" patternUnits="userSpaceOnUse"><path d="M 48 0 H 0 V 48" fill="none" stroke="#c6b8d9" stroke-opacity=".05" stroke-width="1"/></pattern>
</defs>
<style>
 .turn {{ animation: turn 42s linear infinite; }}
 .counter {{ animation: turn 64s linear infinite reverse; }}
 .slow {{ animation: turn 90s linear infinite; }}
 .signal {{ animation: flow 10s linear infinite; }}
 .breathe {{ animation: breathe 6s ease-in-out infinite; }}
 .blink {{ animation: breathe 4s ease-in-out infinite; }}
 @keyframes turn {{ to {{ transform: rotate(360deg); }} }}
 @keyframes flow {{ to {{ stroke-dashoffset: -400; }} }}
 @keyframes breathe {{ 0%,100% {{ opacity:.35; }} 50% {{ opacity:.95; }} }}
 @media (prefers-reduced-motion: reduce) {{ .turn,.counter,.slow,.signal,.breathe,.blink {{ animation:none !important; }} }}
{dragon_css}
</style>
<rect width="100%" height="100%" rx="18" fill="{INK}"/>
{body}
<rect x=".5" y=".5" width="{width-1}" height="{height-1}" rx="18" fill="none" stroke="#30283f"/>
</svg>\n'''
    (OUT / name).write_text(artwork, encoding="utf-8")
    # Embedded SVG media preferences are not propagated by every browser.
    # README <picture> sources select these animation-free assets directly.
    still = OUT / 'still'
    still.mkdir(exist_ok=True)
    still_css = '<style>.wing-mid,.wing-low,.void-breath{opacity:0}.wing-open,.dragon-eye{opacity:1}.void-spark{opacity:.35}</style>'
    still_artwork = re.sub(r'<style>.*?</style>', still_css, artwork, flags=re.S)
    (still / name).write_text(still_artwork, encoding="utf-8")


def stars(width, height, count=75):
    rng = random.Random(39)
    return "".join(f'<circle cx="{rng.uniform(25,width-25):.1f}" cy="{rng.uniform(20,height-20):.1f}" r="{rng.choice([.6,.8,1,1.4])}" fill="#dbe6d9" opacity="{rng.uniform(.15,.65):.2f}"/>' for _ in range(count))


def singularity(cx, cy, scale=1):
    # An abstract orbital sculpture, not a physical simulation or a data chart.
    parts = [f'<g transform="translate({cx} {cy}) scale({scale})">',
             '<circle r="290" fill="url(#space)"/>']
    for r in [214, 246, 278]:
        parts.append(f'<circle r="{r}" fill="none" stroke="#3e334d" stroke-width=".8" stroke-dasharray="2 9"/>')
    parts.append('<g class="slow">')
    for i in range(72):
        a = i * pi / 36
        r2 = 265 if i % 6 == 0 else 260
        parts.append(f'<path d="M {cos(a)*254:.2f} {sin(a)*254:.2f} L {cos(a)*r2:.2f} {sin(a)*r2:.2f}" stroke="#887d96" stroke-width="1" opacity=".55"/>')
    parts.append('</g><g transform="rotate(-24)">')
    for i in range(22):
        rx, ry = 194 + i * 3.4, 47 + i * 1.48
        parts.append(f'<ellipse rx="{rx:.1f}" ry="{ry:.1f}" fill="none" stroke="url(#metal)" stroke-width="{1.1 if i%4 else 1.8}" opacity="{.18 + .32*(1-abs(i-10)/12):.2f}"/>')
    parts.append('</g><circle r="135" fill="url(#void)" stroke="#433650" stroke-width="1"/>')
    for i in range(18):
        r = 128 + i * 1.65
        parts.append(f'<circle r="{r:.1f}" fill="none" stroke="url(#metal)" stroke-width="{.65 if i%4 else 1.2}" opacity="{max(.1,.62-i*.027):.2f}"/>')
    parts += ['<circle r="126" fill="#030207"/>',
              '<g class="turn"><circle r="144" fill="none" stroke="#e2dcf4" stroke-width="2.1" stroke-dasharray="190 714"/><circle cx="144" r="3" fill="#f0f1ec"/></g>',
              f'<g class="counter"><circle r="181" fill="none" stroke="{ACCENT}" stroke-width="1.25" stroke-dasharray="35 1102" opacity=".7"/><circle cx="181" r="4" fill="{ACCENT}"/><circle cx="181" r="9" fill="{ACCENT}" opacity=".25" filter="url(#glow)"/></g>',
              '<g transform="rotate(-24)">']
    for i in range(18):
        rx, ry = 191+i*4, 48+i*1.65
        parts.append(f'<path d="M {-rx} 0 A {rx} {ry} 0 0 0 {rx} 0" fill="none" stroke="url(#metal)" stroke-width="{1 if i%3 else 1.7}" opacity="{.28 + .4*(1-abs(i-8)/10):.2f}"/>')
    parts += ['</g>', text(0, -7, "Ω", 35, "#d0c6df", 400, 'text-anchor="middle"'),
              text(0, 18, "BELOW THE SURFACE", 8, "#7f708f", 400, 'text-anchor="middle" letter-spacing="2"', mono=True),
              '<path d="M -11 -195 H 11 M 0 -206 V -184 M -11 195 H 11 M 0 184 V 206" stroke="#776984" stroke-width="1"/>',
              '</g>']
    return "".join(parts)


def hero(mobile=False):
    w,h = (640,930) if mobile else (1200,650)
    body = '<rect x="1" y="1" width="99.8%" height="99.7%" rx="18" fill="url(#grid)"/>' + stars(w,h)
    if mobile:
        body += text(36,48,"FIELD RECORD / 039",14,MUTED,extra='letter-spacing="2"',mono=True)
        body += text(36,133,"RISHABH D.",70,PAPER,700,extra='letter-spacing="-3"')
        body += text(38,175,"ARCHITECT. ARTIST. SCIENTIST.",15,ACCENT,extra='letter-spacing="2"',mono=True)
        body += singularity(320,433,.82)
        body += sparks(357,460,1)
        body += dragon(365,458,3.7)
        body += text(433,703,"VOID DRAGON / 01",11,ACCENT,extra='letter-spacing="1"',mono=True)
        body += '<path d="M 36 742 H 604" stroke="#30283f"/>'
        body += text(36,793,"THE LAYER BENEATH",31,PAPER,700,extra='letter-spacing="-1"')
        body += text(36,835,"INTELLIGENCE.",40,PAPER,700,extra='letter-spacing="-1"')
        body += text(36,888,"AI / NETWORKS / AUTONOMOUS SYSTEMS",13,MUTED,mono=True)
    else:
        body += singularity(935,287,.86)
        body += sparks(900,365,1.15)
        body += dragon(906,354,4)
        body += f'<path d="M 48 48 H 62" stroke="{ACCENT}" stroke-width="2"/>'
        body += text(76,53,"FIELD RECORD / 039",13,MUTED,extra='letter-spacing="2"',mono=True)
        body += text(48,171,"RISHABH",99,PAPER,700,extra='letter-spacing="-5"')
        body += text(48,269,"D.",99,PAPER,700,extra='letter-spacing="-5"')
        body += text(51,311,"ARCHITECT. ARTIST. SCIENTIST.",13,ACCENT,extra='letter-spacing="2"',mono=True)
        body += '<path d="M 50 350 H 530" stroke="#30283f"/>'
        body += text(48,403,"THE LAYER BENEATH",31,PAPER,700,extra='letter-spacing="-.7"')
        body += text(48,447,"INTELLIGENCE.",39,PAPER,700,extra='letter-spacing="-1"')
        body += text(50,488,"AI infrastructure / Networks / Autonomous systems",13,MUTED,mono=True)
        body += text(702,614,"THE VOID OBSERVATORY",11,MUTED,extra='letter-spacing="2"',mono=True)
        body += text(979,599,"VOID DRAGON / 01",11,ACCENT,extra='letter-spacing="1"',mono=True)
        body += f'<circle cx="1127" cy="48" r="4" fill="{ACCENT}" class="blink"/>'
        body += text(50,607,"ROOTUSER39",12,MUTED,extra='letter-spacing="2"',mono=True)
    svg("observatory-mobile.svg" if mobile else "observatory.svg",w,h,"Rishabh D. — The Void Observatory",body,"An original pixel-art Void Dragon hovers beside a silver event horizon. Its wings beat, its cyan eye blinks, its tail sways, and a faint breath of void particles drifts away. Architect. Artist. Scientist. AI infrastructure, networking and autonomous systems. Reduced-motion settings show a still illustration.")


def card(name, number, title, subtitle, tags, art, stage="EXPERIMENTAL SYSTEM"):
    body = '<rect x="1" y="1" width="558" height="238" rx="18" fill="url(#grid)"/>'
    body += text(28,34,f"{number} / {stage}",10,MUTED,extra='letter-spacing="1.5"',mono=True)
    body += text(28,96,title,42,PAPER,700,extra='letter-spacing="-1.5"')
    body += text(29,134,subtitle,17,MUTED)
    body += text(29,203,tags,10,ACCENT,extra='letter-spacing=".5"',mono=True)
    body += '<path d="M 29 160 H 335" stroke="#30283f"/>'
    body += '<path d="M 511 30 H 531 V 50 M 531 30 L 509 52" fill="none" stroke="#9c8eaf" stroke-width="1.5"/>'
    body += '<g transform="translate(445 125)">'+art+'</g>'
    svg(name,560,240,title+" — "+subtitle,body)


def project_cards():
    cortex = '<g transform="translate(0 -9)">'
    for i in range(5):
        y=i*20-30
        cortex += f'<path d="M -60 {y} L 0 {y-26} L 60 {y} L 0 {y+26} Z" fill="{INK}" stroke="{ACCENT if i==0 else "#8c809c"}" stroke-width="1.3"/>'
    cortex += '</g><path d="M 0 -76 V 83" fill="none" stroke="#bdacff" stroke-width="2" stroke-dasharray="4 16" class="signal"/>'
    card("cortex.svg","01","CORTEX Ω","Intelligence, from intent to compute.","AGENTS / INFERENCE / RUNTIMES",cortex)
    argus='<path d="M 0 -69 L 58 -46 V -4 C 58 33 30 58 0 76 C -30 58 -58 33 -58 -4 V -46 Z" fill="none" stroke="#8f809f" stroke-width="1.2"/>'
    argus+='<path d="M -43 0 Q 0 -46 43 0 Q 0 46 -43 0 Z" fill="none" stroke="#d5cbe5" stroke-width="1.3"/><circle r="15" fill="none" stroke="#bdacff"/><circle r="5" fill="#bdacff" class="breathe"/><path d="M -57 47 H 57" stroke="#bdacff" stroke-dasharray="6 9" class="signal"/>'
    card("argus.svg","02","ARGUS","Intent. Permission. Execution.","PLANNING / ROUTING / MEMORY",argus)
    fabric=''
    for x in [-54,0,54]:
        for x2 in [-54,0,54]:
            fabric+=f'<path d="M {x} -45 L {x2} 45" stroke="#6d5f80" stroke-width=".85" fill="none"/>'
    fabric+='<path d="M -54 -45 L 54 45 M 54 -45 L -54 45" stroke="#bdacff" stroke-width="2" fill="none" stroke-dasharray="5 30" class="signal"/>'
    for y in [-45,45]:
        for x in [-54,0,54]:
            fabric+=f'<rect x="{x-10}" y="{y-10}" width="20" height="20" rx="4" fill="{INK}" stroke="#c3b3d5"/>'
    card("fabric.svg","03","AI FABRIC LAB","The conversation between GPUs.","CONGESTION / COLLECTIVES / TELEMETRY",fabric)
    aegis='<circle r="65" fill="none" stroke="#342b46"/><circle r="42" fill="none" stroke="#625773" stroke-dasharray="3 6"/><g class="turn"><path d="M 0 0 L 0 -65 A 65 65 0 0 1 56 -32 Z" fill="#bdacff" opacity=".10"/><path d="M 0 0 L 0 -65" stroke="#bdacff" stroke-width="1.5"/></g><path d="M -74 8 H -41 L -29 -16 L -11 31 L 5 -5 H 30 L 38 -27 L 52 8 H 74" fill="none" stroke="#e4dcf3" stroke-width="1.8"/><circle cx="38" cy="-27" r="4" fill="#bdacff" class="breathe"/>'
    card("aegisnet.svg","04","AEGISNET","Break. Observe. Diagnose.","NETWORKS / FAILURE / AUTOMATION",aegis,stage="EARLY SCAFFOLD")


def signal_rail():
    # A looping artistic motif. It deliberately contains no fabricated metrics.
    body = text(28,35,"EXECUTION LEAVES A TRACE.",12,MUTED,extra='letter-spacing="2"',mono=True)
    body += '<path d="M 28 68 H 134 L 163 45 L 190 91 L 225 32 L 258 68 H 378 L 405 48 L 439 85 L 466 56 L 485 68 H 690 L 718 45 L 748 89 L 780 35 L 817 68 H 1172" stroke="#625472" fill="none" stroke-width="1.2"/>'
    body += '<path d="M 28 68 H 134 L 163 45 L 190 91 L 225 32 L 258 68 H 378 L 405 48 L 439 85 L 466 56 L 485 68 H 690 L 718 45 L 748 89 L 780 35 L 817 68 H 1172" stroke="#bdacff" fill="none" stroke-width="2" stroke-dasharray="50 350" class="signal"/>'
    svg("signal.svg",1200,112,"Execution leaves a trace",body,"A decorative moving signal trace, not live telemetry.")


def companion():
    body = stars(640,640,55)
    body += '<circle cx="320" cy="302" r="215" fill="url(#space)"/>'
    body += '<g transform="translate(320 302)"><circle r="196" fill="none" stroke="#4a3a61" stroke-dasharray="1 9"/><g class="void-orbit"><circle r="205" fill="none" stroke="#bca4e0" stroke-dasharray="32 1256"/><rect x="202" y="-3" width="6" height="6" fill="#82eced"/></g></g>'
    body += '<ellipse cx="325" cy="494" rx="129" ry="8" fill="#6b498c" opacity=".16" class="breathe"/>'
    body += sparks(123,202,1.7)
    body += dragon(144,170,5.5)
    body += text(320,558,"VOID DRAGON",26,PAPER,700,'text-anchor="middle" letter-spacing="4"')
    body += text(320,594,"AN OBSERVATORY COMPANION / 01",12,ACCENT,extra='text-anchor="middle" letter-spacing="1.5"',mono=True)
    svg("void-dragon.svg",640,640,"Void Dragon — an observatory companion",body,"An original purple pixel-art dragon with silver horns, cyan eyes, a curved tail and animated bat wings. It floats, blinks and occasionally exhales small void particles. Reduced-motion settings reveal a still frame.")


def footer(mobile=False):
    w,h = (640,404) if mobile else (1200,214)
    body = stars(w,h,32)
    body += '<rect width="100%" height="100%" rx="18" fill="url(#grid)"/>'
    if mobile:
        body += sparks(196,63,.85)
        body += dragon(211,20,3.4)
        body += text(320,278,"CURIOSITY HAS TEETH.",29,PAPER,700,'text-anchor="middle" letter-spacing="-1"')
        body += text(320,318,"Follow the signal.",18,MUTED,extra='text-anchor="middle"')
        body += text(320,367,"FIELD RECORD / 039",11,ACCENT,extra='text-anchor="middle" letter-spacing="2"',mono=True)
    else:
        body += sparks(45,57,.8)
        body += dragon(52,28,2.8)
        body += text(295,86,"CURIOSITY HAS TEETH.",32,PAPER,700,extra='letter-spacing="-1"')
        body += text(296,125,"Follow the signal. Build what’s underneath.",17,MUTED)
        body += text(296,179,"FIELD RECORD / 039",11,ACCENT,extra='letter-spacing="2"',mono=True)
        body += '<path d="M 904 43 V 171" stroke="#30283f"/><g transform="translate(1050 105)"><circle r="57" fill="none" stroke="#30283f"/><g class="counter"><circle r="69" fill="none" stroke="#bdacff" stroke-dasharray="9 425"/><rect x="66" y="-3" width="6" height="6" fill="#82eced"/></g></g>'
        body += text(1050,118,"Ω",38,"#c9bfdc",extra='text-anchor="middle"')
    svg("void-footer-mobile.svg" if mobile else "void-footer.svg",w,h,"Curiosity has teeth — the Void Dragon",body,"The pixel-art Void Dragon returns at the edge of the observatory. Follow the signal. Build what's underneath. Reduced-motion settings show a still illustration.")


if __name__ == "__main__":
    hero()
    hero(mobile=True)
    project_cards()
    signal_rail()
    companion()
    footer()
    footer(mobile=True)
    for path in sorted(OUT.glob("*.svg")):
        print(f"{path.name}: {path.stat().st_size:,} bytes")
