"""Verify and optionally write the exact Zhang Conjecture 4.1 certificate."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

if __package__:
    from .certificate import build_certificate
else:
    from certificate import build_certificate


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    certificate = build_certificate()
    rendered = json.dumps(certificate, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
        print(f"Wrote exact certificate: {args.output}")
    else:
        print(rendered, end="")
    print("All exact checks passed.")


if __name__ == "__main__":
    main()
