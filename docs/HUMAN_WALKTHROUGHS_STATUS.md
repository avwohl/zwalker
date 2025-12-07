# Human Walkthroughs Status Report

**Date**: 2025-12-06
**Goal**: Find and convert human-written walkthroughs to JSON for z2js testing

## Current Status

### ✓ Successfully Downloaded: 12 walkthroughs

We downloaded walkthroughs from IF Archive for:

1. **Zork I** - hints.many format
2. **Zork II** - hints.many format
3. **Zork III** - hints.many format
4. **Enchanter** - hints.many format
5. **Planetfall** - hints.many format
6. **Trinity** - prose walkthrough ✓
7. **Curses** - detailed solution ✓
8. **Anchorhead** - command sequence ✓
9. **Photopia** - command sequence ✓
10. **Dreamhold** - ZIP archive (mixed format)
11. **Jigsaw** - detailed solution ✓
12. **Aisle** - multiple endings guide

**Files stored in**: `walkthroughs/`

### ⚠ Conversion Problem

The automated converter created JSON files, but there's a **quality issue**:

**Two different source formats**:

1. **Hints format** (Infocom hints.many):
   - NOT actual commands
   - Just cryptic clues like "Consider the uses of a basket"
   - Example: Zork I, Enchanter, Planetfall
   - **Not usable** for automated testing

2. **Prose walkthroughs**:
   - Natural language instructions
   - Example: "go NE to The Wabe", "unscrew the gnomon from the dial"
   - Needs parsing: "go NE" → "ne", "unscrew gnomon" → "unscrew gnomon"
   - **Partially usable** with better parser

3. **Actual command sequences** (best format):
   - Direct commands like "> north", "> take lamp", "> light lamp"
   - Trinity walkthrough has some of this embedded
   - **Fully usable** as-is

### Problem Example

**Zork I solution.json** currently contains:
```json
{
  "commands": [
    "* * *  zork i hints  * * *",
    "3. the platinum bar",
    "4. the pot of gold",
    ...
  ]
}
```

These are **not actual commands** - they're hint section headers!

## What We Need

### Better Sources

We need **actual command-sequence walkthroughs**, not hints or prose descriptions.

**Known better sources**:
- https://ifarchive.org/if-archive/infocom/hints/solutions/zorkI.txt (found via search)
- Sols1.zip, Sols3.zip archives (mentioned in search results)
- IFDB game pages often have community-contributed command-sequence walkthroughs

### Format We Want

The ideal format is:
```
> open mailbox
> read leaflet
> drop leaflet
> south
> east
> take lamp
> light lamp
```

Or at minimum, clean command lists:
```
open mailbox
read leaflet
drop leaflet
south
...
```

## Action Items

### Option 1: Download Better Walkthroughs

Fetch actual command-sequence files:

```bash
# Download the better Zork I walkthrough
wget https://ifarchive.org/if-archive/infocom/hints/solutions/zorkI.txt -O walkthroughs/zork1_commands.txt

# Find and download Sols archives
# Parse ZIP files for command sequences
```

### Option 2: Use AI to Extract Commands from Prose

For walkthroughs like Trinity (prose format), use Claude to extract commands:

**Input** (prose):
> "From the Palace Gate, go NE to The Wabe and the sundial. Unscrew the gnomon from the dial and get it."

**Output** (commands):
```
ne
unscrew gnomon
take gnomon
```

This is actually a perfect use case for Claude - parsing natural language walkthroughs.

### Option 3: Use Opus-Solved Solutions Instead

Given that we now have the advanced Opus solver, we could:
1. Run Opus on all major games
2. Get actual command sequences that work
3. Use those as the "ground truth" solutions

**Pros**:
- Commands guaranteed to work in our Z-machine
- Already in perfect JSON format
- No parsing issues

**Cons**:
- Costs money ($50-100 for batch)
- May not complete hardest games
- Takes time (2-4 hours)

## Current Usable Solutions

Of the 12 downloaded walkthroughs, estimate of true usability:

- **Fully usable** (clean commands): **2-3** (Trinity, Anchorhead, maybe Photopia)
- **Needs better parsing**: **4-5** (Curses, Jigsaw, Dreamhold)
- **Not usable** (hints only): **5** (Zork I/II/III, Enchanter, Planetfall)

**Real count of usable human walkthroughs**: ~5-7, not 12

## Recommendation

**Hybrid approach**:

1. **Immediate** (today):
   - Download better Zork I walkthrough from the found URL
   - Test if it has actual commands
   - If yes, find similar for other Infocom games

2. **Short-term** (this week):
   - Use Claude to parse prose walkthroughs (Trinity, Curses, etc.)
   - Extract command sequences automatically
   - Verify by replaying in Z-machine

3. **Medium-term** (once Opus solver tested):
   - Run Opus on all 28 unsolved games
   - Get 15-20 AI-generated complete solutions
   - Combine with best human walkthroughs
   - Target: 30-35 total complete solutions

## Status for z2js Testing

**Current reality**:
- **3** complete AI solutions (simple games)
- **~5-7** usable human walkthroughs (after proper parsing)
- **~28** games with no complete solution

**Total ready for z2js**: ~8-10 complete solutions (not 15 as previously reported)

**Target**: 30-40 complete solutions covering all Z-versions

## Next Steps

1. Download zorkI.txt and check if it's command-based
2. If yes, find similar for other Infocom games
3. Create improved parser for prose walkthroughs
4. OR just run Opus solver and use those results

---

**Sources**:
- [Zork I Walkthrough](https://ifarchive.org/if-archive/infocom/hints/solutions/zorkI.txt)
- [IF Archive Solutions Index](https://ifarchive.org/indexes/if-archive/infocom/hints/solutions/)
- [IF Archive Main Solutions](http://ifarchive.org/indexes/if-archive/solutions/)
