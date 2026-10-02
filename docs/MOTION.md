# Machinery, with boundaries

The existing README, pixel art, Ω sculpture, cards, typography and plain static stack are retained. This extension adds controllable inline versions of the existing SVGs, not a replacement design.

## Architecture
Shared JSON → Python standard-library renderer → semantic static HTML + README assets → optional small motion controller.

Hierarchy: identity/core → signal/resident → systems and relations → ARGUS execution → memory geography → conceptual fabric → evidence/failures → connected depth → instruments → channel.

- `content/motion.json`: conceptual sequences, labels and explanatory boundaries.
- `content/depth.json`: intentional mobile/desktop node geometry and relationships.
- `scripts/lab_graphics.py`: SVG reuse, accessible instruments, factual plots and README diagrams.
- `interface/machinery.css`: scene, trace, node and interaction vocabulary.
- `interface/motion.js`: one foreground task, visibility lifecycle and resident state machine.

## Evidence
ARGUS playback follows the pinned public orchestrator: parse, plan, route, generate, non-empty output check, conditional JSONL write, returned trace. Empty text bypasses memory. Playback does not run a provider; “verified” does not mean semantically correct.

Fabric modes are conceptual illustrations independent of the recorded FIFO model. Packet timing, queue cells and topology are illustrative. Alternate links do not remove a shared receiver bottleneck. AegisNet animation demonstrates its intended architecture; only schemas are documented.

Memory paths show locality and transfer boundaries, without numerical latency claims. Field plots read actual linked experiment records. Telemetry marks count actual records, not invented time series.

F-001 playback illustrates the documented embedded-image preference problem. Its browser internal cause remains unknown. Future unresolved failures stop at the failed node and never imply repair.

## Motion budget
One user-triggered foreground task owns attention. It cancels the previous task and pauses ambient scenes. Traces play once and settle. Slow orbital motion and the resident are the idle background. No permanent requestAnimationFrame loop, canvas, WebGL or animation dependency.

Finite Web Animations use transform/opacity. Native scroll pauses ambient motion briefly. IntersectionObserver stops scenes and foreground tasks outside the viewport; hidden tabs suspend motion. Timers are cleared on cancellation.

## Resident
The original pixel grid is preserved and split into anchored head, ear and foot poses. One resident moves only between reserved 132 × 106 pixel perches. Relocation is instantaneous between sections; short walking happens inside the destination. No flight across copy or controls. Focused resident controls prevent relocation. Inactivity leads to sleeping; inspection, failures and the terminal produce finite reactions. These are fictional interface states, not engineering telemetry.

## Responsive and accessible
Mobile has a focused two-column fabric, vertical readable execution/memory, and a two-column depth map. Desktop expands to four workers, three-column depth and a side execution rail. HTML labels accompany decorative SVGs. All modes have native buttons and selected-path text; hover is supplemental.

Reduced motion displays completed highlighted paths and static poses, with immediate reveals. Global Pause also cancels JavaScript tasks, pauses CSS and selects still external images. No-JavaScript retains native disclosures, evidence, diagrams and readable explanations.

## Performance and verification
No runtime dependencies or remote requests. SVG styles are folded into the existing hashed CSP. Image boxes, instruments and perches reserve space. Tests check concepts, responsive widths, keyboard focus, no-JS, single motion ownership, offscreen/hidden cancellation and actual resident bounds. Browser tools are development dependencies only. No Lighthouse score is claimed.
