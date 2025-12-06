# ZWalker - Automated Z-Machine Walkthrough Generator

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**ZWalker** is an automated walkthrough generator for Z-machine interactive fiction games. It uses AI assistance to explore games, generate solution walkthroughs, and provide regression testing for Z-machine compilers like z2js.

## 📚 Documentation

**[→ View Full Documentation & Game Index](https://avwohl.github.io/zwalker/)**

- [100+ Game Sources with Download URLs](https://avwohl.github.io/zwalker/GAME_SOURCES.html)
- [49 AI-Generated Walkthroughs](https://avwohl.github.io/zwalker/WALKTHROUGHS.html)
- [Complete Test Suite Results](https://avwohl.github.io/zwalker/#testing)

## Features

- 🎮 **Z-Machine Interpreter**: 100% CZECH compliance (425/425 tests passing)
  - Supports Z-machine versions 3, 4, 5, and 8
  - Accurate opcode implementation
  - Full state save/restore

- 🤖 **AI-Assisted Solving**: Generate walkthroughs automatically
  - Claude (Anthropic) integration
  - OpenAI GPT integration
  - Local heuristic fallback

- 🧪 **Compiler Testing**: Validate z2js and other compilers
  - Generate test walkthroughs
  - Compare outputs between interpreters
  - Automated regression detection

- 📊 **Game Exploration**: Automated mapping and analysis
  - Room discovery and mapping
  - Object detection and tracking
  - Command success/failure analysis

## Installation

### From PyPI (when published)

```bash
pip install zwalker
```

### From Source

```bash
git clone https://github.com/avwohl/zwalker.git
cd zwalker
pip install -e .
```

### With AI Support

```bash
pip install zwalker[ai]
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

```python
# Solve a game and test with z2js
python scripts/solve_game.py game.z5 --real-ai
python scripts/compare_outputs.py game_solution.json
```

## Use Cases

### 1. Compiler Testing (Primary Use Case)

ZWalker was built to provide regression testing for the [z2js](https://github.com/yourusername/z2js) compiler (ZIL/ZILF to JavaScript).

**The Problem**: z2js was released with bugs that upset users due to lack of testing.

**The Solution**: ZWalker generates comprehensive test walkthroughs that can be:
- Generated from a known-good .z compile
- Replayed on new compiles to detect regressions
- Used to compare output between interpreters

```bash
# Generate walkthrough with working compiler
python scripts/solve_top5.py

# Test new compiler version against walkthrough
python scripts/compare_outputs.py photopia_solution.json
```

### 2. Game Analysis

Automatically map and analyze IF games:

```bash
zwalker explore game.z5 --thorough --commands
```

### 3. Automated QA

Generate test coverage for your IF game:

```bash
python scripts/solve_game.py your_game.z5 --max-iterations 100
```

## Project Status

**Version**: 0.1.0 (Alpha)

**What Works**:
- ✅ Z-machine interpreter (100% CZECH compliance)
- ✅ AI-assisted game solving
- ✅ Walkthrough generation
- ✅ z2js compilation testing
- ✅ Output comparison tools

**Current Limitations**:
- Menu-based IF needs special handling
- Complex opening puzzles can stall AI
- Not all games solve to completion (60-80% success rate expected)

See [docs/STATUS.md](docs/STATUS.md) for detailed status and [docs/PROGRESS_REPORT.md](docs/PROGRESS_REPORT.md) for test results.

## Results

**Top 5 IF Games Test** (completed 2025-12-06):

| Game | Rank | Rooms | Commands | Quality |
|------|------|-------|----------|---------|
| Photopia | #6 (2023) | 2 | 4 | ✅ Best |
| Lost Pig | #8 (2023) | 2 | 123 | ✅ Good |
| Anchorhead | #2 (2023) | 1 | 174 | ⚠ Stuck |
| Trinity | Classic | 1 | 0 | ✗ Failed |
| Curses | Classic | 1 | 0 | ✗ Failed |

**Z2JS Compilation**: 5/5 (100% success - no compiler errors found)

## Documentation

- [CHANGELOG.md](docs/CHANGELOG.md) - Z-machine bug fixes
- [STATUS.md](docs/STATUS.md) - Project status and roadmap
- [PROGRESS_REPORT.md](docs/PROGRESS_REPORT.md) - Test results
- [WALKTHROUGHS_STATUS.md](docs/WALKTHROUGHS_STATUS.md) - Walkthrough quality analysis

## Architecture

```
zwalker/
├── zmachine.py      # Z-machine interpreter (425/425 CZECH tests)
├── walker.py        # Game exploration engine
├── ai_assist.py     # AI integration (Claude, GPT, local)
└── cli.py           # Command-line interface

scripts/
├── solve_game.py       # Single game AI solver
├── solve_top5.py       # Batch solver for top games
├── compare_outputs.py  # Output comparison tool
└── summarize_results.py # Analysis reports

docs/                # All documentation
solutions/           # Generated walkthroughs
tests/              # Test files
```

## Contributing

Contributions welcome! Areas needing improvement:

1. **Menu Detection**: Better handling of menu-based IF
2. **Puzzle Solving**: Improved AI strategies for complex puzzles
3. **Game Completion**: Detection of win/loss/ending states
4. **More Games**: Test coverage for additional IF games

## License

MIT License - see [LICENSE](LICENSE) file.

## Credits

- **Z-Machine Spec**: Based on the [Z-Machine Standards Document](https://www.inform-fiction.org/zmachine/standards/)
- **CZECH Test Suite**: Compliance testing by Amir Karger
- **AI Assistance**: Powered by Anthropic Claude and OpenAI

## Links

- **Source**: https://github.com/avwohl/zwalker
- **Issues**: https://github.com/avwohl/zwalker/issues
- **z2js Compiler**: https://github.com/yourusername/z2js
- **IF Archive**: https://www.ifarchive.org/
- **IFDB**: https://ifdb.org/

## Acknowledgments

Built to prevent "pissing off users" by providing comprehensive testing for the z2js compiler. Thanks to the Interactive Fiction community for their feedback and patience.

---

**Note**: This is alpha software under active development. Use for testing and exploration. Bug reports and contributions welcome!
