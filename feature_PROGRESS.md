# Progress: feature

Started: Thu Feb  5 07:59:38 EST 2026

## Status

IN_PROGRESS

## Goal
Extend zwalker to play at least 130 games to completion.

## Current State
- 73 solution files exist in solutions/ directory (excluding batch_summary.json)
- 55 games marked as "pass" in game_list.txt (updated)
- 172 games total in game_list.txt (71 newly added)
- 116 games marked as "untested" in game_list.txt
- Need 57 more solved games to reach 130 total (73 + 57 = 130)

## Task List

### Phase 1: Audit and Sync Game List
- [x] Task 1: Audit existing solutions against game_list.txt
  - Count actual solution files (73 found, excluding batch_summary.json)
  - Update game_list.txt to mark solved games as "pass"
  - Identify which solutions correspond to which game_list entries
  - Created scripts/audit_solutions.py
  - Found 52 matches, updated 1 entry, 55 games now marked as "pass"
  - 21 solutions don't match game_list (games not in list or name variations)

### Phase 2: Expand Game Collection
- [x] Task 2: Find and add 50+ more Z-machine games to game_list.txt
  - Searched IFDB top 150 for Z-machine games not in current list
  - Searched IF Archive for additional quality games
  - Added 71 new games to game_list.txt (from 101 to 172 total)
  - Format distribution: 48 z5, 10 z8, 13 zblorb, 1 z3, 1 z6
  - Now have 172 total games (73 solved, 99 untested)

### Phase 3: Batch Solve Games
- [ ] Task 3: Download all untested game files from game_list.txt
- [ ] Task 4: Run batch solver on all untested games
  - Use scripts/batch_solve_all.py or solve_game.py
  - Target: solve 52+ new games to reach 130 total
- [ ] Task 5: Update game_list.txt with results (pass/fail status)
- [ ] Task 6: For any failed games, try advanced Opus solver
- [ ] Task 7: Verify we have 130+ games with solution files

### Phase 4: Validation
- [ ] Task 8: Run tests to verify solutions work
- [ ] Task 9: Generate test scripts for new solutions
- [ ] Task 10: Update TODO.md with new game count

## Tasks Completed

### Iteration 1
- Created scripts/audit_solutions.py to match solutions with game_list entries
- Updated game_list.txt with pass/fail status for solved games (55 now marked as pass)
- Added 71 new Z-machine games to game_list.txt from IF Archive & IFDB
- Game list expanded from 101 to 172 total games

