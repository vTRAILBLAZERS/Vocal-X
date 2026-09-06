import numpy as np
from scipy.signal import butter, sosfilt, lfilter
from .audio import read, write
from .models import infer

def execute(root, stage, source, target, folder):
    kind, p = stage['type'], stage['parameters']
    if kind == 'restoration':
        if stage['model']=='anyenhance-360m-selfcritic-v2':
            from .restoration_full import infer as restore
        else:
            from .restoration import infer as restore
        return restore(root, stage, source, target, folder)
    if kind in ('vocal_separation', 'dereverb', 'deecho'):
        infer(root, stage, source, target, folder)
        return [target]
    x, sr = read(source)
    if kind == 'deesser':
        hz = p.get('frequency_hz', 5500)
        if hz >= sr/2:
            raise ValueError('De-esser frequency exceeds Nyquist')
        high = sosfilt(butter(2, hz, fs=sr, btype='highpass', output='sos'), x, axis=0)
        a = np.exp(-1/(sr*0.01))
        envelope = np.sqrt(lfilter([1-a], [1, -a], np.max(high**2, axis=1)))
        threshold = 10**(p.get('threshold_db', -30)/20)
        gain = np.maximum(10**(-p.get('max_reduction_db', 6)/20), np.minimum(1, threshold/np.maximum(envelope, 1e-12)))
        x = x + high*(gain[:, None]-1)
    elif kind == 'cleanup':
        hz = p.get('highpass_hz', 65)
        if hz >= sr/2:
            raise ValueError('Cleanup frequency exceeds Nyquist')
        x = sosfilt(butter(2, hz, fs=sr, btype='highpass', output='sos'), x, axis=0)
    elif kind != 'export':
        raise ValueError(kind)
    outputs = [write(target, x, sr)]
    if kind=='export' and p.get('flac', False):
        # FLAC supports integer PCM only; prevent silent clipping.
        peak = float(np.max(np.abs(x)))
        outputs.append(write(target.with_suffix('.flac'), x/max(1, peak/0.999999), sr, flac=True))
    return outputs
