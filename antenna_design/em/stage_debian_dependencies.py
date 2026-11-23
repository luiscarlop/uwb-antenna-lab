"""Recreate workspace-only dependencies from the recorded official manifest.

Downloads Debian binary packages, verifies recorded SHA256, and extracts them
without package installation or maintainer scripts. Uses inherited proxy/TLS.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import urllib.request


def main():
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("--manifest", type=Path, required=True)
    cli.add_argument("--prefix", type=Path, required=True)
    cli.add_argument("--cache", type=Path, required=True)
    args = cli.parse_args()
    args.prefix.mkdir(parents=True, exist_ok=True)
    args.cache.mkdir(parents=True, exist_ok=True)
    for package in json.loads(args.manifest.read_text()):
        if not package["url"].startswith("https://deb.debian.org/debian/"):
            raise ValueError("Expected an official Debian package URL")
        path = args.cache / package["url"].rsplit("/", 1)[-1]
        if not path.exists():
            with urllib.request.urlopen(package["url"], timeout=30) as response:
                data = response.read(32 * 1024 * 1024 + 1)
            if len(data) > 32 * 1024 * 1024:
                raise ValueError("Bounded download exceeded 32 MiB")
            path.write_bytes(data)
        if hashlib.sha256(path.read_bytes()).hexdigest() != package["sha256"]:
            raise ValueError(f"SHA256 mismatch: {package['name']}")
        subprocess.run(["dpkg-deb", "-x", str(path), str(args.prefix)], check=True)
        print("staged", package["name"], package["version"], flush=True)


if __name__ == "__main__":
    main()
