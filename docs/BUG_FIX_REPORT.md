# Z-Machine Output Bug - Fix Report

**Date**: 2025-12-06
**Issue**: GameWalker incorrectly blocking commands and restoring state
**Status**: ✅ FIXED

## The Bug

### Symptoms

When running the Opus solver on Zork I, after correctly moving the rug to reveal the trap door, the solver would:
1. Try to open the trap door
2. Get response: "You can't see any trap door here!"
3. Think the trap door doesn't exist
4. Get stuck and unable to progress

### Root Cause

**Location**: `zwalker/walker.py`, lines 64-78 (BLOCKED_PATTERNS)

The pattern list included `r"closed"` and `r"locked"` as bare words:

```python
BLOCKED_PATTERNS = [
    ...
    "closed",
    "locked",
]
```

This caused false positives. When "move rug" returned:

```
"With a great effort, the rug is moved to one side of the room,
 revealing the dusty cover of a closed trap door."
```

The word "**closed**" matched the pattern, making GameWalker think:
1. Command was blocked (failed)
2. State should be restored
3. Rug move was undone!

Result: The rug was moved, then immediately un-moved by state restoration.

### The Fix

Changed BLOCKED_PATTERNS to be more specific:

**Before**:
```python
BLOCKED_PATTERNS = [
    ...
    r"closed",
    r"locked",
]
```

**After**:
```python
BLOCKED_PATTERNS = [
    ...
    r"door is (locked|closed)",  # Only if door is the subject
    r"window is (locked|closed)",
    r"(locked|closed)\s*\.",  # At end of sentence - "It is locked."
    r"way is blocked",
]
```

This prevents false positives from phrases like:
- "revealing a **closed** trap door" ✅ Not blocked
- "The **door is closed**" ❌ Blocked (correct)
- "It is **locked**." ❌ Blocked (correct)

## Testing

### Test Case 1: Move Rug

**Before fix**:
```
> move rug
Blocked: True (false positive!)
State: Restored (rug still covering trap door)
```

**After fix**:
```
> move rug
Blocked: False ✓
Output: "revealing the dusty cover of a closed trap door"
State: Preserved ✓
```

### Test Case 2: Open Trap Door

**Before fix**:
```
> open trap door
Output: "You can't see any trap door here!" (because rug wasn't actually moved)
```

**After fix**:
```
> open trap door
Blocked: False ✓
Output: "The door reluctantly opens to reveal a rickety staircase"
```

### Test Case 3: Descend

**Before fix**:
- Could not proceed (trapped in Living Room)

**After fix**:
```
> down
New room: True ✓
Output: "You have moved into a dark place. The trap door crashes shut..."
```

## Impact

### What Now Works

1. **Complex puzzle sequences** - Multi-step puzzles like rug → trap door → cellar
2. **State persistence** - Commands that succeed are not undone
3. **Opus solver unblocked** - Can now progress past the trap door

### Potential Edge Cases

The new patterns are more conservative. Need to monitor for:
- Doors/windows with unusual phrasing
- Movement blockers we haven't seen yet
- Edge cases in specific games

If we find new blocking patterns, add them specifically rather than using bare words.

## Verification

Tested on Zork I opening sequence:
- ✅ Open mailbox: Works
- ✅ Enter window: Works
- ✅ Move rug: **FIXED** - Now works
- ✅ Open trap door: **FIXED** - Now works
- ✅ Descend to cellar: **FIXED** - Now works

## Next Steps

1. ✅ Rerun Opus solver on Zork I with fix
2. Monitor for any new blocking pattern issues
3. Test on other games to verify fix doesn't break anything
4. Update test suite if needed

## Files Changed

- `zwalker/walker.py` - Updated BLOCKED_PATTERNS (lines 64-78)

## Lesson Learned

**Be specific with regex patterns for game state detection.**

Bare words like "closed" or "locked" will match in many contexts beyond just blocking messages. Always consider the context and phrase structure when detecting game states.

---

**Bug Status**: ✅ RESOLVED
**Opus Solver**: Now unblocked and re-running
