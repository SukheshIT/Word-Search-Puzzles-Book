from __future__ import annotations

import argparse
import json
from pathlib import Path


SIGNATURES = [
    (b"%PDF-", "PDF document"),
    (b"\x89PNG\r\n\x1a\n", "PNG image"),
    (b"\xff\xd8\xff", "JPEG image"),
    (b"PK\x03\x04", "ZIP archive"),
]


def describe_file(path: Path) -> str:
    header = path.read_bytes()[:32]
    size = path.stat().st_size

    if header.startswith(b"%PDF-"):
        version = header[5:8].decode("ascii", errors="ignore") or "unknown"
        return f"{path}: PDF document, version {version}, {size} bytes"

    for signature, label in SIGNATURES[1:]:
        if header.startswith(signature):
            return f"{path}: {label}, {size} bytes"

    if _looks_like_json(path, header):
        return f"{path}: JSON text data, {size} bytes"

    if _looks_like_text(header):
        return f"{path}: UTF-8 text data, {size} bytes"

    return f"{path}: data, {size} bytes"


def _looks_like_json(path: Path, header: bytes) -> bool:
    stripped = header.lstrip()
    if not stripped.startswith((b"{", b"[")):
        return False
    try:
        json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return False
    return True


def _looks_like_text(header: bytes) -> bool:
    try:
        header.decode("utf-8")
    except UnicodeDecodeError:
        return False
    return all(byte in b"\t\n\r" or 32 <= byte <= 126 or byte >= 128 for byte in header)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Lightweight replacement for the `file` command used in this project."
    )
    parser.add_argument("path", type=Path, help="File path to inspect.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    print(describe_file(args.path))


if __name__ == "__main__":
    main()
