"""Build a reproducible LOCAL full-app validation candidate.

The candidate contains the application payload plus the previously prepared Python
runtime. Model weights are deliberately NOT copied. This is not an external release
approval and does not bypass package/model-rights blockers.
"""
import hashlib
import json
import shutil
import uuid
from pathlib import Path

from package_plan import plan

ROOT = Path(__file__).resolve().parents[1]
STAGING = (ROOT / "Release/Staging").resolve()
VERSION = "0.1.0-beta.1"

FORBIDDEN_PREFIXES = (
    "Private/",
    "Activator/",
    "Tools/LicenseAdmin/",
    ".venv/",
    ".venv-anyenhance/",
    "Models/",
)

def sha256(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()

def copy_file(source, destination, build, records):
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, destination)
    records.append({
        "path": destination.relative_to(build).as_posix(),
        "bytes": destination.stat().st_size,
        "sha256": sha256(destination),
    })

def copy_tree(source, destination, build, records):
    if not source.is_dir():
        raise FileNotFoundError(str(source))
    for path in sorted(source.rglob("*")):
        relative = path.relative_to(source)
        if "__pycache__" in relative.parts or path.suffix.lower() == ".pyc":
            continue
        if path.is_symlink() or path.is_junction():
            raise ValueError("Linked content requires review: " + str(path))
        if path.is_file():
            copy_file(path, destination / relative, build, records)

def main():
    selected = json.loads((ROOT / "Release/latest-runtime-candidate.json").read_text(encoding="utf-8"))
    runtime_candidate = (ROOT / selected["path"]).resolve()
    if not runtime_candidate.is_relative_to(STAGING):
        raise ValueError("Runtime candidate outside Release/Staging")
    if not (runtime_candidate / "Runtime/python.exe").is_file():
        raise FileNotFoundError("Runtime candidate is incomplete")

    payload = plan(ROOT)
    build = STAGING / ("VocalX-" + VERSION + "-AppCandidate-" + uuid.uuid4().hex[:12])
    build.mkdir(parents=True, exist_ok=False)
    records = []

    for entry in payload["files"]:
        source_name = entry["source"]
        normalized = source_name.replace("\\\\", "/")
        if normalized.startswith(FORBIDDEN_PREFIXES):
            raise ValueError("Forbidden payload source: " + source_name)
        source = (ROOT / source_name).resolve()
        if not source.is_relative_to(ROOT.resolve()) or not source.is_file():
            raise FileNotFoundError(source_name)
        if source.stat().st_size != entry["bytes"] or sha256(source) != entry["sha256"]:
            raise ValueError("Payload changed after planning: " + source_name)
        destination = build / entry["destination"]
        copy_file(source, destination, build, records)

    copy_tree(runtime_candidate / "Runtime", build / "Runtime", build, records)

    notices = runtime_candidate / "ThirdPartyNotices"
    if notices.is_dir():
        copy_tree(notices, build / "ThirdPartyNotices", build, records)

    metadata = build / "ReleaseMetadata"
    metadata.mkdir(parents=True, exist_ok=True)
    for name in ("runtime-manifest.json", "verification.json"):
        source = runtime_candidate / name
        if source.is_file():
            copy_file(source, metadata / name, build, records)

    (build / "Models").mkdir(parents=True, exist_ok=True)

    required = [
        "App/runtime-layout.json",
        "Config/core-model-download-report.json",
        "Tools/AnyEnhance-360M-Recovered/models/se/anyenhance/modules/encoder_loss.py",
        "Tools/AnyEnhance-360M-Recovered/models/se/anyenhance/anyenhance_model.py",
        "Tools/AnyEnhance-360M-Recovered/models/se/anyenhance/modules/anyenhance_modules.py",
        "Tools/AnyEnhance-v1/config/anyenhance_v1.json",
        "Tools/AnyEnhance-v1/anyenhance/__init__.py",
        "Runtime/python.exe",
    ]
    missing = [name for name in required if not (build / name).is_file()]
    if missing:
        raise FileNotFoundError("Required app candidate files missing: " + ", ".join(missing))

    preset_files = sorted((build / "Pipelines/Presets").glob("*.json"))
    preset_names = [json.loads(p.read_text(encoding="utf-8-sig"))["name"] for p in preset_files]
    if len(preset_files) != 11 or len(set(preset_names)) != 11:
        raise ValueError("Built-in preset inventory must contain exactly 11 unique presets")

    forbidden_found = []
    for prefix in ("Private", "Activator", ".venv", ".venv-anyenhance"):
        if (build / prefix).exists():
            forbidden_found.append(prefix)
    if (build / "Tools/LicenseAdmin").exists():
        forbidden_found.append("Tools/LicenseAdmin")
    if forbidden_found:
        raise ValueError("Forbidden content copied: " + ", ".join(forbidden_found))

    manifest = {
        "status": "LOCAL FULL-APP VALIDATION CANDIDATE ONLY",
        "version": VERSION,
        "runtime_source": runtime_candidate.relative_to(ROOT).as_posix(),
        "models_included": False,
        "preset_count": len(preset_files),
        "package_blockers": payload["blockers"],
        "files": records,
    }
    manifest_path = build / "app-candidate-manifest.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

    latest = ROOT / "Release/latest-app-candidate.json"
    latest.write_text(json.dumps({"path": build.relative_to(ROOT).as_posix()}), encoding="utf-8")

    print("APP_CANDIDATE=" + str(build))
    print("PAYLOAD_FILES=" + str(len(payload["files"])))
    print("TOTAL_RECORDED_FILES=" + str(len(records)))
    print("PRESET_COUNT=" + str(len(preset_files)))
    print("MODELS_INCLUDED=False")
    print("RELEASE_CLEARED=False")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
