# Z-Machine restore_state() Bug - Fix Report

**Date**: 2025-12-06
**Issue**: After entering cellar in Zork I, ALL commands returned "You can't go that way."
**Root Cause**: restore_state() corrupted waiting_for_input state
**Status**: ✅ FIXED

## The Bug

### Symptoms

After successfully descending to the cellar in Zork I (turn ~60 in Opus solver), EVERY subsequent command returned "You can't go that way." regardless of what was typed:

```
🎯 Step 9/12: down
  → The trap door crashes shut...
  Cellar
  You are in a dark and damp cellar...
  ℹ️  ✓ Entered new room

🎯 Step 10/12: d
  → You can't go that way.

🎯 Step 1/11: examine cretin
  → You can't go that way.

🎯 Step 2/11: north
  → You can't go that way.

🎯 Step 3/11: look
  → You can't go that way.

🎯 Step 4/11: inventory
  → You can't go that way.
```

Even non-movement commands like `look` and `inventory` failed!

### Root Cause

**Location**: `zwalker/zmachine.py`, line 1068 in `restore_state()`

The problem was a multi-step sequence:

1. **Turn N**: "down" command successfully enters cellar
   - saved state before command
   - executed "down"
   - moved to new room ✓
   - did NOT restore state (correct)

2. **Turn N+1**: "d" command (try to go down from cellar)
   - saved state (cellar, `waiting_for_input = True`)
   - sent "d" via `send_input()`
   - got output "You can't go that way." (correct - no down exit)
   - detected as blocked ✓
   - called `restore_state(state_before)` to undo the command
   - **BUG**: `restore_state()` set `waiting_for_input = False`! ❌

3. **Turn N+2**: "examine cretin"
   - saved state (cellar, but now `waiting_for_input = False`)
   - called `send_input("examine cretin")`
   - **`send_input()` checked `if self.waiting_for_input` → False!**
   - **Command was never sent to the VM!** ❌
   - called `run()` anyway
   - `get_output()` returned stale output from buffer
   - Result: wrong output, game appears broken

### The Code

**Before (BROKEN)**:
```python
def restore_state(self, state: GameState) -> None:
    """Restore game state"""
    self.memory[:self.header.static_memory] = state.memory
    self.pc = state.pc
    self.stack = list(state.stack)
    self.call_stack = [copy.copy(f) for f in state.call_stack]
    self.locals = list(state.locals)
    self.rng.setstate(state.random_state)
    self.waiting_for_input = False  # ❌ BUG: Unconditionally set to False
    self.pending_input_callback = None
```

**After (FIXED)**:
```python
def restore_state(self, state: GameState) -> None:
    """Restore game state"""
    self.memory[:self.header.static_memory] = state.memory
    self.pc = state.pc
    self.stack = list(state.stack)
    self.call_stack = [copy.copy(f) for f in state.call_stack]
    self.locals = list(state.locals)
    self.rng.setstate(state.random_state)
    # Clear output buffer and input state
    self.output_buffer = ""
    self.waiting_for_input = False
    self.pending_input_callback = None
    # Run until we're waiting for input again to get VM into consistent state
    self.run()  # ✅ FIX: Let VM reach waiting state naturally
```

### Why The Fix Works

After restoring memory/PC/stack state:
1. Clear output buffer (clean slate)
2. Set `waiting_for_input = False` (we're about to run)
3. **Call `run()`** - lets the VM execute until it hits the next input prompt
4. Now `waiting_for_input = True` and VM is in a consistent state
5. Next `send_input()` will work correctly

## Testing

### Test Case: Blocked Command Followed By Valid Command

```python
# This gets blocked and triggers restore_state()
result1 = walker.try_command("down")  # "You can't go that way."
result1.blocked == True  ✓

# This should work after restore
result2 = walker.try_command("inventory")
result2.output == "You are empty-handed."  ✓

# This should also work
result3 = walker.try_command("north")
result3.new_room == True  ✓
```

**Before fix**: result2 and result3 would return wrong output
**After fix**: All work correctly ✓

## Impact

### What Now Works

1. **State restoration after blocked commands** - The VM correctly returns to a playable state
2. **Commands after entering new rooms** - No more "stuck" state after room transitions
3. **Opus solver can progress past cellar** - Can now explore the full game

### What This Unlocks

- Opus solver can now complete Zork I (or make significant progress)
- Batch solving of 20-30 games becomes viable
- Reliable solution generation for z2js testing

## Related Bugs

This is the SECOND critical Z-machine bug fixed today:

1. **BLOCKED_PATTERNS bug** (fixed earlier) - `r"closed"` matched "revealing a closed trap door"
   - Caused rug → trap door sequence to fail

2. **restore_state() bug** (THIS FIX) - `waiting_for_input` not restored correctly
   - Caused ALL commands to fail after entering cellar

Both bugs needed to be fixed for the solver to progress.

## Verification

**Test sequence that now works**:
```
> open mailbox     ✓
> north            ✓
> east             ✓
> east             ✓
> open window      ✓
> enter window     ✓
> west             ✓
> take all         ✓
> turn on lantern  ✓
> move rug         ✓ (BLOCKED_PATTERNS fix)
> open trap door   ✓ (BLOCKED_PATTERNS fix)
> down             ✓ (Both fixes)
> look             ✓ (restore_state fix)
> inventory        ✓ (restore_state fix)
> north            ✓ (restore_state fix)
```

## Files Changed

- `zwalker/zmachine.py` - Fixed `restore_state()` method (line 1060-1073)

## Next Steps

1. ✅ Restart Opus solver on Zork I with both fixes
2. Monitor progress through cellar and beyond
3. If successful, test on other complex games
4. Generate solution set for z2js testing

---

**Bug Status**: ✅ RESOLVED
**Opus Solver**: Running with BOTH critical fixes applied
**Expected outcome**: Solver should now be able to explore the full game without getting stuck
