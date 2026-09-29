"""Report the repository's development package identity.

This repository has no package metadata or release version yet, so use its
current Git revision as a truthful development version.
"""

import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent


def main() -> None:
    revision = subprocess.check_output(
        ["git", "rev-parse", "--short", "HEAD"], cwd=ROOT, text=True
    ).strip()
    print(f"hermes-contextmux 0+g{revision}")


if __name__ == "__main__":
    main()
