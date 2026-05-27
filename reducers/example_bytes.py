from __future__ import annotations

import argparse
from pathlib import Path

import yaml


def reduce(recipe: Path, output_dir: Path) -> list[Path]:
    data = yaml.safe_load(recipe.read_text(encoding="utf-8"))
    message = data.get("reducer", {}).get("parameters", {}).get("message", "")
    written: list[Path] = []

    for artifact in data["artifacts"]:
        target = output_dir / artifact["path"]
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(message, encoding="utf-8")
        written.append(target)

    return written


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--recipe", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    args = parser.parse_args()
    reduce(args.recipe, args.output_dir)


if __name__ == "__main__":
    main()
