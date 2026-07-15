#!/usr/bin/env python3
"""Regenerate docs/WALKTHROUGHS.html from the walkthrough/solution JSON actually in git.

The GitHub Pages workflow (.github/workflows/pages.yml) deploys docs/ as the
site root and copies games/results/, solutions/ and walkthroughs/ alongside it,
so links in the generated page are site-root relative (no "../").

Only git-tracked files are listed: untracked local solver output would 404 on
the deployed site.

Usage: python3 scripts/generate_docs_pages.py
"""

import html
import json
import subprocess
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
OUT = REPO / "docs" / "WALKTHROUGHS.html"
INDEX = REPO / "docs" / "index.html"

# Test suites, not playable games — excluded from the exploration table (see TODO.md).
TEST_SUITES = {"czech", "gntests", "etude"}


def tracked(pattern: str) -> list[Path]:
    """Git-tracked files matching pattern, sorted."""
    out = subprocess.run(
        ["git", "ls-files", pattern], cwd=REPO, capture_output=True, text=True, check=True
    ).stdout.split()
    return [REPO / p for p in sorted(out)]


def load(path: Path):
    try:
        with open(path) as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return None


def game_name(path: Path) -> str:
    return (
        path.name.replace("_walkthrough.json", "")
        .replace("_solution.json", "")
        .replace("_verified.json", "")
    )


def collect():
    """Return (verified, rows): verified complete solves and exploration runs."""
    verified = []
    rows = []

    for path in tracked("solutions/*_verified.json"):
        d = load(path)
        if not d or "score" not in d:
            continue
        verified.append(
            {
                "game": game_name(path),
                "score": d.get("score", 0),
                "max_score": d.get("max_score", 0),
                "won": d.get("won", False),
                "turns": d.get("turns", 0),
                "commands": d.get("num_commands", 0),
                "seed": d.get("rng_seed"),
                "json": f"solutions/{path.name}",
                "txt": d.get("walkthrough"),  # repo-relative path to the .txt
            }
        )

    for path in tracked("games/results/*_walkthrough.json"):
        if game_name(path) in TEST_SUITES:
            continue
        d = load(path)
        if not d:
            continue
        stats = d.get("stats", {})
        rooms = stats.get("rooms_found", len(d.get("rooms", {})))
        commands = len(d.get("commands", []))
        rows.append(
            {
                "game": game_name(path),
                "rooms": rooms,
                "commands": commands,
                "href": f"games/results/{path.name}",
            }
        )

    seen = {r["game"] for r in rows} | {v["game"] for v in verified}
    for path in tracked("solutions/*_solution.json"):
        name = game_name(path)
        if name in seen or name in TEST_SUITES:
            continue
        d = load(path)
        if not d or "commands" not in d:
            continue
        rows.append(
            {
                "game": name,
                "rooms": d.get("total_rooms", len(d.get("rooms_visited", []))),
                "commands": d.get("total_commands", len(d.get("commands", []))),
                "href": f"solutions/{path.name}",
            }
        )

    rows.sort(key=lambda r: r["game"].lower())
    return verified, rows


def quality(rooms: int, commands: int) -> tuple[str, str]:
    if rooms >= 10:
        return "status-good", "Broad exploration"
    if rooms >= 3:
        return "status-medium", "Partial exploration"
    if commands > 0:
        return "status-low", "Shallow"
    return "status-low", "Minimal"


def render(verified, rows) -> str:
    e = html.escape

    vrows = "\n".join(
        f"""    <tr>
        <td>{e(v['game'])}</td>
        <td class="status-good">{'win (unscored)' if v['max_score'] in (None, 0) else f"{v['score']}/{v['max_score']}"}</td>
        <td>{'Yes' if v['won'] else 'No'}</td>
        <td>{v['turns']}</td>
        <td>{v['commands']}</td>
        <td>{v['seed'] if v['seed'] is not None else '-'}</td>
        <td><a href="{e(v['json'])}">JSON</a>{f' | <a href="{e(v["txt"])}">Text</a>' if v['txt'] else ''}</td>
    </tr>"""
        for v in verified
    )

    trows = "\n".join(
        f"""    <tr>
        <td>{e(r['game'])}</td>
        <td>{r['rooms']}</td>
        <td>{r['commands']}</td>
        <td><span class="{quality(r['rooms'], r['commands'])[0]}">{quality(r['rooms'], r['commands'])[1]}</span></td>
        <td><a href="{e(r['href'])}">JSON</a></td>
    </tr>"""
        for r in rows
    )

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Walkthroughs - ZWalker</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            line-height: 1.6;
            color: #333;
            background: #f5f5f5;
        }}
        header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 2rem;
            text-align: center;
        }}
        .container {{ max-width: 1200px; margin: 2rem auto; padding: 0 2rem; }}
        section {{
            background: white;
            margin: 2rem 0;
            padding: 2rem;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.05);
        }}
        h2 {{
            color: #667eea;
            margin-bottom: 1.5rem;
            font-size: 1.8rem;
            border-bottom: 3px solid #667eea;
            padding-bottom: 0.5rem;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 1rem 0;
        }}
        th, td {{ padding: 0.8rem; text-align: left; border-bottom: 1px solid #e0e0e0; }}
        th {{
            background: #f5f5f5;
            font-weight: 600;
            color: #667eea;
        }}
        tr:hover {{ background: #f9f9f9; }}
        a {{ color: #667eea; text-decoration: none; }}
        a:hover {{ text-decoration: underline; }}
        .back-link {{
            display: inline-block;
            margin: 1rem 0;
            padding: 0.5rem 1rem;
            background: #667eea;
            color: white;
            border-radius: 5px;
        }}
        .status-good {{ color: #4CAF50; font-weight: 600; }}
        .status-medium {{ color: #FF9800; font-weight: 600; }}
        .status-low {{ color: #f44336; font-weight: 600; }}
    </style>
</head>
<body>
    <header>
        <h1>ZWalker Walkthroughs</h1>
        <p>Verified complete solves and AI exploration runs for Z-machine games</p>
    </header>
    <div class="container">
        <a href="index.html" class="back-link">&larr; Back to Main</a>

        <section>
            <h2>Verified Complete Solves ({len(verified)})</h2>
            <p>These walkthroughs play the game start to finish for a perfect score,
               verified by deterministic replay (<code>scripts/replay_solve.py</code>)
               against a fixed RNG seed. The JSON includes the full command list and
               a step-by-step score timeline; the text file is a plain command script.</p>
            <table>
                <tr>
                    <th>Game</th>
                    <th>Score</th>
                    <th>Won</th>
                    <th>Turns</th>
                    <th>Commands</th>
                    <th>RNG Seed</th>
                    <th>Download</th>
                </tr>
{vrows}
            </table>
        </section>

        <section>
            <h2>AI Exploration Runs ({len(rows)})</h2>
            <p>Automated exploration output: room mapping and command coverage generated
               by the solver. These are regression-test fixtures for the
               <a href="https://github.com/avwohl/z2js">z2js</a> compiler, not complete
               solutions &mdash; most do not finish the game.</p>
            <table>
                <tr>
                    <th>Game</th>
                    <th>Rooms Explored</th>
                    <th>Commands</th>
                    <th>Coverage</th>
                    <th>Download</th>
                </tr>
{trows}
            </table>
        </section>

        <section>
            <h2>Walkthrough Formats</h2>
            <p>Verified solves (<code>solutions/*_verified.json</code>):</p>
            <pre style="background: #2d2d2d; color: #f8f8f2; padding: 1rem; border-radius: 8px; overflow-x: auto;">
{{
  "game": "games/zcode/zork1.z3",
  "walkthrough": "walkthroughs/zork1_verified_350.txt",
  "solver": "replay+seed",
  "rng_seed": 3,
  "score": 350,
  "max_score": 350,
  "won": true,
  "turns": 499,
  "num_commands": 431,
  "score_timeline": [ {{ "step": 3, "command": "enter window", "score": 10 }}, ... ],
  "commands": [ ... ]
}}</pre>
            <p>Exploration runs (<code>games/results/*_walkthrough.json</code>):</p>
            <pre style="background: #2d2d2d; color: #f8f8f2; padding: 1rem; border-radius: 8px; overflow-x: auto;">
{{
  "format_version": 1,
  "commands": [ "north", "take lamp", ... ],
  "rooms": {{ "1": {{ "name": "West of House", "exits": [...] }}, ... }},
  "objects": {{ ... }},
  "stats": {{ "rooms_found": 8, "commands_tried": 126, ... }}
}}</pre>
        </section>

        <footer style="text-align: center; padding: 1rem; color: #777;">
            <p>Generated by <code>scripts/generate_docs_pages.py</code> from the JSON files in this repository.</p>
        </footer>
    </div>
</body>
</html>
"""


def sync_index_counts(n_verified: int, n_rows: int) -> None:
    """Keep the hand-maintained counts in docs/index.html in step with the table."""
    import re

    html_text = INDEX.read_text()
    total = n_verified + n_rows
    games_results = len(tracked("games/results/*_walkthrough.json")) - len(
        [p for p in tracked("games/results/*_walkthrough.json") if game_name(p) in TEST_SUITES]
    )
    subs = [
        (
            r'(<span class="stat-number">)\d+(</span>\s*<span class="stat-label">Exploration Walkthroughs)',
            rf"\g<1>{n_rows}\g<2>",
        ),
        (
            r'(<span class="stat-number">)\d+(</span>\s*<span class="stat-label">Verified Complete Solves)',
            rf"\g<1>{n_verified}\g<2>",
        ),
        (r"All \d+ walkthroughs", f"All {total} walkthroughs"),
        (
            r"\d+ games have exploration data in the repo \(\d+ walkthrough dumps",
            f"{n_rows} games have exploration data in the repo ({games_results} walkthrough dumps",
        ),
        (
            r"\d+ verified complete solves and \d+ exploration runs",
            f"{n_verified} verified complete solves and {n_rows} exploration runs",
        ),
    ]
    for pattern, repl in subs:
        html_text, n = re.subn(pattern, repl, html_text)
        if n != 1:
            print(f"  WARNING: index.html pattern matched {n} times (expected 1): {pattern}")
    INDEX.write_text(html_text)


def main():
    verified, rows = collect()
    OUT.write_text(render(verified, rows))
    print(f"Wrote {OUT}: {len(verified)} verified solves, {len(rows)} exploration runs")
    sync_index_counts(len(verified), len(rows))
    print(f"Synced counts into {INDEX}")


if __name__ == "__main__":
    main()
