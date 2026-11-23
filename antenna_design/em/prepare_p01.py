"""Export a declarative P01 model and conservative resource estimate; no solve.

This specification is not an openEMS XML project or an EM simulation result.
An executable implementation still requires review with installed openEMS/CSXCAD.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from pathlib import Path
import sys

DESIGN_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(DESIGN_ROOT))
import designs


def subdivide(anchors, max_step):
    points = sorted(set(anchors))
    values = [points[0]]
    for start, stop in zip(points, points[1:]):
        count = math.ceil((stop - start) / max_step)
        values.extend(start + (stop - start) * i / count for i in range(1, count + 1))
    return values


def specification():
    candidate = designs.candidates()["P01_rectangular_patch"]
    xs, ys = zip(*candidate["patch"])
    fx, fy = candidate["feed"]
    grid = {"x": subdivide([-35, -13, min(xs), fx, max(xs), 13, 35], .5),
            "y": subdivide([-35, -13, min(ys), fy, max(ys), 13, 35], .5),
            "z": subdivide([-25, *[i * designs.H_MM / 8 for i in range(9)], 35], .8)}
    shape = [len(grid[axis]) - 1 for axis in "xyz"]
    cells = math.prod(shape)
    min_steps = [min(b - a for a, b in zip(grid[axis], grid[axis][1:])) * .001 for axis in "xyz"]
    courant_s = 1 / (designs.C0 * math.sqrt(sum(step ** -2 for step in min_steps)))
    spec = {
        "id": "P01_EM_MODEL_SPEC_V1", "design_id": "P01_rectangular_patch",
        "evidence": "GEOMETRY_ONLY", "em_status": "EM_NOT_RUN",
        "artifact_type": "declarative_model_specification_not_solver_XML",
        "implementation_validation": "NOT_VALIDATED_WITH_OPENEMS",
        "source_geometry_sha256": hashlib.sha256((DESIGN_ROOT / "designs.py").read_bytes()).hexdigest(),
        "units": "mm", "center_hz": designs.F0_HZ,
        "channel_band_hz": [designs.F0_HZ - designs.BW_HZ / 2, designs.F0_HZ + designs.BW_HZ / 2],
        "frequency_samples_hz": {"start": 7.5e9, "stop": 8.5e9, "step": 1e6,
                                 "additional_exact_samples": [designs.F0_HZ - designs.BW_HZ / 2, designs.F0_HZ + designs.BW_HZ / 2],
                                 "sampling_caveat": "DTFT evaluation spacing is not physical frequency resolution; finite record and decay govern accuracy"},
        "excitation": {"type": "Gaussian", "center_hz": designs.F0_HZ, "corner_offset_hz": 1e9},
        "substrate": {"name": "generic_FR4_PROVISIONAL", "epsilon_r": designs.ER,
                      "tan_delta_at_center": designs.TAN_D, "thickness_mm": designs.H_MM,
                      "conductivity_S_per_m": 2 * math.pi * designs.F0_HZ * 8.8541878128e-12 * designs.ER * designs.TAN_D,
                      "loss_model": "constant electric conductivity; tan_delta varies as f0/f",
                      "box_start_mm": [-13, -13, 0], "box_stop_mm": [13, 13, designs.H_MM]},
        "metal": {"name": "copper_smooth_provisional", "conductivity_S_per_m": 5.8e7,
                  "thickness_m": 35e-6, "model": "finite conducting sheet, API needs verification",
                  "roughness": "not modeled", "patch_polygon_mm": candidate["patch"],
                  "patch_z_mm": designs.H_MM, "ground_box_mm": [[-13, -13, 0], [13, 13, 0]]},
        "port": {"number": 1, "reference_ohm": 50, "type": "ideal vertical lumped port",
                 "axis": "z", "start_mm": [fx, fy, 0], "stop_mm": [fx, fy, designs.H_MM],
                 "deembedding": "none", "scope": "ideal probe replaces connector; no coax launch or finite via barrel"},
        "boundaries": {"all_six": "PML_8", "domain_mm": [[-35, -35, -25], [35, 35, 35]]},
        "mesh": {"type": "explicit nonuniform rectilinear", "max_xy_step_mm": .5,
                 "max_air_z_step_mm": .8, "substrate_z_cells": 8,
                 "metal_edge_alignment": "edges on grid; thirds-rule refinement not implemented",
                 "cells_xyz": shape, "total_cells": cells},
        "convergence": {"energy_end_criterion": 1e-5, "maximum_timesteps": 30000,
                        "must_verify_actual_energy_decay": True,
                        "mesh_convergence": "NOT_ESTABLISHED; only one initial solve permitted in first task",
                        "acceptance": "no EM_SIMULATED claim without actual solver completion and logs; one mesh cannot establish mesh independence"},
        "resource_estimate": {"maximum_threads": 2, "conservative_bytes_per_cell": 2048,
                              "estimated_peak_RAM_bytes": cells * 2048,
                              "courant_upper_bound_s": courant_s,
                              "max_time_window_s": courant_s * 30000,
                              "runtime": "unbenchmarked; potentially minutes to tens of minutes on two CPUs",
                              "execution_gate": "do not run until APIs/mesh/PML reviewed, resource estimate accepted and bounded wall time set"},
        "required_outputs": ["actual solver XML", "solver versions", "stdout/stderr and energy decay",
                             "complex S11 CSV and incident/reflected complex port fields", "complex Zin CSV",
                             "CPU time/peak RAM", "coverage over entire exact channel band"],
        "far_field": "not configured; complex near-to-far-field monitor and multi-frequency angular samples still required",
        "reference": "https://docs.openems.de/en/latest/python/openEMS/Tutorials/Simple_Patch_Antenna.html",
    }
    return spec, grid


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("--out", type=Path, required=True)
    args = cli.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    spec, grid = specification()
    (args.out / "p01_model_spec.json").write_text(json.dumps(spec, indent=2) + "\n")
    with (args.out / "p01_mesh.csv").open("w", newline="") as stream:
        writer = csv.writer(stream, lineterminator="\n")
        writer.writerow(["axis", "coordinate_mm"])
        for axis, values in grid.items():
            writer.writerows((axis, value) for value in values)
    print(json.dumps({"em_status": spec["em_status"], "mesh": spec["mesh"],
                      "resource_estimate": spec["resource_estimate"]}, indent=2))
