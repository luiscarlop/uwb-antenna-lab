"""IR-UWB CH9: candidate 2D layouts. GEOMETRY_ONLY; never EM results."""
from __future__ import annotations
import argparse
import json
from math import cos, pi, sin, sqrt
from pathlib import Path

C0 = 299_792_458.0
F0_HZ = 7_987_200_000.0
BW_HZ = 499_200_000.0
ER = 4.4  # provisional generic FR4, not manufacturer data
H_MM = 1.6
TAN_D = 0.017
BOARD_MM = 26.0

def rectangular_patch_dimensions(f_hz=F0_HZ, er=ER, h_mm=H_MM):
    """Transmission-line TM10 first guess; NOT a full-wave solution."""
    if f_hz <= 0 or er <= 1 or h_mm <= 0: raise ValueError("Nonphysical inputs")
    h = h_mm / 1000.0
    width = C0 / (2*f_hz) * sqrt(2/(er+1))
    eps_eff = (er+1)/2 + (er-1)/(2*sqrt(1+12*h/width))
    d_len = 0.412*h*((eps_eff+0.3)*(width/h+0.264))/((eps_eff-0.258)*(width/h+0.8))
    length = C0/(2*f_hz*sqrt(eps_eff))-2*d_len
    if length <= 0: raise ValueError("Nonphysical patch length")
    return width*1000, length*1000, eps_eff

def rectangle(w,h):
    return [(-w/2,-h/2),(w/2,-h/2),(w/2,h/2),(-w/2,h/2)]

def hexagon(r):
    return [(r*cos(i*pi/3),r*sin(i*pi/3)) for i in range(6)]

def u_slot(w,h,t=0.35):
    """Concave removal polygon on copper. Shape is heuristic."""
    xl,xr=-0.275*w,0.275*w; yi,yo=xl+t,xr-t
    yt,yb=.36*h,-.08*h
    return [(xl,yt),(yi,yt),(yi,yb+t),(yo,yb+t),(yo,yt),(xr,yt),(xr,yb),(xl,yb)]

def candidates():
    w,l,_=rectangular_patch_dimensions()
    r=w*.53
    return {
      "P01_rectangular_patch":{"patch":rectangle(w,l),"slots":[],"feed":(0.,-l*.22),"note":"TM10 line-model starting dimensions"},
      "P02_u_slot_patch":{"patch":rectangle(w,l),"slots":[u_slot(w,l)],"feed":(0.,-l*.22),"note":"U-slot dimensions heuristic"},
      "P03_hex_slot_patch":{"patch":hexagon(r),"slots":[hexagon(1.1)],"feed":(0.,-r*.42),"note":"Hex patch/slot heuristic, no resonance prediction"}
    }

def _svg_points(poly):
    return " ".join(f"{x+BOARD_MM/2:.4f},{BOARD_MM/2-y:.4f}" for x,y in poly)

def export_svg(path,design):
    body=f'<polygon points="{_svg_points(design["patch"])}" fill="#c58e50" stroke="#47321f" stroke-width=".12"/>'
    body+="".join(f'<polygon points="{_svg_points(s)}" fill="#fffaf0" stroke="#a24e42" stroke-width=".08"/>' for s in design["slots"])
    fx,fy=design["feed"]
    body+=f'<circle cx="{fx+BOARD_MM/2:.4f}" cy="{BOARD_MM/2-fy:.4f}" r=".14" fill="#1d6eac"/>'
    Path(path).write_text(f'<svg xmlns="http://www.w3.org/2000/svg" width="600" height="600" viewBox="-1 -1 {BOARD_MM+2} {BOARD_MM+2}"><rect width="{BOARD_MM}" height="{BOARD_MM}" fill="#fffaf0" stroke="#888" stroke-width=".08"/>{body}</svg>\n',encoding="utf-8")

def export_dxf(path,design):
    try: import ezdxf
    except ImportError as exc: raise RuntimeError("Install ezdxf") from exc
    doc=ezdxf.new("R2013")
    doc.units=4  # millimeters
    for name,color in (("BOARD",8),("PATCH",2),("SLOT",1),("FEED_PROBE_CENTER",5)):
        doc.layers.new(name=name,dxfattribs={"color":color})
    space=doc.modelspace()
    space.add_lwpolyline(rectangle(BOARD_MM,BOARD_MM),close=True,dxfattribs={"layer":"BOARD"})
    space.add_lwpolyline(design["patch"],close=True,dxfattribs={"layer":"PATCH"})
    for poly in design["slots"]:
        space.add_lwpolyline(poly,close=True,dxfattribs={"layer":"SLOT"})
    space.add_circle(design["feed"],.12,dxfattribs={"layer":"FEED_PROBE_CENTER"})
    doc.saveas(path)

def export_all(folder):
    p=Path(folder);p.mkdir(parents=True,exist_ok=True)
    proposed=candidates()
    manifest={
        "evidence":"GEOMETRY_ONLY", "em_simulated":False,"channel":9,
        "frequency_hz":{"center":F0_HZ,"min":F0_HZ-BW_HZ/2,"max":F0_HZ+BW_HZ/2},
        "material_provisional":{"name":"generic_FR4","epsilon_r":ER,"h_mm":H_MM,"tan_delta":TAN_D},
        "board_mm":[BOARD_MM,BOARD_MM],"reference_impedance_ohm":50,
        "baseline_rectangular_dimensions_mm":rectangular_patch_dimensions(),
        "units":"mm","layers":["BOARD","PATCH","SLOT","FEED_PROBE_CENTER"],
        "limitations":["no full-wave EM validation","HFSS requires 3D PCB/ground/port and solver setup"],
        "designs":proposed}
    for name,design in proposed.items():
        export_svg(p/(name+".svg"),design)
        export_dxf(p/(name+".dxf"),design)
    (p/"manifest.json").write_text(json.dumps(manifest,indent=2)+"\n",encoding="utf-8")
    return manifest

if __name__=="__main__":
    cli=argparse.ArgumentParser()
    cli.add_argument("--out",default="outputs")
    args=cli.parse_args()
    result=export_all(args.out)
    print("Exported",len(result["designs"]),"unvalidated geometry candidates to",args.out)
    print("Rectangular patch estimate W x L (mm):",result["baseline_rectangular_dimensions_mm"][:2])
    print("EM evidence: NOT RUN")
