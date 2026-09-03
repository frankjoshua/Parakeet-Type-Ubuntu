"""Self-check: Wayland control path.

On Wayland the app cannot grab hotkeys, so the compositor runs
`parakeet-dictation --toggle`, which is delivered over a Unix socket to the
running instance and dispatched on the GTK loop.  Also checks the wtype
backspace burst is one process, not one per key.

Run with the app venv: .venv/bin/python3 test_control_socket.py
"""
import subprocess
import tempfile
from pathlib import Path
from unittest import mock

import dictation_app as da
from gi.repository import GLib

failures = []


def check(tag, ok, detail=""):
    print(f"{'PASS' if ok else 'FAIL'} {tag} {detail}", flush=True)
    if not ok:
        failures.append(tag)


# --- 1. socket round trip -------------------------------------------------
with tempfile.TemporaryDirectory() as d:
    da.CONTROL_SOCKET = Path(d) / "ctl.sock"
    check("no listener -> False", da.send_control("toggle") is False)

    got = []
    srv = da.serve_control_socket({c: (lambda c=c: got.append(c))
                                   for c in da.CONTROL_COMMANDS})
    for cmd in ("toggle", "pause", "bogus", "stop"):
        check(f"send {cmd}", da.send_control(cmd))
    ctx = GLib.MainContext.default()
    for _ in range(20):
        ctx.iteration(False)
    check("dispatched in order, unknown ignored", got == ["toggle", "pause", "stop"], got)
    srv.close()

# --- 2. wtype backspaces are one process ------------------------------------
calls = []
with mock.patch.object(subprocess, "run", side_effect=lambda a, **k: calls.append(a)):
    da.TextTyper("wtype")._send_backspaces(3)
check("one wtype call", len(calls) == 1, calls)
check("three -k BackSpace", calls and calls[0] == ["wtype"] + ["-k", "BackSpace"] * 3)

raise SystemExit(1 if failures else 0)
