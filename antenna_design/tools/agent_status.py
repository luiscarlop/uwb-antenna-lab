#!/usr/bin/env python3
"""Terminal progress view of the antenna-lab agents and openEMS runs (no dependencies, Python >= 3.8).

The orchestrator (Claude Code cloud session) writes antenna_design/status/agents_status.json and pushes it to the
branch codex/uwb-ch9-antenna-design whenever it launches or receives a task, or when an FDTD run advances.
This script reads that file and draws one progress bar per running task, refreshing itself.

Usage
  From a clone of the repo (after `git pull`):
      python antenna_design/tools/agent_status.py --file antenna_design/status/agents_status.json --watch 10
  Directly from GitHub (private repo: needs a read token in the env var GITHUB_TOKEN, scope "contents: read"):
      set GITHUB_TOKEN=...            (Windows cmd)   |  export GITHUB_TOKEN=...   (bash)
      python agent_status.py --github luiscarlop/TFG_Beamforming_FBD --watch 30
  --once prints a single snapshot. Ctrl+C exits.

How progress is estimated
  * FDTD openEMS: measured, from its solver.log at the time of the last status update (time step vs the usual
    ~36000 on the base mesh / ~45000 on the fine mesh, and energy decay towards the -50 dB criterion); between
    updates it is extrapolated.
  * Subagents (Sonnet/Fable/Haiku): they do not report internal progress; the bar is elapsed time vs the typical
    duration of similar tasks, capped at 95 % until they finish (shown with a hatched bar and «estimado»).
"""
from __future__ import annotations

import argparse
import base64
import datetime as dt
import json
import os
import shutil
import sys
import time
import urllib.request

BRANCH = "codex/uwb-ch9-antenna-design"
PATH = "antenna_design/status/agents_status.json"


def load(args):
    if args.file:
        with open(args.file, encoding="utf-8") as fh:
            return json.load(fh)
    url = f"https://api.github.com/repos/{args.github}/contents/{PATH}?ref={args.branch}"
    req = urllib.request.Request(url, headers={"Accept": "application/vnd.github+json", "User-Agent": "agent-status"})
    tok = os.environ.get("GITHUB_TOKEN")
    if tok:
        req.add_header("Authorization", "Bearer " + tok)
    with urllib.request.urlopen(req, timeout=15) as r:
        data = json.load(r)
    return json.loads(base64.b64decode(data["content"]).decode("utf-8"))


def ago(iso):
    return (dt.datetime.now(dt.timezone.utc) - dt.datetime.fromisoformat(iso.replace("Z", "+00:00"))).total_seconds()


def fmt(s):
    s = max(0, int(round(s)))
    m, r = divmod(s, 60)
    return f"{m // 60} h {m % 60:02d} min" if m >= 60 else f"{m} min {r:02d} s"


def progress(t, since_update):
    est = t.get("est_s") or 600
    if t.get("progress") is not None:
        p0 = t["progress"]
        return min(0.99, p0 + since_update / est * (1 - p0) * 0.5), True
    return min(0.95, ago(t["started"]) / est), False


def render(st, color):
    cols = max(60, min(shutil.get_terminal_size((100, 30)).columns, 110))
    c = (lambda code, s: f"\033[{code}m{s}\033[0m") if color else (lambda code, s: s)
    up = ago(st["updated"])
    out = [c("1", "Agentes del laboratorio de antenas · canal 9"),
           c("2", f"Última actualización hace {fmt(up)} · rondas {st['rounds']['used']} de {st['rounds']['max']}"), ""]
    if not st["running"]:
        out.append("  Ningún agente ni simulación en marcha.")
    for t in st["running"]:
        p, measured = progress(t, up)
        w = cols - 12
        n = int(round(p * w))
        bar = ("█" * n if measured else "▚" * n) + "░" * (w - n)
        el = ago(t["started"])
        left = max(0, (t.get("est_s") or 600) - el)
        out.append(c("1", f"  {t['agent']}") + c("2", f"  ({t['model']})"))
        out.append(f"  {t['task']}")
        out.append("  " + c("34" if measured else "36", bar) + f" {p * 100:4.0f} %")
        out.append(c("2", f"  {'medido' if measured else 'estimado por tiempo'} · {t.get('detail', '')}"))
        out.append(c("2", f"  lleva {fmt(el)}" + (f" · quedan ~{fmt(left)}" if p < 0.95 else "")))
        out.append("")
    if st.get("done"):
        out.append(c("1", "  Terminadas recientemente"))
        for d in st["done"][:6]:
            out.append(c("2", f"   · {d['agent']} ({d['model']}): {d['task']} — {fmt(d['dur_s'])}, hace {fmt(ago(d['ended']))}"))
    return "\n".join(out)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    src = ap.add_mutually_exclusive_group(required=True)
    src.add_argument("--file", help="local agents_status.json (from a git pull)")
    src.add_argument("--github", metavar="OWNER/REPO", help="read the status file from GitHub")
    ap.add_argument("--branch", default=BRANCH)
    ap.add_argument("--watch", type=float, default=0, help="redraw every N s (reloads the file/GitHub every 60 s)")
    ap.add_argument("--no-color", action="store_true")
    a = ap.parse_args()
    if os.name == "nt":
        os.system("")  # enables ANSI escape codes in the Windows console
    color = not a.no_color and sys.stdout.isatty()
    st, loaded = load(a), time.time()
    if not a.watch:
        print(render(st, color))
        return
    try:
        while True:
            if time.time() - loaded > max(60, a.watch):
                try:
                    st, loaded = load(a), time.time()
                except Exception as e:  # keep the last snapshot if GitHub/the file is momentarily unavailable
                    print(f"(no se pudo recargar: {e})")
            print("\033[2J\033[H" if color else "\n" * 2, end="")
            print(render(st, color))
            time.sleep(a.watch)
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
