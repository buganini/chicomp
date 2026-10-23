#!/usr/bin/env python3
"""Build a self-contained static site; all generated files stay under .build/dist."""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import shlex
import shutil
import subprocess
import urllib.request
from zipfile import ZipFile

import zstandard

ROOT = Path(__file__).resolve().parents[1]
WORK = ROOT / ".build"
DIST = ROOT / "dist"
LOCK = json.loads((ROOT / "sources.lock.json").read_text())
CALLBACKS = ("from/ANY", "from/_UTF-8", "from/BSDCONV", "to/_UTF-8", "to/BSDCONV", "inter/INSERT", "inter/COUNT")
CODECS = ("from/ANY", "from/ASCII", "from/_UTF-8", "from/BSDCONV", "to/ASCII", "to/_UTF-8", "to/BSDCONV",
          "to/BSDCONV-KEYWORD", "inter/COUNT", "inter/INSERT", "inter/ALIAS-FROM", "inter/ALIAS-INTER",
          "inter/ALIAS-TO", "inter/ZH-COMP", "inter/ZH-DECOMP", "inter/CNS11643")


def run(args, **kwargs):
    subprocess.run(list(map(str, args)), check=True, **kwargs)


def checkout(name, local):
    spec = LOCK[name]
    path = Path(local).resolve() if local else WORK / "sources" / name
    if not path.exists():
        path.mkdir(parents=True)
        run(["git", "init", path])
        run(["git", "-C", path, "remote", "add", "origin", spec["url"]])
        run(["git", "-C", path, "fetch", "--depth", "1", "origin", spec["commit"]])
        run(["git", "-C", path, "checkout", "--detach", "FETCH_HEAD"])
    head = subprocess.check_output(["git", "-C", str(path), "rev-parse", "HEAD"], text=True).strip()
    dirty = subprocess.check_output(["git", "-C", str(path), "status", "--porcelain", "--untracked-files=no"], text=True)
    if head != spec["commit"] or dirty:
        raise RuntimeError(f"{name} must be clean and at {spec['commit']}; update sources.lock.json deliberately")
    return path


def properties():
    spec = LOCK["properties"]
    archive = WORK / "Properties.zip"
    if not archive.exists():
        temp = archive.with_suffix(".zip.tmp")
        with urllib.request.urlopen(spec["url"], timeout=60) as response, temp.open("wb") as out:
            shutil.copyfileobj(response, out)
        temp.replace(archive)
    if hashlib.sha256(archive.read_bytes()).hexdigest() != spec["sha256"]:
        raise RuntimeError("Properties.zip changed: review its version and SHA-256 before updating sources.lock.json")
    directory = WORK / "properties"
    if directory.exists():
        shutil.rmtree(directory)
    with ZipFile(archive) as zipped:
        zipped.extractall(directory)
    return directory


def prepare_port(bsdconv):
    """Adapt the pinned core in the build directory, never the source checkout."""
    port = WORK / "port"
    shutil.copytree(bsdconv / "src", port / "src", dirs_exist_ok=True)
    endian = port / "src/portable_endian.h"
    data = endian.read_bytes()
    old = b"defined(__linux__) || defined(__CYGWIN__)"
    if data.count(old) != 1:
        raise RuntimeError("Review the endian adapter for the selected bsdconv revision")
    endian.write_bytes(data.replace(old, old + b" || defined(__EMSCRIPTEN__)"))
    declarations = ['#include "bsdconv.h"']
    branches = []
    sources = []
    for index, name in enumerate(CALLBACKS):
        source = (bsdconv / f"modules/{name}.c").read_text()
        callbacks = re.findall(r"^(int|void) (cb\w+)\(([^)]*)\)", source, re.M)
        if not callbacks:
            raise RuntimeError(f"No callbacks found in {name}")
        for result, callback, args in callbacks:
            renamed = f"module_{index}_{callback}"
            declarations.append(f"{result} {renamed}({args});")
            source = re.sub(r"\b" + callback + r"\b", renamed, source)
        # Each original shared module had its own copy of the hex lookup table.
        source = f"#define hex module_{index}_hex\n" + source
        target = port / f"modules/{name}.c"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(source)
        sources.append(target)
        branches.append(f'if (!strcmp(path, "/usr/local/share/bsdconv/{name}")) {{')
        branches.extend(f"cd->{callback}=module_{index}_{callback};" for _, callback, _ in callbacks)
        branches.append("return; }")
    registry = port / "registry.c"
    registry.write_text("\n".join(declarations) + "\nvoid chicomp_bind_codec(struct bsdconv_codec *cd, const char *path) {\n" + "\n".join(branches) + "\n}\n")
    core = port / "src/libbsdconv.c"
    source = core.read_text()
    marker = '\tstrcat(path, "." SHLIBEXT);'
    if source.count(marker) != 1:
        raise RuntimeError("Review the static callback adapter for the selected bsdconv revision")
    start = source.index(marker)
    end = source.index("\n\treturn 1;", start)
    source = source[:start] + "\tchicomp_bind_codec(cd, path);\n" + source[end:]
    declaration = "int _loadcodec(struct bsdconv_codec *cd, char *path){"
    if source.count(declaration) != 1:
        raise RuntimeError("Cannot find codec loader")
    source = source.replace(declaration, "void chicomp_bind_codec(struct bsdconv_codec *, const char *);\n" + declaration)
    core.write_text(source)
    return port, [core, registry, ROOT / "wasm/wrapper.c", *sources]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bsdconv")
    parser.add_argument("--cns11643")
    args = parser.parse_args()
    os.chdir(ROOT)
    WORK.mkdir(exist_ok=True)
    if DIST.exists():
        shutil.rmtree(DIST)
    DIST.mkdir()
    bsdconv = checkout("bsdconv", args.bsdconv)
    cns = checkout("cns11643", args.cns11643)
    prop = properties()
    emcc = os.environ.get("EMCC", "emcc")
    version = subprocess.check_output([emcc, "--version"], text=True).splitlines()[0]
    if not re.search(r"\b" + re.escape(LOCK["emscripten"]) + r"\b", version):
        raise RuntimeError(f"Expected Emscripten {LOCK['emscripten']}, got {version}")
    table_tool = WORK / "bsdconv-mktable"
    run([*shlex.split(os.environ.get("CC", "cc")), "-O2", "-D_BSDCONV_INTERNAL", "-DUSE_FMALLOC",
         bsdconv / "src/libfmalloc.c", bsdconv / "src/bsdconv-mktable.c", "-o", table_tool])
    binary = bytearray()
    entries = []
    for name in CODECS:
        source_repo = cns if name in ("inter/ZH-COMP", "inter/ZH-DECOMP", "inter/CNS11643") else bsdconv
        source = source_repo / f"modules/{name}.txt"
        if source_repo == cns and f"version {LOCK['properties']['version']}" not in source.read_text().splitlines()[0]:
            raise RuntimeError(f"CNS table and component images have different versions: {name}")
        target = WORK / "codecs" / name
        target.parent.mkdir(parents=True, exist_ok=True)
        run([table_tool, source, target], stdout=subprocess.DEVNULL)
        data = target.read_bytes()
        entries.append({"path": name, "offset": len(binary), "length": len(data)})
        binary.extend(data)
    packed = zstandard.ZstdCompressor(level=22).compress(binary)
    if zstandard.ZstdDecompressor().decompress(packed) != binary:
        raise RuntimeError("Codec compression round trip failed")
    digest = hashlib.sha256(packed).hexdigest()
    archive_name = f"codecs-{digest[:16]}.zst"
    (DIST / archive_name).write_bytes(packed)
    manifest = {"archive": archive_name, "sha256": digest, "size": len(binary), "files": entries,
                "sources": LOCK}
    (DIST / "codecs.json").write_text(json.dumps(manifest, indent=2) + "\n")
    port, sources = prepare_port(bsdconv)
    run([emcc, "-Oz", "-flto", "-D_BSDCONV_INTERNAL", "-DDISABLE_DYNAMIC_LOADING",
         '-DBSDCONV_PATH="/usr/local"', '-DPREFIX="/usr/local"', "-I", port / "src", *sources,
         "--no-entry", "-sMODULARIZE=1", "-sEXPORT_ES6=1", "-sENVIRONMENT=worker,node",
         "-sALLOW_MEMORY_GROWTH=1", "-sINITIAL_MEMORY=67108864",
         '-sEXPORTED_FUNCTIONS=["_chicomp_convert","_bsdconv_free"]',
         '-sEXPORTED_RUNTIME_METHODS=["ccall","UTF8ToString","FS"]',
         "-o", DIST / "bsdconv.mjs"])
    spec = importlib.util.spec_from_file_location("images_generator", ROOT / "gen.py")
    generator = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(generator)
    components = generator.generate(prop, DIST / "images")
    (DIST / "components.json").write_text(json.dumps(components, indent=2) + "\n")
    run(["npm", "run", "build:js"])
    for name in ("index.html", "src/style.css"):
        shutil.copy2(ROOT / name, DIST / Path(name).name)
    shutil.copy2(bsdconv / "LICENSE", DIST / "BSDCONV-LICENSE.txt")
    (DIST / ".nojekyll").touch()
    print(f"Built {len(entries)} codecs: {len(binary):,} bytes -> {len(packed):,} bytes zstd; {len(components)} components")


if __name__ == "__main__":
    main()
