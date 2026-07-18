#!/usr/bin/env python3
"""Lockstep differ: run the OFFICIAL binary and the zorkie build side by side
through a verified route, comparing ROOM (status-line object, variable 16 = the
first global) and SCORE (variable 17 = second global) after every command.
The first divergence IS the next compiler bug (see WIP.md).

Usage:
    python3 scripts/lockstep.py <official.z3> <zorkie.z3> <walkthrough.txt> [seed] [--ctx N]

Prints a PASS line per N commands, and on divergence: the command index, the
command, both room/score states, and both interpreters' last outputs.
"""
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
from zwalker.walker import GameWalker  # noqa: E402


def state(w):
    """(room-name, score) from the V3 status-line globals."""
    vm = w.vm
    m = vm.memory
    gtab = (m[0x0C] << 8) | m[0x0D]
    g16 = (m[gtab] << 8) | m[gtab + 1]
    g17 = (m[gtab + 2] << 8) | m[gtab + 3]
    try:
        room = vm.get_object_name(g16)
    except Exception:  # noqa: BLE001
        room = f"<obj#{g16}>"
    return room, g17


def load_cmds(path):
    cmds = []
    for line in open(path):
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        cmds.append(line)
    return cmds


def step(w, cmd):
    """Run one command; return (output, fault)."""
    try:
        return w.try_command(cmd, skip_if_tried=False).output, None
    except Exception as e:  # noqa: BLE001
        return "", f"{type(e).__name__}: {e}"


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    official, zorkie_build, wt = args[0], args[1], args[2]
    seed = int(args[3]) if len(args) > 3 else 1
    cmds = load_cmds(wt)

    wa = GameWalker(open(official, "rb").read())
    wa.vm.rng.seed(seed)
    wa.start()
    wb = GameWalker(open(zorkie_build, "rb").read())
    wb.vm.rng.seed(seed)
    wb.start()

    ra_out = rb_out = "(boot)"
    for i, cmd in enumerate(cmds):
        pa_out, pb_out = ra_out, rb_out
        ra_out, fa = step(wa, cmd)
        rb_out, fb = step(wb, cmd)
        (room_a, sc_a) = state(wa)
        (room_b, sc_b) = state(wb)
        if fa or fb or room_a != room_b or sc_a != sc_b:
            print(f"DIVERGE at cmd[{i}] {cmd!r}")
            print(f"  official: room={room_a!r} score={sc_a}" + (f" FAULT={fa}" if fa else ""))
            print(f"  zorkie:   room={room_b!r} score={sc_b}" + (f" FAULT={fb}" if fb else ""))
            print(f"--- official output for cmd[{i-1}..{i}] ---")
            print(pa_out, "\n", ra_out)
            print(f"--- zorkie output for cmd[{i-1}..{i}] ---")
            print(pb_out, "\n", rb_out)
            return 1
        if i % 25 == 0:
            print(f"  ok cmd[{i:3}] {cmd!r:28} room={room_a!r} score={sc_a}")
    print(f"LOCKSTEP CLEAN: {len(cmds)} commands, final room={room_a!r} score={sc_a}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
