"""Read-only solver probe. Optional network checks use official public indexes.

No installation, subprocess solve, API charge, or simulation is performed.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import importlib
import json
import lzma
import os
from pathlib import Path
import platform
import shutil
import sys
import urllib.error
import urllib.request


def fetch(url):
    try:
        with urllib.request.urlopen(url, timeout=30) as response:
            body = response.read(32 * 1024 * 1024 + 1)
            if len(body) > 32 * 1024 * 1024:
                raise ValueError("Download exceeds bounded 32 MiB probe")
            return {"url": url, "http_status": response.status,
                    "bytes": len(body), "sha256": hashlib.sha256(body).hexdigest()}, body
    except (urllib.error.URLError, ValueError) as exc:
        return {"url": url, "error": str(exc)}, None


def diagnose(network=False):
    result = {"timestamp_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
              "python": sys.version, "platform": platform.platform(),
              "modules": {}, "executables": {}, "resources": {},
              "network_probes": [], "em_status": "EM_NOT_RUN", "solves_started": 0}
    for module in ("openEMS", "CSXCAD"):
        try:
            loaded = importlib.import_module(module)
            result["modules"][module] = {"available": True, "path": loaded.__file__,
                                         "version": str(getattr(loaded, "__version__", "UNKNOWN"))}
        except Exception as exc:
            result["modules"][module] = {"available": False,
                                         "error": f"{type(exc).__name__}: {exc}"}
    for name in ("openEMS", "openems", "AppCSXCAD", "octave", "conda", "mamba", "micromamba"):
        result["executables"][name] = shutil.which(name)
    for filename in ("memory.max", "cpu.max"):
        path = Path("/sys/fs/cgroup") / filename
        result["resources"][filename] = path.read_text().strip() if path.exists() else "UNKNOWN"
    if hasattr(os, "sched_getaffinity"):
        result["resources"]["cpu_affinity"] = sorted(os.sched_getaffinity(0))
    if network:
        for package in ("openEMS", "CSXCAD"):
            evidence, _ = fetch(f"https://pypi.org/pypi/{package}/json")
            result["network_probes"].append(evidence)
        evidence, body = fetch("https://deb.debian.org/debian/dists/trixie/main/binary-amd64/Packages.xz")
        if body is not None:
            records = lzma.decompress(body).decode().split("\n\n")
            evidence["matching_packages"] = [record.splitlines()[0] for record in records
                if any(line.startswith("Package: ") and
                       ("openems" in line.lower() or "csxcad" in line.lower())
                       for line in record.splitlines())]
        result["network_probes"].append(evidence)
        evidence, _ = fetch("https://raw.githubusercontent.com/thliebig/openEMS/master/python/Tutorials/Simple_Patch_Antenna.py")
        result["network_probes"].append(evidence)
    result["python_bindings_importable"] = all(item["available"] for item in result["modules"].values())
    result["solver_operational"] = None if result["python_bindings_importable"] else False
    result["operational_verification"] = "NOT_RUN; imports alone cannot verify solver execution"
    return result


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("--network", action="store_true", help="bounded official package/tutorial reads")
    cli.add_argument("--out", type=Path, required=True)
    args = cli.parse_args()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(diagnose(args.network), indent=2) + "\n")
    print(args.out)
