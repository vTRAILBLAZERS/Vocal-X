"""Executed by the candidate Python; no development imports permitted."""
import json
import os
import sys
import tempfile
from pathlib import Path

runtime = Path(sys.executable).resolve().parent
assert sys.flags.isolated and sys.flags.ignore_environment
assert Path(sys.prefix).resolve() == runtime
for entry in sys.path:
    assert Path(entry).resolve().is_relative_to(runtime.parent), entry

import numpy as np
import scipy.signal
import soundfile as sf
import cryptography
import torch
import torchaudio
import bs_roformer
import mel_band_roformer
os.environ['QT_QPA_PLATFORM'] = 'offscreen'
from PySide6.QtWidgets import QApplication, QLabel
app = QApplication([])
label = QLabel('Vocal X runtime check')
label.show()
app.processEvents()
label.close()
with tempfile.TemporaryDirectory() as folder:
    audio = Path(folder) / 'roundtrip.wav'
    signal = np.zeros((4410, 2), dtype=np.float32)
    sf.write(audio, signal, 44100, subtype='FLOAT')
    actual, sr = sf.read(audio, dtype='float32', always_2d=True)
    assert sr == 44100 and np.array_equal(actual, signal)
assert torch.cuda.is_available(), 'CUDA unavailable'
matrix = torch.eye(16, device='cuda')
assert torch.equal(matrix @ matrix, matrix)
sys.path.insert(0, str(runtime / 'anyenhance'))
import dac
import json5
import transformers
from transformers import Wav2Vec2BertModel
outside = []
for name, module in list(sys.modules.items()):
    location = getattr(module, '__file__', None)
    if location and Path(location).is_absolute() and not Path(location).resolve().is_relative_to(runtime):
        if not (name in ('__main__', '__mp_main__') and Path(location).resolve() == Path(__file__).resolve()):
            outside.append([name, location])
assert not outside, outside
print(json.dumps({'status': 'PASS', 'python': sys.version.split()[0],
                  'isolated': bool(sys.flags.isolated), 'external_modules': outside,
                  'qt': 'PASS', 'wav_float_roundtrip': 'PASS',
                  'cuda_matrix_test': 'PASS', 'gpu': torch.cuda.get_device_name(0),
                  'anyenhance_dependencies': 'PASS',
                  'full_model_audio_test': 'NOT PERFORMED',
                  'fresh_windows_test': 'NOT PERFORMED'}, indent=2))
