"""Paths of the reorganised antenna_design/hfss/ tree (build/, export/, analysis/, results/) shared by the HFSS tests.

Not a test module (no test_ prefix): the tests import it as `from hfss_paths import ...`.
"""
import re
from pathlib import Path

HFSS = Path(__file__).resolve().parents[1] / "hfss"
BUILD = HFSS / "build"        # generators + claude_pyaedt_ch9.py; one subfolder per element with its native/array scripts
EXPORT = HFSS / "export"      # the three AEDT exporters
ANALYSIS = HFSS / "analysis"  # Python analysis scripts
RESULTS = HFSS / "results"    # results_<design>/ folders (no dates)


def build_path(filename):
    """build/<element>/<filename> for the per-element AEDT scripts, build/<filename> for the rest."""
    found = sorted(BUILD.glob(f"*/{filename}"))
    if len(found) > 1:
        raise AssertionError(f"{filename} found in several build/ subfolders: {found}")
    return found[0] if found else BUILD / filename


def set_design(src, name):
    """Make `name` the active (uncommented) DESIGN line of an exporter; the other options stay commented."""
    new, n = re.subn(r'(?m)^DESIGN = ".*?"', 'DESIGN = "%s"' % name, src)
    assert n == 1, "an exporter must have exactly one active DESIGN line"
    return new
