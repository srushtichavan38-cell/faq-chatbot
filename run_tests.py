"""Small dependency-check helper; use pytest for the full test suite."""
import subprocess
import sys

raise SystemExit(subprocess.call([sys.executable, "-m", "pytest", "-q"]))
