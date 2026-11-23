"""Generic probe-fed patch openEMS project driven by a variant JSON.

Same modelling and MESH rules as em/p01_openems.py (P01_OPENEMS_001): box +-35 mm
in x/y and z -25..35 mm, 9 lines in the substrate, AddEdges2Grid on the patch
(metal_edge_res 0.25) and on the ground, vertical 50 ohm lumped port with
edges2grid "xy", SmoothMeshLines x/y 0.5 z 0.8 ratio 1.4, PML_8, Gaussian f0
7.9872 GHz / fc 1 GHz, EndCriteria 1e-5, NrTS 30000, conducting sheets
5.8e7 S/m x 35 um, constant-kappa FR4 evaluated at f0.

Modes (python em/patch_openems.py <mode> --variant variants/<ID>.json --out em/<RUN_ID>):
  prepare    builds the model, writes XML, mesh CSV, variant copy and prepared.json
             (no FDTD is run; use runtime_env.sh first).
  solve      one FDTD run; requires prepared.json with the same XML SHA, CPU affinity
             <= 2 CPUs, an unstarted directory and a budget that passes the abort rule.
             Use an external wall-time limit (timeout) and taskset.
  summarize  log-based summary of a finished run (needs solver.log from the launcher).
  reprocess  FDTD-free re-analysis of the probe files of an existing MSL-port run into a NEW directory
             (python em/patch_openems.py reprocess --out <run> --out-reprocess <new dir>); needs no openEMS.
No action occurs on import. Polygon/slot support: see build() and SLOT_MODEL below.

Options added in Claude round 6 (none of them changes the XML of the probe-fed rectangle
path, so P01_BASE / P01_R2 base+fine still reproduce 001 / 004 / 005 byte for byte):
  feed.type "microstrip_inset_edge"  microstrip line to a board-edge launch plane (owner
             decision for P02/P03; SMA body NOT modelled). See EDGE_PORT_MODEL below.
  --edge-port {msl,lumped}   msl (default): openEMS MSL port + reference-plane shift to
             y = -sy/2 and renormalisation to 50 ohm; lumped: vertical 50 ohm lumped port
             at the line end on the board edge (the openEMS RadarUWB tutorial approach).
  --nf2ff [--nf2ff-points {3,11}]   frequency-domain NF2FF box (see FAR_FIELD_MODEL);
             changes the XML, so it is opt-in. 3 = 7.7376/7.9872/8.2368 GHz; 11 = the 3 plus
             8 intermediate points (49.92 MHz step) used for the radiated group delay.

Options added in Claude round 7 (the XML of 001 / 004 / 005 / 006 is unchanged with the defaults):
  MSL port post-processing replaced (see em/port_postprocess.py): beta from the three voltage probes, fixed 50 ohm
             reference, S11 at the measurement plane (s11_measplane.csv) and at the launch plane over an ideal 50 ohm line
             (s11_complex.csv); the openEMS Z_line/beta extraction is only written with --legacy-zline-diagnostic.
  validity gate: result.json / run_numeric.json carry "port_validity"; PORT_INVALID (max|S11| > 1.02 on any plane or
             P_acc < 0) writes the channel_* metrics under invalid_channel_* and skips NF2FF post-processing.
  --excitation-fc-hz FC   Gaussian corner offset (default 1e9 = unchanged XML); the -20 dB range is f0 +- 1.0116 FC
             (excitation.cpp: spectrum exp(-2.25 (f - f0)^2 / fc^2)) and the wideband grid follows it.

Parasitic support (2026-11-15, Claude round 31) (buried parasitic patches; the XML/prepared.json of every variant WITHOUT the key is unchanged, checked by SHA):
  optional variant key "parasitic_patches": [{"name", "z_mm", "polygon_mm": [[x, y], ...], "slots_polygon_mm": [...] (optional)}]
  = conducting sheets (same copper as the patch) at 0 < z_mm < h inside the homogeneous substrate; see PARASITIC_MODEL,
  parse_parasitics (validation; z at >= 1 substrate cell from 0 and h), substrate_z_lines (hard z line) and
  fixed_mesh_lines(layers=...) (x/y lines of the parasitic edges). With parasitics the polygon meshing path is always used.
  prepared.json: geometry.parasitic_patches (geometry, z, cells ground-parasitic / parasitic-patch), warnings, parasitic_summary.

Inverted stack (2026-11-15, Claude round 32): optional variant key "driven_z_mm": z_d (default h; without the key the XML and prepared.json are
  unchanged, checked against the previous script on US3_MS3 / P01_MS2 / US3_PS1 / probe variants). With z_d < h the DRIVEN layer (patch_polygon_mm
  with slots_polygon_mm, feed_polygons_mm / the 50 ohm line + lambda/4 transformer rectangles) is drawn at z = z_d inside the homogeneous substrate and
  the edge lumped port (--edge-port lumped) integrates vertically 0 -> z_d at y = -size_y/2. Parasitics may then sit above (z_d < z <= h, h = top face)
  or below (0 < z < z_d) the driven layer. See DRIVEN_LAYER_MODEL, parse_driven_layer, parse_parasitics (margins of one substrate cell between all metal
  layers), substrate_z_lines (hard lines at z_d and at every parasitic; cells shared per segment). --edge-port msl and probe feeds are rejected when z_d < h.
  prepared.json: geometry.driven_layer (driven_z_mm, z_segments with cells per segment, warnings).

Round 12 (probe-fed U-slot series; the XML of 001 / 003 / 004 / 005 / 006 / 007 / 010 is unchanged, checked by SHA):
  - probe feed on the polygon path (slots_polygon_mm): the lumped-port x/y lines are hard lines of fixed_mesh_lines;
    prepared.json records geometry.slot_mesh_check (cells across every slot chord, warning below 3) and port.grid_lines_at_port.
  - h != 1.6 mm: every z quantity derives from substrate.h_mm (substrate lines, sheet/slot elevation, port 0..h, budget from
    the actual mesh); verified by tests/test_probe_nf2ff.py.
  - --nf2ff with the lumped probe port: S11/P_inc/P_acc/a_inc from Port.CalcPort (50 ohm, port plane); the PORT_INVALID gate applies.
  - radiated group delay: phase-unwrap reliability criterion (|phase step| < pi/2 and |H| >= -20 dB) in the CSV/JSON; the ripple
    is DIAGNOSTIC and flagged UNRELIABLE_DO_NOT_USE when the criterion fails (GROUP_DELAY_CRITERION).
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
import shutil
import sys
import time

sys.path.insert(0, str(Path(__file__).resolve().parent))
import port_postprocess as pp  # noqa: E402  (numpy only; never imports CSXCAD/openEMS)

# ---- constants identical to P01_OPENEMS_001 (designs.py values) -------------------------
F0_HZ = 7_987_200_000.0
BAND_HZ = (7_737_600_000, 8_236_800_000)
C0 = 299_792_458.0
EPS0 = 8.8541878128e-12
BOX_HALF_MM = 35.0
Z_LOW_MM, Z_HIGH_MM = -25.0, 35.0
SUBSTRATE_LINES = 9
METAL_EDGE_RES_MM = 0.25
XY_MAX_STEP_MM, Z_MAX_STEP_MM, SMOOTH_RATIO = 0.5, 0.8, 1.4
# Mesh profiles (--mesh). "base" = P01_OPENEMS_001 rules (default, unchanged).
# "fine" = P01_OPENEMS_002 rules (p01_openems_mesh.py MESH): xy 0.35, z air 0.6,
# 10 substrate cells, metal_edge_res 0.175 mm. Added Claude round 5.
MESH_PROFILES = {
    "base": {"SUBSTRATE_LINES": 9, "METAL_EDGE_RES_MM": 0.25, "XY_MAX_STEP_MM": 0.5, "Z_MAX_STEP_MM": 0.8},
    "fine": {"SUBSTRATE_LINES": 11, "METAL_EDGE_RES_MM": 0.175, "XY_MAX_STEP_MM": 0.35, "Z_MAX_STEP_MM": 0.6},
    # "xfine" = fine x 0.7 (Claude round 16): convergence check of a candidate
    # before acceptance (owner rule 2026-11-04); 14 substrate cells.
    "xfine": {"SUBSTRATE_LINES": 15, "METAL_EDGE_RES_MM": 0.1225, "XY_MAX_STEP_MM": 0.245, "Z_MAX_STEP_MM": 0.42},
}
MESH_PROFILE = "base"
NR_TS, END_CRITERIA, GAUSS_FC_HZ = 30000, 1e-5, 1e9
RECT_GRADING_FALLBACK = 1.5  # see build(); used only if openEMS smoothing cannot reach 1.4
POLY_GRADING_LIMIT = 1.5  # polygon/microstrip path hard limit (target SMOOTH_RATIO 1.4); rectangle path keeps 001 rule
# Polygon/microstrip fixed-line clean-up (round 6). Rectangle path does not use any of this.
MESH_MERGE_TOL_MM = 0.05      # any two fixed lines closer than this are merged (mean)
MESH_PLAIN_SEP_MM = 0.1       # plain vertex lines closer than this to a rule/hint line are dropped
GAP_MERGE_FACTOR = 0.7        # two "outside" edge lines of facing edges closer than 0.7 * metal_edge_res are merged
RELAX_MAX_SHIFT_MM = 0.04     # fixed lines may move at most this far from their rule position (0.16 * metal_edge_res)
SMOOTH_RATIO_SEARCH = (1.4, 1.35, 1.3, 1.25, 1.2, 1.15, 1.1)  # polygon path: smoothing parameter tried in order until the result is <= 1.4
RELAX_TARGET = 1.3            # neighbour-cell ratio targeted among fixed lines before SmoothMeshLines (margin below 1.4)
GAUSS_20DB_FACTOR = math.sqrt(math.log(10.0) / 2.25)   # 1.0116: spectrum exp(-2.25 (f - f0)^2 / fc^2) (openEMS excitation.cpp)
WIDEBAND_STEP_HZ, WIDEBAND_ROUND_HZ = 5e6, 10e6
CHANNEL_GRID_HZ = (7.5e9, 8.5e9, 1001)
XML_NAME = "patch_openems.xml"
VARIANT_COPY = "variant.json"

# ---- resource model (measured in this container) ----------------------------------------
# P01_OPENEMS_002: peak RSS 758256 KiB, 4841937 solver nodal positions, 10368 steps,
# dt 3.790680663318982e-13 s, 53.2608 Mcell/s, record 3.930177711729121e-9 s.
REF = {"id": "P01_OPENEMS_002", "rss_kib": 758256, "nodal_cells": 4_841_937, "steps": 10368,
       "actual_dt_s": 3.790680663318982e-13, "cells_per_s": 53.0e6,
       "cells_per_s_measured": 53260802.3066374,
       "mesh_min_step_mm": (0.17499999999999982, 0.17499999999999982, 0.15999999999999992)}
RAM_MARGIN = 2.0
CONSERVATIVE_BYTES_PER_CELL = 2048
ABORT_RAM_BYTES = 8 * 1024 ** 3
ABORT_TIME_S = 1800.0
# Owner decision 2026-11-04 (Claude round 12): convergence runs (--mesh fine) may
# use up to 4000 s (~67 min; raised from 2700 s by owner 2026-11-05) with --owner-long-convergence; the rate basis
# (53 Mcell*step/s) is NOT changed. 2 CPU and one FDTD per round still apply.
ABORT_TIME_S_LONG_CONVERGENCE = 4000.0
ABORT_TIME_LIMIT_S = ABORT_TIME_S  # set in main()
SLOT_PRIORITY, SHEET_PRIORITY, PORT_PRIORITY = 20, 10, 5

SLOT_MODEL = ("slot = zero-thickness polygon (CSXCAD AddPolygon, norm_dir z, elevation h) of an air Material "
              "(eps_r 1, kappa 0) with priority 20 > conducting sheet 10. Verified by reading the installed "
              "source: ContinuousStructure::GetPropertyByCoordPriority(coord, primList) returns the first "
              "priority-sorted primitive containing the edge coordinate; Operator::CalcPEC_Range and "
              "Operator_Ext_ConductingSheet::BuildExtension only act when that winner is METAL/ConductingSheet; "
              "Operator::AverageMatCellCenter samples cell centres (never on the z=h plane; drawing tolerance 0), "
              "so the zero-thickness air polygon does not alter substrate epsilon. NOT yet exercised in a solve.")


PROBE_FEED = "probe_lumped_vertical"
EDGE_FEED = "microstrip_inset_edge"
EDGE_QW_FEED = "microstrip_edge_qw"   # 50 ohm line + lambda/4 transformer touching a flat patch side (round 7, P03_MS2)
EDGE_FEEDS = (EDGE_FEED, EDGE_QW_FEED)
SLOT_MAX_CELL_MM = 0.3          # microstrip_edge_qw only: slots are meshed with at least ~6 cells across their smaller extent
NARROW_STRIP_MM = 1.0           # microstrip_edge_qw only: feed rectangles narrower than this get a central x line (>= 3-4 cells)
QW_GEOMETRY_TOL_MM = 1e-6
EDGE_PORT_FEED_SHIFT_MM = 0.5   # excitation plane distance from the launch plane (board edge)
EDGE_PORT_MEAS_MAX_MM = 6.0     # measurement plane at most this far from the launch plane
EDGE_PORT_MIN_SEP_H = 2.0       # warn if the measurement plane is closer than 2 h to the source or the patch edge
EDGE_PORT_STOP_AFTER_MEAS_MM = 1.0
EDGE_PORTS = ("msl", "lumped")
NF2FF_BAND_POINTS = {3: [BAND_HZ[0], 7_987_200_000, BAND_HZ[1]],
                     11: [BAND_HZ[0] + k * 49_920_000 for k in range(11)]}
NF2FF_THETA_DEG = [float(t) for t in range(0, 181, 5)]
NF2FF_PHI_DEG = [0.0, 90.0, 180.0, 270.0]
NF2FF_DFT_COST_CELLS = 1.0 / 6.0  # UNMEASURED assumption: one DFT accumulation (1 component, 1 freq) = 1/6 of a full cell update
NF2FF_RADIUS_M = 1.0

EDGE_PORT_MODEL = (
    "Launch plane = board edge y = -sy/2 (owner decision: SMA at the board edge, connector body not modelled). "
    "Default 'msl': openEMS MSLPort (ports.py MSLPort.__init__ lines 321-417 of the installed source: signature "
    "(CSX, port_nr, metal_prop, start, stop, prop_dir, exc_dir, excite, FeedShift, MeasPlaneShift, Feed_R); "
    "start=[x-w/2, y_launch, h] stop=[x+w/2, y_meas+1 mm, 0], prop_dir 'y' (+y, direction=sign(stop_y-start_y)), exc_dir 'z'; "
    "the metal sheet box is added to the same conducting-sheet property as the patch; E_z soft excitation at the mesh line "
    "nearest start+FeedShift; Feed_R=50 ohm lumped resistor across the line at the launch plane absorbs the backward wave; "
    "voltage probes at 3 y lines around the measurement plane, current probes between them; "
    "MSLPort.ReadUIData lines 419-447 extracts beta=sqrt(-dE dH/(E H)) and Z_line=sqrt(E dE/(H dH)) from them). "
    "Post-processing (round 7, em/port_postprocess.py POSTPROCESS_MODEL; replaces CalcPort(ref_plane_shift) which re-used the "
    "ill-conditioned openEMS beta and gave |S11| up to 1.26 in P02_MS1_OPENEMS_006): U = U_B, I = mean(I_A, I_B)/cos(beta D/2); "
    "beta from cos(beta D) = (U_A + U_C)/(2 U_B) with analytic Hammerstad-Jensen + Getsinger fallback; fixed 50 ohm reference "
    "(a = (U + 50 I)/2, S11 = (U - a)/a, Zin = U/I) at the measurement plane (primary) and, over an ideal lossless 50 ohm line "
    "with that beta, at the launch plane. Line loss between the planes is neglected and a numerical Z_line different from 50 ohm "
    "is not calibrated. "
    "Fallback 'lumped': vertical 50 ohm LumpedPort on the line end at y = -sy/2, x in [x-w/2, x+w/2], z in [0, h] "
    "(same as the openEMS RadarUWBTutorial.py edge-fed monopole, which places its lumped port at the board edge); "
    "its U/I are measured directly at the launch plane and include the port's own step discontinuity.")

FAR_FIELD_MODEL = (
    "openEMS.CreateNF2FFBox(frequency=[...]) (openEMS.pyx lines 464-521; frequency kw selects frequency-domain E/H dumps, "
    "nf2ff.py lines 65-80, dump_type 10/11, single-sided DFT weights Common/processfields_fd.cpp lines 103-106, the same "
    "single-sided convention as the port probes DFT_time2freq utilities.py lines 27-41, so Prad and port powers are "
    "directly comparable as in Tutorials/Helical_Antenna.py line 179 and RadarUWBTutorial.py line 182). Box = the default "
    "derived from the PML_8 boundaries: faces on mesh line index 9 / -10 (one cell inside the PML region, in air, outside "
    "the board and the substrate; no conductor crosses the box because the SMA/port is inside the board). "
    "CalcNF2FF(sim_path, freq, theta, phi, radius=1 m, center in METRES, read_cached=False): E_theta/E_phi include the "
    "factor exp(-jkr)/r at r = 1 m (nf2ff_calc.cpp lines 503-513), P_rad = |E|^2/(2 Z0) in W/m^2, Prad = net Poynting flux through "
    "the box (nf2ff_calc.cpp line 414, independent of the sampled angles), Dmax = max over the SAMPLED directions only "
    "(line 525). Quantities derived here: D = 4 pi r^2 P_rad / Prad; gain (IEEE, excludes mismatch) = 4 pi r^2 P_rad / P_acc; "
    "realised gain = 4 pi r^2 P_rad / P_inc (the formula of RadarUWBTutorial.py line 182, Dmax*Prad/P_inc); "
    "radiation efficiency = Prad / P_acc with P_acc = 0.5 Re(U I*) at the port reference plane (Helical_Antenna.py line 179; MSL edge "
    "ports since round 7: measurement plane, fixed 50 ohm, so the ~4.9 mm of feed line before it is outside the efficiency); "
    "total efficiency = Prad / P_inc. Prad contains radiation only; conductor, dielectric and any feed-stub loss are in "
    "P_acc - Prad. Vertical lumped ports (probe feed, round 12): P_inc and P_acc come from openEMS Port.CalcPort at the port "
    "(reference = the 50 ohm port resistance, no plane shift), so the probe is part of the antenna; same NF2FF box, same "
    "single-sided DFT convention.")

PHASE_STEP_LIMIT_RAD = math.pi / 2   # radiated group delay: max |wrapped phase step| between adjacent frequency points
H_FLOOR_REL_DB = -20.0               # radiated group delay: |H| must stay within 20 dB of its band maximum
GROUP_DELAY_CRITERION = (
    f"phase-unwrap reliability (round 12): a component is RELIABLE only if every wrapped phase step between adjacent frequency "
    f"points is < pi/2 ({PHASE_STEP_LIMIT_RAD:.4f} rad; the unwrap is unambiguous only below pi, pi/2 leaves a factor 2 margin; "
    f"with 49.92 MHz spacing that is a residual delay < 5 ns) AND |H| >= {H_FLOOR_REL_DB:.0f} dB re its maximum over the points "
    "(a broadside null makes the phase jump by ~pi and the delay meaningless). Otherwise the component is UNRELIABLE and its "
    "delay values/ripple must not be used. The CSV columns reliable_* repeat the test per point (1 = both adjacent steps < pi/2 "
    "and |H| above the floor). Ripple (max - min of tau_g over the channel) is DIAGNOSTIC only: 11 correlated samples, one-sided "
    "end points, not validated.")

GROUP_DELAY_MODEL = (
    "Radiated group delay (only with 11 points): H(f) = E_far(theta=0, phi=0, f) exp(+j k r) / a_inc(f), with a_inc the "
    "incident-wave voltage at the reference plane of the port (same plane as S11: launch plane for MSL edge ports, the lumped "
    "port itself for the vertical probe port: no plane shift, no beta), r = 1 m, k = 2 pi f / c0. E_theta and E_phi "
    "of the phi=0 cut are the x and y components at broadside (theta_hat = x_hat, phi_hat = y_hat at phi = 0). "
    "tau_g = -d arg(H)/d omega from the unwrapped phase with central differences (one-sided at the ends). The excitation "
    "spectrum and its phase cancel; the NF2FF phase centre only adds a constant (z of the centre / c0 at broadside). "
    "The absolute value contains the constant electrical length of the line and of the stub; only the variation over the band "
    "(ripple) is meaningful. DIAGNOSTIC: not validated against a reference; 49.92 MHz spacing is below the DTFT resolution "
    "1/T_record of the run, so adjacent samples are not independent.")


def nominal_valid_range_hz(fc_hz=None):
    """-20 dB range of the Gaussian excitation: f0 +- 1.0116 fc (fc = 1 GHz gives 6.976 .. 8.999 GHz)."""
    fc = GAUSS_FC_HZ if fc_hz is None else fc_hz
    return F0_HZ - GAUSS_20DB_FACTOR * fc, F0_HZ + GAUSS_20DB_FACTOR * fc


def wideband_grid(fc_hz=None):
    """5 MHz grid over the nominal -20 dB range rounded to 10 MHz. fc = 1 GHz gives arange(6.98e9, 9.0e9 + 2.5e6, 5e6),
    exactly the grid hard-coded before round 7."""
    import numpy as np
    lo, hi = nominal_valid_range_hz(fc_hz)
    lo, hi = round(lo / WIDEBAND_ROUND_HZ) * WIDEBAND_ROUND_HZ, round(hi / WIDEBAND_ROUND_HZ) * WIDEBAND_ROUND_HZ
    return np.arange(lo, hi + WIDEBAND_STEP_HZ / 2, WIDEBAND_STEP_HZ)


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


# ---- variant handling -------------------------------------------------------------------------
def load_variant(path):
    data = json.loads(Path(path).read_text())
    for key in ("id", "substrate", "metal", "patch_polygon_mm", "feed"):
        if key not in data:
            raise ValueError(f"Variant JSON lacks '{key}'")
    sub, metal, feed = data["substrate"], data["metal"], data["feed"]
    for key in ("name", "eps_r", "tan_delta", "h_mm", "size_mm"):
        if key not in sub:
            raise ValueError(f"substrate lacks '{key}'")
    for key in ("conductivity_S_m", "thickness_m"):
        if key not in metal:
            raise ValueError(f"metal lacks '{key}'")
    if feed.get("type") not in (PROBE_FEED, *EDGE_FEEDS):
        raise ValueError(f"Only feed.type in ('{PROBE_FEED}', '{EDGE_FEED}', '{EDGE_QW_FEED}') is supported")
    required = {PROBE_FEED: ("type", "x_mm", "y_mm", "z0_ohm"),
                EDGE_FEED: ("type", "z0_ohm", "line_width_mm", "line_x_mm", "line_start_y_mm", "line_end_y_mm",
                            "notch_gap_mm", "inset_depth_mm"),
                EDGE_QW_FEED: ("type", "z0_ohm", "line_width_mm", "line_x_mm", "line_start_y_mm", "line_end_y_mm",
                               "transformer_width_mm", "transformer_length_mm", "transformer_start_y_mm", "patch_edge_y_mm",
                               "feed_polygons_mm")}[feed["type"]]
    for key in required:
        if key not in feed:
            raise ValueError(f"feed lacks '{key}'")
    if not (sub["eps_r"] >= 1 and sub["tan_delta"] >= 0 and sub["h_mm"] > 0
            and metal["conductivity_S_m"] > 0 and metal["thickness_m"] > 0 and feed["z0_ohm"] > 0):
        raise ValueError("Nonphysical material/feed parameter")
    sx, sy = sub["size_mm"]
    if sx <= 0 or sy <= 0:
        raise ValueError("Nonphysical substrate size")
    poly = [tuple(map(float, p)) for p in data["patch_polygon_mm"]]
    if len(poly) < 3:
        raise ValueError("patch_polygon_mm needs >= 3 vertices")
    slots = [[tuple(map(float, p)) for p in s] for s in data.get("slots_polygon_mm", [])]
    if any(len(s) < 3 for s in slots):
        raise ValueError("every slot needs >= 3 vertices")
    xs, ys = zip(*poly)
    if min(xs) < -sx / 2 or max(xs) > sx / 2 or min(ys) < -sy / 2 or max(ys) > sy / 2:
        raise ValueError("Patch exceeds the substrate")
    for s in slots:
        sxs, sys_ = zip(*s)
        if min(sxs) < min(xs) or max(sxs) > max(xs) or min(sys_) < min(ys) or max(sys_) > max(ys):
            raise ValueError("A slot exceeds the patch bounding box")
    hints = data.get("mesh_hint_lines_mm", {})
    if not isinstance(hints, dict) or any(k not in ("x", "y", "z") for k in hints):
        raise ValueError("mesh_hint_lines_mm must be {'x': [...], 'y': [...], 'z': [...]} (mm)")
    if feed["type"] == PROBE_FEED:
        if not point_in_polygon(feed["x_mm"], feed["y_mm"], poly):
            raise ValueError("Feed is outside the patch polygon")
        if any(point_in_polygon(feed["x_mm"], feed["y_mm"], s) for s in slots):
            raise ValueError("Feed lies inside a slot")
        return data, poly, slots
    if feed["type"] == EDGE_QW_FEED:
        validate_qw_feed(feed, poly, slots, sx, sy)
        return data, poly, slots
    w, lx = float(feed["line_width_mm"]), float(feed["line_x_mm"])
    y_start, y_end = float(feed["line_start_y_mm"]), float(feed["line_end_y_mm"])
    gap, depth = float(feed["notch_gap_mm"]), float(feed["inset_depth_mm"])
    if w <= 0 or gap < 0 or depth < 0:
        raise ValueError("Nonphysical microstrip parameter")
    if abs(y_start + sy / 2) > 1e-9:
        raise ValueError("line_start_y_mm must equal -size_y/2 (the launch plane is the board edge)")
    if not y_end > y_start:
        raise ValueError("line_end_y_mm must be greater than line_start_y_mm")
    if lx - w / 2 < -sx / 2 or lx + w / 2 > sx / 2:
        raise ValueError("Microstrip line exceeds the substrate")
    if not point_in_polygon(lx, y_end + 1e-6, poly):
        raise ValueError("Microstrip line does not reach/overlap the patch polygon (line_end_y_mm)")
    for k in range(201):
        yy = y_start + (y_end - y_start) * k / 200
        if any(point_in_polygon(lx, yy, s) for s in slots):
            raise ValueError("Microstrip line crosses a slot")
    if gap > 0 and depth > 0:
        for sign in (-1, 1):
            if point_in_polygon(lx + sign * (w / 2 + gap / 2), min(ys) + depth / 2, poly):
                raise ValueError("patch_polygon_mm does not contain the declared inset notch (notch_gap_mm/inset_depth_mm)")
    return data, poly, slots


def validate_qw_feed(feed, poly, slots, sx, sy):
    """microstrip_edge_qw: feed_polygons_mm = [50 ohm line rectangle, transformer rectangle], drawn as given (absolute coordinates)."""
    tol = QW_GEOMETRY_TOL_MM
    w, lx = float(feed["line_width_mm"]), float(feed["line_x_mm"])
    y0, y1 = float(feed["line_start_y_mm"]), float(feed["line_end_y_mm"])
    tw, tl = float(feed["transformer_width_mm"]), float(feed["transformer_length_mm"])
    ty0, pe = float(feed["transformer_start_y_mm"]), float(feed["patch_edge_y_mm"])
    if min(w, tw, tl) <= 0:
        raise ValueError("Nonphysical microstrip_edge_qw parameter")
    if abs(y0 + sy / 2) > 1e-9:
        raise ValueError("line_start_y_mm must equal -size_y/2 (the launch plane is the board edge)")
    if abs(ty0 - y1) > tol or not y1 > y0:
        raise ValueError("transformer_start_y_mm must equal line_end_y_mm (> line_start_y_mm)")
    if abs((ty0 + tl) - pe) > tol:
        raise ValueError("transformer_start_y_mm + transformer_length_mm must equal patch_edge_y_mm")
    if abs(min(p[1] for p in poly) - pe) > tol:
        raise ValueError("patch_edge_y_mm must be the lowest y of patch_polygon_mm")
    if lx - w / 2 < -sx / 2 or lx + w / 2 > sx / 2:
        raise ValueError("Microstrip line exceeds the substrate")
    rects = feed_rectangles(feed)
    if len(rects) != 2 or not all(is_axis_aligned_rectangle(r) for r in rects):
        raise ValueError("feed_polygons_mm must be two axis-aligned rectangles [50 ohm line, transformer]")
    for r, (xa, xb, ya, yb) in zip(rects, ((lx - w / 2, lx + w / 2, y0, y1), (lx - tw / 2, lx + tw / 2, ty0, pe))):
        xs_, ys_ = zip(*r)
        if max(abs(min(xs_) - xa), abs(max(xs_) - xb), abs(min(ys_) - ya), abs(max(ys_) - yb)) > tol:
            raise ValueError("feed_polygons_mm disagree with line_*/transformer_* parameters")
    if not point_in_polygon(lx, pe + 1e-6, poly):
        raise ValueError("Transformer does not reach the patch polygon (patch_edge_y_mm)")
    for r in rects:
        xs_, ys_ = zip(*r)
        for kx in range(21):
            for ky in range(201):
                if any(point_in_polygon(min(xs_) + (max(xs_) - min(xs_)) * kx / 20, min(ys_) + (max(ys_) - min(ys_)) * ky / 200, s_)
                       for s_ in slots):
                    raise ValueError("Feed rectangle crosses a slot")


def feed_rectangles(feed):
    """Metal rectangles (polygons of 4 vertices) of an edge feed: the single line for microstrip_inset_edge, the given
    feed_polygons_mm (absolute coordinates) for microstrip_edge_qw."""
    if feed["type"] == EDGE_QW_FEED:
        return [[tuple(map(float, p)) for p in r] for r in feed["feed_polygons_mm"]]
    return [microstrip_line(feed)]


def microstrip_line(feed):
    """Axis-aligned line rectangle (x in [lx-w/2, lx+w/2], y in [start, end]) of an edge feed."""
    w, lx = float(feed["line_width_mm"]), float(feed["line_x_mm"])
    y0, y1 = float(feed["line_start_y_mm"]), float(feed["line_end_y_mm"])
    return [(lx - w / 2, y0), (lx + w / 2, y0), (lx + w / 2, y1), (lx - w / 2, y1)]


def point_in_polygon(x, y, poly):
    inside = False
    n = len(poly)
    for i in range(n):
        x1, y1 = poly[i]
        x2, y2 = poly[(i + 1) % n]
        if (y1 > y) != (y2 > y) and x < (x2 - x1) * (y - y1) / (y2 - y1) + x1:
            inside = not inside
    return inside


def is_axis_aligned_rectangle(poly):
    if len(poly) != 4:
        return False
    xs, ys = sorted({p[0] for p in poly}), sorted({p[1] for p in poly})
    return len(xs) == 2 and len(ys) == 2 and {(x, y) for x in xs for y in ys} == set(poly)


def polygon_mesh_lines(poly, res, min_sep=0.1):
    """Mesh hints for a general polygon (AddEdges2Grid ignores polygons).

    Bounding-box edges use the same 1/3-2/3 metal_edge_res rule as the automesh box hints;
    every other distinct vertex coordinate adds a plain line unless it is closer than
    min_sep (mm) to an existing hint. Oblique edges remain staircased.
    """
    xs, ys = zip(*poly)
    hints = {}
    mer = (-res / 3, 2 * res / 3)
    for axis, vals in (("x", xs), ("y", ys)):
        lo, hi = min(vals), max(vals)
        hints[axis] = [lo - mer[0], lo - mer[1], hi + mer[0], hi + mer[1]]
        for v in sorted(set(vals)):
            if all(abs(v - u) >= min_sep for u in hints[axis]):
                hints[axis].append(v)
    return hints


def _metal_at(x, y, patch_poly, slots, line_rects):
    inside = point_in_polygon(x, y, patch_poly) or any(point_in_polygon(x, y, r) for r in (line_rects or []))
    return inside and not any(point_in_polygon(x, y, s) for s in slots)


def fixed_mesh_lines(patch_poly, slots, line_rect, board_half, res, box_half, extra=None, extra_plain=None, layers=None):
    """Fixed mesh lines for the polygon/microstrip path (round 6; not used by the rectangle path).

    Rules (recorded in prepared.json):
      1. every axis-aligned edge of the patch, of the slots and of the microstrip line, whose two sides differ in
         metal/no metal (tested 1e-4 mm either side of the edge at 1/2, 1/4, 3/4 of its length; metal = (patch U line)
         minus slots), gets the 1/3-2/3 metal_edge_res rule: line at edge + res/3 on the metal side and edge - 2 res/3
         on the other side (hi/lo orientation resolved from the tested sides). Edges lying on the board edge
         (|c| = size/2) get no rule lines: the grid already has exact lines there.
      2. bounding-box extremes of every contour get the same rule (metal side = interior for patch/line, exterior for slots),
         which covers pointy extremes (hexagon) that have no axis-aligned edge.
      3. every vertex coordinate adds a plain line (oblique edges stay staircased).
      4. optional user lines (variant key mesh_hint_lines_mm) are kept as hard lines.
      5. layers (buried parasitic patches): list of (polygon, slots); each layer is a separate metal sheet at another z, so its
         edges are tested for metal/no-metal against ITS OWN polygon minus ITS OWN slots (not against the driven patch), and
         then get the same rules 1-3. The lines of all layers join the same pool (clean-up/merge/relaxation below).
    Clean-up: plain lines closer than MESH_PLAIN_SEP_MM to a rule/user line are dropped; any lines closer than
    MESH_MERGE_TOL_MM are merged (mean; user lines win); two 'outside' rule lines closer than GAP_MERGE_FACTOR*res (the
    two facing edges of a narrow gap) are merged into one line half-way between them (keeps the cell sequence in a
    gap such as the 0.5 mm inset notch smooth: g/2 + res/3 per cell instead of res*(1, 2/3, 1)).
    Then relax_fixed_lines() (bounded Laplacian relaxation, <= RELAX_MAX_SHIFT_MM per line) removes cell-ratio violations
    among the fixed lines that SmoothMeshLines cannot repair. Returns ({axis: sorted list}, report).
    """
    d = 1e-4
    line_rects = [] if not line_rect else ([line_rect] if isinstance(line_rect[0][0], (int, float)) else list(line_rect))
    main_ctx = (patch_poly, slots, line_rects)
    contours = [(patch_poly, "metal", main_ctx)] + [(s, "slot", main_ctx) for s in slots] + [(r_, "metal", main_ctx) for r_ in line_rects]
    for lp_, ls_ in (layers or []):
        lctx = (lp_, ls_, [])
        contours += [(lp_, "metal", lctx)] + [(s, "slot", lctx) for s in ls_]
    items = {"x": [], "y": []}  # (coord, kind)
    report = {"rule_edges": {"x": 0, "y": 0}, "dropped_plain": {"x": 0, "y": 0}, "merged_close": {"x": 0, "y": 0},
              "merged_outside_pairs": {"x": 0, "y": 0}, "user_lines": {"x": 0, "y": 0}}
    third, two_thirds = res / 3.0, 2.0 * res / 3.0

    def add_rule(axis, c, metal_high_side):
        # metal on the + side of c  ->  lo-type edge: inside line at c + res/3, outside at c - 2 res/3
        sgn = 1.0 if metal_high_side else -1.0
        items[axis].append((c + sgn * third, "in"))
        items[axis].append((c - sgn * two_thirds, "out"))

    for poly, kind, (c_patch, c_slots, c_lines) in contours:
        n = len(poly)
        for i in range(n):
            (x1, y1), (x2, y2) = poly[i], poly[(i + 1) % n]
            for axis, c, c2, a1, a2 in (("x", x1, x2, y1, y2), ("y", y1, y2, x1, x2)):
                if abs(c - c2) > 1e-9:
                    continue
                if abs(abs(c) - (board_half[0] if axis == "x" else board_half[1])) < 1e-6:
                    continue
                for fr in (0.5, 0.25, 0.75):
                    am = a1 + fr * (a2 - a1)
                    lo_pt = (c - d, am) if axis == "x" else (am, c - d)
                    hi_pt = (c + d, am) if axis == "x" else (am, c + d)
                    m_lo, m_hi = _metal_at(*lo_pt, c_patch, c_slots, c_lines), _metal_at(*hi_pt, c_patch, c_slots, c_lines)
                    if m_lo != m_hi:
                        add_rule(axis, c, m_hi)
                        report["rule_edges"][axis] += 1
                        break
        xs, ys = zip(*poly)
        for axis, vals in (("x", xs), ("y", ys)):
            lo, hi = min(vals), max(vals)
            inside_metal = kind == "metal"
            bh = board_half[0] if axis == "x" else board_half[1]
            if abs(abs(lo) - bh) > 1e-6:           # extremes on the board edge keep the exact grid line instead
                add_rule(axis, lo, inside_metal)       # interior is on the + side of the low extreme
            if abs(abs(hi) - bh) > 1e-6:
                add_rule(axis, hi, not inside_metal)   # interior is on the - side of the high extreme
        for (vx, vy) in poly:
            if abs(abs(vx) - board_half[0]) > 1e-6:
                items["x"].append((vx, "plain"))
            if abs(abs(vy) - board_half[1]) > 1e-6:
                items["y"].append((vy, "plain"))
    for axis in "xy":
        for v in (extra or {}).get(axis, []):
            items[axis].append((float(v), "user"))
            report["user_lines"][axis] += 1
        for v in (extra_plain or {}).get(axis, []):
            items[axis].append((float(v), "plain"))
    lines = {}
    anchors = {"x": [-box_half, -board_half[0], board_half[0], box_half],
               "y": [-box_half, -board_half[1], board_half[1], box_half]}
    report["relaxed_lines"] = {"x": 0, "y": 0}
    report["max_shift_mm"] = {"x": 0.0, "y": 0.0}
    for axis in "xy":
        its = sorted(items[axis])
        strong = [c for c, k in its if k != "plain"]
        kept = []
        for c, k in its:
            if k == "plain" and any(abs(c - u) < MESH_PLAIN_SEP_MM for u in strong):
                report["dropped_plain"][axis] += 1
                continue
            kept.append((c, k))
        thresholds = (("merged_close", lambda a_, b_: b_[0] - a_[0] < MESH_MERGE_TOL_MM),
                      ("merged_outside_pairs", lambda a_, b_: a_[1] == "out" and b_[1] == "out"
                       and b_[0] - a_[0] < GAP_MERGE_FACTOR * res))
        changed = True
        while changed:
            changed = False
            for key, pred in thresholds:
                kept.sort()
                merged, run = [], [kept[0]]
                for item in kept[1:]:
                    if pred(run[-1], item):
                        run.append(item)
                    else:
                        merged.append(run)
                        run = [item]
                merged.append(run)
                if any(len(r_) > 1 for r_ in merged):
                    changed = True
                    new_kept = []
                    for r_ in merged:
                        if len(r_) == 1:
                            new_kept.append(r_[0])
                            continue
                        report[key][axis] += len(r_) - 1
                        users = [c for c, k in r_ if k == "user"]
                        kinds = [k for _, k in r_ if k != "plain"]
                        new_kept.append((users[0] if users else sum(c for c, _ in r_) / len(r_),
                                         "user" if users else (kinds[0] if kinds else "plain")))
                    kept = new_kept
                    break
        coords = [c for c, _ in kept]
        movable = [k != "user" for _, k in kept]
        coords, shifts = relax_fixed_lines(coords, movable, anchors[axis], XY_MAX_STEP_MM)
        report["relaxed_lines"][axis] = int(sum(1 for d_ in shifts if d_ > 1e-9))
        report["max_shift_mm"][axis] = float(max(shifts) if shifts else 0.0)
        lines[axis] = coords
    return lines, report


SMOOTH_INFILL_MAX = 4   # smooth_axis_search(infill=True): at most this many extra mid-gap lines per axis


def smooth_axis_search(mesh, np, axis, max_step, infill=False, both_cells=False):
    """Polygon/microstrip path: SmoothMeshLines with the smoothing-ratio PARAMETER lowered until the resulting neighbour
    ratio is <= SMOOTH_RATIO (openEMS tapering can overshoot the parameter, e.g. parameter 1.4 -> 1.54 in a 0.78 mm range
    between 0.25 mm cells). The same CSXCAD function mesh.SmoothMeshLines calls, applied to the same fixed lines.

    infill=True (round 12, probe-fed U-slot path only; edge-feed variants keep the round 6 behaviour so 006 / 007 / 010 reproduce
    byte for byte): if the best ratio is still > SMOOTH_RATIO, the fixed interval that holds the smaller of the two offending
    cells gets one extra hard line at its midpoint (e.g. 0.68 mm between a slot-tip rule line and the patch-edge rule line
    -> two 0.34 mm cells next to 0.25 mm cells, ratio 1.37, instead of 0.25 / 0.163 = 1.54), at most SMOOTH_INFILL_MAX times and
    only while the ratio strictly improves.
    both_cells=True (buried parasitic patches only; every earlier path keeps False and is unchanged): each step tries the midpoint of
    the fixed interval of the smaller AND of the larger offending cell and keeps the trial with the lowest max ratio, if it strictly
    improves (a parasitic edge 0.65 mm outside the patch edge leaves a 0.32 mm cell next to 0.11 mm cells: the useful split is in
    the LARGE cell's interval, which the smaller-cell rule never tries).
    Returns (parameter_used, max_neighbor_ratio, extra_lines)."""
    from CSXCAD.SmoothMeshLines import SmoothMeshLines as smooth

    def run(fixed_):
        best_ = None
        for param in SMOOTH_RATIO_SEARCH:
            lines_ = np.asarray(smooth(fixed_, max_step, param, check_symmetry=True), dtype=float)
            gaps_ = np.diff(lines_)
            ratio_ = float(np.max(np.maximum(gaps_[1:] / gaps_[:-1], gaps_[:-1] / gaps_[1:])))
            if best_ is None or ratio_ < best_[1] - 1e-12:
                best_ = (param, ratio_, lines_)
            if ratio_ <= SMOOTH_RATIO + 1e-8:
                best_ = (param, ratio_, lines_)
                break
        return best_

    fixed = np.asarray(mesh.GetLines(axis), dtype=float)
    best = run(fixed)
    extra = []
    while infill and both_cells and best[1] > SMOOTH_RATIO + 1e-8 and len(extra) < SMOOTH_INFILL_MAX:
        lines, fixed_sorted = best[2], np.sort(fixed)
        gaps = np.diff(lines)
        r = np.maximum(gaps[1:] / gaps[:-1], gaps[:-1] / gaps[1:])
        k = int(np.argmax(r))
        cands = []
        for cell_i in (k, k + 1):
            mid_cell = 0.5 * (lines[cell_i] + lines[cell_i + 1])
            lo_i = int(np.searchsorted(fixed_sorted, mid_cell)) - 1
            if lo_i < 0 or lo_i + 1 >= len(fixed_sorted):
                continue
            a, b = float(fixed_sorted[lo_i]), float(fixed_sorted[lo_i + 1])
            if b - a < 4 * MESH_MERGE_TOL_MM:
                continue
            trial_fixed = np.append(fixed, 0.5 * (a + b))
            trial = run(np.sort(trial_fixed))
            cands.append((trial[1], trial_fixed, trial, 0.5 * (a + b)))
        if not cands:
            break
        key, trial_fixed, trial, new_line = min(cands, key=lambda c: c[0])
        if key >= best[1] - 1e-9:
            break
        fixed, best = trial_fixed, trial
        extra.append(float(new_line))
    while infill and not both_cells and best[1] > SMOOTH_RATIO + 1e-8 and len(extra) < SMOOTH_INFILL_MAX:
        lines, fixed_sorted = best[2], np.sort(fixed)
        gaps = np.diff(lines)
        r = np.maximum(gaps[1:] / gaps[:-1], gaps[:-1] / gaps[1:])
        k = int(np.argmax(r))
        small = k if gaps[k] < gaps[k + 1] else k + 1
        mid_cell = 0.5 * (lines[small] + lines[small + 1])
        lo_i = int(np.searchsorted(fixed_sorted, mid_cell)) - 1
        if lo_i < 0 or lo_i + 1 >= len(fixed_sorted):
            break
        a, b = float(fixed_sorted[lo_i]), float(fixed_sorted[lo_i + 1])
        if b - a < 4 * MESH_MERGE_TOL_MM:
            break
        trial_fixed = np.append(fixed, 0.5 * (a + b))
        trial = run(np.sort(trial_fixed))
        if trial[1] >= best[1] - 1e-9:
            break
        fixed, best = trial_fixed, trial
        extra.append(float(0.5 * (a + b)))
    mesh.SetLines(axis, best[2])
    return best[0], best[1], extra


def relax_fixed_lines(coords, movable, anchors, max_step):
    """Bounded Laplacian relaxation of fixed lines (round 6).

    openEMS SmoothMeshLines cannot grade between two adjacent FIXED cells that disagree by more than the ratio when
    neither exceeds the max step (e.g. 0.158 mm cell between 0.25 mm cells = 1.58). Here every movable fixed line is
    moved toward the midpoint of its two neighbours (anchors = box/board lines are fixed neighbours) while the two cells
    are both <= max_step and their ratio > RELAX_TARGET, never more than RELAX_MAX_SHIFT_MM from its rule position and
    never closer than MESH_MERGE_TOL_MM to a neighbour. Returns (coords, |shift| per line).
    """
    # combined sorted structure: anchors (immovable) + fixed lines
    allp = sorted([(c, False) for c in anchors] + [(c, m) for c, m in zip(coords, movable)])
    xs = [c for c, _ in allp]
    mv = [m for _, m in allp]
    orig = list(xs)
    for _ in range(400):
        moved = False
        for i in range(1, len(xs) - 1):
            if not mv[i]:
                continue
            gl, gr = xs[i] - xs[i - 1], xs[i + 1] - xs[i]
            if gl > max_step or gr > max_step:
                continue
            if max(gl / gr, gr / gl) <= RELAX_TARGET:
                continue
            target = 0.5 * (xs[i - 1] + xs[i + 1])
            new = xs[i] + 0.5 * (target - xs[i])
            new = min(max(new, orig[i] - RELAX_MAX_SHIFT_MM), orig[i] + RELAX_MAX_SHIFT_MM)
            if new - xs[i - 1] < MESH_MERGE_TOL_MM or xs[i + 1] - new < MESH_MERGE_TOL_MM:
                continue
            if abs(new - xs[i]) > 1e-9:
                xs[i] = new
                moved = True
        if not moved:
            break
    out, shifts = [], []
    for i, (c, m) in enumerate(allp):
        if c in anchors and not m:
            continue
        out.append(xs[i])
        shifts.append(abs(xs[i] - orig[i]))
    return out, shifts


SLOT_CELLS_MIN = 3        # slot_mesh_check: minimum mesh cells across a slot chord (cell centre inside the slot)
SLOT_CHORD_MIN_MM = 0.3   # chords narrower than this (pointed slot tips, oblique corners) are not counted
SLOT_CHORD_SCANS = 41


def polygon_chords(poly, axis, c):
    """Intervals (a, b) of the line {other axis = c} inside the polygon; axis 'x' = chords along x at y = c (even-odd rule)."""
    n = len(poly)
    cross = []
    for i in range(n):
        (x1, y1), (x2, y2) = poly[i], poly[(i + 1) % n]
        p1, q1, p2, q2 = (x1, y1, x2, y2) if axis == "x" else (y1, x1, y2, x2)   # p = coordinate along the chord, q = across
        if (q1 > c) != (q2 > c):
            cross.append(p1 + (c - q1) * (p2 - p1) / (q2 - q1))
    cross.sort()
    return [(cross[k], cross[k + 1]) for k in range(0, len(cross) - 1, 2)]


def slot_mesh_check(slots, axes):
    """Cells across every slot (round 12). For each slot, chords along x and along y are scanned (SLOT_CHORD_SCANS positions
    across the slot, irrational offset so that no scan line lies on an edge); the number of mesh cells whose CENTRE lies inside the
    chord is counted. Chords narrower than SLOT_CHORD_MIN_MM are skipped (pointed tips). Returns a report dict; status
    'OK' if every counted chord has >= SLOT_CELLS_MIN cells, else 'WARN_FEWER_THAN_3_CELLS_ACROSS_SLOT'. Diagnostic only
    (does not change the mesh)."""
    import numpy as np
    out = []
    for k, sl in enumerate(slots):
        per_axis = {}
        for axis, other in (("x", "y"), ("y", "x")):
            vals = [q[1] if axis == "x" else q[0] for q in sl]     # coordinate across the chord
            lo, hi = min(vals), max(vals)
            lines = np.asarray(axes[axis], dtype=float)
            centres = 0.5 * (lines[1:] + lines[:-1])
            best = None
            for j in range(SLOT_CHORD_SCANS):
                c = lo + (hi - lo) * (j + 0.5 + 0.0137) / SLOT_CHORD_SCANS
                for a, b in polygon_chords(sl, axis, c):
                    if b - a < SLOT_CHORD_MIN_MM:
                        continue
                    cnt = int(np.sum((centres > a) & (centres < b)))
                    if best is None or cnt < best["cells"] or (cnt == best["cells"] and b - a < best["width_mm"]):
                        best = {"cells": cnt, "width_mm": float(b - a), "chord_along": axis, "at_mm": float(c),
                                "interval_mm": [float(a), float(b)]}
            per_axis[axis] = best
        found = [v for v in per_axis.values() if v is not None]
        worst = min(found, key=lambda v: (v["cells"], v["width_mm"])) if found else None
        out.append({"slot": k, "min_cells_across": (worst["cells"] if worst else None),
                    "narrowest_counted_chord": worst, "per_axis": per_axis,
                    "status": ("OK" if worst and worst["cells"] >= SLOT_CELLS_MIN else
                               "WARN_FEWER_THAN_3_CELLS_ACROSS_SLOT")})
    return {"rule": f">= {SLOT_CELLS_MIN} cells (centre inside the slot) across every chord >= {SLOT_CHORD_MIN_MM} mm", "slots": out,
            "status": ("OK" if all(o["status"] == "OK" for o in out) else "WARN_FEWER_THAN_3_CELLS_ACROSS_SLOT") if out else "NO_SLOTS"}


# ---- buried parasitic patches (round 31) ------------------------------------------------------------
PARASITIC_Z_TOL_MM = 1e-9
PARASITIC_SAMPLES = 120    # sampling grid (per axis) of the parasitic bounding box for the overlap-with-patch diagnostic
PARASITIC_MODEL = (
    "buried parasitic patch = zero-thickness conducting sheet (CSXCAD AddConductingSheet, same conductivity/thickness as the "
    "patch copper, AddPolygon norm_dir z at elevation z_mm, priority 10) inside the HOMOGENEOUS substrate (same eps_r and "
    "tan_delta over the whole thickness h; the substrate is NOT split into different materials). A slot of the parasitic is a "
    "zero-thickness polygon of a Material with the SUBSTRATE eps_r/kappa and priority 20 > sheet 10 at the same elevation, so it "
    "removes the sheet without adding an air layer inside the dielectric (unlike the patch slot_air at the air/substrate "
    "interface). The parasitic is floating (no DC or probe connection); coupling to the driven patch and the ground is "
    "electromagnetic only.")


def _segments_cross(a, b, c, d):
    """True if the open segments ab and cd cross properly or touch (collinear overlap counts)."""
    def orient(p, q, r):
        v = (q[0] - p[0]) * (r[1] - p[1]) - (q[1] - p[1]) * (r[0] - p[0])
        return 0 if abs(v) < 1e-12 else (1 if v > 0 else -1)

    def on_seg(p, q, r):
        return (min(p[0], q[0]) - 1e-12 <= r[0] <= max(p[0], q[0]) + 1e-12
                and min(p[1], q[1]) - 1e-12 <= r[1] <= max(p[1], q[1]) + 1e-12)
    o1, o2, o3, o4 = orient(a, b, c), orient(a, b, d), orient(c, d, a), orient(c, d, b)
    if o1 != o2 and o3 != o4:
        return True
    return ((o1 == 0 and on_seg(a, b, c)) or (o2 == 0 and on_seg(a, b, d))
            or (o3 == 0 and on_seg(c, d, a)) or (o4 == 0 and on_seg(c, d, b)))


def polygon_is_simple(poly):
    """True if no two non-adjacent edges touch/cross and no edge has zero length."""
    n = len(poly)
    edges = [(poly[i], poly[(i + 1) % n]) for i in range(n)]
    if any(e[0] == e[1] for e in edges):
        return False
    for i in range(n):
        for j in range(i + 1, n):
            if j == i + 1 or (i == 0 and j == n - 1):
                # adjacent edges share exactly one vertex; they must not overlap collinearly (spike): checked via area below
                continue
            if _segments_cross(edges[i][0], edges[i][1], edges[j][0], edges[j][1]):
                return False
    return True


def polygon_area(poly):
    return 0.5 * abs(sum(poly[i][0] * poly[(i + 1) % len(poly)][1] - poly[(i + 1) % len(poly)][0] * poly[i][1]
                         for i in range(len(poly))))


def in_metal_layer(x, y, poly, slots):
    return point_in_polygon(x, y, poly) and not any(point_in_polygon(x, y, s_) for s_ in slots)


def substrate_z_lines(h, n_lines, zs=()):
    """z lines of the substrate, 0..h. Without parasitics: np.linspace(0, h, n_lines) (unchanged). With parasitics at the elevations
    zs: a HARD line at every z; if every z already coincides (1e-9 mm) with a linspace line that line is replaced by the exact z and
    all others are kept; otherwise the n_lines - 1 cells are shared among the segments (0, z1, ..., h) by repeatedly splitting the
    segment with the largest cell (>= 1 cell per segment) and every segment is divided uniformly (keeps the substrate cell
    ratio close to 1, so SmoothMeshLines adds nothing inside the board)."""
    import numpy as np
    base = np.linspace(0, h, n_lines)
    # inverted stack: a sheet ON the top face (z == h) needs no extra line (the substrate top line already exists); duplicates collapse
    zs_all = sorted(float(z) for z in zs if float(z) < h - PARASITIC_Z_TOL_MM)
    zs = []
    for z in zs_all:
        if not zs or z - zs[-1] > PARASITIC_Z_TOL_MM:
            zs.append(z)
    if not zs:
        return base
    snapped = base.copy()
    ok = True
    for z in zs:
        i = int(np.argmin(np.abs(base - z)))
        if 0 < i < n_lines - 1 and abs(base[i] - z) <= PARASITIC_Z_TOL_MM:
            snapped[i] = z
        else:
            ok = False
    if ok:
        return snapped
    bounds = [0.0, *zs, float(h)]
    seg = [bounds[i + 1] - bounds[i] for i in range(len(bounds) - 1)]
    n_cells = [1] * len(seg)
    if sum(n_cells) > n_lines - 1:
        raise ValueError("too many parasitic patches for the substrate mesh lines of this mesh profile")
    while sum(n_cells) < n_lines - 1:
        k = max(range(len(seg)), key=lambda i: seg[i] / n_cells[i])
        n_cells[k] += 1
    lines = [0.0]
    for i, n_ in enumerate(n_cells):
        lines += [bounds[i] + seg[i] * j / n_ for j in range(1, n_ + 1)]
    lines[-1] = float(h)
    return np.asarray(lines, dtype=float)


DRIVEN_LAYER_MODEL = (
    "inverted stack (variant key driven_z_mm = z_d < h): the DRIVEN patch (with its U-slot) and its microstrip feed (50 ohm line + lambda/4 "
    "transformer, feed_polygons_mm) are conducting sheets at z = z_d inside the HOMOGENEOUS substrate (same eps_r / tan_delta over the whole "
    "thickness h); the ground is at z = 0. The vertical 50 ohm lumped edge port integrates 0 -> z_d at the line end on the board edge "
    "(y = -size_y/2). Parasitic sheets may lie above (z_d < z <= h) or below (0 < z < z_d) the driven layer; every pair of metal layers "
    "(ground, driven layer, parasitics) is >= one substrate cell apart. Slots of the driven patch are zero-thickness polygons of a "
    "substrate-eps/kappa Material (priority 20 > sheet 10) at z_d (no air layer inside the dielectric). The edge line is an EMBEDDED "
    "microstrip (substrate above it when z_d < h): its impedance and wavelength differ from the exposed microstrip the widths in the "
    "variant were designed for, and this is NOT re-synthesised. Only --edge-port lumped is supported (the MSL port post-processing "
    "assumes an exposed line of height h).")


def parse_driven_layer(data, n_substrate_lines=None):
    """Validate the optional variant key 'driven_z_mm' (z of the driven patch + feed layer; default and 'inverted' = False when absent or == h).
    Returns {"key_present", "z_mm" (== substrate h_mm object when not inverted), "inverted", "cell_mm", "warnings"}. Raises ValueError for: non-numeric
    value; z <= 0 or z > h; z closer than ONE substrate cell (h / (substrate lines - 1)) to the ground or to the top face (when 0 < z < h); probe
    feeds (only edge feeds are supported with z_d < h)."""
    sub, feed = data["substrate"], data["feed"]
    h = sub["h_mm"]
    n_lines = SUBSTRATE_LINES if n_substrate_lines is None else n_substrate_lines
    cell = float(h) / (n_lines - 1)
    key = data.get("driven_z_mm")
    out = {"key_present": "driven_z_mm" in data, "z_mm": h, "inverted": False, "cell_mm": cell, "warnings": []}
    if key is None:
        if out["key_present"]:
            raise ValueError("driven_z_mm must be a number (mm) or absent")
        return out
    if isinstance(key, bool) or not isinstance(key, (int, float)) or not math.isfinite(float(key)):
        raise ValueError(f"driven_z_mm must be a finite number in mm, got {key!r}")
    zd = float(key)
    if not (0.0 < zd <= float(h) + PARASITIC_Z_TOL_MM):
        raise ValueError(f"driven_z_mm = {zd} must satisfy 0 < driven_z_mm <= h_mm = {float(h)}")
    if abs(zd - float(h)) <= PARASITIC_Z_TOL_MM:
        return out   # == h: the classic stack (the key only documents it)
    if feed["type"] == PROBE_FEED:
        raise ValueError("driven_z_mm < h_mm is supported for edge feeds (microstrip_inset_edge / microstrip_edge_qw) only, not for the probe feed")
    if zd < cell - PARASITIC_Z_TOL_MM or zd > float(h) - cell + PARASITIC_Z_TOL_MM:
        raise ValueError(f"driven_z_mm = {zd} is closer than one substrate mesh cell ({cell:.4f} mm = h/{n_lines - 1}) to the ground (0) or to the "
                         f"top face (h = {float(h)}); allowed range [{cell:.4f}, {float(h) - cell:.4f}] mm (or exactly h)")
    out.update({"z_mm": zd, "inverted": True})
    return out


def parse_parasitics(data, poly, slots, n_substrate_lines=None):
    """Validate and normalise the optional variant key 'parasitic_patches' (buried parasitic patches in the homogeneous substrate).
    Returns a list of dicts {name, z_mm, poly, slots, bbox, area_mm2, overlap} ([] if the key is absent) plus warnings stored in
    each item ('warnings'). Raises ValueError (clear message) for: z outside the substrate or closer than ONE substrate mesh cell
    (h / (substrate lines - 1)) to the ground (0) or to the driven patch (h) or to another parasitic at a different elevation;
    polygon outside the board, non-simple or degenerate; slots outside the parasitic bounding box; probe/line port short-circuited by the
    sheet. WARNS (not an error) if the parasitic is not (fully) under the driven patch outline."""
    items = data.get("parasitic_patches")
    if items is None:
        return []
    if not isinstance(items, list):
        raise ValueError("parasitic_patches must be a list of {name, z_mm, polygon_mm[, slots_polygon_mm]}")
    sub, feed = data["substrate"], data["feed"]
    h = float(sub["h_mm"])
    sx, sy = sub["size_mm"]
    n_lines = SUBSTRATE_LINES if n_substrate_lines is None else n_substrate_lines
    cell = h / (n_lines - 1)
    drv = parse_driven_layer(data, n_lines)
    inverted, zd = drv["inverted"], float(drv["z_mm"])
    out, names = [], set()
    pxs, pys = zip(*poly)
    for k, it in enumerate(items):
        for key in ("name", "z_mm", "polygon_mm"):
            if key not in it:
                raise ValueError(f"parasitic_patches[{k}] lacks '{key}'")
        name = str(it["name"])
        if not re.fullmatch(r"[A-Za-z0-9_\-]+", name) or name in names:
            raise ValueError(f"parasitic_patches[{k}]: name '{name}' must be unique and made of letters, digits, '_' or '-'")
        names.add(name)
        z = float(it["z_mm"])
        if inverted:
            # inverted stack: the driven layer is at zd < h; the top face z = h is allowed (parasitic on the board surface)
            if not (0.0 < z <= h + PARASITIC_Z_TOL_MM):
                raise ValueError(f"parasitic '{name}': z_mm = {z} must satisfy 0 < z_mm <= h_mm = {h} (inverted stack: driven_z_mm = {zd})")
            if abs(z - h) <= PARASITIC_Z_TOL_MM:
                z = h
            if abs(z - zd) <= PARASITIC_Z_TOL_MM:
                raise ValueError(f"parasitic '{name}': z_mm = {z} equals driven_z_mm = {zd}: a parasitic cannot lie on the driven layer plane")
            if z < cell - PARASITIC_Z_TOL_MM or (z != h and z > h - cell + PARASITIC_Z_TOL_MM):
                raise ValueError(f"parasitic '{name}': z_mm = {z} is closer than one substrate mesh cell ({cell:.4f} mm = h/{n_lines - 1}) "
                                 f"to the ground (0) or to the top face (h = {h}); allowed [{cell:.4f}, {h - cell:.4f}] mm or exactly h")
            if abs(z - zd) < cell - PARASITIC_Z_TOL_MM:
                raise ValueError(f"parasitic '{name}': z_mm = {z} is closer than one substrate mesh cell ({cell:.4f} mm) to the driven layer "
                                 f"(driven_z_mm = {zd})")
        else:
            if not (0.0 < z < h):
                raise ValueError(f"parasitic '{name}': z_mm = {z} must satisfy 0 < z_mm < h_mm = {h} (a parasitic on the ground or on the "
                                 f"patch plane is not a buried patch)")
            if z < cell - PARASITIC_Z_TOL_MM or z > h - cell + PARASITIC_Z_TOL_MM:
                raise ValueError(f"parasitic '{name}': z_mm = {z} is closer than one substrate mesh cell ({cell:.4f} mm = h/{n_lines - 1}) "
                                 f"to the ground (0) or to the patch plane (h = {h}); allowed range [{cell:.4f}, {h - cell:.4f}] mm")
        ppoly = [tuple(map(float, q)) for q in it["polygon_mm"]]
        if len(ppoly) < 3 or any(len(q) != 2 for q in it["polygon_mm"]):
            raise ValueError(f"parasitic '{name}': polygon_mm needs >= 3 [x, y] vertices")
        if polygon_area(ppoly) <= 1e-9 or not polygon_is_simple(ppoly):
            raise ValueError(f"parasitic '{name}': polygon_mm must be a simple (non self-intersecting) polygon with area > 0")
        qx, qy = zip(*ppoly)
        if min(qx) < -sx / 2 - 1e-9 or max(qx) > sx / 2 + 1e-9 or min(qy) < -sy / 2 - 1e-9 or max(qy) > sy / 2 + 1e-9:
            raise ValueError(f"parasitic '{name}': polygon exceeds the board ({sx} x {sy} mm)")
        pslots = [[tuple(map(float, q)) for q in sl] for sl in it.get("slots_polygon_mm", [])]
        for j, sl in enumerate(pslots):
            if len(sl) < 3 or polygon_area(sl) <= 1e-9 or not polygon_is_simple(sl):
                raise ValueError(f"parasitic '{name}': slot {j} must be a simple polygon with >= 3 vertices and area > 0")
            sxs, sys_ = zip(*sl)
            if min(sxs) < min(qx) or max(sxs) > max(qx) or min(sys_) < min(qy) or max(sys_) > max(qy):
                raise ValueError(f"parasitic '{name}': slot {j} exceeds the parasitic bounding box")
        warnings = []
        if feed["type"] == PROBE_FEED:
            if in_metal_layer(float(feed["x_mm"]), float(feed["y_mm"]), ppoly, pslots):
                raise ValueError(f"parasitic '{name}': the probe at ({feed['x_mm']}, {feed['y_mm']}) mm crosses the parasitic sheet "
                                 "(it would short the port); give the parasitic a slot around the probe or move it")
        else:
            lx, w, y0 = float(feed["line_x_mm"]), float(feed["line_width_mm"]), float(feed["line_start_y_mm"])
            if inverted and z > zd + PARASITIC_Z_TOL_MM:
                # above the driven layer the sheet cannot touch the 0 -> zd port; it still loads the embedded line if it covers it
                for r_ in feed_rectangles(feed):
                    rxs, rys = [v[0] for v in r_], [v[1] for v in r_]
                    if not (max(qx) < min(rxs) or max(rxs) < min(qx) or max(qy) < min(rys) or max(rys) < min(qy)):
                        warnings.append(f"parasitic '{name}' (z = {z}, above the driven layer) overlaps the projection of a feed rectangle "
                                        f"(x {min(rxs):.3f}..{max(rxs):.3f}, y {min(rys):.3f}..{max(rys):.3f}); it loads the line")
                        break
            elif min(qy) <= y0 + 1e-9 and max(qx) >= lx - w / 2 and min(qx) <= lx + w / 2:
                raise ValueError(f"parasitic '{name}': reaches the launch plane under the feed line (x {lx - w / 2:.3f}..{lx + w / 2:.3f}, "
                                 f"y = {y0}); it would touch the 50 ohm port")
        # overlap with the driven patch outline (projection), sampled on a grid over the parasitic bounding box
        n_in = n_pp = 0
        for ix in range(PARASITIC_SAMPLES):
            for iy in range(PARASITIC_SAMPLES):
                x_ = min(qx) + (max(qx) - min(qx)) * (ix + 0.5) / PARASITIC_SAMPLES
                y_ = min(qy) + (max(qy) - min(qy)) * (iy + 0.5) / PARASITIC_SAMPLES
                if in_metal_layer(x_, y_, ppoly, pslots):
                    n_pp += 1
                    if point_in_polygon(x_, y_, poly):
                        n_in += 1
        frac_inside = n_in / n_pp if n_pp else 0.0
        if n_pp == 0:
            raise ValueError(f"parasitic '{name}': no metal left after the slots")
        if frac_inside == 0.0:
            warnings.append(f"parasitic '{name}' is NOT under the driven patch outline (0 % of its area overlaps the patch projection)")
        elif frac_inside < 0.999:
            warnings.append(f"parasitic '{name}': only {100 * frac_inside:.1f} % of its area lies under the driven patch outline")
        out.append({"name": name, "z_mm": z, "poly": ppoly, "slots": pslots,
                    "bbox": [min(qx), min(qy), max(qx), max(qy)], "area_mm2": polygon_area(ppoly) - sum(polygon_area(s_) for s_ in pslots),
                    "fraction_under_patch_outline": frac_inside, "warnings": warnings})
    for i in range(len(out)):
        for j in range(i + 1, len(out)):
            a, b = out[i], out[j]
            if abs(a["z_mm"] - b["z_mm"]) < PARASITIC_Z_TOL_MM:
                if not (a["bbox"][2] < b["bbox"][0] or b["bbox"][2] < a["bbox"][0] or a["bbox"][3] < b["bbox"][1] or b["bbox"][3] < a["bbox"][1]):
                    raise ValueError(f"parasitics '{a['name']}' and '{b['name']}' share z_mm and overlap in projection (they would merge)")
            elif abs(a["z_mm"] - b["z_mm"]) < cell - PARASITIC_Z_TOL_MM:
                raise ValueError(f"parasitics '{a['name']}' and '{b['name']}' are closer than one substrate mesh cell ({cell:.4f} mm) in z")
    return out


def parasitic_summary(metadata):
    """Human-readable lines for the prepare output (empty list if the variant has no parasitic patches)."""
    geo = metadata.get("geometry", {})
    lines = []
    dl = geo.get("driven_layer")
    if dl:
        lines.append(f"driven layer z = {dl['driven_z_mm']} mm (h = {dl['substrate_h_mm']} mm, inverted = {dl['inverted']}); z segments: "
                     + "; ".join(f"{sg['from_mm']:.4f}-{sg['to_mm']:.4f} mm ({sg['from']} -> {sg['to']}): {sg['cells']} cells" for sg in dl["z_segments"]))
    for p_ in geo.get("parasitic_patches") or []:
        zc = p_["z_cells"]
        if "parasitic_to_patch" not in zc:   # inverted stack: no cells between parasitic and 'the patch'; see driven_layer.z_segments
            lines.append(f"parasitic {p_['name']}: z = {p_['z_mm']} mm ({p_['layer_relation']}), bbox {p_['bbox_mm']}, area {p_['area_mm2']:.2f} mm2, "
                         f"{100 * p_['fraction_under_patch_outline']:.1f} % under the patch; z cells ground-parasitic {zc['ground_to_parasitic']}, "
                         f"parasitic-top face {zc['parasitic_to_top_face']}")
            continue
        lines.append(f"parasitic {p_['name']}: z = {p_['z_mm']} mm, bbox {p_['bbox_mm']}, area {p_['area_mm2']:.2f} mm2, "
                     f"{100 * p_['fraction_under_patch_outline']:.1f} % under the patch; z cells ground-parasitic {zc['ground_to_parasitic']} "
                     f"({zc['ground_to_parasitic_cell_mm']:.4f} mm), parasitic-patch {zc['parasitic_to_patch']} "
                     f"({zc['parasitic_to_patch_cell_mm']:.4f} mm)")
    lines += ["WARNING: " + w for w in metadata.get("warnings", [])]
    return lines


# ---- model construction -------------------------------------------------------------------------
def add_edge_port(fdtd, patch, feed, sub, poly, model, np, zd=None):
    """Create the 50 ohm port of a microstrip_inset_edge feed. Must run AFTER the mesh is final (MSLPort reads
    mesh.GetLines at construction). Returns (port, metadata). See EDGE_PORT_MODEL."""
    h = sub["h_mm"]
    zt = h if zd is None else zd   # height of the line above the ground (inverted stack: z_d < h; only the lumped port supports it)
    if zt != h and model != "lumped":
        raise ValueError("driven_z_mm < h_mm requires --edge-port lumped (the MSL port and its post-processing assume the line at z = h)")
    w, lx = float(feed["line_width_mm"]), float(feed["line_x_mm"])
    y0, y_end = float(feed["line_start_y_mm"]), float(feed["line_end_y_mm"])
    z0 = float(feed["z0_ohm"])
    qw = feed["type"] == EDGE_QW_FEED
    # microstrip_edge_qw: the 50 ohm section ends at the transformer start, so the discontinuity the port must stay away from
    # is transformer_start_y_mm (= line_end_y_mm), not the patch edge
    patch_low = float(feed["transformer_start_y_mm"]) if qw else min(p[1] for p in poly)
    far_name = "transformer start" if qw else "patch edge"
    base = {"model": model, "launch_plane_y_mm": y0, "reference_ohm": z0, "line_width_mm": w, "line_x_mm": lx,
            "connector_declared_in_variant": feed.get("connector"), "connector_body_modelled": False,
            "description": EDGE_PORT_MODEL}
    if model == "lumped":
        port = fdtd.AddLumpedPort(1, z0, [lx - w / 2, y0, 0], [lx + w / 2, y0, zt], "z", 1.0, priority=PORT_PRIORITY)
        base.update({"type": "vertical lumped port on the end of the line at the board edge; no edges2grid (grid lines come "
                             "from the microstrip rules); no pin/coax/aperture/de-embedding",
                     "start_mm": [lx - w / 2, y0, 0], "stop_mm": [lx + w / 2, y0, zt], "priority": PORT_PRIORITY,
                     "reference_plane_y_mm": y0, "reference_plane": "board edge (U and I measured at the port itself)"})
        if zt != h:
            base["driven_z_mm"] = zt
            base["vertical_integration_mm"] = [0.0, zt]
            base["note_inverted_stack"] = "port height = driven_z_mm (line layer), not the substrate thickness h"
        return port, base
    shift = EDGE_PORT_FEED_SHIFT_MM
    meas = min(EDGE_PORT_MEAS_MAX_MM, 0.5 * (shift + (patch_low - y0)))
    d_src, d_patch = meas - shift, (patch_low - y0) - meas
    if min(d_src, d_patch) < h:
        raise RuntimeError(f"MSL port does not fit: measurement plane would be {d_src:.2f} mm from the source and "
                           f"{d_patch:.2f} mm from the {far_name} (< h = {h} mm); lengthen the feed line or use --edge-port lumped")
    stop_y = y0 + meas + EDGE_PORT_STOP_AFTER_MEAS_MM
    if stop_y > y_end:
        raise RuntimeError("MSL port metal box would exceed the microstrip line end")
    warnings = []
    if min(d_src, d_patch) < EDGE_PORT_MIN_SEP_H * h:
        warnings.append(f"measurement plane {d_src:.2f} mm from the source / {d_patch:.2f} mm from the {far_name} is below "
                        f"{EDGE_PORT_MIN_SEP_H} h = {EDGE_PORT_MIN_SEP_H * h:.2f} mm: higher-order/evanescent content may bias Z_line and beta")
    port = fdtd.AddMSLPort(1, patch, [lx - w / 2, y0, h], [lx + w / 2, stop_y, 0], "y", "z", 1.0,
                           FeedShift=shift, MeasPlaneShift=meas, Feed_R=z0, priority=SHEET_PRIORITY)
    meas_y_snapped = y0 + float(port.measplane_shift)
    base.update({
        "type": "openEMS MSLPort probes (3 voltage + 2 current); post-processing: voltage-only beta, fixed 50 ohm reference, ideal-line shift to the launch plane (port_postprocess.py)",
        "start_mm": [lx - w / 2, y0, h], "stop_mm": [lx + w / 2, stop_y, 0], "prop_dir": "y (+y)", "exc_dir": "z",
        "feed_shift_mm": shift, "feed_R_ohm": z0, "priority": SHEET_PRIORITY,
        "excitation_plane_y_mm_nominal": y0 + shift,
        "measurement_plane_y_mm_requested": y0 + meas, "measurement_plane_y_mm_snapped_to_grid": meas_y_snapped,
        "measurement_plane_distance_to_source_mm": d_src, "measurement_plane_distance_to_patch_edge_mm": d_patch,
        "patch_lowest_y_mm": min(p[1] for p in poly), "discontinuity_y_mm": patch_low, "discontinuity": far_name,
        "reference_plane_y_mm": y0,
        "reference_plane": "s11_measplane.csv: measurement plane (middle voltage probe), fixed 50 ohm; s11_complex.csv: board edge "
                           "y = -size_y/2, U,I moved over an ideal lossless 50 ohm line with the voltage-estimated beta",
        "postprocess": pp.POSTPROCESS_MODEL,
        "warnings": warnings})
    return port, base


def excitation_metadata():
    lo, hi = nominal_valid_range_hz()
    grid = wideband_grid()
    return {"type": "Gaussian", "center_hz": F0_HZ, "corner_offset_hz": GAUSS_FC_HZ,
            "option": "--excitation-fc-hz (default 1e9 = XML of 001/004/005/006)",
            "nominal_minus20dB_range_hz": [lo, hi],
            "nominal_range_rule": "spectrum exp(-2.25 (f - f0)^2 / fc^2) (openEMS excitation.cpp CalcGaussianPulse/MaxFreq): -20 dB at f0 +- 1.0116 fc",
            "wideband_grid_hz": [float(grid[0]), float(grid[-1]), WIDEBAND_STEP_HZ],
            "pulse_length_s": 2 * 9.0 / (2 * math.pi * GAUSS_FC_HZ),
            "pulse_length_rule": "openEMS CalcGaussianPulsExcitation: 2 * 9 / (2 pi fc)",
            "NrTS": NR_TS, "EndCriteria": END_CRITERIA,
            "NrTS_EndCriteria_note": ("pulse length scales as 1/fc (fc 1 GHz: 2.87 ns; 2.5 GHz: 1.15 ns) and is far below the "
                                      f"{NR_TS}-step cap; the energy criterion is relative to the peak energy, so it is unchanged; the "
                                      "step estimate in budget_before_solve keeps the 006 record length (conservative: a shorter "
                                      "pulse cannot lengthen the ring-down). Higher f_max only raises the probe sampling rate. "
                                      "Cells: xy <= 0.5 mm (lambda_FR4/27 at 10.5 GHz), air z <= 0.8 mm (lambda0/36). PML_8 and the "
                                      "NF2FF box (17.5 mm) are less effective at 5.5 GHz (box 0.32 lambda): outside-band content is "
                                      "for the port only; NF2FF frequencies stay in the channel.")}


def qw_mesh_extras(feed, feed_rects, slots, user_hints):
    """microstrip_edge_qw mesh requirements (round 7). Returns (hard lines incl. the variant's own mesh_hint_lines_mm, plain lines).

    hard: y of the two shared copper edges (transformer_start_y_mm, patch_edge_y_mm); x of the axis of every feed rectangle narrower
    than NARROW_STRIP_MM (a 0.72 mm transformer then has its two edge rules plus a central line: >= 3 cells across).
    plain (dropped/merged when near a rule line): y lines spaced <= SLOT_MAX_CELL_MM across the bounding box of every slot (>= 6 cells)."""
    hard = {a: [float(v) for v in user_hints.get(a, [])] for a in "xyz" if a in user_hints}
    hard.setdefault("x", [])
    hard.setdefault("y", [])
    hard["y"] += [float(feed["transformer_start_y_mm"]), float(feed["patch_edge_y_mm"])]
    for r_ in feed_rects:
        rx = [q[0] for q in r_]
        if max(rx) - min(rx) < NARROW_STRIP_MM:
            hard["x"].append(0.5 * (min(rx) + max(rx)))
    plain = {"x": [], "y": []}
    for sl in slots:
        # y only (the smaller extent, 1.905 mm flat to flat -> 7 intervals): extra plain x lines pushed the neighbour ratio to 1.49
        # next to the transformer rule lines; in x the slot rule lines + SmoothMeshLines already give >= 6 cells across 2.2 mm
        vals = [q[1] for q in sl]
        lo, hi = min(vals), max(vals)
        n = max(2, math.ceil((hi - lo) / SLOT_MAX_CELL_MM))
        plain["y"] += [lo + (hi - lo) * i / n for i in range(1, n)]
    return hard, plain


def build(variant_path, out, opts=None):
    import numpy as np
    from CSXCAD import ContinuousStructure
    from openEMS import openEMS

    opts = {"edge_port": "msl", "nf2ff": False, "nf2ff_points": 11, **(opts or {})}
    data, poly, slots = load_variant(variant_path)
    sub, metal, feed = data["substrate"], data["metal"], data["feed"]
    drv = parse_driven_layer(data)   # inverted stack (driven_z_mm < h); without the key zd == h and every path below is unchanged
    parasitics = parse_parasitics(data, poly, slots)   # [] without the optional key: every path below is then unchanged
    edge = feed["type"] in EDGE_FEEDS
    qw = feed["type"] == EDGE_QW_FEED
    h = sub["h_mm"]
    zd, inverted = drv["z_mm"], drv["inverted"]   # z of the driven patch + feed layer; zd is h (same object) without the key
    if inverted and opts["edge_port"] != "lumped":
        raise ValueError(f"driven_z_mm = {zd} < h_mm = {h} requires --edge-port lumped (the MSL port and its post-processing assume the "
                         "line at z = h)")
    er, tand = sub["eps_r"], sub["tan_delta"]
    sx, sy = sub["size_mm"]
    fx, fy = (None, None) if edge else (feed["x_mm"], feed["y_mm"])
    z0 = feed["z0_ohm"]
    box = max(BOX_HALF_MM, max(sx, sy) / 2 + 22.0)  # 35 mm for a 26 mm board, as in 001
    xs, ys = zip(*poly)
    rect = (not edge) and is_axis_aligned_rectangle(poly) and not slots and not parasitics   # parasitics: polygon meshing path
    feed_rects = feed_rectangles(feed) if edge else []
    line_rect = feed_rects[0] if edge else None

    fdtd = openEMS(NrTS=NR_TS, EndCriteria=END_CRITERIA)
    fdtd.SetGaussExcite(F0_HZ, GAUSS_FC_HZ)  # GAUSS_FC_HZ = --excitation-fc-hz (default 1e9)
    fdtd.SetBoundaryCond(["PML_8"] * 6)
    csx = ContinuousStructure()
    fdtd.SetCSX(csx)
    mesh = csx.GetGrid()
    mesh.SetDeltaUnit(1e-3)
    mesh.AddLine("x", [-box, -sx / 2, sx / 2, box])
    mesh.AddLine("y", [-box, -sy / 2, sy / 2, box])
    sub_z = substrate_z_lines(h, SUBSTRATE_LINES, [q["z_mm"] for q in parasitics] + ([zd] if inverted else []))
    mesh.AddLine("z", [Z_LOW_MM, *sub_z, Z_HIGH_MM])   # parasitics / driven layer: hard line at every z (sub_z == linspace without them)
    kappa = 2 * math.pi * F0_HZ * EPS0 * er * tand
    substrate = csx.AddMaterial(sub["name"], epsilon=er, kappa=kappa)
    substrate.AddBox([-sx / 2, -sy / 2, 0], [sx / 2, sy / 2, h], priority=0)
    patch = csx.AddConductingSheet("patch_copper", conductivity=metal["conductivity_S_m"],
                                   thickness=metal["thickness_m"])
    slot_prop = None
    if rect:
        patch.AddBox([min(xs), min(ys), h], [max(xs), max(ys), h], priority=SHEET_PRIORITY)
    else:
        patch.AddPolygon([[p[0] for p in poly], [p[1] for p in poly]], "z", zd, priority=SHEET_PRIORITY)
        if slots:
            if inverted:   # driven layer inside the dielectric: the slot removes the sheet without adding an air layer (as for parasitics)
                slot_prop = csx.AddMaterial("driven_slot_substrate", epsilon=er, kappa=kappa)
            else:
                slot_prop = csx.AddMaterial("slot_air", epsilon=1.0, kappa=0.0)
            for s in slots:
                slot_prop.AddPolygon([[p[0] for p in s], [p[1] for p in s]], "z", zd, priority=SLOT_PRIORITY)
    for r_ in feed_rects:   # feed copper exactly as given (axis-aligned rectangles; one box per rectangle), on the driven layer
        rx, ry = [q[0] for q in r_], [q[1] for q in r_]
        patch.AddBox([min(rx), min(ry), zd], [max(rx), max(ry), zd], priority=SHEET_PRIORITY)
    par_props = []
    for q in parasitics:   # buried parasitic sheets (PARASITIC_MODEL): same copper as the patch, polygon at z_mm
        prop = csx.AddConductingSheet(f"parasitic_{q['name']}_copper", conductivity=metal["conductivity_S_m"],
                                      thickness=metal["thickness_m"])
        prop.AddPolygon([[v[0] for v in q["poly"]], [v[1] for v in q["poly"]]], "z", q["z_mm"], priority=SHEET_PRIORITY)
        if q["slots"]:
            cut = csx.AddMaterial(f"parasitic_{q['name']}_slot_substrate", epsilon=er, kappa=kappa)
            for sl in q["slots"]:
                cut.AddPolygon([[v[0] for v in sl], [v[1] for v in sl]], "z", q["z_mm"], priority=SLOT_PRIORITY)
        assert prop.GetConductivity() == metal["conductivity_S_m"] and prop.GetThickness() == metal["thickness_m"]
        par_props.append(prop)
    ground = csx.AddConductingSheet("ground_copper", conductivity=metal["conductivity_S_m"],
                                    thickness=metal["thickness_m"])
    ground.AddBox([-sx / 2, -sy / 2, 0], [sx / 2, sy / 2, 0], priority=SHEET_PRIORITY)
    assert patch.GetConductivity() == metal["conductivity_S_m"] and patch.GetThickness() == metal["thickness_m"]
    assert ground.GetThickness() == metal["thickness_m"]
    fixed_report = None
    if rect:
        fdtd.AddEdges2Grid(dirs="xy", properties=patch, metal_edge_res=METAL_EDGE_RES_MM)
    else:
        user_hints = data.get("mesh_hint_lines_mm", {})
        extra_hard, extra_plain = {a: list(v) for a, v in user_hints.items()}, None
        if qw:
            extra_hard, extra_plain = qw_mesh_extras(feed, feed_rects, slots, user_hints)
        elif not edge:
            # probe feed on the polygon path (round 12): the vertical lumped port lines are HARD lines of the fixed set, so that
            # a rule/plain line within MESH_MERGE_TOL_MM of the port is merged into the port line (no sliver cell next to the
            # port) and the relaxation treats them as immovable. The rectangle path (001/003/004/005) does not use this.
            extra_hard.setdefault("x", []).append(float(fx))
            extra_hard.setdefault("y", []).append(float(fy))
        fixed, fixed_report = fixed_mesh_lines(poly, slots, feed_rects, (sx / 2, sy / 2), METAL_EDGE_RES_MM, box, extra_hard,
                                               extra_plain, layers=[(q["poly"], q["slots"]) for q in parasitics] or None)
        if qw:
            fixed_report["qw_extra_lines_mm"] = {"hard": extra_hard, "plain": extra_plain}
        elif not edge:
            fixed_report["probe_hard_lines_mm"] = {"x": float(fx), "y": float(fy)}
        for axis in "xy":
            mesh.AddLine(axis, sorted(fixed[axis]))
        if user_hints.get("z"):
            mesh.AddLine("z", sorted(float(v) for v in user_hints["z"]))
    fdtd.AddEdges2Grid(dirs="xy", properties=ground)
    port = None
    if not edge:
        port = fdtd.AddLumpedPort(1, z0, [fx, fy, 0], [fx, fy, h], "z", 1.0,
                                  priority=PORT_PRIORITY, edges2grid="xy")
    smoothing_param = {}
    if rect:
        mesh.SmoothMeshLines("x", XY_MAX_STEP_MM, SMOOTH_RATIO)
        mesh.SmoothMeshLines("y", XY_MAX_STEP_MM, SMOOTH_RATIO)
    else:
        for axis in "xy":
            smoothing_param[axis] = smooth_axis_search(mesh, np, axis, XY_MAX_STEP_MM, infill=(not edge) or bool(parasitics),
                                                       both_cells=bool(parasitics))
    mesh.SmoothMeshLines("z", Z_MAX_STEP_MM, SMOOTH_RATIO)
    # Fallback (added Claude round 4): openEMS SmoothMeshLines(…, 1.4) can leave a
    # neighbour ratio slightly above 1.4 when fixed lines (feed, edge thirds) are
    # close and no gap exceeds the max step (re-smoothing then adds no line).
    # Rectangular path: target stays 1.4; up to RECT_GRADING_FALLBACK is accepted
    # and recorded as "mesh_grading_limit_used". P01_BASE (== P01_OPENEMS_001)
    # and P01_R1 meet 1.4 and are unaffected.
    resmooth = {}
    axes = {axis: np.asarray(mesh.GetLines(axis), dtype=float) for axis in "xyz"}
    mesh_info = {}
    for axis, values in axes.items():
        gaps = np.diff(values)
        if not np.all(gaps > 0):
            raise RuntimeError(f"Nonmonotone {axis} mesh")
        ratio = float(np.max(np.maximum(gaps[1:] / gaps[:-1], gaps[:-1] / gaps[1:])))
        limit = SMOOTH_RATIO if rect else POLY_GRADING_LIMIT
        if rect and SMOOTH_RATIO + 1e-8 < ratio <= RECT_GRADING_FALLBACK + 1e-8:
            resmooth[axis] = ratio
            limit = RECT_GRADING_FALLBACK
        elif (not rect) and SMOOTH_RATIO + 1e-8 < ratio <= POLY_GRADING_LIMIT + 1e-8:
            resmooth[axis] = ratio
        if ratio > limit + 1e-8:
            r = np.maximum(gaps[1:] / gaps[:-1], gaps[:-1] / gaps[1:])
            j = int(np.argmax(r))
            raise RuntimeError(f"Mesh grading {axis}: {ratio} exceeds {limit} near lines "
                               f"{np.round(values[max(0, j - 2):j + 4], 4).tolist()} mm "
                               "(add 'mesh_hint_lines_mm' to the variant or move the offending feature)")
        mesh_info[axis] = {"cells": len(values) - 1, "min_step_mm": float(gaps.min()),
                           "max_step_mm": float(gaps.max()), "max_neighbor_ratio": ratio,
                           "pml_inner_low_mm": float(values[8]), "pml_inner_high_mm": float(values[-9])}
    slot_check = slot_mesh_check(slots, axes) if slots else None
    par_meta, par_warnings = [], []
    for q in parasitics:
        zl = axes["z"]
        iz = int(np.argmin(np.abs(zl - q["z_mm"])))
        i0, ih = int(np.argmin(np.abs(zl - 0.0))), int(np.argmin(np.abs(zl - h)))
        if abs(zl[iz] - q["z_mm"]) > 1e-9:
            raise RuntimeError(f"parasitic '{q['name']}': no z mesh line at z_mm = {q['z_mm']}")
        below = [float(v) for v in np.diff(zl[i0:iz + 1])]
        above = [float(v) for v in np.diff(zl[iz:ih + 1])]
        if inverted:
            z_cells_meta = {"ground_to_parasitic": len(below), "parasitic_to_top_face": len(above),
                            "ground_to_parasitic_cells_mm": below, "parasitic_to_top_face_cells_mm": above,
                            "z_line_index": iz, "substrate_cells_total": ih - i0}
        else:
            z_cells_meta = {"ground_to_parasitic": len(below), "parasitic_to_patch": len(above),
                            "ground_to_parasitic_cell_mm": float(np.mean(below)), "parasitic_to_patch_cell_mm": float(np.mean(above)),
                            "ground_to_parasitic_cells_mm": below, "parasitic_to_patch_cells_mm": above,
                            "z_line_index": iz, "substrate_cells_total": ih - i0}
        qx_ = [v[0] for v in q["poly"]]
        qy_ = [v[1] for v in q["poly"]]
        par_warnings += q["warnings"]
        par_meta.append({
            "name": q["name"], "z_mm": q["z_mm"], "polygon_mm": [list(v) for v in q["poly"]],
            "slots_polygon_mm": [[list(v) for v in sl] for sl in q["slots"]], "vertices": len(q["poly"]),
            "bbox_mm": [min(qx_), min(qy_), max(qx_), max(qy_)], "area_mm2": q["area_mm2"],
            "fraction_under_patch_outline": q["fraction_under_patch_outline"], "sheet_property": f"parasitic_{q['name']}_copper",
            "slot_model": ("zero-thickness polygon of a substrate-eps/kappa Material, priority 20 > sheet 10" if q["slots"] else None),
            "z_cells": z_cells_meta,
            "slot_mesh_check": slot_mesh_check(q["slots"], axes) if q["slots"] else None,
            "warnings": q["warnings"]})
        if inverted:
            par_meta[-1]["layer_relation"] = ("on the top face (z = h)" if q["z_mm"] == h else
                                              "above the driven layer" if q["z_mm"] > zd else "below the driven layer")
    for pm in par_meta:
        for sc in (pm["slot_mesh_check"] or {}).get("slots", []):
            if sc["status"] != "OK":
                par_warnings.append(f"parasitic '{pm['name']}' slot {sc['slot']}: {sc['status']} (min cells across {sc['min_cells_across']})")
    driven_meta, driven_warnings = None, []
    if drv["key_present"]:
        zl = axes["z"]
        levels = sorted({0.0, float(h), float(zd), *[float(q["z_mm"]) for q in parasitics]})
        names_by_z = {0.0: "ground", float(h): "top face (z = h)" if inverted else "driven layer (z = h)"}
        if inverted:
            names_by_z[float(zd)] = "driven layer (patch + feed)"
        for q in parasitics:
            names_by_z[float(q["z_mm"])] = (names_by_z.get(float(q["z_mm"]), "") + ("; " if float(q["z_mm"]) in names_by_z else "") +
                                            f"parasitic {q['name']}")
        segs = []
        idx = []
        for lv in levels:
            i_ = int(np.argmin(np.abs(zl - lv)))
            if abs(zl[i_] - lv) > 1e-9:
                raise RuntimeError(f"no z mesh line at the metal layer z = {lv} mm")
            idx.append(i_)
        for a_, b_, ia, ib in zip(levels[:-1], levels[1:], idx[:-1], idx[1:]):
            cs = [float(v) for v in np.diff(zl[ia:ib + 1])]
            segs.append({"from_mm": a_, "to_mm": b_, "from": names_by_z[a_], "to": names_by_z[b_], "cells": len(cs),
                         "cell_mm_min": min(cs), "cell_mm_max": max(cs), "cells_mm": cs})
        if inverted:
            driven_warnings = [
                f"inverted stack: driven layer at z = {zd} mm, substrate above it up to h = {h} mm; the 50 ohm line / lambda/4 transformer "
                "widths of the variant were designed for the exposed microstrip and are NOT re-synthesised for the embedded line "
                "(impedance and guided wavelength differ); S11 will include that mismatch",
                f"edge lumped port integrates 0 -> {zd} mm (line height), not 0 -> h; connector not modelled"]
            if not any(q["z_mm"] == h for q in parasitics):
                driven_warnings.append("inverted stack without any parasitic on the top face: the radiating patch is covered by "
                                       f"{float(h) - float(zd):.3f} mm of dielectric (no parasitic at z = h)")
            if not parasitics:
                driven_warnings.append("inverted stack without parasitic patches")
        driven_meta = {
            "driven_z_mm": zd, "substrate_h_mm": h, "inverted": inverted, "model": DRIVEN_LAYER_MODEL if inverted else
            "driven_z_mm == h_mm: classic stack (patch + feed on the top face); nothing changes in the model",
            "driven_layer_contents": "patch_polygon_mm + slots_polygon_mm + feed_polygons_mm / microstrip line rectangles",
            "port_vertical_integration_mm": ([0.0, zd] if (edge and inverted) else None),
            "min_separation_between_metal_layers_rule_mm": drv["cell_mm"],
            "z_segments": segs, "z_levels_mm": levels, "warnings": driven_warnings}
    if edge:
        port, port_meta = add_edge_port(fdtd, patch, feed, sub, poly, opts["edge_port"], np, zd=zd)
        for axis, value in (("y", feed["line_start_y_mm"]), ("z", 0.0), ("z", zd)):
            if not np.any(np.isclose(axes[axis], value, atol=1e-12, rtol=0)):
                raise RuntimeError(f"Port misses grid on {axis}")
        if port_meta["model"] == "msl":
            y_lines = axes["y"]
            mi = int(np.argmin(np.abs(y_lines - port.measplane_pos)))
            port_meta["port_probe_lines_y_mm"] = [float(y_lines[mi - 1]), float(y_lines[mi]), float(y_lines[mi + 1])]
            port_meta["feed_plane_y_mm_snapped_to_grid"] = float(y_lines[int(np.argmin(np.abs(
                y_lines - (feed["line_start_y_mm"] + EDGE_PORT_FEED_SHIFT_MM))))])
            port_meta["probe_spacing_mm"] = [float(v) for v in np.asarray(port.U_delta)]
    else:
        for axis, value in zip("xyzz", [fx, fy, h, 0.0]):
            if not np.any(np.isclose(axes[axis], value, atol=1e-12, rtol=0)):
                raise RuntimeError(f"Port misses grid on {axis}")
        port_meta = None
        # cells adjacent to the probe line (round 12): reported, the ratio limits are enforced above for the whole axis
        port_cells = {}
        for axis, value in zip("xy", [fx, fy]):
            i_ = int(np.argmin(np.abs(axes[axis] - value)))
            port_cells[axis] = {"line_mm": float(axes[axis][i_]), "cell_below_mm": float(axes[axis][i_] - axes[axis][i_ - 1]),
                                "cell_above_mm": float(axes[axis][i_ + 1] - axes[axis][i_])}
        port_cells["z"] = {"line_0_mm": 0.0, "line_h_mm": h, "substrate_cells": SUBSTRATE_LINES - 1,
                           "substrate_cell_mm": h / (SUBSTRATE_LINES - 1)}
    cells = math.prod(info["cells"] for info in mesh_info.values())
    nodal = math.prod(info["cells"] + 1 for info in mesh_info.values())
    cfl = 1 / (C0 * math.sqrt(sum((info["min_step_mm"] * 1e-3) ** -2 for info in mesh_info.values())))
    nf2ff_box, nf2ff_meta, nf2ff_equiv, nf2ff_bytes = None, None, 0.0, 0
    if opts["nf2ff"]:
        n_freq = opts["nf2ff_points"]
        if n_freq not in NF2FF_BAND_POINTS:
            raise ValueError(f"--nf2ff-points must be one of {sorted(NF2FF_BAND_POINTS)}")
        nf2ff_freqs = [float(f) for f in NF2FF_BAND_POINTS[n_freq]]
        nf2ff_box = fdtd.CreateNF2FFBox("nf2ff", frequency=nf2ff_freqs)
        n_lines = [len(axes[a]) - 18 for a in "xyz"]   # lines from index 9 to -10 inclusive (PML_8 -> BC size 9)
        face_nodes = 2 * (n_lines[0] * n_lines[1] + n_lines[1] * n_lines[2] + n_lines[0] * n_lines[2])
        nf2ff_equiv = face_nodes * 6 * n_freq * NF2FF_DFT_COST_CELLS
        nf2ff_bytes = face_nodes * 6 * n_freq * 8  # complex<float> accumulators for E and H (3 comps each)
        # microstrip_edge_qw: phase centre = board origin (fixed, patch off-centre by design); other feeds keep the patch bbox centre
        c_xy = [0.0, 0.0] if qw else [0.5 * (min(xs) + max(xs)), 0.5 * (min(ys) + max(ys))]
        nf2ff_meta = {
            "enabled": True, "name": "nf2ff", "model": FAR_FIELD_MODEL, "frequencies_hz": nf2ff_freqs,
            "frequency_points": n_freq, "domain": "frequency (E/H FD dumps, dump_type 10/11)",
            "box_start_mm": [float(v) for v in nf2ff_box.start], "box_stop_mm": [float(v) for v in nf2ff_box.stop],
            "box_directions": [bool(v) for v in nf2ff_box.directions], "box_mirror": list(nf2ff_box.mirror),
            "box_face_nodes": face_nodes, "box_distance_to_board_edge_mm": [
                float(nf2ff_box.stop[0] - sx / 2), float(nf2ff_box.stop[1] - sy / 2), float(-nf2ff_box.start[2])],
            "box_distance_in_lambda0": float((nf2ff_box.stop[0] - sx / 2) * 1e-3 / (C0 / F0_HZ)),
            "box_distance_to_board_edge_in_lambda_at_5p5GHz_xy_z": [
                float(d_ * 1e-3 / (C0 / 5.5e9)) for d_ in (nf2ff_box.stop[0] - sx / 2, nf2ff_box.stop[1] - sy / 2, -nf2ff_box.start[2])],
            "box_distance_to_board_edge_in_lambda_at_5p46GHz_note": "lambda at 5.5 GHz = 54.5 mm; the box is in the near field of the board below ~5.5 GHz",
            "theta_deg": NF2FF_THETA_DEG, "phi_deg": NF2FF_PHI_DEG, "radius_m": NF2FF_RADIUS_M,
            "phase_center_m": [c_xy[0] * 1e-3, c_xy[1] * 1e-3, 0.0],
            "cuts": "phi=0/180 (xz plane) and phi=90/270 (yz plane), theta 0..180 every 5 deg",
            "dmax_caveat": "Dmax from openEMS is the maximum over the sampled directions only; D(theta,phi) here uses Prad",
            "radiated_group_delay": ("ENABLED_DIAGNOSTIC (11 points): " + GROUP_DELAY_MODEL) if n_freq == 11 else
                                    "NOT_COMPUTED (3 points is not enough; use --nf2ff-points 11)",
            "cpu_note": "CalcNF2FF uses numThreads=0 (all hardware threads) but the process runs under taskset <= 2 CPUs",
            "assumptions": ["PML_8 thin absorber 4 mm (0.1 lambda0) next to the box (box 1 cell inside it, default derived by "
                            "openEMS); box-to-board distance 17.5 mm = 0.47 lambda0 at f0",
                            "near-field box includes the finite 26x26 mm ground and substrate edge fields; "
                            "no substrate/ground crosses the box faces"]}
    out.mkdir(parents=True, exist_ok=True)
    fdtd.Write2XML(str(out / XML_NAME))
    if not (out / XML_NAME).is_file():
        raise RuntimeError("Native XML export failed")
    with (out / "native_mesh.csv").open("w", newline="") as stream:
        writer = csv.writer(stream, lineterminator="\n")
        writer.writerow(["axis", "coordinate_mm"])
        for axis, values in axes.items():
            writer.writerows((axis, float(value)) for value in values)

    # --- budget ---
    kib_per_nodal = REF["rss_kib"] / REF["nodal_cells"]
    ram_measured = nodal * kib_per_nodal * 1024 + nf2ff_bytes
    ref_cfl = 1 / (C0 * math.sqrt(sum((s * 1e-3) ** -2 for s in REF["mesh_min_step_mm"])))
    dt_ratio = REF["actual_dt_s"] / ref_cfl
    est_dt = cfl * dt_ratio
    est_steps = min(NR_TS, int(round(REF["steps"] * REF["actual_dt_s"] / est_dt)))
    est_time = (nodal + nf2ff_equiv) * est_steps / REF["cells_per_s"]
    max_time = (nodal + nf2ff_equiv) * NR_TS / REF["cells_per_s"]
    abort = []
    if ram_measured * RAM_MARGIN > ABORT_RAM_BYTES:
        abort.append("estimated RAM (measured basis x2) > 8 GiB")
    if est_time > ABORT_TIME_LIMIT_S:
        abort.append(f"estimated time > {ABORT_TIME_LIMIT_S:.0f} s")
    budget = {
        "maximum_CPUs_threads": 2,
        "nodal_cells": nodal,
        "estimated_RAM_bytes_measured_basis": int(ram_measured),
        "estimated_RAM_bytes_measured_basis_x2_margin": int(ram_measured * RAM_MARGIN),
        "RAM_basis": f"{REF['id']} RSS {REF['rss_kib']} KiB / {REF['nodal_cells']} nodal cells = {kib_per_nodal:.6f} KiB/cell, x{RAM_MARGIN} margin",
        "estimated_RAM_bytes_conservative_reference_only": nodal * CONSERVATIVE_BYTES_PER_CELL,
        "conservative_basis": "2048 B/cell, unmeasured; reference only, not used in the abort rule",
        "yee_min_cell_reference_step_s": cfl,
        "estimated_actual_timestep_s": est_dt,
        "estimated_timesteps": est_steps,
        "estimated_engine_seconds": est_time,
        "worst_case_engine_seconds_30000_steps": max_time,
        "time_basis": (f"nodal cells * steps / {REF['cells_per_s'] / 1e6:.0f} Mcell/s (measured in {REF['id']}); "
                       f"steps scale with 1/timestep from {REF['id']} ({REF['steps']} steps, record "
                       f"{REF['steps'] * REF['actual_dt_s']:.3e} s); assumes the same physical record (resonator Q may "
                       "lengthen it); capped by NrTS"),
        "maximum_timesteps": NR_TS,
        "external_wall_limit_required_s": int(math.ceil(max(900.0, 1.5 * est_time))),
        "abort_rule": f"do not launch if RAM (measured basis x2) > 8 GiB or estimated time > {ABORT_TIME_LIMIT_S:.0f} s",
        "time_limit_s": ABORT_TIME_LIMIT_S,
        "time_limit_basis": ("owner decision 2026-11-05: up to 4000 s for convergence runs"
                             if ABORT_TIME_LIMIT_S != ABORT_TIME_S else "default 1800 s"),
        "launch_allowed_by_budget": not abort,
        "abort_reasons": abort,
    }
    if nf2ff_box is not None:
        budget["nf2ff_overhead"] = {
            "added_cell_equivalents_per_step": nf2ff_equiv, "added_dump_RAM_bytes": nf2ff_bytes,
            "basis": f"UNMEASURED assumption: each DFT accumulation (1 field component, 1 frequency, 1 face node) costs "
                     f"{NF2FF_DFT_COST_CELLS:.3f} of a full Yee cell update; face nodes x 6 components x {n_freq} frequencies; "
                     "dump RAM = complex<float> x face nodes x 6 x n_freq (the x2 margin applies); NF2FF post-processing "
                     "(CalcNF2FF, 4 phi x 37 theta x n_freq) is separate and not part of the engine time",
            "time_without_nf2ff_s": nodal * est_steps / REF["cells_per_s"]}
    metadata = {
        "id": data["id"], "base_design": data.get("base_design"), "status": "PREPARED_NOT_RUN",
        "mesh_profile": MESH_PROFILE, "mesh_profile_rules": MESH_PROFILES[MESH_PROFILE],
        "variant_evidence_at_input": data.get("evidence"), "variant_file": str(variant_path),
        "variant_sha256": sha256(variant_path),
        "openEMS_version": importlib.metadata.version("openEMS"),
        "CSXCAD_version": importlib.metadata.version("CSXCAD"),
        "script_sha256": sha256(__file__), "native_xml_sha256": sha256(out / XML_NAME),
        "options": {"edge_port": opts["edge_port"] if edge else None, "nf2ff": bool(opts["nf2ff"]),
                    "nf2ff_points": opts["nf2ff_points"] if opts["nf2ff"] else None},
        "center_hz": F0_HZ, "channel_band_hz": list(BAND_HZ),
        "materials": {"substrate": sub["name"], "eps_r": er, "tan_delta_at_f0": tand, "h_mm": h,
                      "size_mm": [sx, sy], "dielectric_conductivity_S_m": kappa,
                      "dielectric_loss_model": "constant conductivity; tan_delta(f)=tan_delta(f0)*f0/f",
                      "metal_model": "2D finite conducting sheet", "conductivity_S_m": metal["conductivity_S_m"],
                      "sheet_thickness_m": patch.GetThickness(), "sheet_API_roundtrip_verified": True,
                      "roughness": "not modeled"},
        "geometry": {"patch_primitive": "AddBox" if rect else "AddPolygon", "patch_vertices": len(poly),
                     "slots": len(slots), "slot_model": SLOT_MODEL if slots else None,
                     "microstrip_line_box_mm": ([list(line_rect[0]), list(line_rect[2])] if edge else None),
                     "feed_boxes_mm": ([[[min(q[0] for q in r_), min(q[1] for q in r_)], [max(q[0] for q in r_), max(q[1] for q in r_)]]
                                        for r_ in feed_rects] if qw else None),
                     "polygon_meshing": None if rect else (
                         "round 6 rules (fixed_mesh_lines): 1/3-2/3 metal_edge_res rule on every axis-aligned metal/no-metal edge "
                         "of patch, slots and line (board-edge coincident edges skipped), bounding-box extremes, plain vertex lines "
                         f"(dropped if < {MESH_PLAIN_SEP_MM} mm from a rule/user line), merge of lines < {MESH_MERGE_TOL_MM} mm, merge of facing "
                         f"'outside' lines < {GAP_MERGE_FACTOR} * res, optional mesh_hint_lines_mm, bounded relaxation of fixed lines "
                         f"(<= {RELAX_MAX_SHIFT_MM} mm shift, target ratio {RELAX_TARGET} among fixed cells), then SmoothMeshLines with the ratio parameter lowered until the result is <= 1.4 (SMOOTH_RATIO_SEARCH); "
                         f"target {SMOOTH_RATIO}, hard limit {POLY_GRADING_LIMIT} (recorded in mesh_ratio_above_1p4_by_axis); staircase on oblique edges"),
                     "polygon_mesh_report": fixed_report, "slot_mesh_check": slot_check,
                     "smoothing_ratio_parameter_used": ({a: v[0] for a, v in smoothing_param.items()} or None),
                     "smoothing_infill_lines_mm": ({a: v[2] for a, v in smoothing_param.items()} if (smoothing_param and (not edge or parasitics)) else None)},
        "port": ({"reference_ohm": z0, "start_mm": [fx, fy, 0], "stop_mm": [fx, fy, h],
                  "type": "ideal vertical lumped line; no pin/coax connector/aperture/deembedding",
                  "priority": PORT_PRIORITY, "grid_lines_at_port": port_cells,
                  "reference_plane": "the lumped port itself (U and I integrated over z 0..h at the feed point); no plane shift, "
                                     "no beta, no de-embedding: the probe inductance belongs to the antenna"}
                 if not edge else port_meta),
        "mesh": mesh_info, "mesh_ratio_above_1p4_by_axis": resmooth, "total_cells": cells, "box_half_mm": box,
        "mesh_grading_limit_used": (RECT_GRADING_FALLBACK if resmooth else SMOOTH_RATIO),
        "budget_before_solve": budget,
        "boundaries": "PML_8 all six; coordinates mm",
        "excitation": excitation_metadata(),
        "energy_end_criterion": END_CRITERIA, "mesh_convergence": "NOT_ESTABLISHED: single mesh",
        "far_field": nf2ff_meta if nf2ff_meta else "not recorded; gain/efficiency/radiated group delay unavailable",
    }
    if not rect:
        metadata["mesh_grading_limit_used"] = POLY_GRADING_LIMIT if resmooth else SMOOTH_RATIO
    if driven_meta is not None:   # only with the optional key driven_z_mm
        metadata["geometry"]["driven_layer"] = driven_meta
        metadata["geometry"]["substrate_z_lines_mm"] = [float(v) for v in sub_z]
    if parasitics:   # keys only exist with the optional variant key; variants without it keep a byte-identical prepared.json layout
        metadata["geometry"]["parasitic_patches"] = par_meta
        metadata["geometry"]["parasitic_model"] = PARASITIC_MODEL
        metadata["geometry"]["parasitic_z_mesh"] = (
            "substrate z lines: hard line at every z_mm (substrate_z_lines); the substrate cells are re-shared between the segments "
            "ground-parasitic-patch (uniform inside each) unless every z_mm coincides with an existing linspace line; x/y lines of the "
            "parasitic edges follow the polygon rules of fixed_mesh_lines (layers), evaluated against the parasitic's own metal")
        metadata["geometry"]["substrate_z_lines_mm"] = [float(v) for v in sub_z]
    if parasitics or driven_meta is not None:
        metadata["warnings"] = driven_warnings + par_warnings
        metadata["parasitic_summary"] = parasitic_summary(metadata)
    return fdtd, port, metadata, nf2ff_box


# ---- results ------------------------------------------------------------------------------------
class PortResponse:
    """Frequency-domain port quantities at the reference plane used for S11/Zin (see EDGE_PORT_MODEL)."""

    def __init__(self, **kw):
        self.planes = None
        self.__dict__.update(kw)


MSL_CURRENT_AVERAGE_CORRECTION = True   # --no-current-correction turns it off (plain mean(I_A, I_B))
_MSL_PROBE_CACHE = {}


def msl_probes(src, metadata):
    key = str(Path(src).resolve())
    if key not in _MSL_PROBE_CACHE:
        _MSL_PROBE_CACHE[key] = pp.MslProbes(src, metadata["port"].get("port_probe_lines_y_mm"))
    return _MSL_PROBE_CACHE[key]


def port_response(port, src, freq, metadata):
    """S11/Zin/incident/total quantities for the probe-fed, lumped-edge or MSL-edge port.

    Probe-fed and lumped-edge ports: Port.CalcPort(freq), reference = port resistance (exactly the pre-round-6 behaviour).
    MSL edge port (round 7): em/port_postprocess.py from the probe files in src (no openEMS object needed): primary S11 at the
    measurement plane with fixed 50 ohm, launch-plane S11 over an ideal 50 ohm line with the voltage-estimated beta. p_inc/p_acc
    are those of the measurement plane (50 ohm).
    """
    import numpy as np
    z0 = metadata["port"]["reference_ohm"]
    if metadata["port"].get("model") != "msl":
        port.CalcPort(str(src), freq)
        return PortResponse(s11=port.uf_ref / port.uf_inc, zin=port.uf_tot / port.if_tot, uf_inc=port.uf_inc,
                            uf_ref=port.uf_ref, uf_tot=port.uf_tot, if_tot=port.if_tot,
                            p_inc=np.real(port.P_inc), p_acc=np.real(port.P_acc), z_line=None, s11_zline=None)
    freq = np.asarray(freq, dtype=float)
    probes = msl_probes(src, metadata)
    w_mm, h_mm, er = metadata["port"]["line_width_mm"], metadata["materials"]["h_mm"], metadata["materials"]["eps_r"]
    length_m = (probes.y_mm[1] - metadata["port"]["launch_plane_y_mm"]) * 1e-3
    spectra = probes.spectra(freq)
    pl = pp.msl_planes(spectra, probes.delta_m, length_m, freq, pp.getsinger_eeff(freq, w_mm, h_mm, er), er, z0,
                       current_correction=MSL_CURRENT_AVERAGE_CORRECTION)
    return PortResponse(s11=pl.s11_launch, zin=pl.zin_launch, uf_inc=pl.inc_launch, uf_ref=pl.ref_launch,
                        uf_tot=pl.u_launch, if_tot=pl.i_launch, p_inc=pl.p_inc, p_acc=pl.p_acc, z_line=None, s11_zline=None,
                        s11_meas=pl.s11_meas, planes=pl, spectra=spectra, probes=probes, length_m=length_m)


def _db(x):
    import numpy as np
    return 10 * np.log10(np.maximum(x, 1e-30))


def far_field_tables(res, resp, plan):
    """Pure post-processing of nf2ff results + port response (unit-testable without a solver run).

    res: object with theta (rad), phi (rad), freq, r, Prad, Dmax, E_theta[n], E_phi[n], P_rad[n] ((theta,phi) arrays).
    resp: PortResponse at the same frequencies. Returns (pattern_rows, summary_rows).
    """
    import numpy as np
    theta, phi = np.rad2deg(np.asarray(res.theta)), np.rad2deg(np.asarray(res.phi))
    r = float(np.asarray(res.r).ravel()[0])
    rows, summary = [], []
    i0 = int(np.argmin(np.abs(theta)))
    j0 = int(np.argmin(np.abs(phi)))
    for n, f in enumerate(res.freq):
        prad = float(np.asarray(res.Prad)[n])
        u_int = np.asarray(res.P_rad[n]) * r * r            # W/sr
        d = 4 * np.pi * u_int / prad
        g_abs = 4 * np.pi * u_int / float(resp.p_acc[n])
        g_real = 4 * np.pi * u_int / float(resp.p_inc[n])
        et, ep = np.asarray(res.E_theta[n]), np.asarray(res.E_phi[n])
        for j, ph in enumerate(phi):
            for i, th in enumerate(theta):
                rows.append([float(f), ph, th, et[i, j].real, et[i, j].imag, ep[i, j].real, ep[i, j].imag,
                             d[i, j], g_abs[i, j], g_real[i, j], _db(d[i, j]), _db(g_abs[i, j]), _db(g_real[i, j])])
        imax = np.unravel_index(int(np.argmax(d)), d.shape)
        s11 = resp.s11[n]
        summary.append({
            "frequency_hz": float(f), "Prad_W": prad, "P_inc_W": float(resp.p_inc[n]), "P_acc_W": float(resp.p_acc[n]),
            "radiation_efficiency_Prad_over_Pacc": prad / float(resp.p_acc[n]),
            "total_efficiency_Prad_over_Pinc": prad / float(resp.p_inc[n]),
            **({"s11_db_launch_plane_50ohm": float(20 * np.log10(abs(s11))),
                "s11_db_measurement_plane_50ohm": float(20 * np.log10(abs(resp.s11_meas[n])))} if hasattr(resp, "s11_meas") else
               {"s11_db_lumped_port_50ohm": float(20 * np.log10(abs(s11)))}),
            "mismatch_loss_db": float(-10 * np.log10(max(1 - abs(s11) ** 2, 1e-30))),
            "D_broadside_dBi": float(_db(d[i0, j0])), "gain_broadside_dBi": float(_db(g_abs[i0, j0])),
            "realized_gain_broadside_dBi": float(_db(g_real[i0, j0])),
            "Dmax_sampled_dBi": float(_db(d[imax])), "Dmax_sampled_theta_deg": float(theta[imax[0]]),
            "Dmax_sampled_phi_deg": float(phi[imax[1]]), "Dmax_openEMS_dBi": float(_db(float(np.asarray(res.Dmax)[n]))),
            "power_balance_flag": ("Prad > 1.05 Pacc: inconsistent power balance (check box/PML/convergence)"
                                   if prad > 1.05 * float(resp.p_acc[n]) else "ok")})
    return rows, summary


def phase_unwrap_check(h, step_limit=PHASE_STEP_LIMIT_RAD, floor_db=H_FLOOR_REL_DB):
    """Reliability of the phase unwrap of H over the frequency points (see GROUP_DELAY_CRITERION).
    Returns dict(phase_step_rad[n] (step to the previous point, 0 for the first), reliable[n] (bool), max_abs_step_rad, min_h_rel_db,
    status 'RELIABLE'/'UNRELIABLE', reasons)."""
    import numpy as np
    h = np.asarray(h)
    step = np.zeros(len(h))
    step[1:] = np.angle(h[1:] * np.conj(h[:-1]))            # wrapped to (-pi, pi]
    rel_db = 20 * np.log10(np.maximum(np.abs(h) / np.max(np.abs(h)), 1e-30))
    big = np.abs(step) >= step_limit
    low = rel_db < floor_db
    bad_step = np.zeros(len(h), dtype=bool)
    bad_step[1:] |= big[1:]
    bad_step[:-1] |= big[1:]                                  # a point next to a big step is unreliable
    reliable = ~(bad_step | low)
    reasons = []
    if big.any():
        reasons.append(f"wrapped phase step >= pi/2 between {int(big.sum())} adjacent point pair(s), max {np.abs(step).max():.3f} rad")
    if low.any():
        reasons.append(f"|H| below {floor_db:.0f} dB re its maximum at {int(low.sum())} point(s) (min {rel_db.min():.1f} dB)")
    return {"phase_step_rad": step, "reliable": reliable, "max_abs_step_rad": float(np.abs(step).max()),
            "min_h_rel_db": float(rel_db.min()), "status": "RELIABLE" if not reasons else "UNRELIABLE", "reasons": reasons}


def radiated_group_delay(res, resp, plan):
    """Diagnostic radiated group delay at broadside (see GROUP_DELAY_MODEL and GROUP_DELAY_CRITERION). Needs >= 9 frequencies.
    Returns (table, summary) or (None, reason). The first 7 table columns are unchanged since round 6; round 12 appends
    phase-step and reliability columns."""
    import numpy as np
    freqs = np.asarray(plan["frequencies_hz"], dtype=float)
    if len(freqs) < 9:
        return None, "NOT_COMPUTED: fewer than 9 frequencies"
    theta, phi = np.rad2deg(np.asarray(res.theta)), np.rad2deg(np.asarray(res.phi))
    i0, j0 = int(np.argmin(np.abs(theta))), int(np.argmin(np.abs(phi)))
    r = float(np.asarray(res.r).ravel()[0])
    k = 2 * np.pi * freqs / C0
    omega = 2 * np.pi * freqs
    cols, extra_cols, out = [freqs], [], {}
    for label, comp in (("x_Etheta_phi0", res.E_theta), ("y_Ephi_phi0", res.E_phi)):
        e = np.array([np.asarray(comp[n])[i0, j0] for n in range(len(freqs))])
        h = e * np.exp(1j * k * r) / np.asarray(resp.uf_inc)
        ph = np.unwrap(np.angle(h))
        tau = -np.gradient(ph, omega)
        chk = phase_unwrap_check(h)
        cols += [np.abs(h), ph, tau]
        extra_cols += [chk["phase_step_rad"], chk["reliable"].astype(float)]
        out[label] = {"mean_abs_H": float(np.mean(np.abs(h))), "tau_mean_ns": float(np.mean(tau) * 1e9),
                      "tau_ripple_pp_ps": float((tau.max() - tau.min()) * 1e12),
                      "tau_ripple_pp_interior_ps": float((tau[1:-1].max() - tau[1:-1].min()) * 1e12),
                      "tau_ripple_status": "DIAGNOSTIC" if chk["status"] == "RELIABLE" else "UNRELIABLE_DO_NOT_USE",
                      "tau_min_ns": float(tau.min() * 1e9), "tau_max_ns": float(tau.max() * 1e9),
                      "phase_unwrap": chk["status"], "max_abs_phase_step_rad": chk["max_abs_step_rad"],
                      "min_abs_H_rel_to_max_db": chk["min_h_rel_db"], "unreliable_reasons": chk["reasons"],
                      "reliable_points": int(chk["reliable"].sum()), "points": int(len(freqs))}
    dominant = max(out, key=lambda k_: out[k_]["mean_abs_H"])
    out["dominant_component"] = dominant
    out["dominant_phase_unwrap"] = out[dominant]["phase_unwrap"]
    out["model"] = GROUP_DELAY_MODEL
    out["reliability_criterion"] = GROUP_DELAY_CRITERION
    out["status"] = "DIAGNOSTIC_NOT_VALIDATED" if out[dominant]["phase_unwrap"] == "RELIABLE" else "DIAGNOSTIC_UNRELIABLE_PHASE_UNWRAP"
    return np.column_stack(cols + extra_cols), out


GROUP_DELAY_CSV_HEADER = ("frequency_hz,abs_H_x,phase_H_x_rad,tau_g_x_s,abs_H_y,phase_H_y_rad,tau_g_y_s,"
                          "dphi_step_x_rad,reliable_x_step_lt_pi_over_2_and_absH_gt_m20dB,"
                          "dphi_step_y_rad,reliable_y_step_lt_pi_over_2_and_absH_gt_m20dB")


def nf2ff_tables_write(out, res, resp, plan, files_extra=(), extra=None):
    """Write nf2ff_pattern_complex.csv / nf2ff_group_delay_broadside.csv / nf2ff_summary.json (res: object as in far_field_tables)."""
    import numpy as np
    rows, summary = far_field_tables(res, resp, plan)
    np.savetxt(out / "nf2ff_pattern_complex.csv", np.array(rows), delimiter=",", comments="", fmt="%.10e",
               header="frequency_hz,phi_deg,theta_deg,E_theta_real_V_per_m,E_theta_imag_V_per_m,E_phi_real_V_per_m,"
                      "E_phi_imag_V_per_m,directivity,gain_lin,realized_gain_lin,directivity_dBi,gain_dBi,realized_gain_dBi")
    gd_table, gd = radiated_group_delay(res, resp, plan)
    if gd_table is not None:
        np.savetxt(out / "nf2ff_group_delay_broadside.csv", gd_table, delimiter=",", comments="", fmt="%.10e",
                   header=GROUP_DELAY_CSV_HEADER)
    result = {"status": "EM_SIMULATED_FAR_FIELD", "frequencies_hz": plan["frequencies_hz"], "summary": summary,
              "radiated_group_delay": gd, "model": FAR_FIELD_MODEL, "radius_m": plan["radius_m"],
              "phase_center_m": plan["phase_center_m"], "E_field_convention": "E at r = 1 m including exp(-jkr)/r; "
              "e^{+j omega t}-style DFT as in openEMS (single-sided); theta_hat=x_hat at theta=0,phi=0",
              "power_reference": (
                  "P_inc, P_acc, efficiencies, gain, realised gain: MSL measurement plane, fixed 50 ohm "
                  "(em/port_postprocess.py); group-delay a_inc: launch plane (ideal-line shift)"
                  if getattr(resp, "planes", None) is not None else
                  "P_inc = |a|^2/(2 R), P_acc = 0.5 Re(U I*) of the 50 ohm vertical lumped port (openEMS Port.CalcPort, reference = "
                  "port resistance 50 ohm); S11, efficiencies, gain, realised gain and the group-delay a_inc (incident wave "
                  "voltage 0.5 (U + R I)) all refer to the lumped port itself: no plane shift, no beta, no de-embedding"),
              "files": ["nf2ff_pattern_complex.csv", "nf2ff_summary.json", *files_extra] + (
                  ["nf2ff_group_delay_broadside.csv"] if gd_table is not None else [])}
    result.update(extra or {})
    (out / "nf2ff_summary.json").write_text(json.dumps(result, indent=2) + "\n")
    return result


def nf2ff_outputs(out, nf2ff_box, port, metadata):
    plan = metadata["far_field"]
    import numpy as np
    freqs = np.asarray(plan["frequencies_hz"], dtype=float)
    res = nf2ff_box.CalcNF2FF(str(out), freqs, plan["theta_deg"], plan["phi_deg"], radius=plan["radius_m"],
                              center=plan["phase_center_m"], read_cached=False, verbose=0)
    resp = port_response(port, out, freqs, metadata)
    return nf2ff_tables_write(out, res, resp, plan, files_extra=("nf2ff.h5",))


def nf2ff_reprocess(src, dst, metadata):
    """FDTD-free NF2FF re-evaluation of the power-referenced quantities from the stored pattern tables of a finished run.

    D(theta, phi), E_theta, E_phi and Prad are taken from src/nf2ff_pattern_complex.csv and src/nf2ff_summary.json (they depend on
    the near-field dumps only, not on the port); gain, realised gain, efficiencies and the radiated group delay are recomputed with
    P_inc / P_acc / a_inc of the NEW port post-processing. P_rad = D Prad / (4 pi r^2) reconstructs res.P_rad."""
    import numpy as np
    old = json.loads((src / "nf2ff_summary.json").read_text())
    plan = metadata["far_field"]
    freqs = np.asarray(old["frequencies_hz"], dtype=float)
    tab = np.genfromtxt(src / "nf2ff_pattern_complex.csv", delimiter=",", names=True)
    theta = np.array(sorted(set(np.round(tab["theta_deg"], 9))))
    phi = np.array(sorted(set(np.round(tab["phi_deg"], 9))))
    r = float(old["radius_m"])
    et, ep, prl = [], [], []
    for n, f in enumerate(freqs):
        sel = tab[np.isclose(tab["frequency_hz"], f, rtol=0, atol=1.0)]
        if len(sel) != len(theta) * len(phi):
            raise RuntimeError("nf2ff_pattern_complex.csv does not hold a full (phi, theta) table per frequency")
        shape = (len(phi), len(theta))           # rows are ordered phi (outer), theta (inner)
        et.append((sel["E_theta_real_V_per_m"] + 1j * sel["E_theta_imag_V_per_m"]).reshape(shape).T)
        ep.append((sel["E_phi_real_V_per_m"] + 1j * sel["E_phi_imag_V_per_m"]).reshape(shape).T)
        prad = old["summary"][n]["Prad_W"]
        prl.append(sel["directivity"].reshape(shape).T * prad / (4 * np.pi * r * r))
    res = PortResponse(theta=np.deg2rad(theta), phi=np.deg2rad(phi), freq=freqs, r=np.array([r]),
                       Prad=np.array([s["Prad_W"] for s in old["summary"]]),
                       Dmax=np.array([10 ** (s["Dmax_openEMS_dBi"] / 10) for s in old["summary"]]),
                       E_theta=et, E_phi=ep, P_rad=prl)
    resp = port_response(None, src, freqs, metadata)
    return nf2ff_tables_write(dst, res, resp, {**plan, "frequencies_hz": [float(f) for f in freqs]}, extra={
        "reprocessed_from": str(src),
        "reprocess_note": "D, E_theta, E_phi, Prad from the stored pattern tables (precision %.10e); not from the raw h5 dumps. "
                          "Directivity caveat of the source run remains (4 phi cuts do not integrate to Prad exactly)."})


# ---- port outputs (shared by solve and reprocess) -------------------------------------------------
def _port_table(freq, s11, zin, inc, ref, u, i, extra_cols=(), extra_names=()):
    import numpy as np
    cols = [freq, s11.real, s11.imag, zin.real, zin.imag, inc.real, inc.imag, ref.real, ref.imag, u.real, u.imag, i.real, i.imag]
    cols += list(extra_cols)
    header = ("frequency_hz,s11_real,s11_imag,zin_real_ohm,zin_imag_ohm,u_inc_real,u_inc_imag,u_ref_real,u_ref_imag,u_tot_real,"
              "u_tot_imag,i_tot_real,i_tot_imag" + "".join("," + n for n in extra_names))
    return np.column_stack(cols), header


def _fallback_counts(planes):
    import numpy as np
    return {pp.FALLBACK_REASONS[k]: int(np.sum(planes.beta_reason == k)) for k in pp.FALLBACK_REASONS if np.any(planes.beta_reason == k)}


def port_outputs(dst, src, port, metadata, legacy_diagnostic=False):
    """Evaluate the channel grid and the wideband grid, write the S11 CSVs into dst, apply the validity gate.

    Returns (numeric dict, channel PortResponse). Channel metrics are written as channel_* only if port_validity is OK; otherwise
    they are written with the prefix invalid_ and the wideband block as invalid_wideband."""
    import numpy as np
    z0 = metadata["port"]["reference_ohm"]
    is_msl = metadata["port"].get("model") == "msl"
    f_lo, f_hi, f_n = CHANNEL_GRID_HZ
    freq = np.unique(np.r_[np.linspace(f_lo, f_hi, f_n), BAND_HZ[0], BAND_HZ[1]])
    resp = port_response(port, src, freq, metadata)
    pl = resp.planes
    s11 = resp.s11
    if is_msl:
        extra, names = (pl.eeff, pl.beta, pl.beta_fallback.astype(float)), ("eeff_used", "beta_rad_per_m", "beta_fallback")
        data, header = _port_table(freq, pl.s11_launch, pl.zin_launch, pl.inc_launch, pl.ref_launch, pl.u_launch, pl.i_launch, extra, names)
        data_m, _ = _port_table(freq, pl.s11_meas, pl.zin_meas, pl.inc_meas, pl.ref_meas, pl.u_meas, pl.i_meas, extra, names)
    else:
        data, header = _port_table(freq, s11, resp.zin, resp.uf_inc, resp.uf_ref, resp.uf_tot, resp.if_tot)
        if resp.z_line is not None:
            data = np.column_stack([data, resp.z_line.real, resp.z_line.imag, resp.s11_zline.real, resp.s11_zline.imag])
            header += ",z_line_real_ohm,z_line_imag_ohm,s11_vs_zline_real,s11_vs_zline_imag"
    if not np.all(np.isfinite(data)):
        raise RuntimeError("Non-finite port outputs (channel grid)")
    np.savetxt(dst / "s11_complex.csv", data, delimiter=",", comments="", fmt="%.16e", header=header)
    if is_msl:
        np.savetxt(dst / "s11_measplane.csv", data_m, delimiter=",", comments="", fmt="%.16e", header=header)
    s_prim = pl.s11_meas if is_msl else s11
    band = (freq >= BAND_HZ[0]) & (freq <= BAND_HZ[1])
    db = 20 * np.log10(np.abs(s_prim))

    # wideband: valid rows = |u_inc| within 20 dB of the peak (|a| is the same at both planes: lossless ideal-line shift)
    fc = metadata.get("excitation", {}).get("corner_offset_hz", 1e9)
    fw = wideband_grid(fc)
    rw = port_response(port, src, fw, metadata)
    pw = rw.planes
    inc_db = 20 * np.log10(np.abs(pw.inc_meas if is_msl else rw.uf_inc) / np.abs(pw.inc_meas if is_msl else rw.uf_inc).max())
    valid = inc_db > -20.0
    if is_msl:
        ex_w = (pw.eeff,)
        for name, s_, z_ in (("s11_wideband.csv", pw.s11_launch, pw.zin_launch), ("s11_wideband_measplane.csv", pw.s11_meas, pw.zin_meas)):
            wide = np.column_stack([fw, s_.real, s_.imag, z_.real, z_.imag, inc_db, *ex_w])[valid]
            if not np.all(np.isfinite(wide)):
                raise RuntimeError("Non-finite port outputs (wideband grid)")
            np.savetxt(dst / name, wide, delimiter=",", comments="", fmt="%.12e",
                       header="frequency_hz,s11_real,s11_imag,zin_real_ohm,zin_imag_ohm,u_inc_rel_db,eeff_used")
        sw, zw = pw.s11_meas[valid], pw.zin_meas[valid]
    else:
        wide = np.column_stack([fw, rw.s11.real, rw.s11.imag, rw.zin.real, rw.zin.imag, inc_db])[valid]
        if not np.all(np.isfinite(wide)):
            raise RuntimeError("Non-finite port outputs (wideband grid)")
        np.savetxt(dst / "s11_wideband.csv", wide, delimiter=",", comments="", fmt="%.12e",
                   header="frequency_hz,s11_real,s11_imag,zin_real_ohm,zin_imag_ohm,u_inc_rel_db")
        sw, zw = rw.s11[valid], rw.zin[valid]
    fv = fw[valid]

    # validity gate on the evaluated frequencies: channel grid + wideband rows inside the valid excitation range
    planes = {"measurement": np.r_[pl.s11_meas, pw.s11_meas[valid]], "launch": np.r_[pl.s11_launch, pw.s11_launch[valid]]} if is_msl \
        else {"port": np.r_[s11, rw.s11[valid]]}
    p_acc = np.r_[resp.p_acc, rw.p_acc[valid]]
    gate = pp.port_gate(planes, p_acc)
    ok = gate["port_validity"] == "OK"
    k, m = int(np.argmax(zw.real)), int(np.argmin(np.abs(sw)))
    metrics = {"channel_samples": int(band.sum()),
               "channel_worst_s11_db": float(db[band].max()),
               "channel_worst_frequency_hz": float(freq[band][np.argmax(db[band])]),
               "channel_best_s11_db": float(db[band].min()),
               "channel_best_frequency_hz": float(freq[band][np.argmin(db[band])]),
               "channel_meets_minus6db_on_sampled_grid": bool(np.all(db[band] <= -6)),
               "channel_meets_minus10db_on_sampled_grid": bool(np.all(db[band] <= -10))}
    wideband = {"grid_hz": [float(fw[0]), float(fw[-1]), WIDEBAND_STEP_HZ], "samples": int(len(fw)),
                "valid_rule": "u_inc within 20 dB of its peak (as reanalyze_port_dft.py)",
                "valid_range_hz": [float(fv[0]), float(fv[-1])], "valid_samples": int(valid.sum()),
                "re_zin_peak_ohm": float(zw.real[k]), "re_zin_peak_hz": float(fv[k]),
                "im_zin_at_re_peak_ohm": float(zw.imag[k]),
                "min_s11_db": float(20 * np.log10(np.abs(sw[m]))), "min_s11_hz": float(fv[m])}
    if is_msl:
        wideband["plane"] = "measurement plane, fixed 50 ohm"
    numeric = {"id": metadata["id"], "numeric_outputs_finite": True, "port_validity": gate["port_validity"],
               "port_validity_detail": gate, "samples": len(freq), "reference_ohm": z0}
    if ok:
        numeric.update(metrics)
        numeric["wideband"] = wideband
    else:
        numeric.update({"invalid_" + key: v for key, v in metrics.items()})
        numeric["invalid_wideband"] = wideband
        numeric["invalid_note"] = "port_validity = PORT_INVALID: S11, Zin, efficiencies, gain and group delay must not be used"
    numeric["s11_metrics_plane"] = "measurement plane" if is_msl else "port"
    if is_msl:
        eff_ch, eff_w = pl.eeff[band], pw.eeff[valid]
        numeric["port_postprocess"] = {
            "method": pp.POSTPROCESS_MODEL, "reference_ohm_fixed": z0,
            "measurement_plane_y_mm": resp.probes.y_mm[1], "launch_plane_y_mm": metadata["port"]["launch_plane_y_mm"],
            "shift_length_mm": resp.length_m * 1e3, "probe_lines_y_mm": resp.probes.y_mm,
            "probe_spacing_mm": [resp.probes.delta_ab_m * 1e3, resp.probes.delta_bc_m * 1e3],
            "probe_spacing_nonuniformity": resp.probes.delta_nonuniformity,
            "current_average_correction_cos_beta_D_over_2": MSL_CURRENT_AVERAGE_CORRECTION,
            "eeff_used_channel": {"min": float(eff_ch.min()), "median": float(np.median(eff_ch)), "max": float(eff_ch.max())},
            "eeff_used_wideband_valid": {"min": float(eff_w.min()), "median": float(np.median(eff_w)), "max": float(eff_w.max())},
            "eeff_analytic_hammerstad_getsinger_f0": float(pp.getsinger_eeff(F0_HZ, metadata["port"]["line_width_mm"],
                                                                            metadata["materials"]["h_mm"], metadata["materials"]["eps_r"])),
            "beta_fallback_channel": _fallback_counts(pl) if pl.beta_fallback[band].any() else {},
            "beta_fallback_channel_count": int(pl.beta_fallback[band].sum()),
            "beta_fallback_wideband_valid_count": int(pw.beta_fallback[valid].sum()),
            "beta_fallback_reasons": {str(k_): v_ for k_, v_ in pp.FALLBACK_REASONS.items()},
            "imag_part_of_cos_beta_D_max": pl.imag_cos_max,
            "max_abs_s11_measplane_channel": float(np.abs(pl.s11_meas[band]).max()),
            "max_abs_s11_launch_channel": float(np.abs(pl.s11_launch[band]).max()),
            "files": ["s11_complex.csv (launch plane)", "s11_measplane.csv", "s11_wideband.csv (launch plane)",
                      "s11_wideband_measplane.csv"],
            "assumptions": ["line loss between the planes neglected (|S11| identical at both planes by construction)",
                            "a numerical Z_line different from 50 ohm is not calibrated",
                            "I = mean(I_A, I_B) is at the middle probe line only through cos(beta D/2)"]}
        if legacy_diagnostic:
            leg = pp.legacy_openems_zline(resp.spectra, resp.probes.delta_m, resp.length_m, freq)
            ld = np.column_stack([freq, leg["s11"].real, leg["s11"].imag, leg["zin"].real, leg["zin"].imag,
                                  leg["z_line"].real, leg["z_line"].imag, leg["beta"].real, leg["beta"].imag, leg["eeff"]])
            np.savetxt(dst / "s11_openems_zline_DIAGNOSTIC.csv", ld, delimiter=",", comments="", fmt="%.16e",
                       header="frequency_hz,s11_real,s11_imag,zin_real_ohm,zin_imag_ohm,z_line_real_ohm,z_line_imag_ohm,"
                              "beta_real,beta_imag,eeff_from_real_beta")
            numeric["port_postprocess"]["legacy_zline_diagnostic"] = {
                "file": "s11_openems_zline_DIAGNOSTIC.csv", "status": "DIAGNOSTIC_ONLY_DO_NOT_USE",
                "max_abs_s11_channel": float(np.abs(leg["s11"][band]).max()),
                "max_abs_s11_whole_grid": float(np.nanmax(np.abs(leg["s11"])))}
    return numeric, resp


def solve_outputs(out, port, metadata, started, nf2ff_box=None, legacy_diagnostic=False):
    numeric, resp = port_outputs(out, out, port, metadata, legacy_diagnostic)
    if numeric["port_validity"] == "OK" and nf2ff_box is not None:
        far = nf2ff_outputs(out, nf2ff_box, port, metadata)
        far_field = {"status": far["status"], "summary_file": "nf2ff_summary.json", "summary": far["summary"]}
    elif nf2ff_box is not None:
        far_field = {"status": "SKIPPED_PORT_INVALID", "note": "NF2FF dumps exist (nf2ff_E_*/nf2ff_H_* in the run directory) but "
                                                              "efficiency, gain and group delay need a valid port"}
    else:
        far_field = "NOT_RECORDED"
    usage = resource.getrusage(resource.RUSAGE_SELF)
    result = {**numeric,
              "wall_seconds": time.monotonic() - started, "cpu_seconds": usage.ru_utime + usage.ru_stime,
              "peak_rss_kib": usage.ru_maxrss, "cpu_affinity": sorted(os.sched_getaffinity(0)),
              "frequency_evaluation_step_hz": 1e6,
              "frequency_grid_caveat": "DTFT evaluation spacing is not physical resolution; finite-record decay/truncation governs accuracy",
              "coverage_caveat": "sampled frequencies including exact endpoints; no mathematical guarantee between samples",
              "native_xml_sha256": metadata["native_xml_sha256"], "variant_sha256": metadata["variant_sha256"],
              "far_field": far_field}
    if metadata["port"].get("model"):
        result["port_model"] = metadata["port"]["model"]
        result["reference_plane_y_mm"] = metadata["port"]["reference_plane_y_mm"]
        result["reference_plane"] = metadata["port"]["reference_plane"]
    (out / "run_numeric.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2), flush=True)


REPROCESS_KEEP = ("energy_end_criterion_met", "maximum_timesteps_warning", "solver_nodal_positions", "actual_timestep_s",
                  "actual_record_time_s", "engine_wall_seconds", "engine_cells_per_second", "inverse_record_time_hz",
                  "mesh_convergence", "actual_timesteps", "final_energy_decay_db")


def reprocess(src, dst, nf2ff=True, legacy_diagnostic=False):
    """FDTD-free re-analysis of an existing MSL-port run: reads the probe files (and the stored NF2FF tables) of src and writes
    new CSV/JSON into the NEW directory dst. Never overwrites; needs neither openEMS nor CSXCAD."""
    src, dst = Path(src).resolve(), Path(dst).resolve()
    if dst == src or src in dst.parents:
        raise RuntimeError("--out-reprocess must be a new directory outside the source run")
    metadata = json.loads((src / "prepared.json").read_text())
    if metadata["port"].get("model") != "msl":
        raise RuntimeError("reprocess supports MSL edge-port runs only (probe/lumped ports need the openEMS Port object)")
    dst.mkdir(parents=True, exist_ok=False)
    numeric, resp = port_outputs(dst, src, None, metadata, legacy_diagnostic)
    far = None
    if nf2ff and numeric["port_validity"] == "OK" and (src / "nf2ff_summary.json").exists():
        far = nf2ff_reprocess(src, dst, metadata)
    old_result = {}
    for name in ("run_numeric.json", "result.json"):
        if (src / name).exists():
            old_result.update(json.loads((src / name).read_text()))
    result = {**numeric,
              "reprocess_of": str(src), "reprocess_mode": "probe files re-analysed without FDTD (patch_openems.py reprocess)",
              "source_probe_files_sha256": resp.probes.sha256, "native_xml_sha256": metadata["native_xml_sha256"],
              "variant_sha256": metadata["variant_sha256"], "port_model": "msl",
              "reference_plane_y_mm": metadata["port"]["reference_plane_y_mm"],
              "reference_plane": ("s11_measplane.csv / metrics: measurement plane, fixed 50 ohm; s11_complex.csv: board edge "
                                  "y = -size_y/2 over an ideal lossless 50 ohm line (voltage-estimated beta)"),
              "original_run": {k: old_result[k] for k in REPROCESS_KEEP + ("wall_seconds", "cpu_seconds", "peak_rss_kib", "cpu_affinity")
                               if k in old_result},
              "original_run_invalidated_outputs": "s11_complex.csv, s11_wideband.csv, channel_* / wideband metrics, z_line, nf2ff "
                                                  "efficiencies, gain, realised gain, group delay of the source run (see its VALIDITY.json)",
              "far_field": ("NOT_REPROCESSED" if far is None else {"status": far["status"], "summary_file": "nf2ff_summary.json",
                                                                  "summary": far["summary"]}),
              "evidence": "EM_SIMULATED" if old_result.get("evidence", "EM_SIMULATED") == "EM_SIMULATED" else old_result["evidence"]}
    if numeric["port_validity"] != "OK":
        result["far_field"] = {"status": "SKIPPED_PORT_INVALID"}
    (dst / "run_numeric.json").write_text(json.dumps(result, indent=2) + "\n")
    (dst / "result.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2), flush=True)
    return result


def summarize(out):
    log = (out / "solver.log").read_text()
    result = json.loads((out / "run_numeric.json").read_text()) if (out / "run_numeric.json").exists() else {}
    decay = re.findall(r"end-criteria of -([\d.]+)dB reached after (\d+) timesteps \(-([\d.]+)dB\)", log)
    result["energy_end_criterion_met"] = bool(decay)
    result["maximum_timesteps_warning"] = "Max. number of timesteps was reached" in log
    if (out / "openEMS_stats.txt").exists():
        values = [float(line.split()[0]) for line in (out / "openEMS_stats.txt").read_text().splitlines()
                  if line.strip() and not line.startswith("%")]
        if len(values) >= 6:
            result["solver_nodal_positions"] = int(values[0])
            result["actual_timestep_s"] = values[1]
            result["actual_record_time_s"] = values[3]
            result["engine_wall_seconds"] = values[4]
            result["engine_cells_per_second"] = values[5]
            result["inverse_record_time_hz"] = 1 / values[3]
    result["mesh_convergence"] = "NOT_ESTABLISHED"
    result["evidence"] = "EM_SIMULATED" if result.get("numeric_outputs_finite") and decay else "EM_RUN_INCOMPLETE"
    if result.get("port_validity") == "PORT_INVALID":
        result["evidence_note"] = "EM_SIMULATED but port_validity = PORT_INVALID: S11, efficiencies, gain and group delay are unusable"
    if decay:
        result["actual_timesteps"] = int(decay[-1][1])
        result["final_energy_decay_db"] = -float(decay[-1][2])
    (out / "result.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


def main():
    global NR_TS
    cli = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    cli.add_argument("mode", choices=["prepare", "solve", "summarize", "reprocess"])
    cli.add_argument("--variant", type=Path, help="variant JSON (prepare/solve)")
    cli.add_argument("--out", type=Path, required=True)
    cli.add_argument("--mesh", choices=sorted(MESH_PROFILES), default="base",
                     help="mesh profile: base (P01_OPENEMS_001 rules) or fine (P01_OPENEMS_002 rules)")
    cli.add_argument("--edge-port", choices=EDGE_PORTS, default="msl",
                     help="microstrip_inset_edge feeds only: msl (MSL port + shift to the board edge, default) or lumped")
    cli.add_argument("--nf2ff", action="store_true",
                     help="add a frequency-domain NF2FF box (changes the XML); results at solve")
    cli.add_argument("--nf2ff-points", type=int, choices=sorted(NF2FF_BAND_POINTS), default=11,
                     help="NF2FF frequencies: 3 (band edges + f0) or 11 (49.92 MHz steps, enables the group-delay diagnostic)")
    cli.add_argument("--owner-long-convergence", action="store_true",
                     help="owner decision 2026-11-04: allow up to 2700 s for --mesh fine convergence runs")
    cli.add_argument("--max-timesteps", type=int, default=None,
                     help="raise the NrTS cap (default %d) for high-Q geometries that do not reach EndCriteria; changes the "
                          "XML; prepare and solve must use the same value" % NR_TS)
    cli.add_argument("--excitation-fc-hz", type=float, default=1e9,
                     help="Gaussian corner offset fc (default 1e9 keeps the XML of 001/004/005/006); the valid -20 dB range is "
                          "f0 +- 1.0116 fc, e.g. 2.5e9 -> 5.46..10.52 GHz (changes the XML; prepare/solve only)")
    cli.add_argument("--out-reprocess", type=Path, help="reprocess: NEW directory for the re-analysed CSV/JSON (never overwritten)")
    cli.add_argument("--no-nf2ff-reprocess", action="store_true", help="reprocess: skip the NF2FF power-quantity recomputation")
    cli.add_argument("--legacy-zline-diagnostic", action="store_true",
                     help="MSL ports: also write s11_openems_zline_DIAGNOSTIC.csv (the openEMS Z_line/beta extraction, known ill-"
                          "conditioned under strong standing waves; diagnostic only)")
    cli.add_argument("--no-current-correction", action="store_true",
                     help="MSL ports: use plain mean(I_A, I_B) instead of mean / cos(beta D / 2)")
    args = cli.parse_args()
    global MESH_PROFILE, GAUSS_FC_HZ, MSL_CURRENT_AVERAGE_CORRECTION
    if args.max_timesteps is not None:
        if args.max_timesteps < NR_TS:
            raise SystemExit("--max-timesteps may only raise the default cap of %d steps" % NR_TS)
        NR_TS = args.max_timesteps
    MESH_PROFILE = args.mesh
    globals().update(MESH_PROFILES[args.mesh])
    global ABORT_TIME_LIMIT_S
    if getattr(args, "owner_long_convergence", False):
        if args.mesh not in ("fine", "xfine"):
            raise SystemExit("--owner-long-convergence is only for --mesh fine/xfine convergence runs")
        ABORT_TIME_LIMIT_S = ABORT_TIME_S_LONG_CONVERGENCE
    if not args.excitation_fc_hz > 0:
        raise SystemExit("--excitation-fc-hz must be positive")
    GAUSS_FC_HZ = args.excitation_fc_hz
    MSL_CURRENT_AVERAGE_CORRECTION = not args.no_current_correction
    out = args.out.resolve()
    if args.mode == "reprocess":
        if args.out_reprocess is None:
            raise SystemExit("--out-reprocess <new dir> is required for reprocess")
        reprocess(out, args.out_reprocess, nf2ff=not args.no_nf2ff_reprocess, legacy_diagnostic=args.legacy_zline_diagnostic)
        return
    if args.mode == "summarize":
        summarize(out)
        return
    if args.variant is None:
        raise SystemExit("--variant is required for prepare/solve")
    variant = args.variant.resolve()
    if (out / "run_started.json").exists():
        raise RuntimeError("Refusing overwrite/relaunch of a started solve")
    previous = json.loads((out / "prepared.json").read_text()) if (out / "prepared.json").exists() else None
    if args.mode == "prepare" and previous is not None:
        raise RuntimeError("Refusing to overwrite an existing prepared.json; choose a new --out")
    if args.mode == "solve" and previous is None:
        raise RuntimeError("Solve requires a previously prepared output directory (prepare first)")
    opts = {"edge_port": args.edge_port, "nf2ff": args.nf2ff, "nf2ff_points": args.nf2ff_points}
    fdtd, port, metadata, nf2ff_box = build(variant, out, opts)
    if args.mode == "prepare":
        shutil.copyfile(variant, out / VARIANT_COPY)
        (out / "prepared.json").write_text(json.dumps(metadata, indent=2) + "\n")
        print(json.dumps(metadata, indent=2), flush=True)
        for line in parasitic_summary(metadata):
            print(line, file=sys.stderr)
        return
    if previous is None or previous["native_xml_sha256"] != metadata["native_xml_sha256"]:
        raise RuntimeError("Solve requires the same reviewed prepared native XML")
    if previous.get("variant_sha256") != metadata["variant_sha256"]:
        raise RuntimeError("Variant JSON changed since prepare")
    if not metadata["budget_before_solve"]["launch_allowed_by_budget"]:
        raise RuntimeError("Budget abort rule: " + "; ".join(metadata["budget_before_solve"]["abort_reasons"]))
    if len(os.sched_getaffinity(0)) > 2:
        raise RuntimeError("Solve requires CPU affinity restricted to at most two CPUs")
    with (out / "run_started.json").open("x") as stream:
        json.dump({"started_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
                   "cpu_affinity": sorted(os.sched_getaffinity(0)),
                   "native_xml_sha256": metadata["native_xml_sha256"]}, stream, indent=2)
    started = time.monotonic()
    status = fdtd.Run(str(out), cleanup=False, numThreads=2, dump_statistics=True, verbose=1)
    if status not in (None, 0):
        raise RuntimeError(f"FDTD setup failed with code {status}")
    solve_outputs(out, port, metadata, started, nf2ff_box, args.legacy_zline_diagnostic)


if __name__ == "__main__":
    main()
