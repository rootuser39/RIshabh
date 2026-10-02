# Void Observatory: architecture and inspection

## Existing system
- Repository: a GitHub README, self-contained SVG assets, and a Python standard-library generator.
- No Pages site, frontend framework, stylesheet system, package runtime, or JavaScript application existed.
- Assets: desktop/mobile heroes, four project panels, signal trace, dragon portrait, footer pairs, and animation-free variants.
- Mascot: original 64 × 56 pixel drawing in scripts/void_dragon.py; three wing poses, tail, eye and breath layers.
- Layout: GitHub Markdown + native details/picture; images wrap and use portrait mobile assets. GitHub owns focus, typography and table behavior.
- Accessibility: SVG titles/descriptions, image alternatives and reduced-motion picture sources. README cannot provide application interactions.
- Project content was embedded in README and the artwork generator. Its cards did not expose implementation depth.

## Extension
Preserve the README and its imagery. Add a static, progressively enhanced HTML interface in the same repository; do not introduce a framework. Both views are generated from content/*.json. README remains useful without JavaScript. The interface adds filters, inspectable records, a responsive layer map, dragon reactions and a small command terminal.

### Hierarchy
Header / navigation → existing hero / identity → current signal + content counts → system panels + relationship map → experiments + field log + failures → principles / questions / depth → instrument drawer → transmissions → collaboration protocol → existing closing artwork.
Native details provide disclosure. Filters and terminal are optional enhancements. Page content exists in the HTML before JavaScript runs.

### Data model
site.json holds identity, principles and channel protocol. Separate files hold signal, systems, experiments, field logs, failures, questions, tools, depth, transmissions and pinned public source snapshots. IDs connect records. Measurements require units, evidence type and provenance. Empty collections render honest empty states. Derived counts are calculated at build time; no runtime GitHub request, fabricated activity feed, or hardware telemetry.

### Evidence boundary
ARGUS: inference/trace prototype; verification is currently a non-empty-output check, not semantic validation or implemented capability security.
AI Fabric Lab: deterministic synthetic FIFO incast suite and NCCL parser; no real GPU/NIC measurements.
AegisNet: Pydantic schemas with otherwise empty source stubs; no working simulator/analyzer.
CORTEX: preserve the existing public architecture summary only; private implementation details are not imported.
Edges distinguish documented scope from shared research questions. No operational integration is inferred.

### Motion
Reuse existing pixel geometry. Hero and footer keep existing SVG vocabulary. One interface companion reacts briefly to opened sections and sleeps after inactivity; it never follows or overlays content. Visibility and reduced-motion state suspend motion. A visible pause control selects still artwork as well as stopping inline animations. Rare wing movement replaces continuous animation in the interface companion.

### Responsive and accessible behavior
360–430px is a first-class viewport. Single-column disclosures, stacked definition lists, readable layer rows and metric tiles replace wide tables. Desktop introduces two columns. Navigation wraps; controls are at least 44px. Use semantic sections, one h1, native summary keyboard behavior, visible focus, explicit labels, a dialog with focus restoration, and non-hover controls. Decorative art is hidden from assistive technology; meaningful content is ordinary text.

### Performance
No runtime dependencies, remote fonts, WebGL, polling, analytics, or scroll-driven rendering. Inline CSS/JS and embedded JSON avoid a loading waterfall. Reuse small local SVGs and reserve image dimensions. Keep the old large PNG out of the deployment artifact. IntersectionObserver only annotates navigation. Sources are pinned and counts are deterministic; activity labels describe content update time, not live monitoring.

### Build and automation
python scripts/build_lab.py validates JSON and renders README.md, index.html, content/derived.json and the Ω favicon. --check detects stale outputs. A path-filtered Actions workflow runs validation and packages the static site; deployment only runs if Pages is already enabled. No scheduled runs or external activity collection. GitHub Pages currently requires one-time repository settings enablement; this connector cannot change Pages settings.

## Graphical extension

See [MOTION.md](MOTION.md) for inspection, component/data hierarchy, responsive geometry, motion ownership and evidence limits. Controllable inline SVGs reuse the existing art. Source-backed ARGUS paths, conceptual fabric/memory instruments, factual field plots, a connected depth map and one safely perched resident share a visibility-aware controller. The README remains the GitHub view; the HTML is the full interactive view.
