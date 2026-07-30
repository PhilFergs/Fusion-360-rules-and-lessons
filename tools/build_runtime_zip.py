import sys
import zipfile
from pathlib import Path


def build_runtime_zip(source: Path, target: Path) -> int:
    source = Path(source)
    files = sorted(path for path in source.rglob("*") if path.is_file())
    if not files:
        raise ValueError(f"runtime tree is empty: {source}")

    target.parent.mkdir(parents=True, exist_ok=True)
    target.unlink(missing_ok=True)
    with zipfile.ZipFile(target, "w") as archive:
        for path in files:
            name = f"{source.name}/{path.relative_to(source).as_posix()}"
            info = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o600 << 16
            archive.writestr(info, path.read_bytes())
    return len(files)


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit("usage: build_runtime_zip.py <source-root> <target-zip>")
    count = build_runtime_zip(Path(sys.argv[1]), Path(sys.argv[2]))
    print(f"Packaged runtime files: {count}")
