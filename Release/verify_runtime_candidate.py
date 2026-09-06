"""Verify every recorded candidate file and summarize collected notices."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def main():
    selected = json.loads((ROOT / 'Release/latest-runtime-candidate.json').read_text())
    build = (ROOT / selected['path']).resolve()
    if not build.is_relative_to((ROOT / 'Release/Staging').resolve()):
        raise ValueError('Candidate outside staging')
    manifest = json.loads((build / 'runtime-manifest.json').read_text(encoding='utf-8'))
    failures = []
    for entry in manifest['files']:
        path = (build / entry['path']).resolve()
        if not path.is_relative_to(build) or not path.is_file():
            failures.append(entry['path'])
            continue
        with path.open('rb') as stream:
            actual = hashlib.file_digest(stream, 'sha256').hexdigest()
        if actual != entry['sha256'] or path.stat().st_size != entry['bytes']:
            failures.append(entry['path'])
    missing_notices = [d['environment'] + ': ' + d['name'] for d in manifest['distributions'] if not d['license_files']]
    result = {'files_checked': len(manifest['files']), 'failed_files': failures,
              'payload_bytes': sum(f['bytes'] for f in manifest['files']),
              'packages_without_collected_license_file': missing_notices,
              'release_cleared': False}
    (build / 'verification.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
    print(json.dumps(result, indent=2))
    return int(bool(failures))

if __name__ == '__main__':
    raise SystemExit(main())
