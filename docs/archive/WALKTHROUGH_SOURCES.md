# Walkthrough Sources Investigation

## Current Status

### Existing Walkthroughs
**Location**: `games/results/*_walkthrough.json`
**Count**: 43 files
**Type**: Exploration data (NOT winning solutions)

These files contain:
- Commands tried during exploration
- Rooms discovered
- Objects found
- **NOT** winning command sequences

### What We Need
**COMPLETE game walkthroughs** that reach the winning condition ("You have won").

## Online Walkthrough Sources

### 1. IF Archive Solutions
- **URL**: https://www.ifarchive.org/indexes/if-archive/solutions/
- **Coverage**: Many classic IF games
- **Format**: Plain text, sometimes with hints

### 2. ClubFloyd Transcripts
- **URL**: https://clubfloyd.com/
- **Coverage**: Community play-throughs
- **Format**: Full transcripts of gameplay

### 3. IFDB (Interactive Fiction Database)
- **URL**: https://ifdb.org/
- **Coverage**: Most IF games have solution links
- **Format**: Various (text, HTML, hints)

### 4. Invisiclues / Hint Systems
- Some games have built-in hint systems
- Can be accessed via game commands

## Known Complete Walkthroughs

### Games with Available Solutions

**Zork 1**:
- IF Archive: https://www.ifarchive.org/if-archive/solutions/zork1.sol
- InvisiClues available

**Curses**:
- IF Archive has hints
- Complex game, full walkthrough rare

**Trinity**:
- IF Archive has walkthrough
- Time-travel puzzles documented

**Lost Pig**:
- Multiple complete walkthroughs available
- Simple enough for AI to solve

**Photopia**:
- Linear story, minimal puzzles
- Multiple transcripts available

**Aisle**:
- Single-move game
- All endings documented

## Integration Strategy

### Option 1: Fetch Walkthroughs When Stuck
When AI gets stuck (no progress for 50 iterations):
1. Search IF Archive for game solution
2. Parse walkthrough into command list
3. Use next few commands as hints for AI
4. Let AI continue with guidance

### Option 2: Pre-Download All Solutions
Download known walkthroughs before starting:
```bash
# Download from IF Archive
wget -r -np -nd -P walkthroughs/ https://www.ifarchive.org/if-archive/solutions/
```

### Option 3: Hybrid AI + Human Solutions
1. Try AI solver first (current approach)
2. If AI completes: ✓ Use AI solution
3. If AI fails: Use human walkthrough
4. Mark solutions as "AI-generated" or "Human walkthrough"

## Current Approach

The completion solver (running now) uses pure AI with:
- 500 iterations per game
- Completion-focused prompting
- Win detection

**Results so far**: 3/11 games completed (simple auto-win games)

## Recommendations

### Short Term (Now)
Let current AI solver finish all 46 games. It will:
- ✓ Complete simple games (10-20 games estimated)
- ⚠ Get stuck on complex games

### Medium Term (After AI Run)
For games AI couldn't complete:
1. Search IF Archive for solutions
2. Download and parse walkthroughs
3. Replay human walkthroughs to verify they work
4. Use as fallback solutions

### Long Term
Build hybrid system:
- AI attempts first
- Falls back to hints from human walkthroughs when stuck
- Creates "AI-guided" solutions that learn from human hints

## Coverage Estimate

### Games AI Will Likely Complete
- 905, Aisle, Bedlam, Blue Chairs ✓ (already done)
- Detective, Failsafe, Etude (simple puzzles)
- Booth, Animals (short games)
**Estimated: 10-15 games**

### Games Needing Human Walkthroughs
- Zork 1/2 (complex, many puzzles)
- Curses (very difficult)
- Trinity (time-travel complexity)
- Enchanter (magic system)
- Dracula, Acheton (large games)
**Estimated: 30-35 games**

## Next Steps

1. ✓ Let AI solver complete (running now - PID 1059581)
2. Analyze which games AI completed
3. For incomplete games:
   - Search IF Archive
   - Download walkthroughs
   - Parse and verify
4. Create unified solution set (AI + human)
5. Update z2js validation tests

---

**Updated**: 2025-12-06
**AI Solver Status**: Running (3 complete, 8 incomplete, 35 pending)
