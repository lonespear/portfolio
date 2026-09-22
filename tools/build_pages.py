"""Generate work/<slug>.qmd and teaching/<slug>.qmd case-study pages from _data/projects/*.json.

Cards come from the portfolio audit. A card renders as a Quarto draft (excluded from
listings and the published site) while it still has blockers, unless _data/site.yml
lists its slug under `publish`. Only results whose evidence status is `verified` or
`traceable` are shown.

    python tools/build_pages.py
"""
import json
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
CARDS = ROOT / "_data" / "projects"
SITE = yaml.safe_load((ROOT / "_data" / "site.yml").read_text(encoding="utf-8"))

SECTION_DIR = {"teaching": "teaching"}
SECTION_LABEL = {
    "flagship": "Decision Analytics",
    "research": "Research",
    "simulation": "Simulation & ML Engineering",
    "teaching": "Teaching",
    "product": "Product Engineering",
}
SHOWN = {"verified", "traceable"}


def q(text):
    """Quote a string for YAML front matter."""
    return json.dumps(text or "", ensure_ascii=False)


def page(card):
    slug = card["slug"]
    section = card.get("site_section", "research")
    shown = [r for r in card.get("headline_results", []) if r.get("status") in SHOWN]
    blockers = card.get("blockers_before_featuring", [])
    publish = slug in SITE.get("publish", [])
    draft = bool(blockers) and not publish
    order = SITE.get("featured", [])

    front = [
        "---",
        f"title: {q(card['display_title'])}",
        f"description: {q(card.get('one_liner'))}",
        f"categories: {json.dumps([SECTION_LABEL.get(section, section)] + card.get('tech', [])[:4], ensure_ascii=False)}",
        f"order: {order.index(slug) + 1 if slug in order else 100}",
        f"featured: {'true' if slug in order else 'false'}",
        f"draft: {'true' if draft else 'false'}",
        "---",
    ]

    links = card.get("links", {})
    buttons = []
    if links.get("github"):
        buttons.append(f"[Code]({links['github']}){{.btn .btn-outline-primary .btn-sm}}")
    if links.get("demo"):
        buttons.append(f"[Live demo]({links['demo']}){{.btn .btn-primary .btn-sm}}")
    if links.get("paper"):
        buttons.append(f"[Paper]({links['paper']}){{.btn .btn-outline-secondary .btn-sm}}")

    body = []
    if buttons:
        body += [" ".join(buttons), ""]
    if shown:
        body += ["## Results", ""] + [f"- {r['claim']}" for r in shown] + [""]
    body += [
        "## The problem", "", card.get("problem", ""), "",
        "## What I built", "", card.get("approach", ""), "",
    ]
    if card.get("decision_relevance"):
        body += ["::: {.callout-note appearance=\"simple\"}", "## What it is for", "",
                 card["decision_relevance"], ":::", ""]
    if card.get("tech"):
        body += ["## Tools", "", ", ".join(card["tech"]), ""]
    if card.get("caveat"):
        body += [f"[{card['caveat']}]{{.fine}}", ""]
    return "\n".join(front + [""] + body)


def main():
    written = []
    for path in sorted(CARDS.glob("*.json")):
        card = json.loads(path.read_text(encoding="utf-8"))
        out_dir = ROOT / SECTION_DIR.get(card.get("site_section"), "work")
        out = out_dir / f"{card['slug']}.qmd"
        out.write_text(page(card), encoding="utf-8")
        written.append(out.relative_to(ROOT).as_posix())
    print("\n".join(written) or "no cards found")


if __name__ == "__main__":
    main()
