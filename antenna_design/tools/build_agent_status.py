"""Build antenna_design/status/agents_status.json for tools/agent_status.py.

Sources:
- em/*_OPENEMS_*/: FDTD rounds. Running = solver.log without an 'exit' line, no run_numeric.json and the
  log written in the last 5 minutes. Finished = run_numeric.json present (wall time and worst channel S11).
- status/agents_manual.json: subagent tasks ("agents" running, "done" finished), edited by the orchestrator.
- automation_policy.json: round counter; raised to the highest finished round folder if that is larger.

Usage: python tools/build_agent_status.py
"""
import datetime
import glob
import json
import os
import re

from datetime import timedelta

A = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + '/'
N_DONE = 8


def iso(ts):
    return datetime.datetime.fromtimestamp(ts, datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')


def load(path):
    """JSON or None if missing or half-written (e.g. while the solver or the orchestrator writes it)."""
    try:
        with open(path, encoding='utf-8') as f:
            return json.load(f)
    except (OSError, ValueError):
        return None


def ended_utc(d, r, rn):
    """End time = started_utc + wall_seconds (survives a fresh clone); mtime only as fallback."""
    st = (load(d + '/run_started.json') or {}).get('started_utc')
    if st and r.get('wall_seconds'):
        t = datetime.datetime.fromisoformat(st.replace('Z', '+00:00')) + timedelta(seconds=r['wall_seconds'])
        return t.astimezone(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
    return iso(os.path.getmtime(rn))


def fdtd_entries(now):
    running, done, last_round = [], [], 0
    for d in sorted(glob.glob(A + 'em/*_OPENEMS_*')):
        name = os.path.basename(d)
        m = re.search(r'_OPENEMS_(\d+)$', name)
        if not m:
            continue
        rnd = int(m.group(1))
        mesh = 'extrafina' if '_XFINE_' in name else 'fina' if '_FINE_' in name else 'base'
        task = name.replace('_OPENEMS_', ' · ronda ')
        log = d + '/solver.log'
        rn = d + '/run_numeric.json'
        if os.path.exists(rn):
            r = load(rn)
            if r is None:  # being written right now: try again next cycle
                continue
            last_round = max(last_round, rnd)
            worst = r.get('channel_worst_s11_db')
            if worst is not None:
                task += f" (peor S11 {worst:.2f} dB)".replace('.', ',').replace('-', '−')
            done.append({"agent": "FDTD openEMS", "model": f"malla {mesh} · 2 vCPU", "task": task,
                         "ended": ended_utc(d, r, rn), "dur_s": round(r.get('wall_seconds') or 0)})
            continue
        if not os.path.exists(log):
            continue
        txt = open(log, errors='ignore').read()
        if re.search(r'^exit ', txt, re.M) or now.timestamp() - os.path.getmtime(log) > 300:
            continue
        st = (load(d + '/run_started.json') or {}).get('started_utc') or iso(os.path.getmtime(log))
        steps = re.findall(r'Timestep:\s+(\d+).*?\(([-0-9. ]+)dB\)', txt)
        ts = int(steps[-1][0]) if steps else 0
        cur = float(steps[-1][1].replace(' ', '')) if steps else 0.0  # current energy (openEMS stops on it)
        best = min([float(e.replace(' ', '')) for _, e in steps] or [0.0])
        exp_steps = 36000 if mesh == 'base' else 45000
        # progress: energy decay towards -50 dB blended with timesteps vs the typical count
        p = 0.5 * min(max(-best / 50.0, 0), 1) + 0.5 * min(ts / exp_steps, 1)
        detail = f"paso {ts} de ~{exp_steps} · " + (
            f"energía {cur:.1f} dB, mínima {best:.1f} dB (criterio −50 dB)".replace('-', '−') if best < -0.5
            else "excitación en curso, la energía aún no decae")
        running.append({"agent": "FDTD openEMS", "model": f"malla {mesh} · 2 vCPU", "task": task, "started": st,
                        "progress": round(max(0.0, min(0.99, p)), 3), "detail": detail,
                        "est_s": 900 if mesh == 'base' else 3100})
    return running, done, last_round


def build():
    now = datetime.datetime.now(datetime.timezone.utc)
    man_path = A + 'status/agents_manual.json'
    man = load(man_path) or {"agents": [], "done": []}
    run, fin, last_round = fdtd_entries(now)
    done = sorted(fin + man.get("done", []), key=lambda x: x.get("ended", ""), reverse=True)[:N_DONE]
    pol = load(A + 'automation_policy.json')
    if pol is None:
        raise SystemExit('automation_policy.json unreadable (being edited?): status not rebuilt')
    cr = pol["claude_routine"]
    status = {"updated": now.isoformat(), "running": run + man.get("agents", []), "done": done,
              "rounds": {"used": max(cr["runs_completed"], last_round), "max": cr["max_runs"]}}
    out = A + 'status/agents_status.json'
    old = load(out) or {}
    old.pop('updated', None)
    if {k: v for k, v in status.items() if k != 'updated'} != old:  # keep the tree clean if nothing changed
        with open(out, 'w', encoding='utf-8') as f:
            f.write(json.dumps(status, ensure_ascii=False, indent=1) + '\n')
    return status


if __name__ == '__main__':
    s = build()
    print(f"running {len(s['running'])}, done {len(s['done'])}, rounds {s['rounds']['used']}/{s['rounds']['max']}")
