# ZWalker - Automated Z-Machine Walkthrough Generator

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)

**ZWalker** is an automated walkthrough generator for Z-machine interactive fiction games. It combines a CZECH-compliant Z-machine interpreter, AI-assisted solvers, and a deterministic replay harness to produce and verify game walkthroughs, primarily as regression tests for the [z2js](https://github.com/avwohl/z2js) compiler.

## 📚 Documentation

**[→ View Full Documentation & Game Index](https://avwohl.github.io/zwalker/)**

- [Verified Solves & AI Walkthroughs](https://avwohl.github.io/zwalker/WALKTHROUGHS.html)
- [100+ Game Sources with Download URLs](https://avwohl.github.io/zwalker/GAME_SOURCES.html)
- [Test Suite Results](https://avwohl.github.io/zwalker/#testing)

## Verified Results

The headline result is both classic Infocom trilogies plus Planetfall and
Wishbringer — eight games, played start to finish and reproducibly won,
verified by deterministic replay against a fixed RNG seed:

| Game | Score | Won | Turns | Commands | Seed | Solution | Walkthrough |
|------|-------|-----|-------|----------|------|----------|-------------|
| Zork I | 350/350 | ✅ | 499 | 431 | 3 | [JSON](solutions/zork1_verified.json) | [Text](walkthroughs/zork1_verified_350.txt) |
| Zork II | 400/400 | ✅ | 416 | 386 | 2 | [JSON](solutions/zork2_verified.json) | [Text](walkthroughs/zork2_verified_400.txt) |
| Zork III | 7/7 | ✅ | 241 | 216 | 1 | [JSON](solutions/zork3_verified.json) | [Text](walkthroughs/zork3_verified_7.txt) |
| Enchanter | 400/400 | ✅ | 300 | 206 | 1 | [JSON](solutions/enchanter_verified.json) | [Text](walkthroughs/enchanter_verified_400.txt) |
| Sorcerer | 400/400 | ✅ | 390 | 234 | 2 | [JSON](solutions/sorcerer_verified.json) | [Text](walkthroughs/sorcerer_verified_400.txt) |
| Spellbreaker | 600/600 | ✅ | 531 | 422 | 1 | [JSON](solutions/spellbreaker_verified.json) | [Text](walkthroughs/spellbreaker_verified_600.txt) |
| Planetfall | 80/80 | ✅ | 5165 (GST) | 444 | 1 | [JSON](solutions/planetfall_verified.json) | [Text](walkthroughs/planetfall_verified_80.txt) |
| Wishbringer | 100/100 | ✅ | 162 | 179 | 1 | [JSON](solutions/wishbringer_verified.json) | [Text](walkthroughs/wishbringer_verified_100.txt) |

(Zork III scores "potential" out of 7; the win is entering the Treasury of Zork
and becoming the Dungeon Master. Planetfall's move counter is its in-game
Galactic Standard Time clock. Wishbringer is a V3 "time" game — the status
line shows a clock, and the interpreter reads its true score from the game's
own GSCORE global.) Reproduce any of them locally:

```bash
python3 scripts/replay_solve.py games/zcode/zork1.z3 walkthroughs/zork1_verified_350.txt --seeds 4
# -> zork1_verified_350.txt: VERIFIED 350/350 at seed 3 | 431 cmds | died=False | won=True

python3 scripts/replay_solve.py games/zcode/zork2.z3 walkthroughs/zork2_verified_400.txt --seeds 3
# -> zork2_verified_400.txt: VERIFIED 400/400 at seed 2 | 386 cmds | died=False | won=True

python3 scripts/replay_solve.py games/zcode/zork_iii.z3 walkthroughs/zork3_verified_7.txt --seeds 3
# -> zork3_verified_7.txt: VERIFIED 7/7 at seed 1 | 216 cmds | died=False | won=True

python3 scripts/replay_solve.py games/zcode/enchanter.z3 walkthroughs/enchanter_verified_400.txt --seeds 3
# -> enchanter_verified_400.txt: VERIFIED 400/400 at seed 1 | 206 cmds | died=False | won=True

python3 scripts/replay_solve.py games/zcode/sorcerer.z3 walkthroughs/sorcerer_verified_400.txt --seeds 3
# -> sorcerer_verified_400.txt: VERIFIED 400/400 at seed 2 | 234 cmds | died=False | won=True

python3 scripts/replay_solve.py games/zcode/spellbreaker.z3 walkthroughs/spellbreaker_verified_600.txt --seeds 2
# -> spellbreaker_verified_600.txt: VERIFIED 600/600 at seed 1 | 422 cmds | died=False | won=True

python3 scripts/replay_solve.py games/zcode/planetfall.z3 walkthroughs/planetfall_verified_80.txt --seeds 2
# -> planetfall_verified_80.txt: VERIFIED 80/80 at seed 1 | 444 cmds | died=False | won=True

python3 scripts/replay_solve.py games/zcode/wishbringer.z3 walkthroughs/wishbringer_verified_100.txt --seeds 2
# -> wishbringer_verified_100.txt: VERIFIED 100/100 at seed 1 | 179 cmds | died=False | won=True
```

Beyond the verified solves, the repo carries exploration-grade coverage data: 43 room-mapping
walkthrough dumps in `games/results/` and 73 batch solver runs in `solutions/`. These map
rooms and exercise the parser for compiler regression testing — they are **not** complete
solutions and are labeled accordingly.

## Features

- 🎮 **Z-Machine Interpreter**: 100% CZECH compliance — 1,604/1,604 tests passing
  across versions 3, 4, 5, and 8 (v3: 368, v4: 386, v5: 425, v8: 425)
  - Plays Z-machine versions 1–5 and 8 (v6/v7 screen model not supported); CZECH-verified on 3, 4, 5, 8
  - Accurate opcode implementation, full state save/restore

- ✅ **Deterministic Replay Verification**: `scripts/replay_solve.py` replays a walkthrough
  with a pinned RNG seed and searches seeds until random events (combat, thief, wizard)
  line up — making "did we really win?" a reproducible yes/no

- 🤖 **AI-Assisted Solving**: multiple solver generations
  - Agentic solver (`zwalker/agentic_solver.py`): perceive→decide→act→verify loop with
    BFS navigation, world model, and checkpoint backtracking; runs free with a local
    decider or with Claude via API
  - Strategic LLM solver (`zwalker/advanced_solver.py`) and assist layer (`zwalker/ai_assist.py`)
  - Persistent cross-run knowledge base (`zwalker/knowledge.py`)

- 🧪 **Compiler Testing**: validate z2js and other compilers
  - Convert solutions into Node.js replay test scripts (155 tracked, including 73 "smart"
    tests that tolerate random events)
  - Compare outputs between interpreters, detect regressions automatically

- 📊 **Game Exploration**: automated mapping and analysis
  - Room discovery and mapping, object detection and tracking
  - Command success/failure analysis

## Installation

Not yet published to PyPI — install from source:

```bash
git clone https://github.com/avwohl/zwalker.git
cd zwalker
pip install -e .

# with AI backends (anthropic, openai)
pip install -e ".[ai]"
```

## Quick Start

### Basic Game Exploration

```bash
# Explore a game and generate a map
zwalker explore game.z5 --max-rooms 50 --json walkthrough.json

# Use AI assistance (requires ANTHROPIC_API_KEY)
zwalker explore game.z5 --ai --ai-backend anthropic --max-rooms 100

# Interactive play mode
zwalker play game.z5
```

### Verify a Walkthrough

```bash
python3 scripts/replay_solve.py games/zcode/zork1.z3 walkthroughs/zork1_verified_350.txt --seeds 4
```

### Python API

```python
from zwalker.zmachine import ZMachine
from zwalker.walker import GameWalker
from zwalker.ai_assist import AIAssistant

# Load and explore a game
game_data = open('game.z5', 'rb').read()
walker = GameWalker(game_data)

# Start game
output = walker.start()
print(output)

# Explore with AI
ai = AIAssistant(backend='anthropic')
results = walker.explore_with_ai(ai, max_commands=20)

# Save walkthrough
walkthrough = walker.get_walkthrough_json()
```

### Generate Walkthroughs for Testing

```bash
# Solve a game (iterations fixed at 50; add --real-ai for LLM assistance)
python scripts/solve_game.py game.z5 --real-ai

# Compare interpreter output against a recorded solution
python scripts/compare_outputs.py solutions/lostpig_solution.json
```

## Use Cases

### 1. Compiler Testing (Primary Use Case)

ZWalker was built to provide regression testing for the [z2js](https://github.com/avwohl/z2js) compiler (ZIL/ZILF to JavaScript).

**The Problem**: z2js was released with bugs that upset users due to lack of testing.

**The Solution**: ZWalker generates comprehensive test walkthroughs that can be:
- Generated from a known-good .z compile
- Replayed on new compiles to detect regressions
- Used to compare output between interpreters

```bash
# Generate JS test scripts from recorded solutions (smart tests handle random events)
python scripts/generate_all_smart_tests.py

# Run the z2js regression suite
./scripts/run_smart_tests.sh
```

See [docs/TEST_GENERATION.md](docs/TEST_GENERATION.md) for the full pipeline.

### 2. Game Analysis

Automatically map and analyze IF games:

```bash
zwalker explore game.z5 --thorough --commands
```

### 3. Automated QA

Generate test coverage for your IF game:

```bash
python scripts/solve_game.py your_game.z5 --real-ai
```

## Project Status

**Version**: 0.1.0 (Alpha)

**What Works**:
- ✅ Z-machine interpreter (1,604/1,604 CZECH tests across v3/v4/v5/v8)
- ✅ Verified complete solves: Zork I 350/350, Zork II 400/400, Zork III 7/7,
  Enchanter 400/400, Sorcerer 400/400, Spellbreaker 600/600,
  Planetfall 80/80, Wishbringer 100/100 (deterministic replay)
- ✅ Replay/verification harness (`scripts/replay_solve.py`)
- ✅ Agentic solver with navigation, world model, and backtracking
- ✅ Walkthrough generation and z2js test-script generation
- ✅ Output comparison tools

**Current Limitations**:
- Most games beyond the eight verified solves have exploration coverage only, not verified wins
- Menu-based IF and Y/N prompts need special handling
- Complex opening puzzles can stall the AI solvers

See [TODO.md](TODO.md) for current status and [docs/CHANGELOG.md](docs/CHANGELOG.md) for
interpreter fixes. Historical reports live in [docs/archive/](docs/archive/).

## Documentation

- [CHANGELOG.md](docs/CHANGELOG.md) - Z-machine bug fixes
- [TEST_GENERATION.md](docs/TEST_GENERATION.md) - z2js test pipeline
- [ADVANCED_SOLVER.md](docs/ADVANCED_SOLVER.md) - strategic solver design (Dec 2025)
- [PROJECT_NOTES.md](docs/PROJECT_NOTES.md) - project overview and approach
- [docs/archive/](docs/archive/) - historical status and progress reports

## Architecture

```
zwalker/
├── zmachine.py        # Z-machine interpreter (1,604/1,604 CZECH tests)
├── walker.py          # Game exploration engine
├── agentic_solver.py  # Agentic solver: perceive→act→verify + navigation + backtracking
├── advanced_solver.py # Strategic LLM solver (multi-turn planning)
├── ai_assist.py       # AI integration (Claude, GPT, local)
├── knowledge.py       # Persistent cross-run knowledge base
└── cli.py             # Command-line interface

scripts/               # (selection)
├── replay_solve.py       # Deterministic seed-search walkthrough verifier
├── solve_zork3_adaptive.py # Adaptive recorder that produced the Zork III solve
├── solve_enchanter_adaptive.py # Adaptive recorder for the Enchanter solve
├── solve_sorcerer_adaptive.py # Adaptive recorder for the Sorcerer solve
├── solve_spellbreaker_adaptive.py # Adaptive recorder for the Spellbreaker solve
├── solve_planetfall_adaptive.py # Adaptive recorder for the Planetfall solve
├── solve_wishbringer_adaptive.py # Adaptive recorder for the Wishbringer solve
├── debug_replay.py       # Transcript-printing replayer for walkthrough debugging
├── solve_game.py         # Single game AI solver
├── generate_all_smart_tests.py  # z2js test generation (random-event tolerant)
├── compare_outputs.py    # Output comparison tool
└── generate_docs_pages.py # Regenerates docs/WALKTHROUGHS.html from repo data

docs/                # Documentation + GitHub Pages site
solutions/           # Solution JSONs (8 verified solves + exploration runs)
walkthroughs/        # Human + verified walkthroughs (text + JSON command lists)
games/zcode/         # Game corpus (155 story files)
games/results/       # Exploration walkthrough dumps (43 games)
tests/               # Interpreter regression tests
```

## Contributing

Contributions welcome! Areas needing improvement:

1. **More Verified Solves**: extend the adaptive-recorder treatment to other games
2. **Menu Detection**: better handling of menu-based IF and Y/N prompts
3. **Puzzle Solving**: improved AI strategies for complex puzzles
4. **More Games**: test coverage for additional IF games

## License

GPL v3 License - see [LICENSE](LICENSE) file.

## Credits

- **Z-Machine Spec**: Based on the [Z-Machine Standards Document](https://www.inform-fiction.org/zmachine/standards/)
- **CZECH Test Suite**: Compliance testing by Amir Karger
- **AI Assistance**: Powered by Anthropic Claude and OpenAI

## Links

- **Source**: https://github.com/avwohl/zwalker
- **Issues**: https://github.com/avwohl/zwalker/issues
- **z2js Compiler**: https://github.com/avwohl/z2js
- **IF Archive**: https://www.ifarchive.org/
- **IFDB**: https://ifdb.org/

## Acknowledgments

Built to prevent "pissing off users" by providing comprehensive testing for the z2js compiler. Thanks to the Interactive Fiction community for their feedback and patience.

---

**Note**: This is alpha software under active development. Use for testing and exploration. Bug reports and contributions welcome!
