#!/usr/bin/env python3
"""Render docs/assets/squad-architecture.svg (and an .html wrapper) for the README.

Hand-placed layout in the architecture-diagram style (dark grid, semantic
colours). Edit the boxes/arrows below and re-run:

    python3 scripts/render_architecture.py
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT_SVG = ROOT / "docs" / "assets" / "squad-architecture.svg"
OUT_HTML = ROOT / "docs" / "assets" / "squad-architecture.html"

W, H = 1280, 880
FONT = "'JetBrains Mono', ui-monospace, SFMono-Regular, Menlo, Consolas, monospace"
STYLE = {
    "external": ("rgba(30, 41, 59, 0.5)", "#94a3b8"),
    "interface": ("rgba(8, 51, 68, 0.4)", "#22d3ee"),
    "runtime": ("rgba(120, 53, 15, 0.3)", "#fbbf24"),
    "store": ("rgba(76, 29, 149, 0.4)", "#a78bfa"),
    "agent": ("rgba(6, 78, 59, 0.4)", "#34d399"),
    "guard": ("rgba(136, 19, 55, 0.4)", "#fb7185"),
}

parts_back: list[str] = []   # arrows (drawn first, behind boxes)
parts_front: list[str] = []  # boxes and labels


def esc(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def box(x, y, w, h, kind, title, *subs):
    fill, stroke = STYLE[kind]
    cx = x + w / 2
    out = [
        f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="6" fill="#0f172a"/>',
        f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="6" fill="{fill}" stroke="{stroke}" stroke-width="1.5"/>',
    ]
    ty = y + (h - 16 * len(subs)) / 2 + 4
    out.append(f'<text x="{cx}" y="{ty}" fill="#f8fafc" font-size="12" font-weight="600" text-anchor="middle">{esc(title)}</text>')
    for i, s in enumerate(subs):
        out.append(f'<text x="{cx}" y="{ty + 16 * (i + 1)}" fill="#94a3b8" font-size="9.5" text-anchor="middle">{esc(s)}</text>')
    parts_front.extend(out)


def region(x, y, w, h, color, label, dash="8,4", label_x=None):
    parts_back.insert(0, f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="12" fill="{color}" fill-opacity="0.04" stroke="{color}" stroke-width="1" stroke-dasharray="{dash}"/>')
    lx = x + 12 if label_x is None else label_x
    parts_front.append(f'<text x="{lx}" y="{y + 17}" fill="{color}" font-size="10" font-weight="600">{esc(label)}</text>')


def arrow(d, color="#64748b", label=None, lx=0, ly=0, dash=None, anchor="start", end=True):
    da = f' stroke-dasharray="{dash}"' if dash else ""
    mk = f' marker-end="url(#ah-{color[1:]})"' if end else ""
    parts_back.append(f'<path d="{d}" fill="none" stroke="{color}" stroke-width="1.4"{da}{mk}/>')
    if label:
        parts_front.append(f'<text x="{lx}" y="{ly}" fill="#94a3b8" font-size="9" text-anchor="{anchor}">{esc(label)}</text>')


# ---- Row A: people and surfaces -------------------------------------------
box(40, 80, 200, 64, "external", "Anil (product owner)", "writes briefs, answers blocks,", "merges and deploys")
box(290, 80, 250, 64, "interface", "default profile (chat)", "drafts cards with you, verifies,", "merges + ships on \"done\"")
box(610, 80, 290, 64, "interface", "Desktop: squad dashboard", "::preview widget in chat", "refreshed every 5 min")
box(970, 80, 270, 64, "external", "WhatsApp", "squad digest · daily AI brief", "Saturday deep-dive")

# ---- Row B: gateway --------------------------------------------------------
region(30, 176, 1220, 124, "#fbbf24", "Gateway · launchd service · one multiplexed process serving every profile", label_x=330)
box(60, 208, 240, 70, "runtime", "Kanban dispatcher", "every 60 s: claims ready cards,", "spawns hermes -p <role>")
box(330, 208, 230, 70, "runtime", "Goal judge (aux model)", "after each turn of a goal-mode", "card: done yet? else continue")
box(590, 208, 630, 70, "runtime", "Cron scheduler",
    "no model: digest 07:30 · dashboard 5m · release finished worktrees 5m",
    "model: AI brief daily 07:45 (Sonnet) · deep-dive Sat 09:00 (Opus)")

# ---- Row C: boards ----------------------------------------------------------
box(60, 340, 330, 64, "store", "Repo boards (one per ~/git repo)", "git worktree + branch per card", "workers see only their board")
box(600, 340, 230, 64, "store", "cross-repo board", "lead creates one card per", "repo, producer → consumer")
box(920, 340, 300, 64, "store", "research board", "dir workspace ~/git/research", "per-card citation ledger")

# ---- Row D: squads ----------------------------------------------------------
region(30, 444, 800, 250, "#34d399", "Dev squad")
region(315, 462, 500, 222, "#fb7185", "approvals.deny: no deploy / push / cloud writes", dash="4,4", label_x=462)
box(60, 512, 220, 64, "agent", "lead · Opus xhigh", "plans, decides contracts,", "judges vs original criteria")
box(335, 486, 220, 64, "agent", "engineer · Sonnet xhigh", "code + tests in the card's", "worktree; never pushes")
box(335, 602, 220, 64, "agent", "ops · Sonnet high", "Bicep, pipelines, Docker;", "validates only (what-if)")
box(600, 544, 200, 64, "agent", "reviewer · Opus xhigh", "re-runs Verify, red checks;", "never edits")

region(850, 444, 400, 250, "#34d399", "Research squad")
box(870, 512, 170, 64, "agent", "pm · Opus xhigh", "frames 2–5 questions", "tied to a decision")
box(1060, 486, 175, 64, "agent", "researcher ×N", "Sonnet · one question", "each, cited findings")
box(1060, 602, 175, 64, "agent", "analyst · Opus xhigh", "spot-checks sources,", "writes the brief")

# ---- Row E: outputs -----------------------------------------------------------
box(60, 744, 330, 64, "store", "Branch per card in ~/git/<repo>", "worktree released when done;", "you merge (ff-only) and push")
box(460, 744, 330, 64, "external", "Langfuse", "a trace per turn, env hermes-<role>;", "cost per role (v2 metrics)")
box(870, 744, 360, 64, "store", "~/git/research", "briefs · findings · AI briefings", "archive + glossary")

# ---- Arrows -----------------------------------------------------------------
arrow("M 240 112 L 288 112", "#94a3b8")
arrow("M 315 144 V 322 H 225 V 338", "#22d3ee", "creates cards", 322, 168)
arrow("M 315 322 H 715 V 338", "#22d3ee")
arrow("M 715 322 H 1070 V 338", "#22d3ee")
arrow("M 180 278 V 338", "#fbbf24", "claims", 186, 314)
arrow("M 905 212 V 146", "#fbbf24", "writes html", 840, 170, anchor="end")
arrow("M 1105 212 V 146", "#fbbf24", "delivers", 1112, 170)
arrow("M 170 404 V 510", "#34d399", "spawns workers", 178, 476)
arrow("M 715 404 V 426 H 250 V 510", "#34d399")
arrow("M 955 404 V 510", "#34d399", "spawns workers", 962, 476)
arrow("M 445 278 V 484", "#fbbf24", "goal-mode turns", 438, 316, dash="4,3", anchor="end")
# dev flow
arrow("M 280 532 L 333 518", "#34d399")
arrow("M 280 556 L 333 628", "#34d399", "routes by kind", 290, 600)
arrow("M 555 520 L 598 566", "#34d399", "request_review", 552, 576, anchor="end")
arrow("M 555 634 L 598 590", "#34d399")
arrow("M 680 544 Q 680 500 557 508", "#fb7185", "changes", 640, 500, dash="5,4")
arrow("M 700 608 V 680 H 170 V 578", "#34d399", "approved → lead judges", 330, 676)
# research flow
arrow("M 1040 532 L 1058 520", "#34d399")
arrow("M 1147 550 V 600", "#34d399")
arrow("M 1058 640 H 955 V 578", "#34d399", "brief", 990, 636)
# outputs
arrow("M 225 694 V 742", "#34d399", "commits", 232, 724)
arrow("M 625 694 V 742", "#94a3b8", "traces", 632, 724, dash="3,3")
arrow("M 1050 694 V 742", "#34d399", "writes", 1057, 724)

# ---- Legend -------------------------------------------------------------------
lx, ly = 40, 846
legend = [
    ("external", "person / external"), ("interface", "surface"), ("runtime", "gateway runtime"),
    ("store", "board / storage"), ("agent", "agent role"),
]
x = lx
parts_front.append(f'<text x="{x}" y="{ly - 10}" fill="#f8fafc" font-size="10" font-weight="600">Legend</text>')
for kind, name in legend:
    fill, stroke = STYLE[kind]
    parts_front.append(f'<rect x="{x}" y="{ly}" width="16" height="10" rx="2" fill="{fill}" stroke="{stroke}"/>')
    parts_front.append(f'<text x="{x + 22}" y="{ly + 9}" fill="#94a3b8" font-size="9">{name}</text>')
    x += 30 + len(name) * 6.2
for color, dash, name in [("#fb7185", "4,4", "guardrail boundary"), ("#fbbf24", "4,3", "goal-judge loop"), ("#fb7185", "5,4", "changes requested")]:
    parts_front.append(f'<line x1="{x}" y1="{ly + 5}" x2="{x + 18}" y2="{ly + 5}" stroke="{color}" stroke-dasharray="{dash}"/>')
    parts_front.append(f'<text x="{x + 24}" y="{ly + 9}" fill="#94a3b8" font-size="9">{name}</text>')
    x += 34 + len(name) * 6.2

colors = {c for _, c in STYLE.values()} | {"#64748b"}
markers = "".join(
    f'<marker id="ah-{c[1:]}" markerWidth="9" markerHeight="7" refX="8" refY="3.5" orient="auto">'
    f'<polygon points="0 0, 9 3.5, 0 7" fill="{c}"/></marker>'
    for c in sorted(colors)
)

svg = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" font-family="{FONT}">
<defs>{markers}
<pattern id="grid" width="40" height="40" patternUnits="userSpaceOnUse"><path d="M 40 0 L 0 0 0 40" fill="none" stroke="#1e293b" stroke-width="0.5"/></pattern>
</defs>
<rect width="100%" height="100%" fill="#020617"/>
<rect width="100%" height="100%" fill="url(#grid)"/>
<circle cx="46" cy="38" r="5" fill="#22d3ee"/>
<text x="60" y="43" fill="#f8fafc" font-size="17" font-weight="700">Hermes squads: how a card flows</text>
<text x="60" y="62" fill="#94a3b8" font-size="10">Two Kanban teams on Hermes Agent, Claude 5.5 models · cards drafted with a human, executed by role profiles, reviewed, merged by the human</text>
{chr(10).join(parts_back)}
{chr(10).join(parts_front)}
</svg>
"""

OUT_SVG.parent.mkdir(parents=True, exist_ok=True)
OUT_SVG.write_text(svg)
OUT_HTML.write_text(
    "<!doctype html><html><head><meta charset='utf-8'><title>Hermes squads architecture</title>"
    "<link href='https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;600;700&display=swap' rel='stylesheet'>"
    "<style>body{margin:0;background:#020617;display:flex;justify-content:center;padding:24px}svg{max-width:100%;height:auto}</style>"
    f"</head><body>{svg}</body></html>"
)
print(OUT_SVG)
