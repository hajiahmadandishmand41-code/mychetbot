"""ZIP archive helpers with bounded extraction."""
from pathlib import Path
import zipfile


def zip_info(args: dict) -> dict:
    path = Path(args["path"]).expanduser()
    with zipfile.ZipFile(path) as zf:
        return {"path": str(path), "files": zf.namelist()[:1000], "count": len(zf.infolist())}


def zip_extract(args: dict) -> str:
    archive = Path(args["path"]).expanduser().resolve()
    destination = Path(args.get("destination", archive.with_suffix(""))).expanduser().resolve()
    destination.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(archive) as zf:
        for member in zf.infolist():
            target = (destination / member.filename).resolve()
            if not str(target).startswith(str(destination) + "/") and target != destination:
                raise ValueError("Unsafe ZIP path traversal detected")
        zf.extractall(destination)
    return f"extracted {len(zf.infolist())} entries to {destination}"


def build_archive_tools():
    return {"zip_info": zip_info, "zip_extract": zip_extract}
