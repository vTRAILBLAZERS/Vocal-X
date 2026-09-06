import importlib
import json
from pathlib import Path, PureWindowsPath

def catalog(root):
    report = json.loads((Path(root)/'Config/core-model-download-report.json').read_text(encoding='utf-8-sig'))
    return {m['slug']: m for m in report['models']}

def assets(root, engine, slug):
    m = catalog(root)[slug]
    if engine != m['engine']:
        raise ValueError('Model/engine mismatch: ' + slug)
    root = Path(root).resolve()
    paths = []
    for kind in ('checkpoint','config'):
        value = PureWindowsPath(m[kind]['path'])
        # Legacy development reports are rebased at the Models boundary.
        if value.is_absolute():
            parts = value.parts
            index = next((i for i,part in enumerate(parts) if part.casefold()=='models'), None)
            if index is None:raise ValueError('Model path has no Models boundary')
            value = PureWindowsPath(*parts[index:])
        path = (root/Path(*value.parts)).resolve()
        if not path.is_relative_to(root/'Models'):raise ValueError('Model path escapes Models')
        paths.append(path)
    for p in paths:
        if not p.is_relative_to(Path(root)/'Models') or not p.is_file() or not p.stat().st_size:
            raise FileNotFoundError(str(p))
    return paths


def align_bs_chunk_size(session):
    # BS_CHUNK_ALIGNMENT_V1
    # ISTFT without explicit length returns a multiple of the model hop size.
    # Align the requested window before overlap-add; never pad missing vocals.
    from bs_roformer.backends.base import ChunkingPlan
    config = session._config
    plan = ChunkingPlan.from_config(config)
    hop = int(config.model.stft_hop_length)
    if hop <= 0:
        raise ValueError('Invalid BS STFT hop length')
    aligned = (plan.chunk_size // hop) * hop
    if aligned < max(hop, plan.num_overlap, 10):
        raise ValueError('Invalid BS chunk size')
    config.inference.chunk_size = aligned
    if aligned != plan.chunk_size:
        print(f'BS chunk alignment: {plan.chunk_size} -> {aligned} samples (hop={hop})', flush=True)

def select_stem(entries, stem):
    # Model registries differ in capitalization, not in stem semantics.
    matches = [e['output_path'] for e in entries
               if str(e.get('output_id', '')).strip().casefold() == str(stem).strip().casefold()]
    if len(matches) != 1:
        raise RuntimeError(f'Expected one stem {stem}; manifest: {entries}')
    return matches[0]

def infer(root, stage, source, target, folder):
    from .audio import read, write, resample
    engine, slug = stage['engine'], stage['model']
    module = importlib.import_module('bs_roformer' if engine == 'BS' else 'mel_band_roformer')
    cls = getattr(module, 'BSRoformerSession' if engine == 'BS' else 'MelBandRoformerSession')
    ckpt, config = assets(root, engine, slug)
    session = cls(model_name=slug, model_path=ckpt, config_path=config, device=stage['parameters'].get('device', 'cuda'), backend='torch')
    try:
        session.load()
        if engine == 'BS':
            align_bs_chunk_size(session)
        x, sr = read(source)
        model_sr = int(session._config.audio.sample_rate)
        write(folder/'input/source.wav', resample(x, sr, model_sr), model_sr)
        manifest = session.infer(folder/'input', store_dir=folder/'raw', output_format='wav_float32')
        entries = manifest.as_dict()['outputs'] if hasattr(manifest, 'as_dict') else manifest
        stem = stage['parameters'].get('stem', 'vocals' if stage['type']=='vocal_separation' else 'dry')
        y, rate = read(select_stem(entries, stem))
        y = resample(y, rate, sr)[:len(x)]
        if y.shape != x.shape:
            raise ValueError('Model changed audio shape')
        wet = stage['parameters'].get('wet', 1.0)
        write(target, x*(1-wet)+y*wet, sr)
    finally:
        session.close()
