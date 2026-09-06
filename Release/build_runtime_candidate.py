"""Create an isolated LOCAL validation candidate from the installed runtime.

No model weights, app data, signing tools or launcher are included. This is not
a redistributable build: dependency rights and installer verification remain open.
"""
import hashlib
import importlib.metadata as metadata
import json
import shutil
import sys
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def copy_tree(source, destination, records, exclude=()):
    for path in sorted(source.rglob('*')):
        relative = path.relative_to(source)
        if any(part in {'__pycache__', *exclude} for part in relative.parts):
            continue
        if path.is_symlink() or path.is_junction():
            raise ValueError('Linked runtime content requires review: ' + str(path))
        if not path.is_file() or path.suffix.lower() in ('.pyc', '.pth'):
            continue
        copy_file(path, destination / relative, records)

def copy_file(source, destination, records):
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, destination)
    with destination.open('rb') as stream:
        digest = hashlib.file_digest(stream, 'sha256').hexdigest()
    records.append({'path': destination.relative_to(BUILD).as_posix(),
                    'bytes': destination.stat().st_size, 'sha256': digest})

def notices(site, label, records):
    result = []
    for dist in sorted(metadata.distributions(path=[str(site)]), key=lambda d: d.metadata['Name'].lower()):
        name = dist.metadata['Name']
        texts = []
        for item in dist.files or []:
            if not any(word in item.name.lower() for word in ('license', 'licence', 'copying', 'notice')):
                continue
            source = Path(dist.locate_file(item)).resolve()
            if not source.is_relative_to(site.resolve()) or not source.is_file():
                continue
            relative = source.relative_to(site)
            target = BUILD / 'ThirdPartyNotices' / label / relative
            copy_file(source, target, records)
            texts.append(target.relative_to(BUILD).as_posix())
        result.append({'environment': label, 'name': name, 'version': dist.version,
                       'declared_license': dist.metadata.get('License-Expression') or dist.metadata.get('License'),
                       'license_files': texts, 'review_status': 'not reviewed'})
    return result

def main():
    global BUILD
    if sys.version_info[:2] != (3, 12):
        raise RuntimeError('Run with the prepared Python 3.12 environment')
    base = Path(sys.base_prefix)
    BUILD = ROOT / 'Release/Staging' / ('RuntimeCandidate-' + uuid.uuid4().hex[:12])
    BUILD.mkdir(parents=True, exist_ok=False)
    runtime = BUILD / 'Runtime'
    records = []
    print('Local candidate:', BUILD, flush=True)
    for name in ('python.exe', 'pythonw.exe', 'python3.dll', 'python312.dll',
                 'vcruntime140.dll', 'vcruntime140_1.dll', 'LICENSE.txt'):
        copy_file(base / name, runtime / name, records)
    copy_tree(base / 'DLLs', runtime / 'DLLs', records)
    copy_tree(base / 'Lib', runtime / 'Lib', records, ('site-packages', 'test', 'tests', 'idlelib', 'ensurepip'))
    dependencies = []
    for label, source, target in (
        ('main', ROOT / '.venv/Lib/site-packages', runtime / 'Lib/site-packages'),
        ('anyenhance', ROOT / '.venv-anyenhance/Lib/site-packages', runtime / 'anyenhance')):
        print('Copying and hashing:', label, flush=True)
        copy_tree(source, target, records)
        dependencies.extend(notices(source, label, records))
    # A DLL-named _pth file ignores registry/PYTHONPATH, enabling isolated mode.
    # AnyEnhance is inserted explicitly by its adapter, preserving main Qt imports.
    (runtime / 'python312._pth').write_text('.\nLib\nDLLs\nLib/site-packages\n../App\nimport site\n', encoding='utf-8')
    config = runtime / 'python312._pth'
    records.append({'path': config.relative_to(BUILD).as_posix(), 'bytes': config.stat().st_size,
                    'sha256': hashlib.sha256(config.read_bytes()).hexdigest()})
    manifest = {'status': 'LOCAL CANDIDATE ONLY', 'python': sys.version,
                'files': records, 'distributions': dependencies,
                'excluded': ['*.pth (replaced with explicit relative paths)', '__pycache__',
                             'Models', 'Private', 'App', 'user data', 'old launcher'],
                'limitations': ['Not built from downloaded hash-locked wheels',
                               'Third-party licenses collected, not legally cleared',
                               'Fresh Windows test not performed', 'Not a full app or installer']}
    (BUILD / 'runtime-manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding='utf-8')
    (ROOT / 'Release/latest-runtime-candidate.json').write_text(json.dumps({'path': BUILD.relative_to(ROOT).as_posix()}), encoding='utf-8')
    print('Files:', len(records), 'Distributions:', len(dependencies), flush=True)
    print('Collected license files:', sum(len(d['license_files']) for d in dependencies), flush=True)
    print('Runtime candidate completed. NOT RELEASE CLEARED.', flush=True)

if __name__ == '__main__':
    main()
