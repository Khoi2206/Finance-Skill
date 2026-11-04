"""Raw (bronze) store: content-addressed immutable copies + append-only manifest.

- The same bytes are never ingested twice (sha256 idempotency).
- A corrected export for the same report × company × period is a NEW extraction; the newest
  extraction covering a month becomes effective, older ones stay for audit (restatement history).
"""
from __future__ import annotations

import datetime as dt
import getpass
import hashlib
import json
import shutil
from pathlib import Path


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


class RawStore:
    def __init__(self, root: Path):
        self.root = Path(root)
        self.raw = self.root / "raw"
        self.raw.mkdir(parents=True, exist_ok=True)
        self.manifest_path = self.root / "manifest.jsonl"

    def entries(self) -> list[dict]:
        if not self.manifest_path.exists():
            return []
        out = {}
        for line in self.manifest_path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                e = json.loads(line)
                out[e["extraction_id"]] = {**out.get(e["extraction_id"], {}), **e}  # later lines update status
        return list(out.values())

    def get(self, extraction_id: str) -> dict | None:
        return next((e for e in self.entries() if e["extraction_id"] == extraction_id), None)

    def append(self, entry: dict) -> None:
        with open(self.manifest_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False, default=str) + "\n")

    def put(self, src: Path, uploader: str | None = None) -> tuple[dict, bool]:
        """Copy file into the raw store. Returns (entry, is_new)."""
        src = Path(src)
        digest = sha256(src)
        existing = self.get(digest)
        if existing:
            return existing, False
        dst = self.raw / f"{digest}{src.suffix.lower()}"
        if not dst.exists():
            shutil.copy2(src, dst)
            dst.chmod(0o444)
        entry = {
            "extraction_id": digest,
            "seq": len(self.entries()) + 1,  # monotonic order: later extraction supersedes earlier
            "source_filename": src.name,
            "raw_path": str(dst.relative_to(self.root)),
            "size_bytes": src.stat().st_size,
            "uploader": uploader or getpass.getuser(),
            "ingested_at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
            "status": "RAW",
        }
        self.append(entry)
        return entry, True
