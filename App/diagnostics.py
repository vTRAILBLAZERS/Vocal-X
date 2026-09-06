"""Bounded, redacted diagnostics. No audio or arbitrary configuration dumps."""
import json
import os
import platform
import re
from datetime import datetime, timezone
from pathlib import Path

from vocal_license import APP_VERSION, mask
from vocal_pipeline.paths import data_root
from vocal_pipeline.policy import output_root, wav_info
from vocal_pipeline.models import catalog, assets


def redact(value):
    text = str(value)
    text = re.sub(r'-----BEGIN [^-]*PRIVATE KEY-----.*?-----END [^-]*PRIVATE KEY-----', '[PRIVATE KEY REDACTED]', text, flags=re.S)
    text = re.sub(r'VX(?:LIC|REQ)1\.[A-Za-z0-9_.-]+', '[ACTIVATION REDACTED]', text)
    text = re.sub(r'VX-BETA-[A-Z0-9]{4}-[A-Z0-9]{4}-[A-Z0-9]{4}', lambda m: mask(m[0]), text, flags=re.I)
    home = os.environ.get('USERPROFILE')
    if home:
        text = re.sub(re.escape(home), '%USERPROFILE%', text, flags=re.I)
        text = re.sub(re.escape(home.replace('\\', '/')), '%USERPROFILE%', text, flags=re.I)
    return text[:12000]


def record(root, event, **fields):
    """Logging failure must never stop processing. One bounded JSON line per event."""
    allowed = {'job', 'preset', 'stage', 'model', 'status', 'duration', 'error', 'gpu', 'cuda', 'vram', 'runtime'}
    try:
        folder = data_root(root) / 'Logs'
        folder.mkdir(parents=True, exist_ok=True)
        now = datetime.now(timezone.utc)
        entry = {'timestamp': now.isoformat(), 'version': APP_VERSION, 'windows': platform.platform(), 'event': redact(event)}
        entry.update({k: redact(v) for k, v in fields.items() if k in allowed})
        with (folder / ('VocalX_' + now.strftime('%Y-%m-%d') + '.log')).open('a', encoding='utf-8') as stream:
            stream.write(json.dumps(entry, ensure_ascii=False) + '\n')
    except (OSError, ValueError):
        pass


def report(root, hardware=None, item=None):
    item = item or {}
    lines = ['=== VOCAL X DIAGNOSTIC ===', 'Created UTC: ' + datetime.now(timezone.utc).isoformat(), 'Version: ' + APP_VERSION, 'Windows: ' + platform.platform()]
    for key in ('gpu', 'cuda', 'vram', 'runtime'):
        lines.append(key + ': ' + str((hardware or {}).get(key, 'Not checked')))
    try:
        models = catalog(root)
        missing = []
        for slug, model in models.items():
            try:
                assets(root, model['engine'], slug)
            except (OSError, ValueError, KeyError):
                missing.append(slug)
        lines.append(f'Core models: {len(models)-len(missing)}/{len(models)} files present (not full hash verification)')
        lines.extend('Missing model: ' + slug for slug in missing)
    except (OSError, ValueError, KeyError):
        lines.append('Core models: inventory unavailable')
    # Report optional restoration packs separately; do not claim a core check covers them.
    for name, files in [('AnyEnhance-v1', ['model.pt', 'dac.pth']), ('AnyEnhance-360M', ['model.pt', 'dac.pth', 'w2v-bert-2.0/model.safetensors'])]:
        present = sum((Path(root) / 'Models' / name / f).is_file() for f in files)
        lines.append(f'{name}: {present}/{len(files)} weight files present (not full verification)')
    import license_service
    value, error = license_service.status(root)
    lines.append('License: ' + (mask(value['serial']) if value else 'Not active: ' + error.code))
    lines.append('Preset: ' + str(item.get('pipeline', {}).get('name', 'None selected')))
    for stage in item.get('pipeline', {}).get('stages', []):
        if stage.get('enabled'):
            lines.append('Stage: ' + str(stage.get('type')) + ' | Model: ' + str(stage.get('model') or 'DSP'))
    try:
        info = wav_info(item['source'])
        lines.append('Input WAV Validation: OK | ' + str(info['rate']) + ' Hz | ' + info['subtype'])
    except (OSError, ValueError, KeyError):
        lines.append('Input WAV Validation: unavailable or invalid')
    lines.extend(['Last operation: ' + str(item.get('status', 'None')), 'Last error: ' + str(item.get('error', 'None')), 'Install path: ' + str(Path(root).resolve()), 'User data path: ' + str(data_root(root)), 'Output path: ' + str(output_root(root)), 'Clean Windows PC test: NOT PERFORMED; unavailable', 'Audio content: NOT INCLUDED'])
    return redact('\n'.join(lines)) + '\n'


def save_report(path, root, hardware=None, item=None):
    # Exclusive creation protects an accidentally selected existing audio/file.
    with Path(path).open('x', encoding='utf-8') as stream:
        stream.write(report(root, hardware, item))
