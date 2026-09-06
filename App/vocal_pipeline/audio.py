from pathlib import Path
from math import gcd
import numpy as np
import soundfile as sf
from scipy.signal import resample_poly

def read(path):
    x, sr = sf.read(path, dtype='float32', always_2d=True)
    if not len(x) or x.shape[1] not in (1, 2) or not np.isfinite(x).all():
        raise ValueError('Audio must be nonempty, finite, mono or stereo')
    return x, sr

def resample(x, old, new):
    g = gcd(old, new)
    return resample_poly(x, new//g, old//g, axis=0).astype('float32') if old != new else x

def write(path, x, sr, flac=False):
    if not np.isfinite(x).all():
        raise ValueError('Non-finite output')
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + '.part')
    sf.write(tmp, x, sr, format='FLAC' if flac else 'WAV', subtype='PCM_24' if flac else 'FLOAT')
    tmp.replace(path)
    return path
