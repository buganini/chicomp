#!/usr/bin/env python3
"""Generate component GIFs and their manifest from the locked CNS data."""
import json
import shutil
import subprocess
from pathlib import Path
from zipfile import ZipFile


def generate(properties, output):
    output.mkdir(parents=True, exist_ok=True)
    parts = properties / "parts"
    with ZipFile(properties / "CNS_component_word.zip") as archive:
        archive.extractall(properties)
    groups = {}
    for line in (properties / "CNS_component_word.txt").read_text(encoding="utf-8").splitlines():
        part, group, strokes = map(int, line.split())
        code = f"{group:X}"
        code = "0400" if part == 1111 else "04" + code.zfill(len(code) + len(code) % 2)
        groups.setdefault(code, []).append((part, strokes))
    command = shutil.which("magick") or shutil.which("convert")
    if not command:
        raise RuntimeError("Install ImageMagick (magick or convert)")
    manifest = []
    for code, entries in sorted(groups.items(), key=lambda item: (item[0] == "0400", int(item[0], 16))):
        frames = [parts / f"{part}.png" for part, _ in sorted(entries)]
        missing = [str(p) for p in frames if not p.is_file()]
        if missing:
            raise RuntimeError(f"Missing component images: {missing}")
        subprocess.run([command, "-delay", "50", "-loop", "0", *map(str, frames),
                        "-resize", "48x48", "-strip", str(output / f"{code}.gif")], check=True)
        manifest.append({"code": code, "image": f"images/{code}.gif",
                         "strokes": min(strokes for _, strokes in entries)})
    return manifest


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("properties", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    result = generate(args.properties, args.output)
    (args.output.parent / "components.json").write_text(json.dumps(result), encoding="utf-8")
