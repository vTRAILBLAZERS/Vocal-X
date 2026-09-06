"""Read-only payload planning. This does not build or authorize an installer."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = ("diagnostic_ui diagnostics gui_i18n gui_worker license_dialog license_service "
       "pipeline preset_info qol_audio qol_window qol_windows vocal_gui vocal_license").split()
ENGINE = "__init__ audio models output_layout paths policy restoration_full restoration runner schema stages".split()
ASSETS = "instagram.png taskbar-x.ico taskbar-x.png trailblazers.png vocal-x.ico vocal-x.png".split()

def contained(root, relative):
    path = (root / relative).resolve()
    if not path.is_relative_to(root.resolve()):
        raise ValueError("Payload path escapes project: " + relative)
    return path

def digest(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()

def runtime_support_mappings(root, blockers):
    mappings = [
        ("Config/core-model-download-report.json", "Config/core-model-download-report.json"),
        ("Tools/AnyEnhance-v1/config/anyenhance_v1.json", "Tools/AnyEnhance-v1/config/anyenhance_v1.json"),
    ]

    code360 = root / "Tools/AnyEnhance-360M-Recovered/models"
    if code360.is_dir():
        for path in sorted(code360.rglob("*.py")):
            relative = path.relative_to(root).as_posix()
            mappings.append((relative, relative))
    else:
        blockers.append("Missing AnyEnhance 360M runtime source directory.")

    codev1 = root / "Tools/AnyEnhance-v1/anyenhance"
    if codev1.is_dir():
        for path in sorted(codev1.glob("*.py")):
            relative = path.relative_to(root).as_posix()
            mappings.append((relative, relative))
    else:
        blockers.append("Missing AnyEnhance v1 runtime source directory.")

    return mappings

def plan(root=ROOT):
    root = Path(root).resolve()
    audit = json.loads((root / "Release/model-rights-audit.json").read_text(encoding="utf-8"))
    models = {item["model"]: item for item in audit["models"]}
    blockers = [
        "Local runtime candidate exists; dependency/license review and full app integration remain incomplete.",
        "Launcher replacement and installer have not been built or verified.",
        "Fresh Windows test unavailable; no external release approval.",
    ]

    mappings = [(f"App/{name}.py", f"App/{name}.py") for name in APP]
    mappings += [(f"App/vocal_pipeline/{name}.py", f"App/vocal_pipeline/{name}.py") for name in ENGINE]
    mappings += [(f"App/assets/{name}", f"App/assets/{name}") for name in ASSETS]
    mappings += [
        ("App/license-public-key.json", "App/license-public-key.json"),
        ("Release/runtime-layout.json", "App/runtime-layout.json"),
    ]
    mappings += runtime_support_mappings(root, blockers)

    presets = []
    for path in sorted((root / "Pipelines/Presets").glob("*.json")):
        relative = path.relative_to(root).as_posix()
        contained(root, relative)
        data = json.loads(path.read_text(encoding="utf-8-sig"))
        required = sorted({s["model"] for s in data["stages"] if s["enabled"] and s.get("model")})
        blocked = [slug for slug in required if not models.get(slug, {}).get("release_allowed", False)]
        presets.append({"name": data["name"], "source": relative, "models": required, "blocked_models": blocked})
        mappings.append((relative, relative))
        if blocked:
            blockers.append(data["name"] + ": model package review incomplete: " + ", ".join(blocked))

    if not presets:
        blockers.append("No built-in presets found.")

    files = []
    seen = set()
    for source, destination in mappings:
        key = (source, destination)
        if key in seen:
            continue
        seen.add(key)
        path = contained(root, source)
        if not path.is_file():
            blockers.append("Missing payload file: " + source)
            continue
        files.append({
            "source": source,
            "destination": destination,
            "bytes": path.stat().st_size,
            "sha256": digest(path),
        })

    return {
        "purpose": "permanently noncommercial, confirmed by owner 2026-09-06",
        "mode": "planning only; no files copied",
        "release_ready": False,
        "files": files,
        "presets": presets,
        "blockers": blockers,
        "excluded": [
            "Private",
            "Activator",
            "Tools/LicenseAdmin",
            ".venv",
            ".venv-anyenhance",
            "Models (separate reviewed package)",
            "Input",
            "Output",
            "Processing",
            "License",
            "Config user data except Config/core-model-download-report.json",
            "Backups",
            "tests",
            "Vocal X.exe",
        ],
    }

def main():
    result = plan()
    target = ROOT / "Release/package-plan.json"
    target.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print("Plan created:", target)
    print("Explicit payload files:", len(result["files"]))
    print("Built-in presets checked:", len(result["presets"]))
    print("Release ready: NO (planning only)")
    for reason in result["blockers"]:
        print("OPEN:", reason)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
