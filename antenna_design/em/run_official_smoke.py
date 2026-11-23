"""Bounded official rectangular-waveguide example with numerical CSV output.

Geometry, mesh, excitation, step count and postprocessing are upstream's.
Only output path, two-thread limit, dump suppression and plotting are adapted.
External launcher must enforce a 60 s wall-time limit and two-CPU affinity.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
from pathlib import Path
import resource
import time


def main():
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("--source", type=Path, required=True)
    cli.add_argument("--out", type=Path, required=True)
    args = cli.parse_args()
    out = args.out.resolve()
    out.mkdir(parents=True, exist_ok=False)
    source = args.source.read_text()
    import numpy as np
    import matplotlib.pyplot as plt
    plt.show = lambda: None
    original = "Sim_Path = os.path.join(tempfile.gettempdir(), 'Rect_WG')"
    assert original in source
    source = source.replace(original, f"Sim_Path = {str(out)!r}")
    original = "FDTD.Run(Sim_Path, cleanup=True)"
    assert original in source
    source = source.replace(original, "FDTD.Write2XML(os.path.join(Sim_Path, 'official_waveguide.xml'))\n    FDTD.Run(Sim_Path, cleanup=False, numThreads=2, disable_dumps=True, dump_statistics=True)")
    (out / "adapted_official_waveguide.py").write_text(source)
    started = time.monotonic()
    namespace = {"__name__": "__main__"}
    exec(compile(source, str(args.source), "exec"), namespace)
    freq, s11, s21, impedance, analytic = (namespace[key] for key in ("freq", "s11", "s21", "ZL", "ZL_a"))
    data = np.column_stack([freq, s11.real, s11.imag, s21.real, s21.imag,
                            impedance.real, impedance.imag, np.real(analytic)])
    if not np.all(np.isfinite(data)):
        raise RuntimeError("Non-finite official example outputs")
    np.savetxt(out / "waveguide_complex.csv", data, delimiter=",", comments="",
               header="frequency_hz,s11_real,s11_imag,s21_real,s21_imag,zin_real_ohm,zin_imag_ohm,analytic_ohm")
    u = resource.getrusage(resource.RUSAGE_SELF)
    metrics = {"test": "official_Rect_Waveguide", "solver_executed": True,
               "upstream_source_sha256": hashlib.sha256(args.source.read_bytes()).hexdigest(),
               "openEMS_python_version": importlib.metadata.version("openEMS"),
               "CSXCAD_python_version": importlib.metadata.version("CSXCAD"),
               "frequency_range_hz": [float(freq[0]), float(freq[-1])],
               "samples": len(freq), "max_s11_abs": float(np.max(np.abs(s11))),
               "min_s21_abs": float(np.min(np.abs(s21))),
               "max_real_impedance_relative_error": float(np.max(np.abs(impedance.real - analytic) / np.abs(analytic))),
               "wall_seconds": time.monotonic() - started,
               "cpu_seconds": u.ru_utime + u.ru_stime, "peak_rss_kib": u.ru_maxrss,
               "limitations": "installation smoke test, not antenna validation; finite outputs alone do not establish numerical accuracy"}
    (out / "smoke_result.json").write_text(json.dumps(metrics, indent=2) + "\n")
    print(json.dumps(metrics, indent=2), flush=True)


if __name__ == "__main__":
    main()
