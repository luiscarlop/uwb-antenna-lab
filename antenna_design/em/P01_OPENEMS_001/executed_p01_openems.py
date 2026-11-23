"""Native P01 project: explicit prepare, single solve, and log-based summary.

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
    mesh.AddLine("z", [-25, *np.linspace(0, h, 9), 35])
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
    fdtd.AddEdges2Grid(dirs="xy", properties=patch, metal_edge_res=.25)
    fdtd.AddEdges2Grid(dirs="xy", properties=ground)
    port = fdtd.AddLumpedPort(1, 50, [fx, fy, 0], [fx, fy, h], "z", 1.0,
                              priority=5, edges2grid="xy")
    mesh.SmoothMeshLines("x", .5, 1.4)
    mesh.SmoothMeshLines("y", .5, 1.4)
    mesh.SmoothMeshLines("z", .8, 1.4)
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
    fdtd.Write2XML(str(out / "p01_openems.xml"))
    if not (out / "p01_openems.xml").is_file():
        raise RuntimeError("Native XML export failed")
    with (out / "native_mesh.csv").open("w", newline="") as stream:
        writer = csv.writer(stream, lineterminator="\n")
        writer.writerow(["axis", "coordinate_mm"])
        for axis, values in axes.items():
            writer.writerows((axis, float(value)) for value in values)
    metadata = {
        "id": "P01_OPENEMS_001", "design_id": "P01_rectangular_patch", "status": "PREPARED_NOT_RUN",
        "openEMS_version": importlib.metadata.version("openEMS"),
        "CSXCAD_version": importlib.metadata.version("CSXCAD"),
        "script_sha256": sha256(__file__), "geometry_source_sha256": sha256(ROOT / "designs.py"),
        "native_xml_sha256": sha256(out / "p01_openems.xml"),
        "center_hz": designs.F0_HZ, "channel_band_hz": [7737600000, 8236800000],
        "materials": {"substrate": "generic FR4 provisional; not manufacturer specified",
                      "eps_r": designs.ER, "tan_delta_at_f0": designs.TAN_D, "h_mm": h,
                      "dielectric_conductivity_S_m": kappa, "dielectric_loss_model": "constant conductivity; tan_delta(f)=tan_delta(f0)*f0/f",
                      "metal_model": "2D finite conducting sheet", "conductivity_S_m": 5.8e7,
                      "sheet_thickness_m": patch.GetThickness(), "sheet_API_roundtrip_verified": True,
                      "roughness": "not modeled"},
        "port": {"reference_ohm": 50, "start_mm": [fx, fy, 0], "stop_mm": [fx, fy, h],
                 "type": "ideal vertical lumped line; no pin/coax connector/aperture/deembedding", "priority": 5},
        "mesh": mesh_info, "total_cells": cells,
        "budget_before_solve": {"maximum_CPUs_threads": 2, "estimated_RAM_bytes": cells * 2048,
                                "RAM_basis": "conservative 2048 bytes/cell, unmeasured",
                                "courant_upper_bound_s": cfl, "maximum_record_upper_bound_s": cfl * 30000,
                                "maximum_timesteps": 30000, "external_wall_limit_required_s": 900},
        "boundaries": "PML_8 all six; coordinates mm",
        "excitation": {"type": "Gaussian", "center_hz": designs.F0_HZ, "corner_offset_hz": 1e9},
        "energy_end_criterion": 1e-5, "mesh_convergence": "NOT_ESTABLISHED: single mesh",
        "far_field": "not recorded; gain/efficiency/radiated group delay unavailable",
    }
    return fdtd, port, metadata


def summarize(out):
    log = (out / "solver.log").read_text()
    result = json.loads((out / "run_numeric.json").read_text()) if (out / "run_numeric.json").exists() else {}
    decay = re.findall(r"end-criteria of -([\d.]+)dB reached after (\d+) timesteps \(-([\d.]+)dB\)", log)
    result["energy_end_criterion_met"] = bool(decay)
    result["maximum_timesteps_warning"] = "Max. number of timesteps was reached" in log
    result["mesh_convergence"] = "NOT_ESTABLISHED"
    result["evidence"] = "EM_SIMULATED" if result.get("numeric_outputs_finite") and decay else "EM_RUN_INCOMPLETE"
    if decay:
        result["actual_timesteps"] = int(decay[-1][1])
        result["final_energy_decay_db"] = -float(decay[-1][2])
    (out / "result.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


def main():
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("mode", choices=["prepare", "solve", "summarize"])
    cli.add_argument("--out", type=Path, required=True)
    args = cli.parse_args()
    out = args.out.resolve()
    if args.mode == "summarize":
        summarize(out)
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
    freq = np.unique(np.r_[np.linspace(7.5e9, 8.5e9, 1001), 7737600000, 8236800000])
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
    band = (freq >= 7737600000) & (freq <= 8236800000)
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
