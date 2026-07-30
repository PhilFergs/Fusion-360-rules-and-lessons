import sys
from pathlib import Path
from xml.etree import ElementTree

PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"


def validate_runtime(root: Path) -> int:
    files = 0
    for path in Path(root).rglob("*"):
        if not path.is_file():
            continue
        files += 1
        suffix = path.suffix.casefold()
        if suffix == ".py":
            compile(path.read_text(encoding="utf-8"), str(path), "exec")
        elif suffix == ".svg":
            if not ElementTree.parse(path).getroot().tag.endswith("svg"):
                raise ValueError(f"invalid SVG root: {path}")
        elif suffix == ".png" and not path.read_bytes().startswith(PNG_SIGNATURE):
            raise ValueError(f"invalid PNG signature: {path}")
    if files == 0:
        raise ValueError(f"runtime tree is empty: {root}")
    return files


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("usage: validate_runtime.py <runtime-root>")
    print(f"Validated runtime files: {validate_runtime(Path(sys.argv[1]))}")
