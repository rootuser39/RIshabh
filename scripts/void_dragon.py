"""Original pixel-art companion, rendered as compact SVG with the stdlib.

The dragon is drawn on a 64 by 56 pixel grid. Every visible tile is a whole
pixel; wing poses share the same body so the discrete loop stays anchored.
"""

from html import escape


PALETTE = {
    "outline": "#08060f",
    "deep": "#241a37",
    "shadow": "#38244e",
    "scale": "#594076",
    "violet": "#8762b3",
    "light": "#bca4e0",
    "silver": "#e3d5ff",
    "eye": "#82eced",
}

DRAGON_CSS = """
 .dragon-hover { animation: dragon-hover 5s ease-in-out infinite; }
 .dragon-tail { transform-origin: 43px 39px; animation: dragon-tail 5s ease-in-out infinite; }
 .wing-open { opacity:1; animation: wing-open 1.8s steps(1,end) infinite; }
 .wing-mid { opacity:0; animation: wing-mid 1.8s steps(1,end) infinite; }
 .wing-low { opacity:0; animation: wing-low 1.8s steps(1,end) infinite; }
 .dragon-eye { animation: dragon-blink 7.2s steps(1,end) infinite; }
 .void-breath { opacity:0; animation: void-breath 10.8s ease-out infinite; }
 .void-spark { animation: quiet-spark 37s steps(1,end) infinite; }
 .void-star { animation: void-star 7s ease-in-out infinite; }
 .void-orbit { animation: void-orbit 34s linear infinite; }
 @keyframes dragon-hover { 0%,100% { transform:translateY(0); } 50% { transform:translateY(-1.5px); } }
 @keyframes dragon-tail { 0%,100% { transform:rotate(-2deg); } 50% { transform:rotate(3deg); } }
 @keyframes wing-open { 0%,100% { opacity:1; } 28% { opacity:0; } 82% { opacity:1; } }
 @keyframes wing-mid { 0%,100% { opacity:0; } 28% { opacity:1; } 45% { opacity:0; } 65% { opacity:1; } 82% { opacity:0; } }
 @keyframes wing-low { 0%,100% { opacity:0; } 45% { opacity:1; } 65% { opacity:0; } }
 @keyframes dragon-blink { 0%,92%,97%,100% { opacity:1; } 94%,99% { opacity:0; } }
 @keyframes void-breath { 0%,58%,100% { opacity:0; transform:translate(0,0); } 61% { opacity:.85; } 76% { opacity:0; transform:translate(-13px,-3px); } }
 @keyframes void-spark { 0%,100% { opacity:.15; transform:translateY(0); } 50% { opacity:.75; transform:translateY(-10px); } }
 @keyframes quiet-spark { 0%,94%,100% { opacity:.15; } 96% { opacity:.45; } }
 @keyframes void-star { 0%,100% { opacity:.2; } 50% { opacity:.8; } }
 @keyframes void-orbit { to { transform:rotate(360deg); } }
 @media (prefers-reduced-motion:reduce) {
   .dragon-hover,.dragon-tail,.wing-open,.wing-mid,.wing-low,.dragon-eye,
   .void-breath,.void-spark,.void-star,.void-orbit { animation:none !important; }
   .wing-open,.dragon-eye { opacity:1; }
   .wing-mid,.wing-low,.void-breath { opacity:0; }
 }
"""


def polygon(points):
    """Rasterize a polygon at pixel centres; no antialiased SVG path edges."""
    result = set()
    for y in range(int(min(p[1] for p in points)), int(max(p[1] for p in points)) + 1):
        for x in range(int(min(p[0] for p in points)), int(max(p[0] for p in points)) + 1):
            px, py, inside = x + .5, y + .5, False
            previous = points[-1]
            for current in points:
                x1, y1 = previous
                x2, y2 = current
                if (y1 > py) != (y2 > py) and px < (x2-x1)*(py-y1)/(y2-y1)+x1:
                    inside = not inside
                previous = current
            if inside:
                result.add((x, y))
    return result


def paint(grid, points, color, outline=False):
    pixels = polygon(points)
    if outline:
        edge = {(x+dx, y+dy) for x,y in pixels for dx,dy in ((-1,0),(1,0),(0,-1),(0,1),(0,0))}
        grid.update({p: PALETTE["outline"] for p in edge})
    grid.update({p: PALETTE[color] for p in pixels})


def tiles(grid):
    """Merge adjacent tiles of the same colour into horizontal pixel runs."""
    result = {}
    for y in sorted({p[1] for p in grid}):
        row = sorted((x, color) for (x, yy), color in grid.items() if yy == y)
        start = end = None
        previous = None
        for x, color in row + [(10000, None)]:
            if previous is not None and (color != previous or x != end+1):
                result.setdefault(previous, []).append(f'M{start} {y}h{end-start+1}v1H{start}z')
                start = None
            if color is not None:
                if start is None:
                    start = x
                end, previous = x, color
    return ''.join(f'<path fill="{color}" d="{"".join(runs)}"/>' for color,runs in result.items())


def wing(pose, far=False):
    grid = {}
    if far:
        shapes = {
            "open": [(30,36),(26,26),(20,28),(16,31),(17,22),(18,17),(27,7),(26,19),(31,15),(34,35)],
            "mid": [(30,36),(27,29),(20,33),(16,32),(19,23),(28,16),(27,26),(34,35)],
            "low": [(30,36),(26,38),(18,38),(19,30),(29,25),(34,35)],
        }
        paint(grid, shapes[pose], "deep", True)
        paint(grid, [(29,35),(24,25 if pose=="open" else 29),(28,19 if pose=="open" else 26),(31,34)], "shadow")
    else:
        shapes = {
            "open": [(34,36),(33,28),(35,18),(39,13),(44,7),(48,2),(48,10),(53,7),(59,9),(55,17),(59,22),(55,31),(49,28),(46,33),(40,30),(38,38)],
            "mid": [(34,36),(35,26),(42,19),(51,11),(54,14),(60,16),(56,22),(61,29),(57,35),(50,31),(45,37),(40,34),(38,39)],
            "low": [(34,36),(38,29),(48,24),(56,20),(58,25),(63,29),(59,34),(61,39),(57,43),(49,38),(45,41),(40,38),(37,40)],
        }
        ribs = {
            "open": ([(35,35),(36,23),(42,14),(47,4),(45,15),(40,22),(38,34)],
                     [(40,22),(54,11),(51,18),(45,24),(43,31)]),
            "mid": ([(35,36),(37,27),(47,19),(52,13),(51,21),(42,29),(38,36)],
                    [(42,28),(57,18),(53,26),(47,32)]),
            "low": ([(35,36),(40,30),(51,26),(56,22),(55,29),(43,34),(38,38)],
                    [(43,34),(60,30),(54,35),(49,37)]),
        }
        paint(grid, shapes[pose], "shadow", True)
        for shape in ribs[pose]:
            paint(grid, shape, "violet")
        paint(grid, [(35,35),(37,27),(40,26),(39,33),(37,38)], "light")
    return tiles(grid)


def tail():
    grid = {}
    paint(grid, [(41,37),(46,37),(49,41),(54,43),(59,41),(61,37),(59,33),(57,32),(56,27),(60,29),(63,34),(64,39),(62,44),(58,47),(52,48),(47,45),(42,42)], "scale", True)
    paint(grid, [(46,39),(50,42),(55,45),(59,43),(62,40),(61,44),(57,46),(51,46)], "violet")
    paint(grid, [(56,29),(55,25),(57,24),(59,29),(62,30),(59,33)], "light", True)
    return tiles(grid)


def body():
    grid = {}
    # Rear haunches and talons.
    paint(grid, [(35,39),(42,40),(43,45),(40,46),(39,49),(42,50),(41,52),(34,52),(35,47),(33,44)], "shadow", True)
    paint(grid, [(23,39),(30,40),(31,45),(28,47),(27,50),(30,51),(28,52),(21,52),(22,48),(24,46)], "scale", True)
    paint(grid, [(21,51),(24,51),(24,53),(20,53)], "silver")
    paint(grid, [(33,51),(36,51),(36,53),(32,53)], "silver")
    paint(grid, [(27,33),(33,32),(41,35),(46,39),(45,43),(40,46),(31,45),(26,42),(23,37)], "scale", True)
    paint(grid, [(29,40),(36,42),(43,40),(42,44),(37,45),(31,44),(27,42)], "light")
    paint(grid, [(30,34),(35,34),(38,36),(35,38),(31,37)], "violet")
    # Curving neck, long muzzle and two crown horns.
    paint(grid, [(21,27),(27,28),(28,32),(26,35),(28,39),(25,42),(21,40),(19,36),(19,31)], "scale", True)
    paint(grid, [(24,30),(26,32),(24,35),(25,39),(23,40),(21,36)], "light")
    paint(grid, [(12,26),(16,23),(21,24),(23,27),(25,31),(22,35),(18,37),(10,36),(7,34),(5,34),(5,30),(11,29)], "scale", True)
    paint(grid, [(13,28),(17,25),(21,27),(22,29),(15,30),(11,32),(7,32),(7,30)], "violet")
    paint(grid, [(7,34),(12,34),(14,35),(18,35),(17,37),(10,37)], "light")
    paint(grid, [(15,24),(13,20),(14,16),(16,19),(18,24)], "silver", True)
    paint(grid, [(20,25),(20,20),(23,17),(23,23),(25,25)], "light", True)
    # Pixel scales and dorsal spines.
    paint(grid, [(26,28),(28,25),(30,27),(28,31)], "violet", True)
    paint(grid, [(29,32),(32,29),(33,32),(31,34)], "light", True)
    paint(grid, [(40,35),(42,32),(44,36)], "violet", True)
    paint(grid, [(13,36),(14,36),(14,39),(13,38)], "silver")
    paint(grid, [(18,30),(21,30),(21,31),(18,31)], "outline")
    paint(grid, [(6,30),(7,30),(7,31),(6,31)], "outline")
    # A tucked foreclaw beneath the neck.
    paint(grid, [(23,35),(27,36),(26,39),(22,39),(20,37),(22,36)], "deep", True)
    paint(grid, [(20,37),(22,37),(22,39),(20,39)], "silver")
    head={(x,y):color for (x,y),color in grid.items() if y<34 and x<29}
    ear={(x,y):color for (x,y),color in head.items() if y<24}
    head={point:color for point,color in head.items() if point not in ear}
    feet={(x,y):color for (x,y),color in grid.items() if y>=47}
    front={point:color for point,color in feet.items() if point[0]<31}
    rear={point:color for point,color in feet.items() if point[0]>=31}
    base={point:color for point,color in grid.items() if point not in head and point not in ear and point not in feet}
    return tiles(base)+'<g class="dragon-head">'+tiles(head)+'</g><g class="dragon-ear">'+tiles(ear)+'</g><g class="dragon-foot-front">'+tiles(front)+'</g><g class="dragon-foot-rear">'+tiles(rear)+'</g>'


def dragon(x, y, scale=4, label="Void Dragon"):
    eye = '<g class="dragon-eye"><rect x="17" y="28" width="3" height="2" fill="#82eced"/><rect x="17" y="28" width="1" height="1" fill="#efffff"/></g>'
    breath = ''.join(f'<rect x="{4-i*3}" y="{31-i%2}" width="{1 if i%2 else 2}" height="1" fill="{PALETTE["eye"] if i%2 else PALETTE["light"]}"/>' for i in range(5))
    result = [f'<g aria-label="{escape(label, quote=True)}" transform="translate({x} {y}) scale({scale})">', '<g class="dragon-hover" shape-rendering="crispEdges">']
    for pose in ("open","mid","low"):
        result.append(f'<g class="wing-{pose}">{wing(pose, far=True)}</g>')
    result.append(f'<g class="dragon-tail">{tail()}</g>')
    for pose in ("open","mid","low"):
        result.append(f'<g class="wing-{pose}">{wing(pose)}</g>')
    result.extend((body(), eye, f'<g class="void-breath">{breath}</g>', '<g class="dragon-smoke" opacity="0"><rect x="9" y="12" width="2" height="2" fill="#aaa3b9"/><rect x="12" y="8" width="3" height="2" fill="#80778f"/></g>', '</g></g>'))
    return ''.join(result)


def sparks(x, y, scale=1):
    parts = [f'<g transform="translate({x} {y}) scale({scale})" shape-rendering="crispEdges">']
    for i, (px,py,size) in enumerate(((12,28,2),(44,12,3),(76,48,2),(116,8,2),(154,26,3),(180,72,2),(214,32,2))):
        parts.append(f'<rect class="void-spark" x="{px}" y="{py}" width="{size}" height="{size}" fill="{PALETTE["light"]}" style="animation-delay:-{i*.7}s"/>')
    parts.append('</g>')
    return ''.join(parts)
