"""Native P01 mesh-sensitivity project (P01_OPENEMS_002): prepare, single solve, summarize, compare.

Same geometry/materials/box/port/excitation/frequency vector as p01_openems.py (P01_OPENEMS_001);
ONLY the mesh differs (see MESH constants and MESH_001 below). Two meshes measure sensitivity, not convergence.

Use runtime_env.sh first. No action occurs on import. Solve requires an already
prepared XML, refuses a second launch, and needs an external wall-time limit.
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import hashlib
import importlib.metadata
import json
import math
import os
from pathlib import Path
import re
import resource
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import designs


RUN_ID = "P01_OPENEMS_002"
REFERENCE_ID = "P01_OPENEMS_001"
XML_NAME = "p01_openems.xml"
# Mesh parameters of this run (refinement) and of the reference run 001.
MESH = {"xy_max_step_mm": 0.35, "z_air_max_step_mm": 0.6, "substrate_lines": 11,
        "metal_edge_res_mm": 0.175, "smooth_ratio": 1.4}
MESH_001 = {"xy_max_step_mm": 0.5, "z_air_max_step_mm": 0.8, "substrate_lines": 9,
            "metal_edge_res_mm": 0.25, "smooth_ratio": 1.4}
REF_001 = {"cells": 1795680, "steps": 7587, "cells_per_s": 101449054.4441231,
           "rss_kib": 333300, "actual_dt_s": 5.002169567155493e-13,
           "courant_ref_dt_s": 4.418164372450769e-13, "engine_wall_s": 137.74067}
BAND = (7737600000, 8236800000)


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def build(out):
    import numpy as np
    from CSXCAD import ContinuousStructure
    from openEMS import openEMS

    candidate = designs.candidates()["P01_rectangular_patch"]
    xs, ys = zip(*candidate["patch"])
    fx, fy = candidate["feed"]
    h = designs.H_MM
    fdtd = openEMS(NrTS=30000, EndCriteria=1e-5)
    fdtd.SetGaussExcite(designs.F0_HZ, 1e9)
    fdtd.SetBoundaryCond(["PML_8"] * 6)
    csx = ContinuousStructure()
    fdtd.SetCSX(csx)
    mesh = csx.GetGrid()
    mesh.SetDeltaUnit(1e-3)
    mesh.AddLine("x", [-35, -13, 13, 35])
    mesh.AddLine("y", [-35, -13, 13, 35])
    mesh.AddLine("z", [-25, *np.linspace(0, h, MESH["substrate_lines"]), 35])
    kappa = 2 * math.pi * designs.F0_HZ * 8.8541878128e-12 * designs.ER * designs.TAN_D
    substrate = csx.AddMaterial("generic_FR4_PROVISIONAL", epsilon=designs.ER, kappa=kappa)
    substrate.AddBox([-13, -13, 0], [13, 13, h], priority=0)
    patch = csx.AddConductingSheet("patch_copper", conductivity=5.8e7, thickness=35e-6)
    patch.AddBox([min(xs), min(ys), h], [max(xs), max(ys), h], priority=10)
    ground = csx.AddConductingSheet("ground_copper", conductivity=5.8e7, thickness=35e-6)
    ground.AddBox([-13, -13, 0], [13, 13, 0], priority=10)
    # Conducting sheets retain SI thickness without a 35 um volume-mesh cell.
    assert patch.GetConductivity() == 5.8e7 and patch.GetThickness() == 35e-6
    assert ground.GetThickness() == 35e-6
    fdtd.AddEdges2Grid(dirs="xy", properties=patch, metal_edge_res=MESH["metal_edge_res_mm"])
    fdtd.AddEdges2Grid(dirs="xy", properties=ground)
    port = fdtd.AddLumpedPort(1, 50, [fx, fy, 0], [fx, fy, h], "z", 1.0,
                              priority=5, edges2grid="xy")
    mesh.SmoothMeshLines("x", MESH["xy_max_step_mm"], MESH["smooth_ratio"])
    mesh.SmoothMeshLines("y", MESH["xy_max_step_mm"], MESH["smooth_ratio"])
    mesh.SmoothMeshLines("z", MESH["z_air_max_step_mm"], MESH["smooth_ratio"])
    axes = {axis: np.asarray(mesh.GetLines(axis), dtype=float) for axis in "xyz"}
    mesh_info = {}
    for axis, values in axes.items():
        gaps = np.diff(values)
        if not np.all(gaps > 0):
            raise RuntimeError(f"Nonmonotone {axis} mesh")
        ratio = float(np.max(np.maximum(gaps[1:] / gaps[:-1], gaps[:-1] / gaps[1:])))
        if ratio > 1.4 + 1e-8:
            raise RuntimeError(f"Mesh grading {axis}: {ratio} exceeds 1.4")
        mesh_info[axis] = {"cells": len(values) - 1, "min_step_mm": float(gaps.min()),
                           "max_step_mm": float(gaps.max()), "max_neighbor_ratio": ratio,
                           "pml_inner_low_mm": float(values[8]), "pml_inner_high_mm": float(values[-9])}
    for axis, value in zip("xyz", [fx, fy, h]):
        if not np.any(np.isclose(axes[axis], value, atol=1e-12, rtol=0)):
            raise RuntimeError(f"Port misses grid on {axis}")
    cells = math.prod(info["cells"] for info in mesh_info.values())
    cfl = 1 / (designs.C0 * math.sqrt(sum((info["min_step_mm"] * 1e-3) ** -2 for info in mesh_info.values())))
    out.mkdir(parents=True, exist_ok=True)
    fdtd.Write2XML(str(out / XML_NAME))
    if not (out / XML_NAME).is_file():
        raise RuntimeError("Native XML export failed")
    with (out / "native_mesh.csv").open("w", newline="") as stream:
        writer = csv.writer(stream, lineterminator="\n")
        writer.writerow(["axis", "coordinate_mm"])
        for axis, values in axes.items():
            writer.writerows((axis, float(value)) for value in values)
    # Time model: cells*steps / throughput of 001; steps scale inversely with the CFL timestep
    # (same ~3.8 ns physical record assumed as 001, which is itself an assumption).
    dt_scale = cfl / REF_001["courant_ref_dt_s"]
    est_dt = REF_001["actual_dt_s"] * dt_scale
    est_steps = int(round(REF_001["steps"] / dt_scale))
    est_time = cells * est_steps / REF_001["cells_per_s"]
    budget = {"maximum_CPUs_threads": 2,
              "estimated_RAM_bytes": cells * 2048,
              "RAM_basis": "conservative 2048 bytes/cell, unmeasured",
              "estimated_RAM_bytes_scaled_from_001_RSS": int(REF_001["rss_kib"] * 1024 * cells / REF_001["cells"]),
              "RAM_scaled_basis": "001 measured RSS 325.5 MiB / 1795680 cells, scaled linearly by cells",
              "yee_min_cell_reference_step_s": cfl, "maximum_record_if_reference_step_s": cfl * 30000,
              "timestep_caveat": "uniform-min-cell Yee reference only; solver Rennings timestep can differ; read actual solver statistics",
              "estimated_actual_timestep_s": est_dt, "estimated_timesteps": est_steps,
              "estimated_engine_seconds": est_time,
              "time_basis": "cells*steps/101.449 Mcell/s (001); steps scale with 1/CFL min-cell step; assumes same physical record as 001",
              "maximum_timesteps": 30000,
              "external_wall_limit_required_s": int(min(2400, max(900, 3 * est_time))),
              "abort_rule": "do not launch if conservative RAM > 8 GiB or estimated time > 1800 s"}
    metadata = {
        "id": RUN_ID, "design_id": "P01_rectangular_patch", "status": "PREPARED_NOT_RUN", "reference_run": REFERENCE_ID,
        "openEMS_version": importlib.metadata.version("openEMS"),
        "CSXCAD_version": importlib.metadata.version("CSXCAD"),
        "script_sha256": sha256(__file__), "geometry_source_sha256": sha256(ROOT / "designs.py"),
        "native_xml_sha256": sha256(out / XML_NAME),
        "center_hz": designs.F0_HZ, "channel_band_hz": list(BAND),
        "materials": {"substrate": "generic FR4 provisional; not manufacturer specified",
                      "eps_r": designs.ER, "tan_delta_at_f0": designs.TAN_D, "h_mm": h,
                      "dielectric_conductivity_S_m": kappa, "dielectric_loss_model": "constant conductivity; tan_delta(f)=tan_delta(f0)*f0/f",
                      "metal_model": "2D finite conducting sheet", "conductivity_S_m": 5.8e7,
                      "sheet_thickness_m": patch.GetThickness(), "sheet_API_roundtrip_verified": True,
                      "roughness": "not modeled"},
        "port": {"reference_ohm": 50, "start_mm": [fx, fy, 0], "stop_mm": [fx, fy, h],
                 "type": "ideal vertical lumped line; no pin/coax connector/aperture/deembedding", "priority": 5},
        "mesh": mesh_info, "total_cells": cells,
        "budget_before_solve": budget,
        "mesh_definition": MESH, "mesh_reference_001": MESH_001,
        "mesh_difference_vs_001": {
            "changed_only": "mesh", "reference_run": REFERENCE_ID,
            "xy_max_step_mm": [MESH_001["xy_max_step_mm"], MESH["xy_max_step_mm"]],
            "z_air_max_step_mm": [MESH_001["z_air_max_step_mm"], MESH["z_air_max_step_mm"]],
            "substrate_lines": [MESH_001["substrate_lines"], MESH["substrate_lines"]],
            "substrate_cells": [MESH_001["substrate_lines"] - 1, MESH["substrate_lines"] - 1],
            "metal_edge_res_mm": [MESH_001["metal_edge_res_mm"], MESH["metal_edge_res_mm"]],
            "total_cells": [REF_001["cells"], cells],
            "unchanged": "geometry, materials, box, PML_8, 50 ohm lumped port position, Gaussian excitation, EndCriteria 1e-5, NrTS 30000, frequency vector"},
        "boundaries": "PML_8 all six; coordinates mm",
        "excitation": {"type": "Gaussian", "center_hz": designs.F0_HZ, "corner_offset_hz": 1e9},
        "energy_end_criterion": 1e-5, "mesh_convergence": "NOT_ESTABLISHED: two meshes measure sensitivity only",
        "far_field": "not recorded; gain/efficiency/radiated group delay unavailable",
    }
    return fdtd, port, metadata


def summarize(out):
    log = (out / "solver.log").read_text()
    result = json.loads((out / "run_numeric.json").read_text()) if (out / "run_numeric.json").exists() else {}
    decay = re.findall(r"end-criteria of -([\d.]+)dB reached after (\d+) timesteps \(-([\d.]+)dB\)", log)
    result["energy_end_criterion_met"] = bool(decay)
    result["maximum_timesteps_warning"] = "Max. number of timesteps was reached" in log
    if (out / "openEMS_stats.txt").exists():
        values = [float(line.split()[0]) for line in (out / "openEMS_stats.txt").read_text().splitlines() if line.strip() and not line.startswith("%")]
        if len(values) >= 6:
            result["solver_nodal_positions"] = int(values[0])
            result["actual_timestep_s"] = values[1]
            result["actual_record_time_s"] = values[3]
            result["engine_wall_seconds"] = values[4]
            result["engine_cells_per_second"] = values[5]
            result["inverse_record_time_hz"] = 1 / values[3]
    result["mesh_convergence"] = "NOT_ESTABLISHED"
    result["evidence"] = "EM_SIMULATED" if result.get("numeric_outputs_finite") and decay else "EM_RUN_INCOMPLETE"
    if decay:
        result["actual_timesteps"] = int(decay[-1][1])
        result["final_energy_decay_db"] = -float(decay[-1][2])
    (out / "result.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


def compare(out, ref):
    """Compare this run against 001 on the identical frequency vector. Sensitivity only."""
    import numpy as np
    def load(path):
        return np.genfromtxt(path, delimiter=",", names=True)
    a, b = load(ref / "s11_complex.csv"), load(out / "s11_complex.csv")
    if a["frequency_hz"].shape != b["frequency_hz"].shape or not np.allclose(a["frequency_hz"], b["frequency_hz"], rtol=0, atol=1e-3):
        raise RuntimeError("Frequency vectors differ; comparison refused")
    f = a["frequency_hz"]
    sa, sb = a["s11_real"] + 1j * a["s11_imag"], b["s11_real"] + 1j * b["s11_imag"]
    da, db_ = 20 * np.log10(np.abs(sa)), 20 * np.log10(np.abs(sb))
    band = (f >= BAND[0]) & (f <= BAND[1])
    def stats(db, s):
        i = int(np.argmax(np.where(band, db, -np.inf)))
        j = int(np.argmin(db))
        return {"channel_worst_s11_db": float(db[band].max()), "channel_worst_frequency_hz": float(f[i]),
                "channel_best_s11_db": float(db[band].min()),
                "min_abs_s11_db_7p5_8p5GHz": float(db[j]), "min_abs_s11_frequency_hz": float(f[j]),
                "meets_minus6db_all_channel_samples": bool(np.all(db[band] <= -6)),
                "meets_minus10db_all_channel_samples": bool(np.all(db[band] <= -10)),
                "channel_samples_above_minus6db": int(np.sum(db[band] > -6))}
    dd = np.abs(db_ - da)
    ds = np.abs(sb - sa)
    result = {"mesh_001": stats(da, sa), "mesh_002": stats(db_, sb),
              "samples": int(f.size), "channel_samples": int(band.sum()),
              "max_abs_delta_s11_complex_channel": float(ds[band].max()),
              "max_abs_delta_s11_complex_all": float(ds.max()),
              "max_abs_delta_s11_db_channel": float(dd[band].max()),
              "mean_abs_delta_s11_db_channel": float(dd[band].mean()),
              "max_abs_delta_s11_db_all": float(dd.max()),
              "delta_min_frequency_hz": float(f[int(np.argmin(db_))] - f[int(np.argmin(da))]),
              "interpretation": "Sensitivity of S11 to two meshes only; mesh convergence NOT_ESTABLISHED. No far field: gain/efficiency/radiated group delay unavailable.",
              "mesh_convergence": "NOT_ESTABLISHED"}
    (out / "mesh_comparison.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        fig, ax = plt.subplots(figsize=(7, 4))
        ax.plot(f / 1e9, da, label=f"{REFERENCE_ID} (coarse mesh)")
        ax.plot(f / 1e9, db_, label=f"{RUN_ID} (fine mesh)")
        ax.axvspan(BAND[0] / 1e9, BAND[1] / 1e9, color="0.9", label="channel 9")
        ax.axhline(-6, ls="--", c="r", lw=.8); ax.axhline(-10, ls=":", c="g", lw=.8)
        ax.set_xlabel("Frequency (GHz)"); ax.set_ylabel("|S11| (dB), 50 ohm ideal lumped port")
        ax.set_title("P01 mesh sensitivity (EM_SIMULATED, convergence not established)")
        ax.grid(alpha=.3); ax.legend(fontsize=8)
        fig.tight_layout(); fig.savefig(out / "s11.png", dpi=130)
    except Exception as exc:  # figure is optional
        print("figure skipped:", exc)


def main():
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("mode", choices=["prepare", "solve", "summarize", "compare"])
    cli.add_argument("--out", type=Path, required=True)
    args = cli.parse_args()
    out = args.out.resolve()
    if args.mode == "summarize":
        summarize(out)
        return
    if args.mode == "compare":
        compare(out, out.parent / REFERENCE_ID)
        return
    if (out / "run_started.json").exists():
        raise RuntimeError("Refusing overwrite/relaunch of a started P01 solve")
    previous = json.loads((out / "prepared.json").read_text()) if (out / "prepared.json").exists() else None
    fdtd, port, metadata = build(out)
    if args.mode == "prepare":
        (out / "prepared.json").write_text(json.dumps(metadata, indent=2) + "\n")
        print(json.dumps(metadata, indent=2), flush=True)
        return
    if previous is None or previous["native_xml_sha256"] != metadata["native_xml_sha256"]:
        raise RuntimeError("Solve requires the same reviewed prepared native XML")
    if len(os.sched_getaffinity(0)) > 2:
        raise RuntimeError("Solve requires CPU affinity restricted to at most two CPUs")
    with (out / "run_started.json").open("x") as stream:
        json.dump({"started_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
                   "cpu_affinity": sorted(os.sched_getaffinity(0)), "native_xml_sha256": metadata["native_xml_sha256"]}, stream, indent=2)
    started = time.monotonic()
    status = fdtd.Run(str(out), cleanup=False, numThreads=2, dump_statistics=True, verbose=1)
    if status not in (None, 0):
        raise RuntimeError(f"FDTD setup failed with code {status}")
    import numpy as np
    freq = np.unique(np.r_[np.linspace(7.5e9, 8.5e9, 1001), BAND[0], BAND[1]])
    port.CalcPort(str(out), freq)
    s11 = port.uf_ref / port.uf_inc
    zin = port.uf_tot / port.if_tot
    arrays = [freq, s11.real, s11.imag, zin.real, zin.imag, port.uf_inc.real, port.uf_inc.imag,
              port.uf_ref.real, port.uf_ref.imag, port.uf_tot.real, port.uf_tot.imag, port.if_tot.real, port.if_tot.imag]
    data = np.column_stack(arrays)
    if not np.all(np.isfinite(data)):
        raise RuntimeError("Non-finite P01 port outputs")
    np.savetxt(out / "s11_complex.csv", data, delimiter=",", comments="", fmt="%.16e",
               header="frequency_hz,s11_real,s11_imag,zin_real_ohm,zin_imag_ohm,u_inc_real,u_inc_imag,u_ref_real,u_ref_imag,u_tot_real,u_tot_imag,i_tot_real,i_tot_imag")
    band = (freq >= BAND[0]) & (freq <= BAND[1])
    db = 20 * np.log10(np.abs(s11))
    usage = resource.getrusage(resource.RUSAGE_SELF)
    result = {"id": metadata["id"], "numeric_outputs_finite": True,
              "samples": len(freq), "channel_samples": int(band.sum()), "reference_ohm": 50,
              "channel_worst_s11_db": float(db[band].max()),
              "channel_best_s11_db": float(db[band].min()),
              "channel_meets_minus6db_on_sampled_grid": bool(np.all(db[band] <= -6)),
              "channel_meets_minus10db_on_sampled_grid": bool(np.all(db[band] <= -10)),
              "wall_seconds": time.monotonic() - started, "cpu_seconds": usage.ru_utime + usage.ru_stime,
              "peak_rss_kib": usage.ru_maxrss, "cpu_affinity": sorted(os.sched_getaffinity(0)),
              "frequency_evaluation_step_hz": 1e6,
              "frequency_grid_caveat": "DTFT evaluation spacing is not physical resolution; finite-record decay/truncation governs accuracy",
              "coverage_caveat": "sampled frequencies including exact endpoints; no mathematical guarantee between samples",
              "native_xml_sha256": metadata["native_xml_sha256"], "far_field": "NOT_RECORDED"}
    (out / "run_numeric.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2), flush=True)


if __name__ == "__main__":
    main()
